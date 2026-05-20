import re

_HTML_TAG = re.compile(r"<[^>]+>")
_URL = re.compile(r"https?://\S+|www\.\S+")
_WHITESPACE = re.compile(r"\s+")


def preprocess(text: str) -> str:
    """Normalize raw user input before it reaches the tokenizer.

    Three transformations applied in order:

    1. Strip HTML tags — users frequently submit rich-text editor output.
       Tags become a space (not empty string) so surrounding words don't
       merge into a single token (e.g. "<b>great</b>product" → "great product").

    2. Replace URLs with [URL] — the model was trained on clean prose. Long URLs
       tokenize into dozens of meaningless subwords that dilute the sentiment
       signal. Replacing with the literal token [URL] is an NLP convention the
       model understands as "a URL was here."

    3. Collapse whitespace — steps 1 and 2 can leave runs of spaces behind.
       Collapsing them avoids wasting token budget on padding.
    """
    text = _HTML_TAG.sub(" ", text)
    text = _URL.sub("[URL]", text)
    text = text.strip()
    text = _WHITESPACE.sub(" ", text)
    return text
