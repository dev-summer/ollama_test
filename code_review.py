import os
import sys
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Tuple

def load_environment_variables() -> dict:
    """Load and validate required environment variables."""
    required_vars = {
        'DIFF_CONTENT': 'PR diff content',
        'CHANGED_FILES': 'List of changed files',
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

def load_prompt(filename: str) -> str:
    """Load a review prompt from a file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error loading prompt from {filename}: {e}")
        sys.exit(1)

def format_markdown_review(review: str) -> str:
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

def save_review(review: str, index: int) -> None:
    """Save a generated review to a file."""
    try:
        with open(f"review_comment_{index}.txt", "w", encoding='utf-8') as f:
            f.write(format_markdown_review(review))
    except Exception as e:
        print(f"Error saving review {index}: {e}")
        sys.exit(1)

def create_attention_mask(input_ids, pad_token_id):
    """Create attention mask for the input."""
    return (input_ids != pad_token_id).long()

def generate_review(model, tokenizer, prompt: str, max_tokens: int, temperature: float) -> str:
    """Generate review using the local model."""
    try:
        # Tokenize with padding
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096,
            padding=True,
            add_special_tokens=True
        )
        
        # Create attention mask
        attention_mask = create_attention_mask(inputs.input_ids, tokenizer.pad_token_id)
        inputs['attention_mask'] = attention_mask
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=int(max_tokens),
                do_sample=True,
                temperature=float(temperature),
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                bos_token_id=tokenizer.bos_token_id,
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the prompt from the response
        response = response[len(prompt):].strip()
        return response
        
    except Exception as e:
        print(f"Error generating review: {e}")
        sys.exit(1)

def main():
    # Load environment variables
    env_vars = load_environment_variables()
    
    # Cache directory for model
    cache_dir = os.getenv('RUNNER_TEMP', '/tmp') + '/model_cache'
    os.makedirs(cache_dir, exist_ok=True)
    
    # Load model and tokenizer
    print("Loading model and tokenizer...")
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    
    try:
        # Set tokenizer configurations
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            cache_dir=cache_dir,
            pad_token='<|endoftext|>',  # Explicitly set pad token
            padding_side='right'
        )
        
        # Set model configurations
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16,  # Use fp16 to reduce memory usage
            cache_dir=cache_dir,
            low_cpu_mem_usage=True,
            offload_folder="offload"  # Enable model offloading
        )
        
        print("Model and tokenizer loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)
    
    # Define prompt files and their corresponding review types
    prompt_files: List[Tuple[str, str]] = [
        ('architecture_review.md', '🏗 Architecture Review'),
        ('ui_review.md', '🎨 UI Implementation Review'),
        ('technical_review.md', '🔧 Technical Review')
    ]
    
    # Process each review type
    for i, (prompt_file, review_type) in enumerate(prompt_files, 1):
        print(f"\nGenerating {review_type}...")
        
        # Load prompt content
        prompt_content = load_prompt(prompt_file)
        
        # Generate full prompt with diff
        full_prompt = f"{prompt_content}\n\nChanges to review:\n```diff\n{env_vars['DIFF_CONTENT']}\n```\n\n"
        
        # Generate review
        review = generate_review(
            model,
            tokenizer,
            full_prompt,
            env_vars['MAX_TOKENS'],
            env_vars['TEMPERATURE']
        )
        
        # Validate review
        if not review.strip():
            print(f"Error: Generated {review_type} is empty")
            sys.exit(1)
        
        # Save review
        save_review(review, i)
        print(f"✅ {review_type} generated and saved successfully")
    
    print("\nAll reviews generated and saved successfully")

if __name__ == "__main__":
    main()
