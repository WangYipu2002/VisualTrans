import time
import logging
import os
from pathlib import Path
from typing import List, Tuple, Dict, Set
import base64
import json
import re
import concurrent.futures
from collections import OrderedDict
from prompts_meta import *
from openai import OpenAI
import ast
import argparse


client = OpenAI(
    api_key="your_api_key",
    base_url="base_url",
)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
scene_name = [
    "stack_unstack_bowls", "setup_cleanup_table", "insert_remove_bookshelf",
    "pick_place_food", "sort_beads", "insert_remove_cups_from_rack",
    "assemble_disassemble_legos", "make_sandwich", "build_unstack_lego", "play_reset_connect_four",
    "screw_unscrew_fingers_fixture","add_remove_lid"]

TWO_STAGE_SCENES = ["assemble_disassemble_legos", "stack_unstack_bowls", "stack_unstack_plates"]
NON_API_SCENES = ["screw_unscrew_fingers_fixture","add_remove_lid"]

# ====== PROMPT Distribution Definition (must be consistent with prompts.py) ======
PROMPT_STAGE1 = {
    "assemble_disassemble_legos": SYSTEM_PROMPT_LEGO1,
    "stack_unstack_bowls": SYSTEM_PROMPT_BOWL1,
    "stack_unstack_plates": SYSTEM_PROMPT_PLATE1,
}
PROMPT_STAGE2 = {
    "assemble_disassemble_legos": SYSTEM_PROMPT_LEGO2,
    "stack_unstack_bowls": SYSTEM_PROMPT_BOWL2,
    "stack_unstack_plates": SYSTEM_PROMPT_PLATE2,
}
PROMPT_SINGLE = {
    "build_unstack_lego": SYSTEM_PROMPT_BUILD_LEGO,
    "assemble_disassemble_soft_legos": SYSTEM_PROMPT_BUILD_LEGO,
    "make_sandwich": SYSTEM_PROMPT_SANDWICH,
    "setup_cleanup_table": SYSTEM_PROMPT_TABLE_CLEANUP,
    "insert_remove_bookshelf": SYSTEM_PROMPT_BOOKSHELF,
    "pick_place_food": SYSTEM_PROMPT_FOOD,
    "sort_beads": SYSTEM_PROMPT_BEADS,
    "play_reset_connect_four": SYSTEM_PROMPT_CONNECT_FOUR,
    "insert_remove_cups_from_rack": SYSTEM_PROMPT_INSERT_CUP,
}

# ========== Utility Functions ==========
def get_meta_file_path(scene_type: str, meta_output_dir: str, failed: bool = False) -> str:
    """Generate unified metadata file path"""
    suffix = "_failed.jsonl" if failed else "_meta.jsonl"
    return f"{meta_output_dir}/{scene_type}{suffix}"

def load_existing_results(scene_type: str, meta_output_dir: str) -> Dict[str, Dict]:
    result_file = get_meta_file_path(scene_type, meta_output_dir)
    results = {}
    if os.path.exists(result_file):
        with open(result_file, 'r') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    results[item['image']] = item
    return results

def save_result(scene_type: str, result: Dict, meta_output_dir: str):
    result_file = get_meta_file_path(scene_type, meta_output_dir)
    # Ensure output directory exists
    os.makedirs(os.path.dirname(result_file), exist_ok=True)
    
    ordered = OrderedDict()
    if 'image' in result:
        ordered['image'] = result['image']
        for k, v in result.items():
            if k != 'image':
                ordered[k] = v
    else:
        ordered = result
    with open(result_file, 'a') as f:
        f.write(json.dumps(ordered, ensure_ascii=False) + '\n')

