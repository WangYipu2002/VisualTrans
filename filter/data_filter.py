import base64
import os
import json
import argparse
import shutil
from pathlib import Path
from openai import OpenAI
from prompts_filter import FOOD_PROMPT, BOOKEND_PROMPT, BLOCK_PROMPT, BOWL_STACKING_PROMPT, SANDWICH_PROMPT, OTHER_PROMPT
import threading
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures


client = OpenAI(
    api_key="your_api_key",
    base_url="your_base_url",
)

# Scene to prompt mapping
def get_prompt(scene):
    if scene in ["pick_place_food"]:
        return FOOD_PROMPT
    elif scene in ["insert_remove_bookshelf"]:
        return BOOKEND_PROMPT
    elif scene in ["assemble_disassemble_legos", "build_unstack_lego", "assemble_disassemble_soft_legos"]:
        return BLOCK_PROMPT
    elif scene in ["stack_unstack_bowls"]:
        return BOWL_STACKING_PROMPT
    elif scene in ["make_sandwich"]:
        return SANDWICH_PROMPT
    else:
        return OTHER_PROMPT

# Scenes to be processed
SCENES = [
    "assemble_disassemble_legos",
    "build_unstack_lego",
    "assemble_disassemble_soft_legos",
    "stack_unstack_bowls",
    "make_sandwich",
    "insert_remove_bookshelf",
    "pick_place_food",
    "sort_beads",
    "stack_unstack_plates"
]

def initialize_scene_data(output_base_dir):
    """Initialize scene locks and read already processed image pairs"""
    # Write locks for each scene to ensure thread-safe writing
    scene_locks = {scene: threading.Lock() for scene in SCENES}

    # Pre-read already processed image pairs
    scene_done = {}
    for scene in SCENES:
        out_path = f"{output_base_dir}/{scene}_filter.jsonl"
        done = set()
        if os.path.exists(out_path):
            with open(out_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        done.add(obj["image"])
                    except Exception:
                        continue
        scene_done[scene] = done
    
    return scene_locks, scene_done

def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def process_pair(scene, prefix, start_img_path, end_img_path, output_base_dir, model_name, scene_done, scene_locks):
    image_key = os.path.join(scene, prefix)
    if image_key in scene_done[scene]:
        print(f"Skip already processed: {image_key}")
        return
    
    start_img_base64 = encode_image(start_img_path)
    end_img_base64 = encode_image(end_img_path)
    prompt = get_prompt(scene)
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{start_img_base64}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{end_img_base64}"}}
        ]}
    ]
    
    completion = client.chat.completions.create(model=model_name, messages=messages)
    reply = completion.choices[0].message.content
    
    final_answer = None
    for line in reply.splitlines():
        if line.strip().lower().startswith("#final answer:"):
            ans = line.split(":",1)[-1].strip()
            if ans:
                final_answer = ans
            else:
                idx = reply.splitlines().index(line)
                if idx+1 < len(reply.splitlines()):
                    final_answer = reply.splitlines()[idx+1].strip()
            break
    
    result = {
        "image": image_key,
        "final_answer": final_answer
    }
    
    out_path = f"{output_base_dir}/{scene}_filter.jsonl"
    os.makedirs(output_base_dir, exist_ok=True)
    
    with scene_locks[scene]:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    print(f"{scene}/{prefix} -> {final_answer}")

def process_scene(scene, image_base_dir, filter_base_dir, model_name, max_workers, scene_done, scene_locks):
    scene_dir = os.path.join(image_base_dir, scene)
    if not os.path.exists(scene_dir):
        print(f"Scene directory not found: {scene_dir}")
        return
    
    pairs = []
    for fname in os.listdir(scene_dir):
        if not fname.endswith("_start.jpg"):
            continue
        prefix = fname[:-10]
        start_img_path = os.path.join(scene_dir, prefix + "_start.jpg")
        end_img_path = os.path.join(scene_dir, prefix + "_end.jpg")
        if not os.path.exists(end_img_path):
            continue
        pairs.append((scene, prefix, start_img_path, end_img_path, filter_base_dir, model_name, scene_done, scene_locks))
    
    print(f"Processing scene {scene}: {len(pairs)} image pairs found")
    
    # Multi-threaded processing of all image pairs in this scene
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(lambda args: process_pair(*args), pairs)

