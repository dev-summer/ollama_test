import os
import sys
from transformers import pipeline
from huggingface_hub import snapshot_download
import torch
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_environment_variables() -> dict:
    """Load and validate required environment variables."""
    required_vars = {
        'DIFF_CONTENT': 'PR diff content',
        'CHANGED_FILES': 'List of changed files',
        'MAX_TOKENS': 'Maximum tokens for generation',
        'TEMPERATURE': 'Temperature for generation'
    }
    
    return {var: os.getenv(var) for var in required_vars if os.getenv(var)}

def prepare_model_cache():
    """Download and cache the model files."""
    # Use the Hugging Face cache directory
    cache_dir = os.getenv('HUGGINGFACE_HUB_CACHE', os.path.expanduser('~/.cache/huggingface'))
    os.makedirs(cache_dir, exist_ok=True)
    
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    
    logger.info(f"Using cache directory: {cache_dir}")
    logger.info(f"Preparing model: {model_name}")
    
    try:
        # Use local files first if available
        snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            local_files_only=True,
            resume_download=True
        )
        logger.info("Model loaded from cache successfully")
    except Exception as e:
        logger.info(f"Cache miss or error: {e}. Downloading model...")
        snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            local_files_only=False,
            resume_download=True
        )
        logger.info("Model downloaded successfully")
    
    return model_name, cache_dir

def generate_review(prompt: str, max_tokens: int, temperature: float) -> str:
    """Generate review using the pipeline."""
    model_name, cache_dir = prepare_model_cache()
    
    logger.info("Initializing pipeline...")
    # Initialize pipeline with optimized settings
    generator = pipeline(
        'text-generation',
        model=model_name,
        device_map="auto",
        torch_dtype=torch.float16,
        model_kwargs={
            "cache_dir": cache_dir,
            "low_cpu_mem_usage": True,
        }
    )
    
    logger.info("Generating review...")
    # Generate response
    response = generator(
        prompt,
        max_new_tokens=int(max_tokens),
        do_sample=True,
        temperature=float(temperature),
        num_return_sequences=1
    )[0]['generated_text']
    
    return response[len(prompt):].strip()

def main():
    # Load environment variables
    env_vars = load_environment_variables()
    
    prompt_files = [
        ('architecture_review.md', '🏗 Architecture Review'),
        ('ui_review.md', '🎨 UI Implementation Review'),
        ('technical_review.md', '🔧 Technical Review')
    ]
    
    # Single pipeline initialization for all reviews
    for i, (prompt_file, review_type) in enumerate(prompt_files, 1):
        logger.info(f"\nGenerating {review_type}...")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read().strip()
        
        full_prompt = f"{prompt_content}\n\nChanges to review:\n```diff\n{env_vars['DIFF_CONTENT']}\n```\n\n"
        
        review = generate_review(
            full_prompt,
            env_vars['MAX_TOKENS'],
            env_vars['TEMPERATURE']
        )
        
        if not review.strip():
            logger.error(f"Error: Generated {review_type} is empty")
            sys.exit(1)
        
        with open(f"review_comment_{i}.txt", "w", encoding='utf-8') as f:
            f.write(review)
        
        logger.info(f"✅ {review_type} generated and saved successfully")
    
    logger.info("\nAll reviews generated and saved successfully")

if __name__ == "__main__":
    main()
