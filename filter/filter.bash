#!/bin/bash

# ========== Path Configuration ==========
IMAGE_BASE_DIR="your/image/base/dir"
FILTER_BASE_DIR="your/filter/jsonl/dir"
DISCARDED_OUTPUT_DIR="your/discarded/image/dir"

# ========== Processing Configuration ==========
MAX_WORKERS=4
MODEL="o3" #your api model name
MOVE_FILTERED=true  #whether to move filtered images to filtered_out directory


# ========== Run Python Script ==========

python VisualTrans/filter/data_filter.py \
    --image_base_dir "${IMAGE_BASE_DIR}" \
    --filter_base_dir "${FILTER_BASE_DIR}" \
    --model "${MODEL}" \
    --max_workers "${MAX_WORKERS}" \
    --move_filtered "${MOVE_FILTERED}" \
    --filtered_image_dir "${DISCARDED_OUTPUT_DIR}"


