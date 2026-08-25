import torch

from peft import LoraConfig, get_peft_model
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

from bot.src.training.utils.config_loader import load_yaml
from bot.src.training.utils.dataset_loader import load_rick_dataset
from bot.src.training.utils.logging_utils import setup_logging
from bot.src.training.utils.seed_utils import set_seed


def tokenize_function(example, tokenizer, max_length):
    return tokenizer(example["text"], truncation=True, max_length=max_length)


def main():
    logger = setup_logging()
    set_seed(42)

    logger.info("Loading configurations...")
    model_cfg = load_yaml("bot/src/training/config/model_config.yaml")
    lora_cfg = load_yaml("bot/src/training/config/lora_config.yaml")

    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_cfg["tokenizer_name"])
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id
    tokenizer.padding_side = "right"

    logger.info("Configuring 4-bit quantization (QLoRA)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    logger.info("Loading base model in 4-bit...")
    model = AutoModelForCausalLM.from_pretrained(
        model_cfg["model_name"],
        device_map="auto",
        quantization_config=bnb_config,
    )

    logger.info("Applying LoRA configuration...")
    peft_config = LoraConfig(
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["alpha"],
        lora_dropout=lora_cfg["dropout"],
        target_modules=lora_cfg["target_modules"],
        bias=lora_cfg["bias"],
        task_type=lora_cfg["task_type"],
    )

    model = get_peft_model(model, peft_config)
    model.config.use_cache = False
    model.config.pretraining_tp = 1
    model.gradient_checkpointing_enable()

    logger.info("Loading dataset...")
    dataset = load_rick_dataset(model_cfg["dataset_path"])

    logger.info("Tokenizing dataset...")
    tokenized = dataset["train"].map(
        lambda x: tokenize_function(
            x,
            tokenizer,
            model_cfg["max_seq_length"],
        ),
        batched=True,
    )

    logger.info("Setting up data collator...")
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    logger.info("Setting up training arguments...")
    training_args = TrainingArguments(
        output_dir=model_cfg["output_dir"],
        per_device_train_batch_size=model_cfg["batch_size"],
        gradient_accumulation_steps=model_cfg["gradient_accumulation"],
        learning_rate=model_cfg["learning_rate"],
        num_train_epochs=model_cfg["num_epochs"],
        logging_steps=20,
        save_steps=500,
        logging_first_step=True,
        save_strategy="epoch",
        save_total_limit=2,
        gradient_checkpointing=True,
        optim="paged_adamw_32bit",
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        fp16=False,
        bf16=False,
        report_to="none",
    )

    logger.info("Initializing Trainer...")
    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized, data_collator=data_collator)

    logger.info("Starting training...")
    trainer.train()

    logger.info("Saving LoRA adapter...")
    trainer.model.save_pretrained(model_cfg["output_dir"])

    logger.info("Training complete.")


if __name__ == "__main__":
    main()
