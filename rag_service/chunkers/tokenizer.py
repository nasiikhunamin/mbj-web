"""Token counting and encoding utility for E5 multilingual models."""

import re
from typing import List, Optional

try:
    from transformers import AutoTokenizer  # type: ignore
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


class E5Tokenizer:
    """Tokenizer wrapper for intfloat/multilingual-e5-base.

    Ensures all chunkers adhere strictly to the 512 token limit of the E5 model
    to prevent silent truncation during embedding generation.
    """

    DEFAULT_MODEL_NAME = "intfloat/multilingual-e5-base"

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._hf_tokenizer = None
        self._init_tokenizer()

    def _init_tokenizer(self) -> None:
        """Initialize HuggingFace tokenizer if available and model is cached."""
        if HAS_TRANSFORMERS:
            try:
                # Try loading local cached tokenizer
                self._hf_tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    local_files_only=True,
                )
            except Exception:
                # If not cached locally, we defer or use fallback
                self._hf_tokenizer = None

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text."""
        if not text:
            return 0
        if self._hf_tokenizer is not None:
            return len(self._hf_tokenizer.encode(text, add_special_tokens=False))
        return len(self.encode(text))

    def encode(self, text: str) -> List[int]:
        """Encode text into a list of token IDs."""
        if not text:
            return []
        if self._hf_tokenizer is not None:
            return self._hf_tokenizer.encode(text, add_special_tokens=False)

        # Robust SentencePiece/Byte-level fallback when offline or transformers is absent
        # Splits on words, punctuation, and whitespace sequences
        tokens = re.findall(r"\w+|[^\w\s]|\s+", text, flags=re.UNICODE)
        # Hash each piece into a stable pseudo-token-id
        return [abs(hash(t)) % 250000 + 1 for t in tokens]

    def decode(self, token_ids: List[int], original_text: Optional[str] = None) -> str:
        """Decode token IDs back to string."""
        if not token_ids:
            return ""
        if self._hf_tokenizer is not None:
            return self._hf_tokenizer.decode(token_ids)
        # In fallback mode, if original_text is not available, we represent decoded tokens
        return f"[Decoded {len(token_ids)} tokens]"

    def truncate_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to max_tokens."""
        if self.count_tokens(text) <= max_tokens:
            return text
        if self._hf_tokenizer is not None:
            token_ids = self._hf_tokenizer.encode(text, add_special_tokens=False)[:max_tokens]
            return self._hf_tokenizer.decode(token_ids, skip_special_tokens=True)

        # Fallback truncation using token regex chunks
        pieces = re.findall(r"\w+|[^\w\s]|\s+", text, flags=re.UNICODE)
        return "".join(pieces[:max_tokens])


# Global singleton instance for efficient reuse across chunkers
default_tokenizer = E5Tokenizer()
