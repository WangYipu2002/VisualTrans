import os
import json
import random
import argparse
from pathlib import Path

SINGLE_OBJECT_SCENES = ["make_sandwich"]
TABLE_SCENES = ["setup_cleanup_table"]

QUESTION_TEMPLATES = [
    "Which of the following objects should be manipulated first in the transformation process?",
    "Which of the following objects should be manipulated last in the transformation process?"
]

def generate_single_object_questions(item, scene):
    """Generate questions for single object scenes (like make_sandwich)"""
    results = []
    object_list = item.get('object_list', [])
    base_image_path = item["image"].removesuffix('.jpg')
    start_img_path = f"{base_image_path}_start.jpg"
    end_img_path = f"{base_image_path}_end.jpg"
    
    # Cannot sample 0th and last two objects, and remove duplicates
    unique_objs = list(dict.fromkeys(object_list[1:-1]))
    if len(unique_objs) < 1:
        return results
        
    if len(unique_objs) <= 4:
        sampled_objs = unique_objs
    else:
        sampled_objs = random.sample(unique_objs, 4)
    
    # First question (label is the object with the highest index among sampled objects)
    question = QUESTION_TEMPLATES[0]
    options = sampled_objs.copy()
    random.shuffle(options)
    
    # First: label is the one with highest index
    max_idx = -1
    label_obj = None
    for obj in options:
        idx = max([i for i, o in enumerate(object_list) if o == obj])
        if idx > max_idx:
            max_idx = idx
            label_obj = obj
    
    label = chr(ord('A') + options.index(label_obj))
    question_str = question + '\n' + '\n'.join([f"{chr(ord('A')+i)}. {opt}" for i, opt in enumerate(options)])
    
    results.append({
        "task_type": "procedural_plan",
        "images": [start_img_path, end_img_path],
        "scene": scene,
        "question": question_str,
        "label": label
    })
    
    # Last question (label is the object with the lowest index among sampled objects)
    question = QUESTION_TEMPLATES[1]
    options2 = sampled_objs.copy()
    random.shuffle(options2)
    
    min_idx = float('inf')
    label_obj2 = None
    for obj in options2:
        idx = min([i for i, o in enumerate(object_list) if o == obj])
        if idx < min_idx:
            min_idx = idx
            label_obj2 = obj
    
    label2 = chr(ord('A') + options2.index(label_obj2))
    question_str2 = question + '\n' + '\n'.join([f"{chr(ord('A')+i)}. {opt}" for i, opt in enumerate(options2)])
    
    results.append({
        "task_type": "procedural_plan",
        "images": [start_img_path, end_img_path],
        "scene": scene,
        "question": question_str2,
        "label": label2
    })
    
    return results

