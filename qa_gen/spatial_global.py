import json
import argparse
import random
from pathlib import Path

# Define scenes and their corresponding fixed questions
SCENE_QUESTIONS = {
    "insert_remove_bookshelf": {
        "question_template": "Has the relative left-to-right position of the three books (left, middle, right) changed?",
        "type": "multiple_choice"
    },
    "insert_remove_cups_from_rack": {
        "question_templates": [
            "Has the relative position (top-left, top-right, bottom-left, bottom-right) of the four objects changed?",
            "Has the clockwise spatial order of the four objects changed?",
            "Has the counterclockwise spatial order of the four objects changed?"
        ],
        "type": "multiple_choice"
    }
}

def get_book_colors(meta_data):
    """Extract book color information from meta data"""
    if not meta_data:
        return None, None
    
    # Get initial arrangement and final arrangement
    completed_structure = meta_data.get('completed_structure', [])
    object_position = meta_data.get('object_position', {})
    
    if not completed_structure or not object_position:
        return None, None
    
    # Get colors for left, middle, right positions
    left_color = object_position.get('left', '').lower()
    right_color = object_position.get('right', '').lower()
    
    # Infer middle position color from completed_structure
    middle_color = None
    for color in completed_structure:
        if color.lower() != left_color and color.lower() != right_color:
            middle_color = color.lower()
            break
    
    if not all([left_color, middle_color, right_color]):
        return None, None
    
    initial_arrangement = [left_color, middle_color, right_color]
    
    # Final arrangement: assume it's the order in completed_structure
    final_arrangement = [color.lower() for color in completed_structure[:3]]
    
    return initial_arrangement, final_arrangement

def generate_bookshelf_question(item):
    """Generate question for bookshelf scene"""
    # Check surface_type filter
    if item.get("surface_type", None) != "dark blue bed":
        return None
        
    initial_colors, final_colors = get_book_colors(item)
    if not initial_colors or not final_colors:
        return None
    
        # Generate detailed multiple-choice question and answer
    base_question = "Has the relative left-to-right position of the three books (left, middle, right) changed?"
        
    # Check if position changed
    position_changed = initial_colors != final_colors
        
    # Generate options
    if not position_changed:
        # Position unchanged case
        correct_arrangement = ", ".join(initial_colors)
        # Generate a wrong arrangement as distractor
        wrong_arrangement = ", ".join([initial_colors[1], initial_colors[0], initial_colors[2]])
        
        options = [
            f"A. No, the relative positions remain unchanged; the arrangement is: {correct_arrangement}.",
            f"B. No, the relative positions remain unchanged; the arrangement is: {wrong_arrangement}.",
            f"C. Yes, the relative positions have changed; the arrangement changed from {correct_arrangement} to {wrong_arrangement}.",
            f"D. Yes, the relative positions have changed; the arrangement changed from {wrong_arrangement} to {correct_arrangement}."
        ]
        correct_answer = "A"
    else:
        # Position changed case
        initial_str = ", ".join(initial_colors)
        final_str = ", ".join(final_colors)
        # Generate wrong initial arrangement as distractor
        wrong_initial = ", ".join([initial_colors[1], initial_colors[2], initial_colors[0]])
        
        options = [
            f"A. No, the relative positions remain unchanged; the arrangement is: {initial_str}.",
            f"B. No, the relative positions remain unchanged; the arrangement is: {final_str}.",
            f"C. Yes, the relative positions have changed; the arrangement changed from {initial_str} to {final_str}.",
            f"D. Yes, the relative positions have changed; the arrangement changed from {wrong_initial} to {final_str}."
        ]
        correct_answer = "C"
        
    question = base_question + "\n" + "\n".join(options)
    
    # Build image paths
    base_image_path = item['image']
    start_img = base_image_path.removesuffix('.jpg') + '_start.jpg'
    end_img = base_image_path.removesuffix('.jpg') + '_end.jpg'
        
    return {
        "task_type": "spatial_global",
        "images": [start_img, end_img],
        "scene": "insert_remove_bookshelf",
        "question": question,
        "label": correct_answer
    }

