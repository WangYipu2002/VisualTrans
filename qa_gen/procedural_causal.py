import os
import json
import random
import argparse
from pathlib import Path

# Define different types of scenes
MULTI_OBJECT_SCENES = [
    "assemble_disassemble_legos",
    "build_unstack_lego"
]
SINGLE_OBJECT_SCENES = [
    "stack_unstack_bowls",
    "make_sandwich"
]
ALL_SCENES = MULTI_OBJECT_SCENES + SINGLE_OBJECT_SCENES + ["play_reset_connect_four"]

# Define option templates for different scenes
BOWL_OPTION_TEMPLATES = [
    {"above_1": "Place the {} on the {}."},
    {"above_2": "Stack the {} on top of the {}."},
    {"above_3": "Nest the {} above the {}."},
    {"below_1": "Place the {} underneath the {}."},
    {"below_2": "Add the {} beneath the {}"}
]

LEGO_OPTION_TEMPLATES = [
    {"above_1": "Place the {} on top of the {}."},
    {"above_2": "Stack the {} over the {}."},
    {"above_3": "Add the {} piece as the next layer above the {}."},
    {"below_1": "Insert the {} underneath the {}."},
    {"below_2": "Add the {} beneath the {}"}
]

SANDWICH_OPTION_TEMPLATES = [
    {"above_1": "Place the {} on top of the {}."},
    {"above_2": "Stack the {} over the {}."},
    {"below_1": "Place the {} underneath the {}."},
]

def get_templates(scene, relation_type=None):
    """Get templates. Can filter by relation type ('above' or 'below')."""
    if "bowls" in scene or "plates" in scene:
        templates = BOWL_OPTION_TEMPLATES
    elif "sandwich" in scene:
        templates = SANDWICH_OPTION_TEMPLATES
    else:  # legos, soft_legos, etc.
        templates = LEGO_OPTION_TEMPLATES

    if relation_type:
        return [t for t in templates if list(t.keys())[0].startswith(relation_type)]
    return templates

def generate_options_for_single(obj_list, scene):
    """Generate options for single object list (string list)"""
    n = len(obj_list)
    if n < 2:
        return None, None

    # 1. Identify all correct physical relationships (obj_list[i] is on top of obj_list[i+1])
    correct_above_pairs = set()
    for i in range(n - 1):
        correct_above_pairs.add((obj_list[i], obj_list[i+1]))
    
    if not correct_above_pairs:
        return None, None

    # 2. Randomly select one operation from all valid operations (above or below) as correct answer
    possible_correct_ops = []
    for top, bottom in correct_above_pairs:
        possible_correct_ops.append({'type': 'above', 'pair': (top, bottom)})
        possible_correct_ops.append({'type': 'below', 'pair': (bottom, top)})

    chosen_correct_op = random.choice(possible_correct_ops)
    relation_type = chosen_correct_op['type']
    pair = chosen_correct_op['pair']
    
    templates = get_templates(scene, relation_type)
    if not templates:
        return None, None
    correct_template = random.choice(templates)
    correct_option = list(correct_template.values())[0].format(pair[0], pair[1])

    # 3. Generate incorrect options
    # Incorrect options come from pairs that don't describe direct physical support relationships
    all_possible_pairs = set()
    for i in range(n):
        for j in range(n):
            if i != j:
                all_possible_pairs.add((obj_list[i], obj_list[j]))
    
    # Remove all correct combinations (forward and reverse) from distractor candidate pool
    all_correct_permutations = set()
    for top, bottom in correct_above_pairs:
        all_correct_permutations.add((top, bottom))
        all_correct_permutations.add((bottom, top))

    distractor_candidate_pairs = list(all_possible_pairs - all_correct_permutations)
    if not distractor_candidate_pairs:
        return None, None  # Cannot create distractors

    random.shuffle(distractor_candidate_pairs)
    
    distractors = []
    n_options = min(n, 4)
    all_templates = get_templates(scene)
    
    for pair in distractor_candidate_pairs:
        if len(distractors) >= n_options - 1:
            break
        template = random.choice(all_templates)
        distractor_str = list(template.values())[0].format(pair[0], pair[1])
        if distractor_str != correct_option and distractor_str not in distractors:
            distractors.append(distractor_str)
            
    if len(distractors) < n_options - 1:
        return None, None

    return correct_option, distractors

