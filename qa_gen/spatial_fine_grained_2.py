import json
import random
import argparse
from pathlib import Path
from collections import Counter

# Define which scenes have explicit 'Above'/'Below' relationship data
MULTI_OBJECT_SCENES = [
    "assemble_disassemble_legos",
    "build_unstack_lego",
]

# Define which scenes have an implicit relationship based on stack order (top to bottom)
SINGLE_STACK_SCENES = [
    "stack_unstack_bowls",
    "make_sandwich",
    "insert_remove_cups_from_rack"
]

# All scenes for the combined version
SCENES = [
    "assemble_disassemble_legos",
    "build_unstack_lego", 
    "stack_unstack_bowls",
    "make_sandwich",
    "insert_remove_cups_from_rack"
]

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
    
    # Determine final state: check completed_structure_image fields first, then finish_state
    final_state = 'image2'  # default
    
    completed_structure_fields = [key for key in item.keys() if key.startswith("completed_structure_image")]
    if completed_structure_fields:
        image_number = completed_structure_fields[0].replace("completed_structure_image", "")
        final_state = f'image{image_number}'
    else:
        final_state = item.get('finish_state', 'image2')
    
    # Return (initial, final) based on which image is the final state
    if final_state == 'image1':
        return end_img_path, start_img_path  # image1 is final, so _start.jpg is final
    else:
        return start_img_path, end_img_path  # image2 is final, so _end.jpg is final

def create_open_task_item(item_meta: dict, scene: str, question: str, label: list, task_type: str) -> dict:
    """Create an open task item with proper image ordering."""
    initial_image, final_image = get_image_order(item_meta, scene)
    return {
        "task_type": task_type,
        "images": [initial_image, final_image],
        "scene": scene,
        "question": question,
        "label": ", ".join(label)
    }

def find_anchor_layer(anchor_obj_name: str, completed_structure: list, scene: str) -> int:
    """Find the layer number of anchor object in completed structure."""
    if scene in MULTI_OBJECT_SCENES:
        for obj_info in completed_structure:
            if isinstance(obj_info, dict) and obj_info.get("Object", "").strip().lower() == anchor_obj_name.strip().lower():
                return obj_info.get("Layer", -1)
    elif scene in SINGLE_STACK_SCENES:
        total_layers = len(completed_structure)
        for i, layer_objects in enumerate(completed_structure):
            layer_num = total_layers - i
            if isinstance(layer_objects, str) and layer_objects.strip().lower() == anchor_obj_name.strip().lower():
                return layer_num
    return -1

def get_above_below_objects(anchor_layer: int, completed_structure: list, scene: str) -> tuple:
    """Get objects above and below the anchor layer."""
    above_objs = []
    below_objs = []
    
    if scene in MULTI_OBJECT_SCENES:
        above_objs = [obj.get("Object") for obj in completed_structure if obj.get("Layer", 0) > anchor_layer]
        below_objs = [obj.get("Object") for obj in completed_structure if obj.get("Layer", 0) < anchor_layer]
    elif scene in SINGLE_STACK_SCENES:
        total_layers = len(completed_structure)
        for i, layer_objects in enumerate(completed_structure):
            layer_num = total_layers - i
            if layer_num > anchor_layer:
                above_objs.append(layer_objects)
            elif layer_num < anchor_layer:
                below_objs.append(layer_objects)
    
    return above_objs, below_objs

def get_object_list(item: dict, scene: str, label_objects: list = None) -> str:
    """Get the object list string for embedding in question."""
    if scene == "make_sandwich":
        # For make_sandwich, use completed_structure shuffled (no duplicates in this scene)
        object_list = item.get("completed_structure", [])
    else:
        # For other scenes, use object_list field with duplicate handling
        object_list = item.get("object_list", [])

    if object_list:
        if label_objects:
            # Check if there are duplicates in label_objects
            label_counts = Counter(label_objects)
            has_duplicates_in_label = any(count > 1 for count in label_counts.values())
            
            if has_duplicates_in_label:
                # Remove all duplicate objects from label
                valid_label_objs = [obj for obj in label_objects if label_counts[obj] == 1]
                
                # Remove all objects appearing in label_objects from object_list
                object_list_filtered = []
                for obj in object_list:
                    if obj not in label_objects:
                        object_list_filtered.append(obj)
                
                # Combine valid_label_objs and object_list_filtered
                final_objects = valid_label_objs + object_list_filtered
                return ", ".join(final_objects)
            else:
                # No duplicates in label, object_list can have duplicates but each can only appear once
                obj_counts = Counter(object_list)
                object_list_processed = []
                for obj in object_list:
                    if obj_counts[obj] == 1:
                        object_list_processed.append(obj)
                    elif obj_counts[obj] > 1 and obj not in object_list_processed:
                        # Add duplicate objects only once
                        object_list_processed.append(obj)
                return ", ".join(object_list_processed)
        else:
            # No label information, don't allow duplicates by default
            obj_counts = Counter(object_list)
            object_list_unique = [obj for obj in object_list if obj_counts[obj] == 1]
            return ", ".join(object_list_unique)

    return ""

def should_keep_single_object_question() -> bool:
    """Determine if we should keep a single-object question (30% chance)."""
    return random.random() <= 0.3