def save_failed_sample(scene_type: str, image_path: str, meta_output_dir: str, error_msg: str = ""):
    """Save failed samples to dedicated jsonl file"""
    failed_file = get_meta_file_path(scene_type, meta_output_dir, failed=True)
    failed_info = {
        "scene_type": scene_type,
        "image_path": image_path,
        "error": error_msg,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(failed_file, 'a') as f:
        f.write(json.dumps(failed_info) + '\n')

def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def find_image_samples(image_dir: str, scene_type: str):
    scene_path = os.path.join(image_dir, scene_type)
    if not os.path.exists(scene_path):
        logger.warning(f"Scene directory not found: {scene_path}")
        return []
    samples = []
    for root, _, files in os.walk(scene_path):
        starts, mediums, ends = [], [], []
        for file in files:
            p = os.path.join(root, file)
            if file.endswith('start.jpg'): starts.append(p)
            elif file.endswith('medium.jpg'): mediums.append(p)
            elif file.endswith('end.jpg'): ends.append(p)
        if scene_type == "play_reset_connect_four":
            for s in starts:
                m = s.replace('start.jpg', 'medium.jpg')
                e = s.replace('start.jpg', 'end.jpg')
                if m in mediums and e in ends:
                    samples.append((s, m, e))
        else:
            for s in starts:
                e = s.replace('start.jpg', 'end.jpg')
                if e in ends:
                    samples.append((s, e))
    return samples

# ========== LLM Calling ==========
def call_llm(images, scene_type, model, crop_dir, image_dir, meta_output_dir):
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            if scene_type in TWO_STAGE_SCENES:
                start_img, end_img = images[:2]
                start_b64, end_b64 = image_to_base64(start_img), image_to_base64(end_img)
                prompt1 = PROMPT_STAGE1[scene_type]
                messages1 = [
                    #{"role": "system", "content": prompt1},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt1},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{start_b64}"}},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{end_b64}"}}
                    ]}
                ]
                completion1 = client.chat.completions.create(model=model, messages=messages1)
                response1 = completion1.choices[0].message.content
                result1 = parse_response(response1, scene_type, stage=1)
                finish_state = result1.get('finish_state', 'none')
                crop_scene_dir = os.path.join(crop_dir, scene_type)
                base_name = os.path.basename(start_img).replace('_start.jpg','').replace('_end.jpg','')
                if finish_state == 'image1':
                    crop_img = os.path.join(crop_scene_dir, f"{base_name}_start.jpg")
                elif finish_state == 'image2':
                    crop_img = os.path.join(crop_scene_dir, f"{base_name}_end.jpg")
                else:
                    crop_img = None
                result2 = {}
                if crop_img and os.path.exists(crop_img):
                    object_list = response1.split('# Object list:')[1].split('\n')[0].strip()
                    prompt2 = PROMPT_STAGE2[scene_type].format(object_list=object_list)
                    crop_img_base64 = image_to_base64(crop_img)
                    messages2 = [
                        #{"role": "system", "content": prompt2},
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt2},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{crop_img_base64}"}}
                        ]}
                    ]
                    completion2 = client.chat.completions.create(model=model, messages=messages2)
                    response2 = completion2.choices[0].message.content
                    result2 = parse_response(response2, scene_type, stage=2)
                result = {**result1, **result2}
                return result
            else:
                b64s = [image_to_base64(img) for img in images]
                messages = [
                    #{"role": "system", "content": PROMPT_SINGLE[scene_type]},
                    {"role": "user", "content": [
                        {"type": "text", "text": PROMPT_SINGLE[scene_type]},
                        *[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}} for b64 in b64s]
                    ]}
                ]
                completion = client.chat.completions.create(model=model, messages=messages)
                response = completion.choices[0].message.content
                return parse_response(response, scene_type, stage=1)
                
        except Exception as e:
            retry_count += 1
            logger.warning(f"Attempt {retry_count} failed for scene {scene_type}: {str(e)}")
            if retry_count < max_retries:
                time.sleep(2 ** retry_count)  # Exponential backoff
            else:
                # All retries failed, record failure information
                image_path = str(Path(images[0]).relative_to(image_dir)).replace('_start.jpg', '.jpg')
                if scene_type == "play_reset_connect_four":
                    image_path = str(Path(images[0]).relative_to(crop_dir)).replace('_start.jpg', '.jpg')
                save_failed_sample(scene_type, image_path, meta_output_dir, str(e))
                logger.error(f"All {max_retries} attempts failed for {image_path}")
                raise e

