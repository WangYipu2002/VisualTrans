import json
import re
from collections import defaultdict
import argparse
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

def extract_answer(text, answer_patterns):
    """Try to extract answer using multiple patterns"""
    for pattern in answer_patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    
    # Fallback: If no pattern matches, try to extract short answer from last line
    lines = text.strip().split('\n')
    if lines:
        last_line = lines[-1].strip()
        # If last line is short and might be an answer (number or single letter)
        if len(last_line) <= 10 and (last_line.isdigit() or 
                                    last_line.upper() in ['A', 'B', 'C', 'D'] or
                                ',' in last_line):  # Possible object list
            return last_line
    
    return ''

def extract_objects_from_text(text):
    """Extract object names from text"""
    # Remove common punctuation and extra spaces
    text = re.sub(r'[\[\](){}]', '', text)
    # Split and clean
    objects = [obj.strip() for obj in text.split(',') if obj.strip()]
    # Remove empty strings
    objects = [obj for obj in objects if obj]
    return objects

def normalize_objects(objects):
    """Normalize object list (deduplication, sorting)"""
    if isinstance(objects, str):
        objects = extract_objects_from_text(objects)
    # Deduplicate and sort for consistency in comparison
    return sorted(list(set(objects)))

def compare_objects(pred_objects, label_objects):
    """Compare if predicted objects and label objects are exactly the same"""
    pred_normalized = normalize_objects(pred_objects)
    label_normalized = normalize_objects(label_objects)
    return pred_normalized == label_normalized

def normalize_answer(ans):
    """Converts answer to a standardized string format (uppercase for letters)."""
    if isinstance(ans, str):
        ans = ans.strip()
        # Handle formats like "B. the middle of the bookend"
        # Extract leading letter (A, B, C, D)
        if ans and ans[0].upper() in ['A', 'B', 'C', 'D']:
            return ans[0].upper()
        return ans.upper()
    return str(ans)

def save_to_excel(model, new_task_groups, total, correct, excel_path):
    """Save results to Excel file"""
    overall_acc = correct / total if total > 0 else 0
    
    # Prepare row data
    row_data = {
        'Model': model,
        'Overall': f"{overall_acc:.2%}",
        'Quantitative': '',
        'Procedural (intermediate state recognition)': '',  
        'Procedural (latent action reasoning)': '',   
        'Procedural (transformation planning)': '',    
        'Spatial (fine-grained)': '',            
        'Spatial (global)': '',                    
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Fill task accuracies
    task_mapping = {
        'Quantitative': 'Quantitative',
        'Procedural_intermediate_state_recognition': 'Procedural (intermediate state recognition)',
        'Procedural_latent_action_reasoning': 'Procedural (latent action reasoning)',
        'Procedural_transformation_planning': 'Procedural (transformation planning)',
        'Spatial_fine_grained': 'Spatial (fine-grained)',
        'Spatial_global': 'Spatial (global)'
    }
    
    for group_name, stats in new_task_groups.items():
        if group_name in task_mapping and stats['total'] > 0:
            acc = stats['correct'] / stats['total']
            row_data[task_mapping[group_name]] = f"{acc:.2%}"
    
    # Load or create DataFrame
    try:
        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path)
            # Update existing model or add new row
            if model in df['Model'].values:
                # Convert columns to object type to allow string values
                for col in row_data.keys():
                    if col in df.columns and col != 'Model':
                        df[col] = df[col].astype('object')
                
                for col, value in row_data.items():
                    df.loc[df['Model'] == model, col] = value
            else:
                df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        else:
            df = pd.DataFrame([row_data])
        
        df.to_excel(excel_path, index=False)
        print(f"Results saved to Excel: {excel_path}")
    except Exception as e:
        print(f"Warning: Failed to save Excel file: {e}")

def get_answer_patterns():
    """Define answer extraction patterns"""
    return [
        # Original format
        re.compile(r"<answer>\s*(.*?)\s*</answer>", re.IGNORECASE | re.DOTALL),
        # GLM model various formats
        re.compile(r"<\|begin_of_box\|>\s*(.*?)\s*<\|end_of_box\|>", re.IGNORECASE | re.DOTALL),
        # Combined format: **Final answer**: <|begin_of_box|>answer<|end_of_box|>
        re.compile(r"\*\*Final answer\*\*:\s*<\|begin_of_box\|>\s*(.*?)\s*<\|end_of_box\|>", re.IGNORECASE | re.DOTALL),
        re.compile(r"\*\*Final answer\*\*:\s*(.*)", re.IGNORECASE | re.DOTALL),
        re.compile(r"Final Answer:\s*(.*)", re.IGNORECASE | re.DOTALL),
        re.compile(r"Final Anser:\s*(.*)", re.IGNORECASE | re.DOTALL),
        # Other possible formats
        re.compile(r"<start bbox>\s*(.*?)\s*</start bbox>", re.IGNORECASE | re.DOTALL),
        re.compile(r"\*\*Final answer\*\*:\s*<start bbox>\s*(.*?)\s*</start bbox>", re.IGNORECASE | re.DOTALL)
    ]

