import argparse
import os
from pathlib import Path
from github import Github
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def read_file_content(file_path):
    """Read and return the content of a file."""
    with open(file_path, 'r') as f:
        return f.read()

def load_model_and_tokenizer(model_name):
    """Load the model and tokenizer with caching enabled."""
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )
    return model, tokenizer

def generate_review(model, tokenizer, prompt, max_length=2048):
    """Generate code review using the model."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_length=max_length,
        num_return_sequences=1,
        temperature=0.7,
        do_sample=True
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def main():
    parser = argparse.ArgumentParser(description='Generate AI code review')
    parser.add_argument('--model', required=True, help='HuggingFace model name')
    parser.add_argument('--prompt-template', required=True, help='Path to prompt template')
    parser.add_argument('--output-template', required=True, help='Path to output format template')
    parser.add_argument('--files', required=True, help='Space-separated list of changed files')
    
    args = parser.parse_args()
    
    # Load templates
    prompt_template = read_file_content(args.prompt_template)
    output_template = read_file_content(args.output_template)
    
    # Load model and tokenizer
    model, tokenizer = load_model_and_tokenizer(args.model)
    
    # Process each changed file
    changed_files = args.files.split()
    reviews = []
    
    for file_path in changed_files:
        if Path(file_path).exists():
            file_content = read_file_content(file_path)
            
            # Prepare prompt for this file
            file_prompt = prompt_template.format(
                file_path=file_path,
                file_content=file_content
            )
            
            # Generate review
            review = generate_review(model, tokenizer, file_prompt)
            reviews.append({
                'file': file_path,
                'review': review
            })
    
    # Format the final review using the output template
    final_review = output_template.format(
        reviews=reviews,
        pr_number=os.environ.get('GITHUB_EVENT_NUMBER')
    )
    
    # Post comment to PR
    github_token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    pr_number = int(os.environ['GITHUB_EVENT_NUMBER'])
    
    g = Github(github_token)
    repo = g.get_repo(repo)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(final_review)

if __name__ == '__main__':
    main()
