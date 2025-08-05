import os
import json
import random
import argparse
from pathlib import Path

LIKELY_OPERATION_QUESTION = (
    "what is the most likely operation in the [MASK] step to achieve this transformation?"
)
LIKELY_OPERATION_MASKS = ["first", "last"]

SCENE_TYPES = [
    "assemble_disassemble_legos",
    "build_unstack_lego",
    "make_sandwich",
    "screw_unscrew_fingers_fixture",
]

# Simplified templates
FIRST_TEMPLATES = [
    {"": "Place the {} on the surface"},
    {"": "Add the {} to the surface"},
    {"": "Put the {} on the surface"},
]

LAST_TEMPLATES = [
    {"": "Place the {} on the {}"},
    {"": "Add the {} to the {}"},
    {"": "Put the {} on the {}"},
]

# Fixed options for screw scene
SCREW_OPTIONS = [
    "Insert the screws",
    "Place the hollow round parts",
    "Remove the screws",
    "Remove the hollow round parts"
]

def process_screw_scene(item: dict) -> dict:
    """Process screw/unscrew scene."""
    mask = random.choice(LIKELY_OPERATION_MASKS)
    options = SCREW_OPTIONS.copy()
    correct_option = random.choice(options)
    label = "None"
    
    # Build image paths and question
    image_id = item["image"]
    base_image_path = image_id.removesuffix('.jpg')
    start_img_path = f"{base_image_path}_start.jpg"
    end_img_path = f"{base_image_path}_end.jpg"
    
    finish_state = item.get("finish_state")
    # If it's a dismantling process, swap start/end images to convert to assembly process
    if finish_state == 'image1':
        image_field = [end_img_path, start_img_path]
    else:  # 'image2' and screw_fixture (which has no finish_state)
        image_field = [start_img_path, end_img_path]
    
    question = LIKELY_OPERATION_QUESTION.replace("[MASK]", mask)
    option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
    question_options = ' '.join([f"{option_labels[i]}. {options[i]}" for i in range(len(options))])
    question = f"{question}\n{question_options}"
    
    return {
        "task_type": "procedural_plan",
        "images": image_field,
        "scene": "screw_unscrew_fingers_fixture",
        "question": question,
        "label": label,
        "mask": mask
    }

