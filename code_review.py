import os
import sys
import requests
import json

def load_environment_variables():
    """Load and validate required environment variables."""
    required_vars = {
        'DIFF_CONTENT': 'PR diff content',
        'CHANGED_FILES': 'List of changed files',
        'HF_API_TOKEN': 'Hugging Face API Token',
        'MAX_TOKENS': 'Maximum tokens for generation',
        'TEMPERATURE': 'Temperature for generation'
    }
    
    env_vars = {}
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            print(f"Error: Missing required environment variable {var} ({description})")
            sys.exit(1)
        env_vars[var] = value
    
    return env_vars

def load_prompt(filename):
    """Load a review prompt from a file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error loading prompt from {filename}: {e}")
        sys.exit(1)

def call_inference_api(prompt, api_token, max_tokens, temperature):
    """Call Hugging Face Inference API."""
    API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-7B-Instruct"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": int(max_tokens),
            "temperature": float(temperature),
            "return_full_text": False,
            "num_return_sequences": 1
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()[0]['generated_text'].strip()
    except Exception as e:
        print(f"Error calling Hugging Face API: {e}")
        sys.exit(1)

def format_markdown_review(review):
    """Format the review in proper markdown."""
    formatted_review = review
    
    # Ensure code blocks are properly formatted
    code_block_markers = ["Current code:", "Suggested fix:", "Code example:"]
    lines = review.split("\n")
    formatted_lines = []
    
    in_code_block = False
    for line in lines:
        if any(marker in line for marker in code_block_markers):
            formatted_lines.append(line)
            formatted_lines.append("```swift")
            in_code_block = True
        elif in_code_block and line.strip() == "":
            formatted_lines.append("```")
            formatted_lines.append(line)
            in_code_block = False
        else:
            formatted_lines.append(line)
    
    if in_code_block:
        formatted_lines.append("```")
    
    return "\n".join(formatted_lines)

def save_review(review, index):
    """Save a generated review to a file."""
    try:
        with open(f"review_comment_{index}.txt", "w", encoding='utf-8') as f:
            f.write(format_markdown_review(review))
    except Exception as e:
        print(f"Error saving review {index}: {e}")
        sys.exit(1)

def main():
    # Load environment variables
    env_vars = load_environment_variables()
    
    # Define prompt files and their corresponding review types
    prompt_files = [
        ('architecture_review.md', '🏗 Architecture Review'),
        ('ui_review.md', '🎨 UI Implementation Review'),
        ('technical_review.md', '🔧 Technical Review')
    ]
    
    # Process each review type
    for i, (prompt_file, review_type) in enumerate(prompt_files, 1):
        # Load prompt content
        prompt_content = load_prompt(prompt_file)
        
        # Generate full prompt with diff
        full_prompt = f"{prompt_content}\n\nChanges to review:\n```diff\n{env_vars['DIFF_CONTENT']}\n```\n\n"
        
        # Call API and generate review
        review = call_inference_api(
            full_prompt,
            env_vars['HF_API_TOKEN'],
            env_vars['MAX_TOKENS'],
            env_vars['TEMPERATURE']
        )
        
        # Validate review
        if not review.strip():
            print(f"Error: Generated {review_type} is empty")
            sys.exit(1)
        
        # Save review
        save_review(review, i)
    
    print("All reviews generated and saved successfully")

if __name__ == "__main__":
    main()
