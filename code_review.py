import os
import sys
from transformers import pipeline
import json

def load_environment_variables():
    """Load and validate required environment variables."""
    required_vars = {
        'PROMPT_CONTENT': 'Review prompt content',
        'DIFF_CONTENT': 'PR diff content',
        'CHANGED_FILES': 'List of changed files',
        'MODEL_NAME': 'HuggingFace model name',
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

def initialize_model(model_name):
    """Initialize the model pipeline with error handling."""
    try:
        return pipeline(
            "text-generation",
            model=model_name,
            return_full_text=False
        )
    except Exception as e:
        print(f"Error initializing model: {e}")
        sys.exit(1)

def generate_review(model, prompt, diff, max_tokens, temperature):
    """Generate code review using the model."""
    try:
        full_prompt = f"{prompt}\n\nChanges to review:\n```diff\n{diff}\n```\n\nPlease provide a detailed code review:"
        
        review = model(
            full_prompt,
            max_new_tokens=int(max_tokens),
            num_return_sequences=1,
            temperature=float(temperature)
        )[0]['generated_text']
        
        return review.strip()
    except Exception as e:
        print(f"Error generating review: {e}")
        sys.exit(1)

def save_review(review):
    """Save the generated review to a file."""
    try:
        with open("review_comment.txt", "w", encoding='utf-8') as f:
            f.write(review)
    except Exception as e:
        print(f"Error saving review: {e}")
        sys.exit(1)

def main():
    # Load environment variables
    env_vars = load_environment_variables()
    
    # Initialize model
    model = initialize_model(env_vars['MODEL_NAME'])
    
    # Generate review
    review = generate_review(
        model,
        env_vars['PROMPT_CONTENT'],
        env_vars['DIFF_CONTENT'],
        env_vars['MAX_TOKENS'],
        env_vars['TEMPERATURE']
    )
    
    # Validate review content
    if not review.strip():
        print("Error: Generated review is empty")
        sys.exit(1)
    
    # Save review
    save_review(review)
    print("Review generated and saved successfully")

if __name__ == "__main__":
    main()
