import os
import sys
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
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
        'TEMPERATURE': 'Temperature for generation',
        'MODEL_PATH': 'Path to model files'
    }
    
    return {var: os.getenv(var) for var in required_vars if os.getenv(var)}

def initialize_model(model_path: str):
    """Initialize the model from local files."""
    logger.info(f"Loading model from: {model_path}")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            trust_remote_code=True,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        
        generator = pipeline(
            'text-generation',
            model=model,
            tokenizer=tokenizer,
            device_map="auto"
        )
        
        logger.info("Model loaded successfully")
        return generator
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

def generate_review(generator, prompt: str, max_tokens: int, temperature: float) -> str:
    """Generate review using the pipeline."""
    logger.info("Generating review...")
    
    try:
        response = generator(
            prompt,
            max_new_tokens=int(max_tokens),
            do_sample=True,
            temperature=float(temperature),
            num_return_sequences=1
        )[0]['generated_text']
        
        return response[len(prompt):].strip()
        
    except Exception as e:
        logger.error(f"Error generating review: {e}")
        raise

def main():
    # Load environment variables
    env_vars = load_environment_variables()
    
    # Initialize model once
    generator = initialize_model(env_vars['MODEL_PATH'])
    
    prompt_files = [
        ('architecture_review.md', '🏗 Architecture Review'),
        ('ui_review.md', '🎨 UI Implementation Review'),
        ('technical_review.md', '🔧 Technical Review')
    ]
    
    for i, (prompt_file, review_type) in enumerate(prompt_files, 1):
        logger.info(f"\nGenerating {review_type}...")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read().strip()
        
        full_prompt = f"{prompt_content}\n\nChanges to review:\n```diff\n{env_vars['DIFF_CONTENT']}\n```\n\n"
        
        review = generate_review(
            generator,
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