# ========== Result Parsing ==========
def parse_response(response: str, scene_type: str, stage: int = 1) -> Dict:
    result = {}
    # General completion image
    finish_state_match = re.search(r'# Completed image: Image (\d+)', response)
    if finish_state_match:
        result['finish_state'] = f"image{finish_state_match.group(1)}"
    
    # General hands covered
    hands_covered_match = re.search(r'# Hands_covered: (yes|no)', response)
    if hands_covered_match:
        result['hands_covered'] = hands_covered_match.group(1)
    
    # General surface type
    surface_type_match = re.search(r'# Surface type: (.*?)(?=\n#|$)', response)
    if surface_type_match:
        result['surface_type'] = surface_type_match.group(1).strip()
    
    # Parse Object list (general format)
    object_list_match = re.search(r'# Object list: \[(.*?)\]', response)
    if object_list_match:
        objects_str = object_list_match.group(1)
        object_list = [obj.strip().strip("'\"") for obj in objects_str.split(',') if obj.strip()]
        if object_list:
            result['object_list'] = object_list
    
    
    # General object position 
    position_match = re.search(r'# Position: right:(.*?), left:(.*?)(?:, closest:(.*?))?(?=\n#|$)', response)
    if position_match:
        object_position = {}
        right = position_match.group(1).strip()
        left = position_match.group(2).strip()
        closest = position_match.group(3).strip() if position_match.group(3) else None
        
        if right and 'none' not in right.lower():
            object_position['right'] = right
        if left and 'none' not in left.lower():
            object_position['left'] = left
        if closest and 'none' not in closest.lower():
            object_position['closest'] = closest
        if object_position:
            result['object_position'] = object_position
    
    # General Scene Graph parsing
    def parse_scene_graph(scene_graph_text):
        """Parse scene graph text and extract spatial relations"""
        relations = []
        # Match (object1, relation, object2) format
        pattern = r'\(([^,]+),\s*([^,]+),\s*([^)]+)\)'
        matches = re.findall(pattern, scene_graph_text)
        for match in matches:
            obj1, relation, obj2 = match
            relations.append({
                'object1': obj1.strip(),
                'relation': relation.strip(),
                'object2': obj2.strip()
            })
        return relations
    
    # Parse Scene Graph (Image 1)
    scene_graph1_match = re.search(r'# Scene graph \(Image 1\): (.*?)(?=\n#|$)', response)
    if scene_graph1_match:
        scene_graph_text = scene_graph1_match.group(1).strip()
        if scene_graph_text.lower() != 'none':
            result['scene_graph_image1'] = parse_scene_graph(scene_graph_text)
    
    # Parse Scene Graph (Image 2)
    scene_graph2_match = re.search(r'# Scene graph \(Image 2\): (.*?)(?=\n#|$)', response)
    if scene_graph2_match:
        scene_graph_text = scene_graph2_match.group(1).strip()
        if scene_graph_text.lower() != 'none':
            result['scene_graph_image2'] = parse_scene_graph(scene_graph_text)
    
    # General Scene Graph (single image)
    scene_graph_match = re.search(r'# Scene graph: (.*?)(?=\n#|$)', response, re.DOTALL)
    if scene_graph_match:
        scene_graph_text = scene_graph_match.group(1).strip()
        if scene_graph_text.lower() != 'none':
            result['scene_graph'] = parse_scene_graph(scene_graph_text)
    
    
    # Completed Structure (Image 1)
    completed_structure1_match = re.search(r'# Completed structure \(Image 1\): \[(.*?)\]', response)
    if completed_structure1_match:
        structure_text = completed_structure1_match.group(1).strip()
        result['completed_structure_image1'] =  [obj.strip().strip("'\"") for obj in structure_text.split(',') if obj.strip()]
    
    # Completed Structure (Image 2)
    completed_structure2_match = re.search(r'# Completed structure \(Image 2\): \[(.*?)\]', response)
    if completed_structure2_match:
        structure_text = completed_structure2_match.group(1).strip()
        result['completed_structure_image2'] =  [obj.strip().strip("'\"") for obj in structure_text.split(',') if obj.strip()]
    
    # General Completed Structure (single image)
    completed_structure_match = re.search(r'# Completed structure: \[(.*?)\]', response)
    if completed_structure_match:
        structure_text = completed_structure_match.group(1).strip()
        result['completed_structure'] =  [obj.strip().strip("'\"") for obj in structure_text.split(',') if obj.strip()]
    

    completed_structure = []
    completed_structure_match = re.search(r'# Completed lego structure:(.*)', response, re.DOTALL)
    if completed_structure_match:
        content = completed_structure_match.group(1).strip()
        object_blocks = re.findall(r'-\s*Object:(.*?)\n\s*Layer:(.*?)\n\s*Above:(.*?)\n\s*Below:(.*?)(?=\n-|\Z)', content, re.DOTALL)
        for block in object_blocks:
            obj_info = {
                "Object": block[0].strip(),
                "Layer": int(block[1].strip()),
                "Above": [s.strip() for s in block[2].strip().split(',')] if block[2].strip().lower() != 'none' else [],
                "Below": [s.strip() for s in block[3].strip().split(',')] if block[3].strip().lower() != 'none' else []
            }
            completed_structure.append(obj_info)
        if completed_structure:
            result['completed_structure'] = completed_structure
        
    contents1_match = re.search(r'# Plate contents \(Image 1\): \[(.*?)\]', response)
    if contents1_match:
        objects_str = contents1_match.group(1)
        result['plate_contents_image1'] = [obj.strip().strip("'\"") for obj in objects_str.split(',') if obj.strip()]

    contents2_match = re.search(r'# Plate contents \(Image 2\): \[(.*?)\]', response)
    if contents2_match:
        objects_str = contents2_match.group(1)
        result['plate_contents_image2'] = [obj.strip().strip("'\"") for obj in objects_str.split(',') if obj.strip()]
        
    num_groups_match = re.search(r'# Number of groups: (\d+)', response)
    if num_groups_match:
        result['number_of_groups'] = int(num_groups_match.group(1))

    def parse_disc_positions(text):
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        color_dict = {}
        for color in ['red', 'yellow']:
            match = re.search(rf'["\']{color}["\']\s*:\s*\[(.*?)\]', text, re.DOTALL)
            if match:
                items_str = match.group(1)
                items = []
                for obj_match in re.finditer(r'\{.*?\}', items_str):
                    obj_str = obj_match.group(0)
                    try:
                        items.append(json.loads(obj_str))
                    except Exception:
                        try:
                            items.append(ast.literal_eval(obj_str))
                        except Exception:
                            pass
                color_dict[color] = items
            else:
                color_dict[color] = []
        return color_dict
    # Disc positions(Image 1)
    disc1_match = re.search(r'# Disc positions\(Image 1\):\s*([\s\S]*?)# Disc positions\(Image 2\):', response)
    if disc1_match:
        disc1_str = disc1_match.group(1).strip()
        result['disc_positions_image1'] = parse_disc_positions(disc1_str)
    # Disc positions(Image 2)
    disc2_match = re.search(r'# Disc positions\(Image 2\):\s*([\s\S]*?)# Disc positions\(Image 3\):', response)
    if disc2_match:
        disc2_str = disc2_match.group(1).strip()
        result['disc_positions_image2'] = parse_disc_positions(disc2_str)
    # Disc positions(Image 3)
    disc3_match = re.search(r'# Disc positions\(Image 3\):\s*([\s\S]*)', response, re.DOTALL)
    if disc3_match:
        disc3_str = disc3_match.group(1).strip()
        result['disc_positions_image3'] = parse_disc_positions(disc3_str)

    return result


