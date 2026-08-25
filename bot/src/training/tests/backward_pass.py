import torch

from bot.src.training.utils.config_loader import load_yaml
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    model_cfg = load_yaml("bot/src/training/config/model_config.yaml")
    model = AutoModelForCausalLM.from_pretrained(
        model_cfg["model_name"],
        device_map="auto",
        dtype=torch.float16,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_cfg["model_name"])
    inputs = tokenizer("test", return_tensors="pt").to("cuda")

    out = model(**inputs)
    loss = out.logits.sum()
    loss.backward()

    print("Backward pass OK")


if __name__ == "__main__":
    main()
