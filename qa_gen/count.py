"""
Generate counting questions for visual reasoning tasks.
Supports pick_place_food, add_remove_lid, and sort_beads scenes.
"""
import json
import random
import argparse
from pathlib import Path

# Scene-specific question templates
SCENE_QUESTIONS = {
    "pick_place_food": [
        "How many food items are placed back into the basket?",
        "How many food items are in the plate now that were not there before?"
    ],
    "add_remove_lid": "How many paper cups had their lids added or removed?",
    "sort_beads": "How many new groups consisting of beads with the same color have been formed after the transformation?",
}

def load_meta_data(meta_dir: Path, scene: str) -> list:
    """Load and parse metadata for a specific scene."""
    meta_file = meta_dir / f"{scene}_meta.jsonl"
    if not meta_file.exists():
        print(f"Warning: Meta file not found: {meta_file}")
        return []
    
    items = []
    with open(meta_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items

def process_pick_place_food(items: list, question_pool: list) -> list:
    """Process pick_place_food scene items."""
    questions = []
    
    for item in items:
        len1 = len(item.get("plate_contents_image1", []))
        len2 = len(item.get("plate_contents_image2", []))
        abs_diff = abs(len1 - len2)
        
        # Sampling logic: skip some low-difference cases
        if abs_diff in [0, 1] and random.random() > 0.3:
            continue
        
        # Select question based on direction of change
        question = question_pool[1] if len2 > len1 else question_pool[0]
        
        # Build image paths
        base_path = item['image']
        start_path = base_path.replace('.jpg', '_start.jpg')
        end_path = base_path.replace('.jpg', '_end.jpg')
        
        questions.append({
            "task_type": "count",
            "images": [start_path, end_path],
            "scene": "pick_place_food",
            "question": question,
            "label": abs_diff
        })
    
    return questions

def process_sort_beads(items: list, question: str) -> list:
    """Process sort_beads scene items."""
    questions = []
    
    for item in items:
        # Filter by surface type
        if item.get("surface_type") != "red bed":
            continue
        
        label = item.get("number_of_groups", None)
        base_path = item['image']
        start_path = base_path.replace('.jpg', '_start.jpg')
        medium_path = base_path.replace('.jpg', '_medium.jpg')
        end_path = base_path.replace('.jpg', '_end.jpg')
        
        finish_state = item.get('finish_state', 'image2')
        
        # Add questions based on finish state
        if finish_state == 'image1':
            questions.append({
                "task_type": "count",
                "images": [end_path, start_path],
                "scene": "sort_beads",
                "question": question,
                "label": label
            })
        else:
            # Add start->end pair
            questions.append({
                "task_type": "count",
                "images": [start_path, end_path],
                "scene": "sort_beads",
                "question": question,
                "label": label
            })
            # Add medium->end pair
            questions.append({
                "task_type": "count",
                "images": [medium_path, end_path],
                "scene": "sort_beads",
                "question": question,
                "label": label
            })
    
    return questions

def process_add_remove_lid(items: list, question: str) -> list:
    """Process add_remove_lid scene items."""
    questions = []
    
    for item in items:
        base_path = item['image']
        start_path = base_path.replace('.jpg', '_start.jpg')
        end_path = base_path.replace('.jpg', '_end.jpg')
        medium1_path = base_path.replace('.jpg', '_medium1.jpg')
        medium2_path = base_path.replace('.jpg', '_medium2.jpg')
        
        # Add multiple image pair combinations
        pairs = [
            (start_path, medium2_path),
            (medium1_path, medium2_path),
            (start_path, end_path)
        ]
        
        for img1, img2 in pairs:
            questions.append({
                "task_type": "count",
                "images": [img1, img2],
                "scene": "add_remove_lid",
                "question": question
            })
    
    return questions

def generate_questions(meta_dir, output_file):
    """Generate counting questions for all supported scenes."""
    print("Generating counting questions...")
    all_questions = []
    
    for scene, question_pool in SCENE_QUESTIONS.items():
        print(f"Processing scene: {scene}")
        items = load_meta_data(meta_dir, scene)
        
        if not items:
            continue
        
        # Process scene-specific items
        if scene == "pick_place_food":
            scene_questions = process_pick_place_food(items, question_pool)
        elif scene == "sort_beads":
            scene_questions = process_sort_beads(items, question_pool)
        elif scene == "add_remove_lid":
            scene_questions = process_add_remove_lid(items, question_pool)
        else:
            continue
        
        print(f"Generated {len(scene_questions)} questions for {scene}")
        all_questions.extend(scene_questions)
    
    # Save results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, indent=4, ensure_ascii=False)
    
    print(f"Total questions generated: {len(all_questions)}")
    print(f"Results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate counting questions for visual reasoning')
    parser.add_argument('--meta_dir', required=True, help='Directory containing meta files')
    parser.add_argument('--output_file', required=True, help='Output JSON file path')
    args = parser.parse_args()
    
    meta_dir = Path(args.meta_dir)
    output_file = Path(args.output_file)
    
    generate_questions(meta_dir, output_file)

if __name__ == "__main__":
    main() 