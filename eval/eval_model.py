import requests
import base64
import os
import json
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

SYSTEM_PROMPT = """
I will show you two images:

<image1>: Initial state (scene before the task)  
<image2>: Transformed state (final state after task completion)

Your job is to understand the visual transformation between the two images and answer the following question.

There are 3 types of questions:
1. **Multiple choice**: You must output only the corresponding **option letter** (e.g., A, B, C...) as the final answer.
2. **Open-ended numeric**: You must output only the **number** (e.g., 2, 5, 13).
3. **Object enumeration**: You must output only a **comma-separated list of object names** (e.g., red block, green cup). If no objects match, respond with `none`.

### Output Format  
You should first think through the reasoning process internally, and then provide the user with the answer.  
The **reasoning process** and **final answer** must be enclosed within specific tags:

- **Reasoning process**: Enclosed within <think>...</think>  
- **Final answer**: Enclosed within <answer>...</answer>

### Examples:

1. **Multiple choice question**  
**Question**: Provided <image3> is a candidate state (potential intermediate state during the task). Is <image3> a reasonable intermediate step?  
A) Yes  
B) No  

**Response**:  
<think>In the third image, the red cup has already been moved into the basket, but the blue bowl remains unmoved. This matches a likely intermediate stage in the process.</think>  
<answer>A</answer>

2. **Open-ended numeric question**  
**Question**: How many cups changed their state during the transformation?  

**Response**:  
<think>In Image 1, there are 3 cups on the table. In Image 2, one cup is flipped, one is placed inside the basket, and one remains the same. So, two cups have changed their state.</think>  
<answer>2</answer>

3. **Object enumeration question**  
**Question**: After the transformation, list all objects that are positioned above the object that was originally to the left of the blue block.  
Please answer by selecting from the following object list: red block, white block, green block, blue block.  

**Response**:  
<think>The red block was originally to the left of the blue block. In Image 2, both the white block and green block appear vertically above its final position. The blue block is at the same layer. Therefore, white and green blocks are valid answers.</think>  
<answer>white block, green block</answer>
"""
client = OpenAI(
        api_key="your_api_key",
        base_url="base_url"
    )

def encode_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_item(idx, item, client, model, image_base):
    max_retries = 3  # Maximum retry attempts
    retry_delay = 2  # Retry interval (seconds)
    
    for attempt in range(max_retries):
        try:
            base64_images = []
            for rel_path in item["images"]:
                abs_path = os.path.join(image_base, rel_path)
                base64_images.append(encode_image(abs_path))

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT + "\n\n" + item["question"]}
                    ] + [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64img}"
                            }
                        } for b64img in base64_images
                    ]
                }
            ]
            
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            content = completion.choices[0].message.content
            item["assistant"] = content
            # Ensure returned data contains index information
            if 'idx' not in item:
                item['idx'] = idx
            print(f"Item {idx+1} completed")
            return item
            
        except Exception as e:
            print(f"Item {idx+1} attempt {attempt+1} failed: {e}")
            
            # If not the last attempt, wait and retry
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
                # Increase delay time for each retry
                retry_delay *= 1.5
            else:
                print(f"Item {idx+1} failed after {max_retries} attempts")
                return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Evaluate model performance')
    parser.add_argument('--model', type=str, required=True, help='Model name to evaluate')
    parser.add_argument('--benchmark_path', type=str, required=True, help='Path to benchmark JSON file')
    parser.add_argument('--image_base', type=str, required=True, help='Base directory for images')
    parser.add_argument('--result_dir', type=str, required=True, help='Result directory')
    parser.add_argument('--threads', type=int, default=32, help='Number of threads for concurrent processing')
    args = parser.parse_args()


    # Read original data
    with open(args.benchmark_path, "r") as f:
        data = json.load(f)

    # Check existing result file and get tested data
    tested_keys = set()
    eval_path = os.path.join(args.result_dir, f"eval_{args.model}.jsonl")
    if os.path.exists(eval_path):
        print(f"Found existing result file: {eval_path}")
        print("Reading tested data...")
        with open(eval_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    # Use combination of question content and image paths as unique identifier
                    question_key = item.get('question', '') + str(item.get('images', []))
                    tested_keys.add(question_key)
                except json.JSONDecodeError:
                    continue
        print(f"Found {len(tested_keys)} tested items")

    # Filter untested data
    untested_data = []
    for idx, item in enumerate(data):
        # Use combination of question content and image paths as unique identifier
        question_key = item.get('question', '') + str(item.get('images', []))
        if question_key not in tested_keys:
            untested_data.append((idx, item))

    print(f"Total data: {len(data)}")
    print(f"Tested: {len(tested_keys)}")
    print(f"To be tested: {len(untested_data)}")

    if len(untested_data) == 0:
        print("All data has been tested!")
        return

    # Process untested data
    with ThreadPoolExecutor(max_workers=args.threads) as executor, open(eval_path, "a", encoding="utf-8") as fout:
        futures = [executor.submit(process_item, idx, item, client, args.model, args.image_base) for idx, item in untested_data]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                fout.write(json.dumps(result, ensure_ascii=False) + "\n")
                fout.flush()

    print(f"All completed, saved to {eval_path}")

if __name__ == "__main__":
    main()