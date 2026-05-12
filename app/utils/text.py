import re


_HTML_TAG = re.compile(r"<[^>]+>")
_URL = re.compile(r"https?://\S+|www\.\S+")
_WHITESPACE = re.compile(r"\s+")


def preprocess(text: str) -> str:
    text = _HTML_TAG.sub(" ", text)
    text = _URL.sub("[URL]", text)
    text = text.strip()
    text = _WHITESPACE.sub(" ", text)
    return text
