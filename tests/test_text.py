from app.utils.text import preprocess


def test_strips_html_tags():
    assert preprocess("<b>bold</b> text") == "bold text"


def test_strips_nested_html():
    assert preprocess("<div><p>hello</p></div>") == "hello"


def test_replaces_http_url():
    assert preprocess("visit https://example.com now") == "visit [URL] now"


def test_replaces_www_url():
    assert preprocess("go to www.example.com today") == "go to [URL] today"


def test_collapses_internal_whitespace():
    assert preprocess("too   many    spaces") == "too many spaces"


def test_strips_leading_and_trailing_whitespace():
    assert preprocess("  hello world  ") == "hello world"


def test_passthrough_plain_text():
    text = "This is a perfectly normal sentence."
    assert preprocess(text) == text


def test_handles_mixed_html_and_url():
    result = preprocess("<b>Check</b> https://example.com for details")
    assert result == "Check [URL] for details"


def test_empty_tags_collapse_to_nothing():
    assert preprocess("before<br/>after") == "before after"
