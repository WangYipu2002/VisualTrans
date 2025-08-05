#!/bin/bash

# ========== Path Configuration ==========
BENCHMARK_PATH="path/to/your/VisualTrans.json"
IMAGE_BASE="path/to/your/image/base/dir"
RESULT_DIR="path/to/your/result/dir"

# ========== Processing Configuration ==========
MODEL_NAME=gpt-4o # choose your model to evaluate
THREADS=32

# ========== Run Evaluation ==========
python VisualTrans/eval/eval_model.py \
    --benchmark_path "$BENCHMARK_PATH" \
    --image_base "$IMAGE_BASE" \
    --result_dir "$RESULT_DIR" \
    --threads $THREADS \
    --model "$MODEL_NAME"


# ========== Calculate Scores ==========
python VisualTrans/eval/cal_score.py \
    --model "$MODEL_NAME" \
    --result_dir "$RESULT_DIR"

