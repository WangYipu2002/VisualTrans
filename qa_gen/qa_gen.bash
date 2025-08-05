# ========== Path Configuration ==========
META_OUTPUT_DIR="path/to/your/meta/output/dir"
QA_OUTPUT_DIR="path/to/your/qa/output/dir"

# ========== Run Python Script ==========

python VisualTrans/qa_gen/count.py \
    --meta_dir $META_OUTPUT_DIR \
    --output_file $QA_OUTPUT_DIR/count.json

python VisualTrans/qa_gen/spatial_global.py \
    --meta_dir $META_OUTPUT_DIR \
    --output_file $QA_OUTPUT_DIR/spatial_global.json

python VisualTrans/qa_gen/spatial_fine_grained_1.py \
    --meta_dir $META_OUTPUT_DIR \
    --output_file $QA_OUTPUT_DIR/spatial_fine_grained_1.json

python VisualTrans/qa_gen/spatial_fine_grained_2.py \
    --meta_dir $META_OUTPUT_DIR \
    --output_file $QA_OUTPUT_DIR/spatial_fine_grained_2.json

python VisualTrans/qa_gen/procedural_plan_1.py \
    --meta_dir $META_OUTPUT_DIR \
    --output_file $QA_OUTPUT_DIR/procedural_plan_1.json

python VisualTrans/qa_gen/procedural_plan_2.py \
    --meta_dir $META_OUTPUT_DIR \
    --output_file $QA_OUTPUT_DIR/procedural_plan_2.json

python VisualTrans/qa_gen/procedural_interm.py \
    --meta_dir $META_OUTPUT_DIR \
    --output_file $QA_OUTPUT_DIR/procedural_interm.json

python VisualTrans/qa_gen/procedural_causal.py \
    --meta_dir $META_OUTPUT_DIR \
    --output_file $QA_OUTPUT_DIR/procedural_causal.json