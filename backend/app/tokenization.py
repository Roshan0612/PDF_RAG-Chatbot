from functools import lru_cache

from transformers import AutoTokenizer


TOKENIZER_MODEL = "nomic-ai/nomic-embed-text-v1.5"


@lru_cache(maxsize=1)
def get_tokenizer():
    return AutoTokenizer.from_pretrained(
        TOKENIZER_MODEL
    )


def encode_tokens(text: str) -> list[int]:
    tokenizer = get_tokenizer()

    return tokenizer.encode(
        text,
        add_special_tokens=False
    )


def decode_tokens(tokens: list[int]) -> str:
    tokenizer = get_tokenizer()

    return tokenizer.decode(
        tokens,
        skip_special_tokens=True
    )


def count_tokens(text: str) -> int:
    return len(
        encode_tokens(text)
    )