import re

__all__ = ["preprocess"]

_HTML_TAG = re.compile(r"<[^>]+>")
_URL = re.compile(r"https?://\S+|www\.\S+")
_WHITESPACE = re.compile(r"\s+")
# Non-printable control characters excluding normal whitespace (\t \n \r).
# These can appear in copy-pasted content from PDFs or rich editors and
# tokenize into unexpected subword fragments that corrupt the sentiment signal.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def preprocess(text: str) -> str:
    """Normalize raw user input before it reaches the tokenizer.

    Four transformations applied in order:

    1. Strip control characters — null bytes and other non-printable characters
       from PDF/rich-editor copy-paste tokenize into junk subwords.

    2. Strip HTML tags — users frequently submit rich-text editor output.
       Tags become a space (not empty string) so surrounding words don't
       merge into a single token (e.g. "<b>great</b>product" → "great product").

    3. Replace URLs with [URL] — the model was trained on clean prose. Long URLs
       tokenize into dozens of meaningless subwords that dilute the sentiment
       signal. Replacing with the literal token [URL] is an NLP convention the
       model understands as "a URL was here."

    4. Collapse whitespace — prior steps can leave runs of spaces behind.
       Collapsing them avoids wasting token budget on padding.
    """
    text = _CONTROL_CHARS.sub("", text)
    text = _HTML_TAG.sub(" ", text)
    text = _URL.sub("[URL]", text)
    text = text.strip()
    text = _WHITESPACE.sub(" ", text)
    return text
