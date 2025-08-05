import json
import random
import argparse
from pathlib import Path

# The scenes for which to generate questions
SCENES = [
    "assemble_disassemble_legos",
    "build_unstack_lego",
    "stack_unstack_bowls",
    "insert_remove_bookshelf",
    "insert_remove_cups_from_rack"
] 

# Define which scenes have multiple objects with explicit layer info
MULTI_OBJECT_SCENES = ["assemble_disassemble_legos", "build_unstack_lego"]
# Define which scenes have a single stack of objects (layer is implicit)
SINGLE_OBJECT_SCENES = ["stack_unstack_bowls", "stack_unstack_plates"]

def find_layer_for_object(obj_name: str, completed_structure: list, scene_type: str) -> int:
    """Find the layer number for a given object from the completed_structure."""
    if not obj_name or obj_name.lower() == 'none':
        return -1

    obj_name_clean = obj_name.strip().lower()

    if scene_type == "MULTI_OBJECT_SCENES":
        for obj_info in completed_structure:
            if isinstance(obj_info, dict) and obj_info.get("Object", "").strip().lower() == obj_name_clean:
                return obj_info.get("Layer", -1)
    
    elif scene_type == "SINGLE_OBJECT_SCENES":
        total_layers = len(completed_structure)
        for i, layer_objects in enumerate(completed_structure):
            # Layers are counted from bottom (1) to top. The completed_structure from metadata is top-to-bottom.
            layer_num = total_layers - i
            # Standardize the comparison by stripping whitespace and making it case-insensitive.
            if isinstance(layer_objects, list):
                if any(obj.strip().lower() == obj_name_clean for obj in layer_objects):
                    return layer_num
            elif isinstance(layer_objects, str):
                if layer_objects.strip().lower() == obj_name_clean:
                    return layer_num
    return -1

def get_relation_description(relation: str) -> str:
    """Convert relation to human-readable description."""
    relation_map = {
        "left": "to the left of",
        "right": "to the right of", 
        "top": "above",             
        "bottom": "below",          
        "left-top": "to the left and above",
        "right-top": "to the right and above",
        "left-bottom": "to the left and below",
        "right-bottom": "to the right and below"
    }
    return relation_map.get(relation, relation)

def get_image_order(item: dict, scene: str) -> tuple:
    """Get initial and final image paths based on data structure."""
    img_path_prefix = item["image"].removesuffix(".jpg")
    start_img_path = f"{img_path_prefix}_start.jpg"
    end_img_path = f"{img_path_prefix}_end.jpg"
    
    # Check if this is a scene with image-specific fields
    completed_structure_fields = [key for key in item.keys() if key.startswith("completed_structure_image")]
    
    if completed_structure_fields:
        # Extract number from completed_structure_image field
        field_name = completed_structure_fields[0]
        image_number = field_name.replace("completed_structure_image", "")
        
        # If completed_structure_image2, _end.jpg is final; if image1, _start.jpg is final
        if image_number == "1":
            return end_img_path, start_img_path  # _start.jpg is final
        else:
            return start_img_path, end_img_path  # _end.jpg is final
    else:
        # Use finish_state for standard scenes
        finish_state = item.get('finish_state', 'image2')
        if finish_state == 'image1':
            return end_img_path, start_img_path
        else:
            return start_img_path, end_img_path

def generate_bookshelf_questions(item: dict) -> list:
    """Generate questions for bookshelf scene."""
    results = []
    object_positions = item.get("object_position", {})
    book_list = item.get("completed_structure", []) 
    surface_type = item.get("surface_type")
    
    # Check if surface_type is "dark blue bed"
    if surface_type != "dark blue bed":
        return results
    
    if not object_positions or not book_list or not isinstance(book_list, list) or len(book_list) == 0:
        return results
        
    # Bookshelf special options
    bookshelf_options = [
        "the far left of the bookend",
        "the middle of the bookend",
        "the far right of the bookend"
    ]
    
    positions_to_check = {
        "left": "leftmost",
        "right": "rightmost",
        "closest": "closest to the camera"
    }
    
    for pos_key, pos_description in positions_to_check.items():
        book_name = object_positions.get(pos_key)
        if not book_name or book_name.lower() == 'none':
            continue
            
        # Calculate position in book_list
        try:
            book_name_clean = book_name.strip().lower()
            book_list_clean = [b.strip().lower() for b in book_list]
            final_position = book_list_clean.index(book_name_clean) + 1
        except ValueError:
            continue
            
        # Options and label
        if final_position == 1:
            correct_answer_text = bookshelf_options[0]
        elif final_position == len(book_list):
            correct_answer_text = bookshelf_options[2]
        else:
            correct_answer_text = bookshelf_options[1]
            
        answer_char = chr(ord('A') + bookshelf_options.index(correct_answer_text))
        
        # Question
        question = f"After the transformation, where is the object originally at the {pos_description} position now located?"
        question_with_options = question + "\n" + "\n".join([f"{chr(ord('A') + i)}. {opt}" for i, opt in enumerate(bookshelf_options)])
        
        # Get image paths
        initial_image, final_image = get_image_order(item, "insert_remove_bookshelf")
        
        results.append({
            "task_type": "spatial_fine_grained",
            "images": [initial_image, final_image],
            "scene": "insert_remove_bookshelf",
            "question": question_with_options,
            "label": answer_char
        })
    
    return results