def move_filtered_images(filter_base_dir, image_base_dir, output_dir):
    """Move images marked as 'no' in filtering results to output directory"""
    print("Starting to move filtered images...")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    moved_count = 0
    
    # Process all jsonl files in filter directory
    for jsonl_file in Path(filter_base_dir).glob("*_filter.jsonl"):
        print(f"Processing filter results: {jsonl_file.name}")
        
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                    
                try:
                    data = json.loads(line)
                    final_answer = data.get("final_answer", "")
                    
                    if not final_answer:
                        continue
                        
                    # Find data with final_answer "no"
                    if final_answer.strip().lower() == "no":
                        img_path = data.get("image")
                        if not img_path:
                            continue
                            
                        # Special handling for add_remove_lid
                        if "add_remove_lid" in img_path:
                            suffixes = ["_start.jpg", "_medium1.jpg", "_medium2.jpg", "_end.jpg"]
                        else:
                            suffixes = ["_start.jpg", "_end.jpg", "_medium.jpg"]
                            
                        for suffix in suffixes:
                            src_img = os.path.join(image_base_dir, img_path + suffix)
                            rel_dir = os.path.dirname(img_path)
                            target_dir = os.path.join(output_dir, rel_dir)
                            os.makedirs(target_dir, exist_ok=True)
                            target_img = os.path.join(target_dir, os.path.basename(src_img))
                            
                            if os.path.exists(target_img):
                                print(f"Already exists, skip: {target_img}")
                                continue
                                
                            if os.path.exists(src_img):
                                shutil.move(src_img, target_img)
                                print(f"Moved {src_img} -> {target_img}")
                                moved_count += 1
                            else:
                                print(f"Not found: {src_img}")
                                
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON line: {e}")
                    continue
    
    print(f"Image moving completed! Total moved: {moved_count} images")

def main():
    parser = argparse.ArgumentParser(description='Data filtering script for visual reasoning scenes')
    parser.add_argument('--image_base_dir', required=True, help='Base directory for input images')
    parser.add_argument('--filter_base_dir', required=True, help='Base directory for output filtered jsonl data')
    parser.add_argument('--filtered_image_dir', help='Directory to move filtered images')    
    parser.add_argument('--model', default='o3', help='Model name')
    parser.add_argument('--max_workers', type=int, default=4, help='Maximum number of worker threads per scene')
    parser.add_argument('--move_filtered', action='store_true', help='Move filtered images to separate directory')

    args = parser.parse_args()
    
    # Set default filtered output directory if not provided
    if args.move_filtered and not args.filtered_image_dir:
        args.filtered_image_dir = os.path.join(os.path.dirname(args.image_base_dir), "filtered_out")
    
    # Initialize scene data
    scene_locks, scene_done = initialize_scene_data(args.filter_base_dir)
    

    # Use ThreadPoolExecutor to process all scenes concurrently
    with ThreadPoolExecutor(max_workers=len(SCENES)) as executor:
        # Submit all scene processing tasks
        future_to_scene = {
            executor.submit(process_scene, scene, args.image_base_dir, args.filter_base_dir, 
                          args.model, args.max_workers, scene_done, scene_locks): scene 
            for scene in SCENES
        }
        
        # Wait for all tasks to complete and handle results
        for future in concurrent.futures.as_completed(future_to_scene):
            scene = future_to_scene[future]
            try:
                future.result()  # This will re-raise any exception that occurred
                print(f"✓ Scene {scene} completed successfully")
            except Exception as e:
                print(f"✗ Scene {scene} failed with exception: {str(e)}")
    
    print("All scenes processing completed!")
    
    # Move filtered images if requested
    if args.move_filtered:
        print("\n" + "="*50)
        move_filtered_images(args.filter_base_dir, args.image_base_dir, args.filtered_image_dir)
        print("="*50)

if __name__ == "__main__":
    main()