def generate_options_for_multi(obj_list_data, scene):
    """Generate options for multi-object list (list of dictionaries)"""
    all_obj_names = {obj['Object'] for obj in obj_list_data}
    if len(all_obj_names) < 2:
        return None, None

    # 1. Extract all correct physical support relationships (top, bottom) from 'Below' field
    correct_above_pairs = set()
    for obj_data in obj_list_data:
        obj_on_top = obj_data['Object']
        for obj_below in obj_data.get('Below', []):
            if obj_below in all_obj_names:
                correct_above_pairs.add((obj_on_top, obj_below))

    if not correct_above_pairs:
        return None, None

    # 2. Randomly select one operation from all valid operations (above or below) as correct answer
    possible_correct_ops = []
    for top, bottom in correct_above_pairs:
        possible_correct_ops.append({'type': 'above', 'pair': (top, bottom)})
        possible_correct_ops.append({'type': 'below', 'pair': (bottom, top)})

    chosen_correct_op = random.choice(possible_correct_ops)
    relation_type = chosen_correct_op['type']
    pair = chosen_correct_op['pair']

    templates = get_templates(scene, relation_type)
    if not templates:
        return None, None
    correct_template = random.choice(templates)
    correct_option = list(correct_template.values())[0].format(pair[0], pair[1])

    # 3. Generate incorrect options
    # Incorrect options come from pairs without direct physical support relationships
    all_possible_pairs = set()
    name_list = list(all_obj_names)
    for i in range(len(name_list)):
        for j in range(len(name_list)):
            if i != j:
                all_possible_pairs.add((name_list[i], name_list[j]))
    
    # Remove all correct combinations (forward and reverse) from distractor candidate pool
    all_correct_permutations = set()
    for top, bottom in correct_above_pairs:
        all_correct_permutations.add((top, bottom))
        all_correct_permutations.add((bottom, top))

    distractor_candidate_pairs = list(all_possible_pairs - all_correct_permutations)
    if not distractor_candidate_pairs:
        return None, None

    random.shuffle(distractor_candidate_pairs)
    
    distractors = []
    n_options = min(len(all_obj_names), 4)
    all_templates = get_templates(scene)

    for pair in distractor_candidate_pairs:
        if len(distractors) >= n_options - 1:
            break
        template = random.choice(all_templates)
        distractor_str = list(template.values())[0].format(pair[0], pair[1])
        if distractor_str != correct_option and distractor_str not in distractors:
            distractors.append(distractor_str)

    if len(distractors) < n_options - 1:
        return None, None

    return correct_option, distractors

def generate_connect_four_options(meta_item):
    """Generate options for connect four scene"""
    images = []
    for k in ['disc_positions_image1', 'disc_positions_image2', 'disc_positions_image3']:
        if k in meta_item:
            images.append(meta_item[k])
    if len(images) < 2:
        return None

    pairs = []
    for i in range(len(images)):
        for j in range(len(images)):
            if i != j:
                A, B = images[i], images[j]
                if sum(len(v) for v in A.values()) < sum(len(v) for v in B.values()):
                    pairs.append((i, j, A, B))
    if not pairs:
        return None
    i, j, A, B = random.choice(pairs)

    def get_all_positions(disc_dict):
        positions = set()
        for color, lst in disc_dict.items():
            for d in lst:
                positions.add((color, d['row'], d['col']))
        return positions

    pos_A = get_all_positions(A)
    pos_B = get_all_positions(B)
    diff = list(pos_B - pos_A)
    if not diff:
        return None

    # Correct option
    correct = random.choice(diff)
    correct_option = f"Place a {correct[0]} disc in row {correct[1]}, column {correct[2]}."

    distractor_pool = set()

    # 1. Existing pieces in A
    for d in pos_A:
        distractor_pool.add(f"Place a {d[0]} disc in row {d[1]}, column {d[2]}.")

    # Generate three types of distractors based on each object in diff
    for diff_obj in diff:
        diff_color, diff_row, diff_col = diff_obj

        # 2. Different color: change color to another, position can be same or adjacent
        other_color = 'yellow' if diff_color == 'red' else 'red'
        
        # Same position different color
        if (other_color, diff_row, diff_col) not in pos_B and (other_color, diff_row, diff_col) not in diff:
            distractor_pool.add(f"Place a {other_color} disc in row {diff_row}, column {diff_col}.")
        
        # Adjacent position different color
        for delta in [-1, 1]:
            # Adjacent row
            neighbor_row = diff_row + delta
            if 1 <= neighbor_row <= 6:
                if (other_color, neighbor_row, diff_col) not in pos_B and (other_color, neighbor_row, diff_col) not in diff:
                    distractor_pool.add(f"Place a {other_color} disc in row {neighbor_row}, column {diff_col}.")
            
            # Adjacent column
            neighbor_col = diff_col + delta
            if 1 <= neighbor_col <= 7:
                if (other_color, diff_row, neighbor_col) not in pos_B and (other_color, diff_row, neighbor_col) not in diff:
                    distractor_pool.add(f"Place a {other_color} disc in row {diff_row}, column {neighbor_col}.")
        
        # 3. Adjacent cell: use diff's row/col, same color, row/col ±1
        for delta in [-1, 1]:
            # Adjacent row
            neighbor_row = diff_row + delta
            if 1 <= neighbor_row <= 6:
                if (diff_color, neighbor_row, diff_col) not in pos_B and (diff_color, neighbor_row, diff_col) not in diff:
                    distractor_pool.add(f"Place a {diff_color} disc in row {neighbor_row}, column {diff_col}.")
            
            # Adjacent column
            neighbor_col = diff_col + delta
            if 1 <= neighbor_col <= 7:
                if (diff_color, diff_row, neighbor_col) not in pos_B and (diff_color, diff_row, neighbor_col) not in diff:
                    distractor_pool.add(f"Place a {diff_color} disc in row {diff_row}, column {neighbor_col}.")
    
    # Remove correct option, sample 3 incorrect options
    distractor_pool.discard(correct_option)
    if len(distractor_pool) < 3:
        return None
    distractors = random.sample(list(distractor_pool), k=3)

    base_image_path = meta_item["image"].replace('.jpg', '')
    img_paths = [f"{base_image_path}_start.jpg", f"{base_image_path}_medium.jpg", f"{base_image_path}_end.jpg"]
    image_field = [img_paths[i], img_paths[j]]
    question_prefix = (
        "Identify which of the following operations is most likely to occur during the transformation process from <image1> to <image2>.\n"
        "(Row 1 is the bottom row; Column 1 is the leftmost column.)\n"
    )
    return correct_option, distractors, image_field, question_prefix

