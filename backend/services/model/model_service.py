import threading
import torch
import warnings

from peft import PeftModel
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

from backend.config import settings
from backend.utils.logger_utils import logger

_model = None
_tokenizer = None
_lock = threading.Lock()


def get_model():
    logger.info("Model: fetching...")
    global _model, _tokenizer
    warnings.filterwarnings("ignore", message="Merge lora module to 4-bit linear")

    if _model is not None:
        logger.info("Model: already loaded")
        return _model, _tokenizer

    with _lock:
        if _model is not None:
            return _model, _tokenizer

        base_model_name = settings.base_model_name
        lora_path = settings.lora_adapter_path

        _tokenizer = AutoTokenizer.from_pretrained(base_model_name, token=settings.hf_token)
        _tokenizer.pad_token = _tokenizer.eos_token
        _tokenizer.padding_side = "right"

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        base = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            device_map="auto",
            quantization_config=bnb_config,
            token=settings.hf_token,
            trust_remote_code=True,
        )

        _model = PeftModel.from_pretrained(base, lora_path)
        _model = _model.merge_and_unload()
        _model.eval()

        logger.info("Model: fetched")
        return _model, _tokenizer
