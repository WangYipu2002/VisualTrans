"""
Object detection and cropping using Grounding DINO model.

This script performs zero-shot object detection and crops detected objects.
All paths and parameters are provided via command line arguments.
"""

import argparse
import os

import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', required=True, help='Path to the Grounding DINO model')
    parser.add_argument('--image_base_dir', required=True, help='Base directory for input images')
    parser.add_argument('--crop_dir', required=True, help='Root directory for output images')
    args = parser.parse_args()

    # Fixed configuration
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Scene and text query mapping
    SCENE_TEXT_MAPPING = {
        "build_unstack_lego": "stacked blocks",
        "assemble_disassemble_legos": "stacked blocks", 
        "stack_unstack_bowls": "stacked bowls",
        "make_sandwich": "prepared sandwich",
        "play_reset_connect_four": "Connect Four board (blue plastic grid)"
    }

    # Load model once
    print("Loading model...")
    processor = AutoProcessor.from_pretrained(args.model_path)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(args.model_path).to(device)
    print("Model loaded successfully")

    # Process each scene
    for scene_name, text_query in SCENE_TEXT_MAPPING.items():
        print(f"\nProcessing scene: {scene_name}")
        print(f"Text query: {text_query}")
        
        input_dir = os.path.join(args.image_base_dir, scene_name)
        output_dir = os.path.join(args.crop_dir, scene_name)
        
        if not os.path.exists(input_dir):
            print(f"Warning: Input directory not found: {input_dir}, skipping...")
            continue
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Define file patterns based on scene
        if scene_name == "play_reset_connect_four":
            # Process start, medium, end images
            file_patterns = ["_start.jpg", "_medium.jpg", "_end.jpg"]
        else:
            # Process only start and end images
            file_patterns = ["_start.jpg", "_end.jpg"]
        
        # Collect all image files matching the patterns
        img_files = []
        for pattern in file_patterns:
            pattern_files = [f for f in os.listdir(input_dir) if f.endswith(pattern)]
            img_files.extend(pattern_files)
        
        if not img_files:
            print(f"No matching image files found in {input_dir}")
            continue
            
        print(f"Found {len(img_files)} images to process (patterns: {file_patterns})")
        
        success_count = 0
        for fname in tqdm(img_files, desc=f"Processing {scene_name}"):
            img_path = os.path.join(input_dir, fname)
            try:
                image = Image.open(img_path)
            except Exception as e:
                print(f"Cannot open image: {img_path}, error: {e}")
                continue
                
            inputs = processor(images=image, text=text_query, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = model(**inputs)
                
            results = processor.post_process_grounded_object_detection(
                outputs,
                inputs.input_ids,
                box_threshold=0.2,
                text_threshold=0.2,
                target_sizes=[image.size[::-1]]
            )
            
            if results and len(results[0]["boxes"]) > 0:
                scores = results[0]["scores"]
                boxes = results[0]["boxes"]
                max_idx = scores.argmax().item()
                box = boxes[max_idx].tolist()
                x_min, y_min, x_max, y_max = map(int, box)
                crop = image.crop((x_min, y_min, x_max, y_max))
                save_path = os.path.join(output_dir, fname)
                crop.save(save_path)
                success_count += 1
            else:
                print(f"No objects detected: {fname}")
        
        print(f"Scene {scene_name}: {success_count}/{len(img_files)} images processed successfully")
    
    print("\nAll scenes processing completed!")
    return 0

if __name__ == "__main__":
    exit(main())