def generate_table_questions(item, scene):
    """Generate questions for table scenes (like setup_cleanup_table)"""
    results = []
    object_list = item.get('object_list', [])
    finish_state = item.get('finish_state', 'image2')
    base_image_path = item["image"].removesuffix('.jpg')
    start_img_path = f"{base_image_path}_start.jpg"
    end_img_path = f"{base_image_path}_end.jpg"
    
    tablecloth_objs = [obj for obj in object_list if 'tablecloth' in obj]
    other_objs = [obj for obj in object_list if 'tablecloth' not in obj]
    
    if len(tablecloth_objs) == 0 or len(other_objs) == 0:
        return results
    
    # Sample 3 non-tablecloth + 1 tablecloth
    if len(other_objs) >= 3:
        sampled_others = random.sample(other_objs, 3)
    else:
        sampled_others = other_objs
    options_4 = tablecloth_objs[:1] + sampled_others
    random.shuffle(options_4)
    
    # Sample 1 non-tablecloth + 1 tablecloth
    options_2 = random.sample(other_objs, 1) + tablecloth_objs[:1]
    random.shuffle(options_2)
    
    if finish_state == 'image2':
        # First: four choices, label is tablecloth
        question = QUESTION_TEMPLATES[0]
        label = chr(ord('A') + options_4.index(tablecloth_objs[0]))
        question_str = question + '\n' + '\n'.join([f"{chr(ord('A')+i)}. {opt}" for i, opt in enumerate(options_4)])
        
        results.append({
            "task_type": "procedural_plan",
            "images": [start_img_path, end_img_path],
            "scene": scene,
            "question": question_str,
            "label": label
        })
        
        # Last: two choices, label is non-tablecloth
        question = QUESTION_TEMPLATES[1]
        non_tablecloth = [o for o in options_2 if 'tablecloth' not in o][0]
        label2 = chr(ord('A') + options_2.index(non_tablecloth))
        question_str2 = question + '\n' + '\n'.join([f"{chr(ord('A')+i)}. {opt}" for i, opt in enumerate(options_2)])
        
        results.append({
            "task_type": "procedural_plan",
            "images": [start_img_path, end_img_path],
            "scene": scene,
            "question": question_str2,
            "label": label2
        })
        
    elif finish_state == 'image1':
        # First: two choices, label is non-tablecloth
        question = QUESTION_TEMPLATES[0]
        non_tablecloth = [o for o in options_2 if 'tablecloth' not in o][0]
        label = chr(ord('A') + options_2.index(non_tablecloth))
        question_str = question + '\n' + '\n'.join([f"{chr(ord('A')+i)}. {opt}" for i, opt in enumerate(options_2)])
        
        results.append({
            "task_type": "procedural_plan",
            "images": [start_img_path, end_img_path],
            "scene": scene,
            "question": question_str,
            "label": label
        })
        
        # Last: four choices, label is tablecloth
        question = QUESTION_TEMPLATES[1]
        label2 = chr(ord('A') + options_4.index(tablecloth_objs[0]))
        question_str2 = question + '\n' + '\n'.join([f"{chr(ord('A')+i)}. {opt}" for i, opt in enumerate(options_4)])
        
        results.append({
            "task_type": "procedural_plan",
            "images": [start_img_path, end_img_path],
            "scene": scene,
            "question": question_str2,
            "label": label2
        })
    
    return results

def generate_question(item, scene):
    """Generate complete question item for a specific scene"""
    if scene in SINGLE_OBJECT_SCENES:
        return generate_single_object_questions(item, scene)
    elif scene in TABLE_SCENES:
        return generate_table_questions(item, scene)
    else:
        return []

def generate_questions(meta_dir, output_file):
    """Generate procedural plan questions (type 2)"""
    print("Generating procedural plan questions (type 2)...")
    scene_types = SINGLE_OBJECT_SCENES + TABLE_SCENES
    result = []
    
    for scene in scene_types:
        print(f"Processing scene: {scene}")
        meta_file_path = meta_dir / f"{scene}_meta.jsonl"
        if not meta_file_path.exists():
            print(f"Warning: Meta file not found for '{scene}', skipping. Path: {meta_file_path}")
            continue

        scene_count = 0
        with open(meta_file_path, 'r', encoding='utf-8') as fin:
            for line in fin:
                try:
                    item = json.loads(line)
                    question_items = generate_question(item, scene)
                    result.extend(question_items)
                    scene_count += len(question_items)
                except Exception as e:
                    print(f"Error processing line in {scene}: {e} - Line: {line.strip()}")
        
        print(f"Generated {scene_count} questions for scene: {scene}")

    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as fout:
        json.dump(result, fout, ensure_ascii=False, indent=2)
    print(f"Total questions generated: {len(result)}")
    print(f"Results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate procedural plan questions (type 2)')
    parser.add_argument('--meta_dir', required=True, help='Directory containing meta files')
    parser.add_argument('--output_file', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    meta_dir = Path(args.meta_dir)
    output_file = Path(args.output_file)
    
    generate_questions(meta_dir, output_file)

if __name__ == '__main__':
    main() 