def generate_absolute_based_questions(item: dict, scene: str, scene_type: str) -> list:
    """Generate absolute-based questions."""
    results = []
    object_positions = item.get("object_position", {})
    completed_structure = item.get("completed_structure", [])
    
    if not object_positions or not completed_structure:
        return results
    
    # Get object_list to check for duplicates
    object_list = item.get("object_list", [])
    
    # Position-based question mapping
    position_map = {
        "leftmost": "left",
        "rightmost": "right",
        "closest-to-camera": "closest",
    }
    
    # Check each position's object for duplicates
    valid_positions = []
    for pos_long, pos_short in position_map.items():
        # For multi-object scenes, skip the 'closest-to-camera' question
        if scene_type == "MULTI_OBJECT_SCENES" and pos_long == "closest-to-camera":
            continue

        obj_name = object_positions.get(pos_short)
        
        if not obj_name or obj_name.lower() == 'none' or 'none' in obj_name.lower():
            continue

        # Check if this object is duplicated in object_list
        if object_list and obj_name in object_list:
            obj_count = object_list.count(obj_name)
            if obj_count > 1:
                # Skip if object is duplicated
                continue
        
        valid_positions.append((pos_long, pos_short, obj_name))
    
    # If all position objects are duplicated, skip entire sample
    if not valid_positions:
        return results
    
    for pos_long, pos_short, obj_name in valid_positions:
        layer = find_layer_for_object(obj_name, completed_structure, scene_type)
        if layer != -1:
            question = f"After the transformation, which layer is the object originally at the {pos_long} position now located in?"
            
            # Get image paths
            initial_image, final_image = get_image_order(item, scene)
            
            # Generate multiple choice options
            correct_answer = layer
            options = {correct_answer}
            
            # Determine the pool of possible answers for distractors
            max_layer = 0
            if scene_type == "MULTI_OBJECT_SCENES":
                if completed_structure:
                    layers_in_scene = [d.get('Layer', 0) for d in completed_structure if isinstance(d, dict)]
                    if layers_in_scene:
                        max_layer = max(layers_in_scene)
            elif scene_type == "SINGLE_OBJECT_SCENES":
                max_layer = len(completed_structure)
            
            possible_distractors = set(range(1, max(5, max_layer + 2)))
            possible_distractors.discard(correct_answer)
            
            # Select 3 distractors
            distractors = random.sample(list(possible_distractors), 3)
            options.update(distractors)
            
            final_options = sorted(list(options))
            
            # Create question with options and find the label
            answer_char = chr(ord('A') + final_options.index(correct_answer))
            question_with_options = question + "\n" + "\n".join([f"{chr(ord('A') + i)}. Layer {opt} (from the bottom)" for i, opt in enumerate(final_options)])

            results.append({
                "task_type": "spatial_fine_grained",
                "images": [initial_image, final_image],
                "scene": scene,
                "question": question_with_options,
                "label": answer_char
            })
    
    return results

