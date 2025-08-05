# VisualTrans

A comprehensive framework for generating and evaluating visual transformation benchmarks across multiple task types including quantitative, procedural, and spatial transformation.

## Overview

VisualTrans provides an end-to-end pipeline for:
1. **Data Cleaning** - Filter and preprocess raw visual data
2. **Meta Annotation** - Annotate metadata and extract visual features  
3. **Question Generation** - Synthesize reasoning questions across 6 task categories
4. **Model Evaluation** - Evaluate vision-language models and generate reports


## Quick Start

### Prerequisites

**Environment Setup:**
```bash
# Create conda environment
conda create -n VisualTrans python=3.10
conda activate VisualTrans

# Install dependencies
pip install -r requirements.txt
```

If you want to use our data synthesis pipeline to generate transformation QA data, please start from here. If you only wish to evaluate VisualTrans, you can skip directly to Step 4.

### 1. Data Cleaning

Configure paths in `VisualTrans/filter/filter.bash` and run:

```bash
bash VisualTrans/filter/filter.bash
```

### 2. Meta Annotation

Configure paths in `VisualTrans/meta_annotation/meta_annotation.bash` and run:

```bash
bash VisualTrans/meta_annotation/meta_annotation.bash
```

### 3. Question Generation
First, download the model grounding-dino from huggingface 
Then, Configure paths in `VisualTrans/qa_gen/qa_gen.bash` and run:

```bash
bash VisualTrans/qa_gen/qa_gen.bash
```
You can write your own script to sample a certain number of QA pairs and save them as a JSON file

### 4. Model Evaluation

Configure paths in `VisualTrans/eval/eval.bash` and choose the model you want to evaluate:

```bash
bash VisualTrans/eval/eval.bash
```

## Configuration

Before running each step, edit the corresponding bash files to set your paths:

**VisualTrans/filter/filter.bash:**
```bash
IMAGE_BASE_DIR="path/to/your/image/base/dir"
FILTER_BASE_DIR="path/to/your/filter/jsonl/dir"
DISCARDED_OUTPUT_DIR="path/to/your/discarded/image/dir"
```

**VisualTrans/meta_annotation/meta_annotation.bash:**
```bash
IMAGE_BASE_DIR="path/to/your/image/base/dir"
CROP_IMAGE_DIR="path/to/your/crop/image/dir"
META_OUTPUT_DIR="path/to/your/meta/output/dir"
```

**VisualTrans/qa_gen/qa_gen.bash:**
```bash
IMAGE_BASE_DIR="path/to/your/image/base/dir"
META_OUTPUT_DIR="path/to/your/meta/output/dir"
```

**VisualTrans/eval/eval.bash:**
```bash
MODEL_NAME="your_model_name"
API_KEY="your_api_key"
BENCHMARK_PATH="path/to/your/VisualTrans.json"
IMAGE_BASE="path/to/your/image/base/dir"
RESULT_DIR="path/to/your/result/dir"
```

## Task Categories

The framework generates questions across 6 reasoning categories:

1. **Quantitative** - Counting and numerical reasoning
2. **Procedural (Intermediate State)** - Understanding process states
3. **Procedural (Causal Reasoning)** - Cause-effect relationships
4. **Procedural (Transformation Planning)** - Multi-step planning
5. **Spatial (Fine-grained)** - Precise spatial relationships
6. **Spatial (Global)** - Overall spatial configuration


## Citation

If you use this framework, please cite our work:
```bibtex
```


