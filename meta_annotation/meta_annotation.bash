#!/bin/bash

# ========== Path Configuration ==========
IMAGE_BASE_DIR="path/to/your/image/base/dir"
CROP_IMAGE_DIR="path/to/your/crop/image/dir"
META_OUTPUT_DIR="path/to/your/meta/output/dir"

# ========== Processing Configuration ==========
MODEL="gemini-2.5-pro"  #your api model name
MAX_SCENE_WORKERS=8
NUM_THREADS_PER_SCENE=64

# ========== crop_with_grounding_dino ==========
python VisualTrans/meta_annotation/crop_with_grounding_dino.py \
    --model_path "$GROUNDING_DINO_MODEL_PATH" \
    --image_base_dir "$IMAGE_BASE_DIR" \
    --crop_dir "$CROP_IMAGE_DIR"

# ========== add_meta_with_api ==========
python VisualTrans/meta_annotation/add_meta.py \
    --image_dir "$IMAGE_BASE_DIR" \
    --crop_dir "$CROP_IMAGE_DIR" \
    --meta_output_dir "$META_OUTPUT_DIR" \
    --model "$MODEL" \
    --num_threads_per_scene "$NUM_THREADS_PER_SCENE" \
    --max_scene_workers "$MAX_SCENE_WORKERS"