def initialize_stats():
    """Initialize statistics dictionaries"""
    task_type_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
    new_task_groups = {
        'Quantitative': {'total': 0, 'correct': 0},
        'Procedural_intermediate_state_recognition': {'total': 0, 'correct': 0},
        'Procedural_latent_action_reasoning': {'total': 0, 'correct': 0},
        'Procedural_transformation_planning': {'total': 0, 'correct': 0},
        'Spatial_fine_grained': {'total': 0, 'correct': 0},
        'Spatial_global': {'total': 0, 'correct': 0}
    }
    return task_type_stats, new_task_groups

def process_item(item, answer_patterns, item_idx):
    """Process a single evaluation item"""
    task_type = item.get('task_type', 'unknown')
    label= item.get('label', '')
    assistant = item.get('assistant', '')
    
    # Determine question type (classification/counting/object list)
    if task_type in ['count']:
        # Counting questions: numeric answer
        try:
            pred = extract_answer(assistant, answer_patterns)

            is_correct = (pred == label)
        except:
            is_correct = False
        pred = str(pred) if pred is not None else ''
    else:
        # Check if it's a multi-choice question (A, B, C, D)
        if isinstance(label, str) and label.upper() in ['A', 'B', 'C', 'D']:
            # Multiple choice question
            label = label.upper()
            pred = normalize_answer(extract_answer(assistant, answer_patterns))
            is_correct = (pred == label)
        else:

            pred_objects = extract_objects_from_text(extract_answer(assistant, answer_patterns))
            pred = ', '.join(pred_objects) if pred_objects else ''
            is_correct = compare_objects(pred_objects, label)
    
    return {
        'idx': item_idx,
        'task_type': task_type,
        'scene': item.get('scene', 'unknown'),
        'images': item.get('images', []),
        'question': item.get('question', ''),
        'label': label,
        'pred': pred,
        'is_correct': is_correct,
        'assistant': assistant
    }

def print_statistics(total, correct, new_task_groups):
    """Print statistics"""
    print(f"Total: {total}, Correct: {correct}, Overall accuracy: {correct/total:.2%}")
    for group_name, stat in new_task_groups.items():
        if stat['total'] > 0:
            acc = stat['correct'] / stat['total']
            print(f"{group_name}: {stat['correct']}/{stat['total']} ({acc:.2%})")

def process_evaluation_file(eval_path, answer_patterns):
    """Process evaluation file and return results and statistics"""
    new_task_groups = {
        'Quantitative': {'total': 0, 'correct': 0},
        'Procedural_intermediate_state_recognition': {'total': 0, 'correct': 0},
        'Procedural_latent_action_reasoning': {'total': 0, 'correct': 0},
        'Procedural_transformation_planning': {'total': 0, 'correct': 0},
        'Spatial_fine_grained': {'total': 0, 'correct': 0},
        'Spatial_global': {'total': 0, 'correct': 0}
    }
    
    results = []
    total = correct = 0
    
    with open(eval_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            total += 1
            
            result = process_item(item, answer_patterns, total)
            if result['is_correct']:
                correct += 1
            
            # Update new task groups statistics  
            task_type = result['task_type']
            group_map = {
                'count': 'Quantitative',
                'procedural_interm': 'Procedural_intermediate_state_recognition',
                'procedural_causal': 'Procedural_latent_action_reasoning', 
                'procedural_plan': 'Procedural_transformation_planning',
                'spatial_fine_grained': 'Spatial_fine_grained',
                'spatial_global': 'Spatial_global'
            }
            
            if task_type in group_map:
                group = group_map[task_type]
                new_task_groups[group]['total'] += 1
                if result['is_correct']:
                    new_task_groups[group]['correct'] += 1
            
            results.append(result)
    
    return results, total, correct, new_task_groups

def main():
    parser = argparse.ArgumentParser(description='Calculate evaluation scores')
    parser.add_argument('--model', type=str, required=True, help='Model name')
    parser.add_argument('--result_dir', type=str, required=True, help='Result directory')
    args = parser.parse_args()

    result_dir = Path(args.result_dir)
    eval_path = result_dir / f"eval_{args.model}.jsonl"
    detail_path = result_dir / f"eval_{args.model}_score_detail.json"
    excel_path = result_dir / "result.xlsx"
    
    if not eval_path.exists():
        print(f"Error: Evaluation file not found: {eval_path}")
        return 1

    answer_patterns = get_answer_patterns()
    results, total, correct, new_task_groups = process_evaluation_file(str(eval_path), answer_patterns)
    print_statistics(total, correct, new_task_groups)

    result_dir.mkdir(parents=True, exist_ok=True)
    with open(detail_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Detailed results saved to: {detail_path}")
    
    save_to_excel(args.model, new_task_groups, total, correct, str(excel_path))
    return 0

if __name__ == '__main__':
    main() 