def process_multi_object_scene(item: dict, scene: str) -> list:
    """Process multi-object scenes (like LEGO assembly)."""
    obj_list = item.get('completed_structure', [])
    if not obj_list:
        return []
    
    is_multi_object_scene = isinstance(obj_list[0], dict)
    n = len(obj_list)
    
    if not is_multi_object_scene or n < 2:
        return []
    
    n_options = 4  # Option limit
    results = []
    
    # Adjust first/last ratio for LEGO scenes
    if scene in ["assemble_disassemble_legos", "build_unstack_lego"]:
        # 2.5:7.5 ratio, i.e., 25% probability for first, 75% for last
        mask = random.choices(LIKELY_OPERATION_MASKS, weights=[0.25, 0.75])[0]
    else:
        mask = random.choice(LIKELY_OPERATION_MASKS)
    
    if mask == "first":
        templates = FIRST_TEMPLATES
        layer1_objs = [layer['Object'] for layer in obj_list if layer.get('Layer') == 1]
        higher_layer_objs = [layer['Object'] for layer in obj_list if layer.get('Layer', 0) > 1]

        if not layer1_objs or not higher_layer_objs:
            return []

        correct_template = random.choice(templates)
        correct_obj = random.choice(layer1_objs)
        correct_option = list(correct_template.values())[0].format(correct_obj)

        distractors = []
        num_distractors = min(n_options - 1, len(higher_layer_objs))
        
        if num_distractors > 0:
            distractor_objs_sample = random.sample(higher_layer_objs, num_distractors)
            
            for obj in distractor_objs_sample:
                template = random.choice(templates)
                option = list(template.values())[0].format(obj)
                if option not in distractors:
                    distractors.append(option)

    else:  # mask == "last"
        templates = LAST_TEMPLATES
        correct_template = random.choice(templates)
        
        # Find object with maximum Layer (top layer object)
        max_layer = max(layer.get('Layer', 0) for layer in obj_list)
        top_layer_obj = None
        for layer_info in obj_list:
            if layer_info.get('Layer') == max_layer:
                top_layer_obj = layer_info
                break
        
        if not top_layer_obj:
            return []
            
        top_obj = top_layer_obj['Object']
        # Check if Below list is empty
        if not top_layer_obj['Below']:
            return []
        obj_below = top_layer_obj['Below'][0]
        correct_option = list(correct_template.values())[0].format(top_obj, obj_below)

        distractors = []
        # For LEGO scenes, generate mutually contacting wrong options
        if scene in ["assemble_disassemble_legos", "build_unstack_lego"]:
            # Collect all contacting object pairs
            contact_pairs = []
            for layer_info in obj_list:
                if isinstance(layer_info, dict) and 'Below' in layer_info:
                    obj = layer_info['Object']
                    below_objs = layer_info['Below']
                    for below_obj in below_objs:
                        if below_obj:  # Ensure not empty string
                            contact_pairs.append((obj, below_obj))
            
            # Filter out correct answer's contact pair
            contact_pairs = [(obj1, obj2) for obj1, obj2 in contact_pairs 
                           if not (obj1 == top_obj and obj2 == obj_below)]
            
            # Generate distractor options from contact pairs
            while len(distractors) < n_options - 1 and contact_pairs:
                template = random.choice(LAST_TEMPLATES)
                obj1, obj2 = random.choice(contact_pairs)
                option = list(template.values())[0].format(obj1, obj2)
                if option not in distractors and option != correct_option:
                    distractors.append(option)
                    # Avoid reusing the same contact pair
                    contact_pairs.remove((obj1, obj2))
            
            # If not enough contact pairs, supplement with random object pairs
            all_objs = [layer['Object'] for layer in obj_list]
            while len(distractors) < n_options - 1:
                template = random.choice(LAST_TEMPLATES)
                o1, o2 = random.sample(all_objs, 2)
                if o1 == top_obj and o2 == obj_below:
                    continue
                option = list(template.values())[0].format(o1, o2)
                if option not in distractors and option != correct_option:
                    distractors.append(option)
        else:
            # Original logic for other scenes
            all_objs = [layer['Object'] for layer in obj_list]
            while len(distractors) < n_options - 1:
                template = random.choice(LAST_TEMPLATES)
                o1, o2 = random.sample(all_objs, 2)
                if o1 == top_obj and o2 == obj_below:
                    continue
                option = list(template.values())[0].format(o1, o2)
                if option not in distractors and option != correct_option:
                    distractors.append(option)

    options = distractors.copy()
    insert_pos = random.randint(0, len(options))
    options.insert(insert_pos, correct_option)
    option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
    label = option_labels[insert_pos]
    
    # Build image paths and question
    image_id = item["image"]
    base_image_path = image_id.removesuffix('.jpg')
    start_img_path = f"{base_image_path}_start.jpg"
    end_img_path = f"{base_image_path}_end.jpg"
    
    finish_state = item.get("finish_state")
    # If it's a dismantling process, swap start/end images to convert to assembly process
    if finish_state == 'image1':
        image_field = [end_img_path, start_img_path]
    else:  # 'image2'
        image_field = [start_img_path, end_img_path]
    
    question = LIKELY_OPERATION_QUESTION.replace("[MASK]", mask)
    question_options = ' '.join([f"{option_labels[i]}. {options[i]}" for i in range(len(options))])
    question = f"{question}\n{question_options}"
    
    return [{
        "task_type": "procedural_plan",
        "images": image_field,
        "scene": scene,
        "question": question,
        "label": label,
        "mask": mask
    }]