def generate_question(item, scene):
    """Generate complete question item for a specific scene"""
    options_labels = ['A', 'B', 'C', 'D']
    
    if scene == "play_reset_connect_four":
        options_result = generate_connect_four_options(item)
        if not options_result:
            return None
            
        correct_option, distractors, image_field, question_prefix = options_result
        options = [correct_option] + distractors
        random.shuffle(options)
        label_index = options.index(correct_option)
        label = options_labels[label_index]
        question_options = ' '.join([f"{options_labels[i]}. {options[i]}" for i in range(len(options))])
        question = f"{question_prefix}{question_options}"
        
        return {
            "task_type": "procedural_causal",
            "images": image_field,
            "scene": scene,
            "question": question,
            "label": label
        }
    else:
        # Handle other scenes
        completed_structure = item.get('completed_structure', [])
        if not completed_structure:
            return None
        
        if scene in MULTI_OBJECT_SCENES:
            options_result = generate_options_for_multi(completed_structure, scene)
        else:
            options_result = generate_options_for_single(completed_structure, scene)
        
        if not options_result:
            return None
            
        correct_option, distractors = options_result
        if not correct_option or distractors is None:
            return None
            
        options = [correct_option] + distractors
        random.shuffle(options)
        label_index = options.index(correct_option)
        label = options_labels[label_index]
        
        # Build image paths
        base_image_path = item["image"].replace('.jpg', '')
        start_img_path = f"{base_image_path}_start.jpg"
        end_img_path = f"{base_image_path}_end.jpg"
        finish_state = item.get('finish_state')
        if finish_state == 'image2':
            image_field = [start_img_path, end_img_path]
        else:
            image_field = [end_img_path, start_img_path]
            
        question_options = ' '.join([f"{options_labels[i]}. {options[i]}" for i in range(len(options))])
        question = f"Identify which of the following operations is most likely to occur during the transformation process from the <image1> to the <image2>.\n{question_options}"
        
        return {
            "task_type": "procedural_causal",
            "images": image_field,
            "scene": scene,
            "question": question,
            "label": label
        }

def generate_questions(meta_dir, output_file):
    """Generate procedural causal questions"""
    print("Generating procedural causal questions...")
    result = []

    for scene in ALL_SCENES:
        print(f"Processing scene: {scene}")
        meta_file_path = meta_dir / f"{scene}_meta.jsonl"
        if not meta_file_path.exists():
            print(f"Warning: Meta file not found for scene '{scene}', skipping. Path: {meta_file_path}")
            continue
            
        scene_count = 0
        with open(meta_file_path, 'r', encoding='utf-8') as fin:
            for line in fin:
                try:
                    item = json.loads(line)
                    question_item = generate_question(item, scene)
                    if question_item:
                        result.append(question_item)
                        scene_count += 1
                except Exception as e:
                    print(f"Error processing line in file {scene}_meta.jsonl: {e} - Line: {line.strip()}")
        
        print(f"Generated {scene_count} questions for scene: {scene}")

    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as fout:
        json.dump(result, fout, ensure_ascii=False, indent=2)
    print(f"Total questions generated: {len(result)}")
    print(f"Results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate procedural causal questions')
    parser.add_argument('--meta_dir', required=True, help='Directory containing meta files')
    parser.add_argument('--output_file', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    meta_dir = Path(args.meta_dir)
    output_file = Path(args.output_file)
    
    generate_questions(meta_dir, output_file)

if __name__ == '__main__':
    main()