def generate_relative_based_questions(item: dict, scene: str, scene_type: str) -> list:
    """Generate relative-based questions."""
    results = []
    # Get scene graph and completed structure data
    scene_graph = item.get("scene_graph", [])
    completed_structure = item.get("completed_structure", [])
    
    # If standard format doesn't exist, look for image-specific fields
    if not scene_graph or not completed_structure:
        scene_graph_fields = [key for key in item.keys() if key.startswith("scene_graph_image")]
        completed_structure_fields = [key for key in item.keys() if key.startswith("completed_structure_image")]
        
        if scene_graph_fields and completed_structure_fields:
            scene_graph = item.get(scene_graph_fields[0], [])
            completed_structure = item.get(completed_structure_fields[0], [])
    
    # Skip if no valid data found
    if not scene_graph or not completed_structure:
        return results
    
    # Get object_list to check for duplicates
    object_list = item.get("object_list", [])
    
    # Check each relation's objects for duplicates
    valid_relations = []
    for relation_info in scene_graph:
        object1 = relation_info.get("object1", "")
        relation = relation_info.get("relation", "")
        object2 = relation_info.get("object2", "")
        
        if not object1 or not relation or not object2:
            continue
        
        # Check if object1 is duplicated in object_list
        if object_list and object1 in object_list:
            obj1_count = object_list.count(object1)
            if obj1_count > 1:
                # Skip if object1 is duplicated
                continue
        
        # Check if object2 is duplicated in object_list
        if object_list and object2 in object_list:
            obj2_count = object_list.count(object2)
            if obj2_count > 1:
                # Skip if object2 is duplicated
                continue
        
        valid_relations.append((object1, relation, object2))
    
    # If all relation objects are duplicated, skip entire sample
    if not valid_relations:
        return results
    
    # Generate question for each valid relation
    for object1, relation, object2 in valid_relations:
        # Find object1's layer number in final structure
        layer = find_layer_for_object(object1, completed_structure, scene_type)
        if layer == -1:
            continue
        
        # Construct question
        relation_desc = get_relation_description(relation)
        question = f"From the camera's viewpoint, after the transformation, which layer did the object that was originally {relation_desc} {object2} move to?"
        
        # Get image paths
        initial_image, final_image = get_image_order(item, scene)
        
        # Generate multiple choice options
        correct_answer = layer
        options = {correct_answer}
        
        # Determine the pool of possible answers for distractors
        max_layer = 0
        if scene_type == "MULTI_OBJECT_SCENES":
            if completed_structure:
                layers_in_scene = [d.get('Layer', 0) for d in completed_structure if isinstance(d, dict)]
                if layers_in_scene:
                    max_layer = max(layers_in_scene)
        elif scene_type == "SINGLE_OBJECT_SCENES":
            max_layer = len(completed_structure)
        
        possible_distractors = set(range(1, max(5, max_layer + 2)))
        possible_distractors.discard(correct_answer)
        
        # Select 3 distractors
        distractors = random.sample(list(possible_distractors), 3)
        options.update(distractors)
        
        final_options = sorted(list(options))
        
        # Create question with options and find the label
        answer_char = chr(ord('A') + final_options.index(correct_answer))
        question_with_options = question + "\n" + "\n".join([f"{chr(ord('A') + i)}. Layer {opt} (from the bottom)" for i, opt in enumerate(final_options)])

        results.append({
            "task_type": "spatial_fine_grained",
            "images": [initial_image, final_image],
            "scene": scene,
            "question": question_with_options,
            "label": answer_char
        })
    
    return results

def generate_question(item, scene):
    """Generate complete question item for a specific scene"""
    # Determine scene type
    scene_type = ""
    if scene in MULTI_OBJECT_SCENES:
        scene_type = "MULTI_OBJECT_SCENES"
    elif scene in SINGLE_OBJECT_SCENES:
        scene_type = "SINGLE_OBJECT_SCENES"
    elif scene == "insert_remove_cups_from_rack":
        scene_type = "SINGLE_OBJECT_SCENES"  # cups scene treated as single object scene
    
    results = []
    
    # Handle special bookshelf scene
    if scene == "insert_remove_bookshelf":
        results.extend(generate_bookshelf_questions(item))
    else:
        # Handle absolute-based questions
        results.extend(generate_absolute_based_questions(item, scene, scene_type))
        
        # Handle relatve-based questions
        results.extend(generate_relative_based_questions(item, scene, scene_type))
    
    return results

def generate_questions(meta_dir, output_file):
    """Generate spatial fine-grained questions (type 1)"""
    print("Generating spatial fine-grained questions (type 1)...")
    all_questions = []
    
    for scene in SCENES:
        print(f"Processing scene: {scene}")
        meta_file = meta_dir / f"{scene}_meta.jsonl"
        
        if not meta_file.exists():
            print(f"Warning: Meta file not found: {meta_file}")
            continue
        
        scene_count = 0
        with open(meta_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    line = line.strip()
                    if line and not line.startswith('//'):  # Skip empty lines and comment lines
                        item = json.loads(line)
                        question_items = generate_question(item, scene)
                        all_questions.extend(question_items)
                        scene_count += len(question_items)
                except Exception as e:
                    print(f"Error processing line in file {scene}_meta.jsonl: {e} - Line: {line[:50]}...")
        
        print(f"Generated {scene_count} questions for scene: {scene}")
    
    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, indent=4, ensure_ascii=False)
    
    print(f"Total questions generated: {len(all_questions)}")
    print(f"Results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate spatial fine-grained questions (type 1)')
    parser.add_argument('--meta_dir', required=True, help='Directory containing meta files')
    parser.add_argument('--output_file', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    meta_dir = Path(args.meta_dir)
    output_file = Path(args.output_file)
    
    generate_questions(meta_dir, output_file)

if __name__ == "__main__":
    main() 