import json
import random
import torch

from pathlib import Path
from text_cleaning_utils import clean_line, MORTY_REPLACEMENTS
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

NUM_MONOLOGUES = 20
MONOLOGUE_SENTENCES = (5, 6)
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"


def generate_monologue(model, tokenizer) -> str:
    nickname = random.choice(MORTY_REPLACEMENTS)

    parts = [
        "Write a 5-6 sentence monologue spoken directly by Rick from Rick and Morty.",
        "Make it comedic, unhinged, sarcastic, and full of chaotic science jokes.",
        f"Never mention Morty or any canonical characters; if Morty appears, replace it with '{nickname}'.",
        "Avoid show references entirely.",
        "Use profanity and keep it uncensored. do not use asterisks like 'f*ck'.",
        "Write the monologue as one continuous paragraph with no line breaks, no newline characters, and no paragraph breaks.",
        "Do not use speaker labels like 'Rick:' or 'Person:'.",
        "Do not use third-person narration, actions, or scene descriptions such as 'Rick walks' or 'Rick, pacing in his lab'.",
        "Do not include stage directions or bracketed descriptions.",
        "Do not include meta-instructions, notes, reminders, or commentary about writing.",
        "Avoid dialogue formatting, excessive quoting, or any text that resembles a script.",
        "Ensure proper spacing, correct punctuation, and no malformed words.",
        "Keep the monologue readable and not overly convoluted.",
        "End the monologue with a complete final sentence and end it with a period.",
        maybe("Include one over-the-top scientific exaggeration or metaphor."),
        maybe("Include one sarcastic insult delivered in Rick's tone."),
        maybe("Include one moment where Rick asserts his superiority or genius."),
        maybe("Include one moment of frustrated commentary about something trivial."),
    ]

    prompt = " ".join([p for p in parts if p])
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    output = model.generate(
        **inputs,
        max_new_tokens=320,
        temperature=0.9,
        top_p=0.92,
        do_sample=True,
    )

    text = tokenizer.decode(output[0], skip_special_tokens=True)
    return text[len(prompt) :].strip()


def maybe(text, chance=0.4):
    return text if random.random() < chance else ""


def main():
    root = Path(__file__).resolve().parents[2]
    out_path = root / "data" / "processed" / "synthetic_monologues.jsonl"

    print("Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=torch.float16, device_map="auto")

    results = []

    print(f"Generating {NUM_MONOLOGUES} synthetic monologues...")
    for _ in tqdm(range(NUM_MONOLOGUES)):
        raw = generate_monologue(model, tokenizer)
        cleaned = clean_line(raw)
        if cleaned:
            results.append(cleaned)

    with open(out_path, "w", encoding="utf-8") as f:
        for line in results:
            f.write(json.dumps({"text": line}, ensure_ascii=False) + "\n")

    print(f"Saved {len(results)} synthetic monologues to {out_path}")


if __name__ == "__main__":
    main()
