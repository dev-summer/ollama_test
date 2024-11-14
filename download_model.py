import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_model():
    """Download and save the model files locally."""
    model_name = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    model_path = os.path.join(os.getenv('MODEL_PATH', 'models'))
    
    logger.info(f"Downloading model to: {model_path}")
    
    try:
        # Download and save tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        tokenizer.save_pretrained(model_path)
        logger.info("Tokenizer downloaded and saved successfully")
        
        # Download and save model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        model.save_pretrained(model_path)
        logger.info("Model downloaded and saved successfully")
        
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        raise

if __name__ == "__main__":
    download_model()
