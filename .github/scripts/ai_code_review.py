import os
import json
import glob
from github import Github
from transformers import pipeline

# Set up GitHub client
github_token = os.environ['GITHUB_TOKEN']
g = Github(github_token)

# Get repository and pull request information
repo_name = os.environ['GITHUB_REPOSITORY']
# GITHUB_REF에서 Pull Request 번호 가져오기
try:
    pr_number = int(os.getenv("GITHUB_REF", "").split("/")[-1])
except ValueError:
    # GITHUB_EVENT_PATH로 대체
    with open(os.getenv("GITHUB_EVENT_PATH", ""), "r") as f:
        event_data = json.load(f)
        pr_number = event_data.get("pull_request", {}).get("number", 0)

if not pr_number:
    raise ValueError("Pull Request number could not be determined!")

print(f"Pull Request number: {pr_number}")

repo = g.get_repo(repo_name)
pr = repo.get_pull(pr_number)

# Set up AI model
model_id = "Qwen/Qwen2.5-Coder-7B-Instruct"
reviewer = pipeline('text-generation', model=model_id)

# Get changed files
changed_files = [file.filename for file in pr.get_files()]

# Load prompts
prompt_files = glob.glob('.github/prompts/*.md')

# Load review template
with open('.github/template/review_format.md', 'r') as f:
    review_template = f.read()

# Function to generate review
def generate_review(prompt, changes):
    input_text = f"{prompt}\n\nChanged files:\n{changes}"
    response = reviewer(input_text, max_new_token=1000, num_return_sequences=1)
    return response[0]['generated_text']

# Generate and post reviews
for prompt_file in prompt_files:
    with open(prompt_file, 'r') as f:
        prompt = f.read()
    
    review = generate_review(prompt, '\n'.join(changed_files))
    
    # Format review using template
    formatted_review = review_template.format(review=review)
    
    # Post comment
    pr.create_issue_comment(formatted_review)

print("AI Code Review completed successfully.")

# End of file. No additional code.
