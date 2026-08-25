import torch

from bot.src.training.utils.config_loader import load_yaml
from transformers import AutoTokenizer, AutoModelForCausalLM


def main():
    model_cfg = load_yaml("bot/src/training/config/model_config.yaml")

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_cfg["model_name"])
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    print("Tokenizer OK")

    print("Loading model on GPU in fp16...")
    model = AutoModelForCausalLM.from_pretrained(
        model_cfg["model_name"],
        device_map="auto",
        dtype=torch.float16,
    )
    print("Model loaded successfully!")

    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / (1024**2)
        reserved = torch.cuda.memory_reserved() / (1024**2)
        print(f"GPU VRAM allocated: {allocated:.2f} MB")
        print(f"GPU VRAM reserved:  {reserved:.2f} MB")
    else:
        print("CUDA not available")

    print("Test complete.")


if __name__ == "__main__":
    main()