def generate_position_based_questions(item: dict, scene: str) -> list:
    """Generate position-based questions."""
    results = []
    object_positions = item.get("object_position", {})
    completed_structure = item.get("completed_structure", [])
    
    if not object_positions or not completed_structure or len(completed_structure) < 4:
        return results
    
    # Get object_list to check for duplicates
    object_list = item.get("object_list", [])
    
    positions_to_check = {
        "left": "leftmost",
        "right": "rightmost",
        "closest": "closest-to-camera"
    }
    shuffled_positions = list(positions_to_check.items())
    random.shuffle(shuffled_positions)
    
    for pos_key, pos_description in shuffled_positions:
        anchor_obj_name = object_positions.get(pos_key)
        if not anchor_obj_name or anchor_obj_name.lower() == 'none':
            continue
        
        # Check if anchor object is duplicated in object_list
        if object_list and anchor_obj_name in object_list:
            obj_count = object_list.count(anchor_obj_name)
            if obj_count > 1:
                # Skip if anchor object is duplicated
                continue
        
        # Find anchor object's layer number
        anchor_layer = find_anchor_layer(anchor_obj_name, completed_structure, scene)
        if anchor_layer == -1:
            continue
        
        # Get above and below objects
        above_objs, below_objs = get_above_below_objects(anchor_layer, completed_structure, scene)
        for rel_objs, rel_en in zip([above_objs, below_objs], ["above", "below"]):
            if not rel_objs:  # Skip if no objects in this relation
                continue
            
            # Check for duplicate objects in rel_objs
            if len(rel_objs) >= 1:  # At least one object
                obj_counts = Counter(rel_objs)
                # Remove all objects that appear more than once
                valid_objs = [obj for obj in rel_objs if obj_counts[obj] == 1]
                
                if not valid_objs:
                    # All objects are duplicated, skip this question
                    continue
                
                # If label has only one object, only keep with 30% probability
                if len(valid_objs) == 1:
                    if not should_keep_single_object_question():
                        continue
            
            # Get object list
            object_list_str = get_object_list(item, scene, rel_objs)
            if not object_list_str:
                continue
            
            # Generate question
            question = (
                f"After the transformation, list all objects that are positioned {rel_en} the object "
                f"that was originally {pos_description}, whether or not they are in direct contact."
                f" Only select from the given object list:{object_list_str}. "
                "Do not add or infer any new objects."
            )
            
            results.append(create_open_task_item(item, scene, question, valid_objs, "where_q2_absolute"))
    
    return results

def generate_relation_based_questions(item: dict, scene: str) -> list:
    """Generate relation-based questions."""
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
    
    # Generate question for each scene graph relation
    for relation_info in scene_graph:
        object1 = relation_info.get("object1", "")
        relation = relation_info.get("relation", "")
        object2 = relation_info.get("object2", "")
        
        if not object1 or not relation or not object2:
            continue
        
        # Check if anchor objects are duplicated in object_list
        if object_list:
            # Check if object1 is duplicated in object_list
            if object1 in object_list:
                obj1_count = object_list.count(object1)
                if obj1_count > 1:
                    # Skip if object1 is duplicated
                    continue
            
            # Check if object2 is duplicated in object_list
            if object2 in object_list:
                obj2_count = object_list.count(object2)
                if obj2_count > 1:
                    # Skip if object2 is duplicated
                    continue
        
        # Find object1's layer number in final structure
        anchor_layer = find_anchor_layer(object1, completed_structure, scene)
        if anchor_layer == -1:
            continue
        
        # Get above and below objects
        above_objs, below_objs = get_above_below_objects(anchor_layer, completed_structure, scene)
        # Generate questions for above and below separately
        for rel_objs, rel_en in zip([above_objs, below_objs], ["above", "below"]):
            if not rel_objs:  # Skip if no objects in this relation
                continue
                
            # Check for duplicate objects in rel_objs
            if len(rel_objs) >= 1:  # At least one object
                obj_counts = Counter(rel_objs)
                # Remove all objects that appear more than once
                valid_objs = [obj for obj in rel_objs if obj_counts[obj] == 1]
                
                if not valid_objs:
                    # All objects are duplicated, skip this question
                    continue
                
                # If label has only one object, only keep with 30% probability
                if len(valid_objs) == 1:
                    if not should_keep_single_object_question():
                        continue

            # Get object list
            object_list_str = get_object_list(item, scene, rel_objs)
            if not object_list_str:
                continue
            
            # Construct question
            relation_desc = get_relation_description(relation)
            question = (
                f"From the camera's viewpoint, after the transformation, list all objects that are "
                f"positioned {rel_en} the object that was originally {relation_desc} {object2}, "
                f"whether or not they are in direct contact. "
                f"Only select from the given object list: {object_list_str}. "
                "Do not add or infer any new objects."
            )
            
            results.append(create_open_task_item(item, scene, question, valid_objs, "spatial_fine_grained"))
    
    return results

def generate_question(item, scene):
    """Generate complete question item for a specific scene"""
    results = []
    
    # Handle position-based questions
    results.extend(generate_position_based_questions(item, scene))
    
    # Handle relation-based questions
    results.extend(generate_relation_based_questions(item, scene))
    
    return results

def generate_questions(meta_dir, output_file):
    """Generate spatial fine-grained questions (type 2)"""
    print("Generating spatial fine-grained questions (type 2)...")
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
    parser = argparse.ArgumentParser(description='Generate spatial fine-grained questions (type 2)')
    parser.add_argument('--meta_dir', required=True, help='Directory containing meta files')
    parser.add_argument('--output_file', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    meta_dir = Path(args.meta_dir)
    output_file = Path(args.output_file)
    
    generate_questions(meta_dir, output_file)

if __name__ == "__main__":
    main() 