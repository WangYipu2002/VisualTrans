# VisualTrans：A Benchmark for Real-World Visual Transformation Reasoning


## Overview
VisualTrans is the first comprehensive benchmark specifically designed for Visual Transformation Reasoning (VTR) in real-world human-object interaction scenarios. 

<p align="center">
  <img src="assets/teaser.png" alt="VisualTrans Framework Overview" width="800"/>
</p>


**📄 Paper:** [VisualTrans: A Benchmark for Real-World Visual Transformation Reasoning](http://arxiv.org/abs/2508.04043)


**Key Features:**
- 🎯 **12 manipulation tasks** covering diverse real-world scenarios
- 🧠 **3 reasoning dimensions**: Spatial, Procedural, and Quantitative
- 📊 **472 high-quality QA pairs** in multiple formats
- 🔄 **End-to-end pipeline** from data processing to evaluation


## Quick Start


### Installation
```bash
# Clone the repository
git clone https://github.com/WangYipu2002/VisualTrans.git
cd VisualTrans

# Create and activate conda environment
conda create -n VisualTrans python=3.10
conda activate VisualTrans

# Install required dependencies
pip install -r requirements.txt
```

### Pipeline Overview

VisualTrans provides an end-to-end pipeline with four main components:

1. **Data Cleaning** - Filter and preprocess raw visual data
2. **Meta Annotation** - Annotate metadata
3. **Question Generation** - Synthesize reasoning questions and answers
4. **Model Evaluation** - Evaluate vision-language models 

**📌 Usage Options:**
- **Full Pipeline**: Start from Step 1 to generate your own transformation QA data  
- **Evaluation Only**: Skip directly to Step 4 if you only want to evaluate models on VisualTrans


### 1. Data Cleaning

Configure paths in `VisualTrans/filter/filter.bash` and run:

```bash
bash VisualTrans/filter/filter.bash
```

### 2. Meta Annotation 

First, download the Grounding DINO model from [HuggingFace](https://huggingface.co/IDEA-Research/grounding-dino-base).

Configure paths in `VisualTrans/meta_annotation/meta_annotation.bash` and run:

```bash
bash VisualTrans/meta_annotation/meta_annotation.bash
```

### 3. Question Generation

Configure paths in `VisualTrans/qa_gen/qa_gen.bash` and run:

```bash
bash VisualTrans/qa_gen/qa_gen.bash
```

You can write your own script to sample a specific number of QA pairs and save them as a JSON file for evaluation.

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

## Citation

If you use this framework, please cite our work:
```bibtex
@misc{ji2025visualtransbenchmarkrealworldvisual,
      title={VisualTrans: A Benchmark for Real-World Visual Transformation Reasoning}, 
      author={Yuheng Ji and Yipu Wang and Yuyang Liu and Xiaoshuai Hao and Yue Liu and Yuting Zhao and Huaihai Lyu and Xiaolong Zheng},
      year={2025},
      eprint={2508.04043},
      archivePrefix={arXiv},
      primaryClass={cs.CV},
      url={https://arxiv.org/abs/2508.04043}, 
}
```