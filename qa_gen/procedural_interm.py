"""
Generate procedural intermediate state recognition questions.
Creates multiple-choice questions to identify reasonable intermediate states.
"""
import json
import random
import argparse
from pathlib import Path

# Supported tasks/scenes
SUPPORTED_TASKS = [
    'assemble_disassemble_legos',
    'build_unstack_lego',
    'insert_remove_cups_from_rack',
    'play_reset_connect_four',
    'stack_unstack_bowls'
]

OPTIONS = ['A', 'B', 'C', 'D']

def get_object_list(meta: dict) -> list:
    """Extract and normalize object list from metadata."""
    obj_list = meta.get('object_list', None)
    if obj_list is None:
        return None
    
    # Handle LEGO-style list of dictionaries
    if isinstance(obj_list, list) and len(obj_list) > 0 and isinstance(obj_list[0], dict):
        return sorted([o['Object'] for o in obj_list if 'Object' in o])
    elif isinstance(obj_list, list):
        return sorted(obj_list)
    return None

def collect_candidate_mediums(meta_dir, scene):
    """Collect all medium image paths for a scene."""
    meta_file = meta_dir / f"{scene}_meta.jsonl"
    if not meta_file.exists():
        return {}
    
    candidates = {}
    with open(meta_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                base_name = item['image'].replace('.jpg', '')
                medium_img = f"{base_name}_medium.jpg"
                candidates[medium_img] = item
    
    return candidates

def generate_question(item, scene, all_candidates):
    """Generate complete question item for a specific scene"""
    base_name = item['image'].replace('.jpg', '')
    start_img = f"{base_name}_start.jpg"
    end_img = f"{base_name}_end.jpg"
    medium_img_true = f"{base_name}_medium.jpg"
    surface_type = item.get('surface_type', None)
    
    # Find wrong medium options with same surface type
    wrong_mediums = []
    for medium_img_path, candidate_meta in all_candidates.items():
        if medium_img_path != medium_img_true:
            if candidate_meta.get('surface_type', None) == surface_type:
                # Special requirement for bowls scene
                if scene == 'stack_unstack_bowls':
                    obj = get_object_list(candidate_meta)
                    obj_true = get_object_list(item)
                    if obj is not None and obj_true is not None and set(obj) == set(obj_true):
                        wrong_mediums.append(medium_img_path)
                else:
                    wrong_mediums.append(medium_img_path)
    
    if len(wrong_mediums) < 3:
        return None
    
    # Select 3 wrong options and mix with correct answer
    wrong_choices = random.sample(wrong_mediums, 3)
    all_mediums = [medium_img_true] + wrong_choices
    random.shuffle(all_mediums)
    correct_idx = all_mediums.index(medium_img_true)
    
    # Create question sample
    return {
        'task_type': 'procedural_interm',
        'scene': scene,
        'images': [
            start_img,
            end_img,
            all_mediums[0],
            all_mediums[1],
            all_mediums[2],
            all_mediums[3]
        ],
        'question': 'Provide additional <image3>, <image4>, <image5>, and <image6>, which represents a possible intermediate state during a manipulation task. Which one is a reasonable intermediate state during the task? \n\n Consider whether the object configuration in each candidate image reflects a plausible transition toward the finish state (<image2>). Evaluate if the operation sequence is reasonable;\nPay attention to whether any image contains structural or object states that conflict with the final state\nA. <image3>\nB. <image4>\nC. <image5>\nD. <image6>',
        'label': OPTIONS[correct_idx]
    }

def generate_questions(meta_dir, output_file):
    """Generate all intermediate state recognition questions."""
    print("Generating procedural intermediate state questions...")
    all_questions = []
    
    for scene in SUPPORTED_TASKS:
        print(f"Processing scene: {scene}")
        meta_file = meta_dir / f"{scene}_meta.jsonl"
        
        if not meta_file.exists():
            print(f"Warning: Meta file not found: {meta_file}")
            continue
        
        # Collect all candidates for this scene
        all_candidates = collect_candidate_mediums(meta_dir, scene)
        
        scene_count = 0
        with open(meta_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    question_item = generate_question(item, scene, all_candidates)
                    if question_item:
                        all_questions.append(question_item)
                        scene_count += 1
                except Exception as e:
                    print(f"Error processing line in file {scene}_meta.jsonl: {e} - Line: {line.strip()}")
        
        print(f"Generated {scene_count} questions for scene: {scene}")
    
    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)
    
    # Print statistics
    print(f"Total questions generated: {len(all_questions)}")
    print(f"Results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate procedural intermediate state questions')
    parser.add_argument('--meta_dir', required=True, help='Directory containing meta files')
    parser.add_argument('--output_file', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    meta_dir = Path(args.meta_dir)
    output_file = Path(args.output_file)
    
    generate_questions(meta_dir, output_file)

if __name__ == '__main__':
    main() 