def generate_cups_question(item):
    """Generate question for cups scene"""
    # Skip data containing completed_structure
    has_completed_structure = any(
        key.startswith("completed_structure") for key in item.keys()
    )
    if has_completed_structure:
        return None
    
    # Build image paths
    base_image_path = item['image']
    start_img = base_image_path.removesuffix('.jpg') + '_start.jpg'
    end_img = base_image_path.removesuffix('.jpg') + '_end.jpg'
                
    # Randomly select a question template
    question_templates = SCENE_QUESTIONS["insert_remove_cups_from_rack"]["question_templates"]
    selected_template = random.choice(question_templates)
                
    # Generate random colors
    colors = ['red', 'green', 'blue', 'yellow']
    random.shuffle(colors)
    colors_copy = colors.copy()
    random.shuffle(colors_copy)
                
    # Generate question based on template type
    if "relative position" in selected_template:
        positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
        arr1 = ", ".join([f"{colors[i]} ({positions[i]})" for i in range(4)])
        arr2 = ", ".join([f"{colors_copy[i]} ({positions[i]})" for i in range(4)])
        from_desc = ", ".join(colors)
        to_desc = ", ".join(colors_copy)
        
        question = f"{selected_template}\n"
        question += f"A. No, the relative positions (top-left, top-right, bottom-left, bottom-right) remain unchanged; the objects are located at: {arr1}.\n"
        question += f"B. No, the relative positions (top-left, top-right, bottom-left, bottom-right) remain unchanged; the objects are located at: {arr2}.\n"
        question += f"C. Yes, the relative positions (top-left, top-right, bottom-left, bottom-right) have changed; the configuration changed from {from_desc} to {to_desc}.\n"
        question += f"D. Yes, the relative positions (top-left, top-right, bottom-left, bottom-right) have changed; the configuration changed from {to_desc} to {from_desc}."
                
    else:
        # For clockwise/counterclockwise questions
        direction = "counterclockwise" if "counterclockwise" in selected_template else "clockwise"
        arr1 = " → ".join(colors)
        arr2 = " → ".join(colors_copy)
                    
        question = f"{selected_template}\n"
        question += f"A. No, the relative positions ({direction}) remain unchanged; the arrangement is: {arr1}.\n"
        question += f"B. No, the relative positions ({direction}) remain unchanged; the arrangement is: {arr2}.\n"
        question += f"C. Yes, the relative positions ({direction}) have changed; the arrangement changed from {arr1} to {arr2}.\n"
        question += f"D. Yes, the relative positions ({direction}) have changed; the arrangement changed from {arr2} to {arr1}."
                
    # Randomly select answer
    label = random.choice(["A", "B", "C", "D"])
                
    return {
        "task_type": "spatial_global",
        "images": [start_img, end_img],
        "scene": "insert_remove_cups_from_rack",
        "question": question,
        "label": label
    }

def generate_question(item, scene):
    """Generate complete question item for a specific scene"""
    if scene == "insert_remove_bookshelf":
        return generate_bookshelf_question(item)
    elif scene == "insert_remove_cups_from_rack":
        return generate_cups_question(item)
    else:
        return None

def generate_questions(meta_dir, output_file):
    """Generate spatial global questions"""
    print("Generating spatial global questions...")
    all_questions = []
    
    for scene in SCENE_QUESTIONS.keys():
        print(f"Processing scene: {scene}")
        meta_file = meta_dir / f"{scene}_meta.jsonl"
        
        if not meta_file.exists():
            print(f"Warning: Meta file not found: {meta_file}")
            continue
                
        scene_count = 0
        with open(meta_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line)
                    question_item = generate_question(item, scene)
                    if question_item:
                        all_questions.append(question_item)
                        scene_count += 1
                except Exception as e:
                    print(f"Error processing line in file {scene}_meta.jsonl: {e} - Line: {line.strip()}")
        
        print(f"Generated {scene_count} questions for scene: {scene}")
    
    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, indent=4, ensure_ascii=False)
    print(f"Total questions generated: {len(all_questions)}")
    print(f"Results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate spatial global questions')
    parser.add_argument('--meta_dir', required=True, help='Directory containing meta files')
    parser.add_argument('--output_file', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    meta_dir = Path(args.meta_dir)
    output_file = Path(args.output_file)
    
    generate_questions(meta_dir, output_file)

if __name__ == "__main__":
    main() 