# ========== Sample Processing ==========
def process_samples(samples, scene_type, model, image_dir, existing_results, crop_dir, meta_output_dir, num_threads=4):
    def process_one_sample(sample):
        try:
            # First, extract start_img for path calculation
            if scene_type == "play_reset_connect_four":
                start_img, medium_img, end_img = sample
            else:
                start_img, end_img = sample
            
            rel = str(Path(start_img).relative_to(image_dir)).replace('_start.jpg', '.jpg')
            if rel in existing_results:
                return

            if scene_type == "play_reset_connect_four":
                result = call_llm((start_img, medium_img, end_img), scene_type, model, crop_dir, image_dir, meta_output_dir)
            elif scene_type in NON_API_SCENES:
                result = {"image": rel}
            else:
                result = call_llm((start_img, end_img), scene_type, model, crop_dir, image_dir, meta_output_dir)
            
            result['image'] = rel
            save_result(scene_type, result, meta_output_dir)
            
        except Exception as e:
            logger.error(f"Failed to process sample {sample}: {str(e)}")
            # Failure information is already recorded in call_llm, no need to record again here
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(process_one_sample, samples)

# ========== Main Process ==========
def process_scene(scene_type, image_dir, crop_dir, model, num_threads, meta_output_dir):
    """Function to process a single scene, used for multi-threaded calls"""
    try:
        scene_image_dir = crop_dir if scene_type == "play_reset_connect_four" else image_dir
        existing_results = load_existing_results(scene_type, meta_output_dir)
        samples = find_image_samples(scene_image_dir, scene_type)
        new_samples = [s for s in samples if (str(Path(s[0]).relative_to(scene_image_dir)).replace('_start.jpg', '.jpg') not in existing_results)]
        
        logger.info(f"{scene_type}: {len(existing_results)} existing, {len(new_samples)}/{len(samples)} new samples")
        
        if new_samples:
            process_samples(new_samples, scene_type, model, scene_image_dir, existing_results, crop_dir, meta_output_dir, num_threads=num_threads)
        
    except Exception as e:
        logger.error(f"Error processing scene {scene_type}: {str(e)}")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description='Meta annotation generation script')
    parser.add_argument('--image_dir', required=True, help='Image directory')
    parser.add_argument('--crop_dir', required=True, help='Crop directory')
    parser.add_argument('--meta_output_dir', required=True, help='Meta output directory')
    parser.add_argument('--model', default='gemini-2.5-pro', help='Model name')
    parser.add_argument('--num_threads_per_scene', type=int, default=64, help='Number of threads per scene')
    parser.add_argument('--max_scene_workers', type=int, default=8, help='Max concurrent scene workers')
    
    args = parser.parse_args()
    
    logger.info(f"Processing {len(scene_name)} scenes (max {args.max_scene_workers} concurrent, {args.num_threads_per_scene} threads each)")
    
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_scene_workers) as executor:
        future_to_scene = {
            executor.submit(process_scene, scene_type, args.image_dir, args.crop_dir, args.model, args.num_threads_per_scene, args.meta_output_dir): scene_type 
            for scene_type in scene_name
        }
        
        for future in concurrent.futures.as_completed(future_to_scene):
            scene_type = future_to_scene[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                    logger.info(f"✓ {scene_type}")
                else:
                    logger.error(f"✗ {scene_type}")
            except Exception as e:
                logger.error(f"✗ {scene_type}: {str(e)}")
    
    logger.info(f"Completed: {success_count}/{len(scene_name)} scenes successful")

if __name__ == "__main__":
    main()