def process_single_object_scene(item: dict, scene: str) -> list:
    """Process single object scenes (like make_sandwich)."""
    obj_list = item.get('completed_structure', [])
    if not obj_list:
        return []
    
    n = len(obj_list)
    
    if n < 3 or n > 4:
        return []
    
    # Filter out paper and crayon for make_sandwich scene (case insensitive)
    if scene == 'make_sandwich' and any('paper' in obj.lower() or 'crayon' in obj.lower() for obj in obj_list):
        return []
    
    n_options = n  # Option count depends on object count
    
    # Randomly choose first or last
    mask = random.choice(LIKELY_OPERATION_MASKS)
    
    # Choose correct answer based on mask
    if mask == "first":
        # First case: use last object
        templates = FIRST_TEMPLATES
        correct_template = random.choice(templates)
        correct_option = list(correct_template.values())[0].format(obj_list[-1])
    else:
        # Last case: use first and second objects
        templates = LAST_TEMPLATES
        correct_template = random.choice(templates)
        # Check if there are enough objects
        if len(obj_list) < 2:
            return []
        correct_option = list(correct_template.values())[0].format(obj_list[0], obj_list[1])

    # Generate distractor options
    distractors = []
    if mask == "first":
        # First case distractors: use other objects
        available_objs = obj_list[:-1]  # Except last object
        while len(distractors) < n_options - 1:
            template = random.choice(FIRST_TEMPLATES)
            obj = random.choice(available_objs)
            option = list(template.values())[0].format(obj)
            if option not in distractors:
                distractors.append(option)
    else:
        # Last case distractors: use first object and other objects, or two other objects
        other_objs = obj_list[2:]  # Starting from third object
        while len(distractors) < n_options - 1:
            template = random.choice(LAST_TEMPLATES)
            if random.random() < 0.5 and other_objs:  # 50% probability to use first object
                obj1 = obj_list[0]
                obj2 = random.choice(other_objs)
            else:  # Use two other objects
                if len(other_objs) >= 2:
                    obj1, obj2 = random.sample(other_objs, 2)
                else:
                    obj1 = random.choice(other_objs)
                    obj2 = random.choice(obj_list[:2])
            option = list(template.values())[0].format(obj1, obj2)
            if option not in distractors:
                distractors.append(option)

    # Randomly insert correct option
    options = distractors.copy()
    insert_pos = random.randint(0, len(options))
    options.insert(insert_pos, correct_option)
    option_labels = ['A', 'B', 'C', 'D', 'E', 'F']
    label = option_labels[insert_pos]
    
    # Build image paths and question
    image_id = item["image"]
    base_image_path = image_id.removesuffix('.jpg')
    start_img_path = f"{base_image_path}_start.jpg"
    end_img_path = f"{base_image_path}_end.jpg"
    
    finish_state = item.get("finish_state")
    # If it's a dismantling process, swap start/end images to convert to assembly process
    if finish_state == 'image1':
        image_field = [end_img_path, start_img_path]
    else:  # 'image2'
        image_field = [start_img_path, end_img_path]
    
    question = LIKELY_OPERATION_QUESTION.replace("[MASK]", mask)
    question_options = ' '.join([f"{option_labels[i]}. {options[i]}" for i in range(len(options))])
    question = f"{question}\n{question_options}"
    
    return [{
        "task_type": "procedural_plan",
        "images": image_field,
        "scene": scene,
        "question": question,
        "label": label,
        "mask": mask
    }]

def generate_questions(meta_dir: Path, output_file: Path):
    """Generate procedural plan questions (type 1)."""
    result = []

    for scene in SCENE_TYPES:
        meta_file_path = meta_dir / f"{scene}_meta.jsonl"
        if not meta_file_path.exists():
            print(f"Warning: Meta file not found for '{scene}', skipping. Path: {meta_file_path}")
            continue
            
        with open(meta_file_path, 'r', encoding='utf-8') as fin:
            for line in fin:
                try:
                    item = json.loads(line)

                    if scene == "screw_unscrew_fingers_fixture":
                        scene_result = process_screw_scene(item)
                        result.append(scene_result)
                    else:
                        if item.get('finish_state') not in ['image1', 'image2']:
                            continue
                        
                        obj_list = item.get('completed_structure', [])
                        if not obj_list:
                            continue
                        
                        is_multi_object_scene = isinstance(obj_list[0], dict)
                        
                        if is_multi_object_scene:
                            scene_results = process_multi_object_scene(item, scene)
                        else:
                            scene_results = process_single_object_scene(item, scene)
                        
                        result.extend(scene_results)
                        
                except Exception as e:
                    print(f"Error in file {scene}: {e}")

    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as fout:
        json.dump(result, fout, ensure_ascii=False, indent=2)

    print(f"Generated data saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate procedural plan questions (type 1)')
    parser.add_argument('--meta_dir', required=True, help='Directory containing meta files')
    parser.add_argument('--output_file', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    meta_dir = Path(args.meta_dir)
    output_file = Path(args.output_file)
    
    generate_questions(meta_dir, output_file)

if __name__ == '__main__':
    main()
