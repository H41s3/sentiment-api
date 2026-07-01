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


def test_strips_null_bytes():
    assert preprocess("hello\x00world") == "helloworld"


def test_strips_bell_character():
    assert preprocess("hello\x07world") == "helloworld"


def test_strips_form_feed():
    assert preprocess("page1\x0cpage2") == "page1page2"


def test_strips_mixed_control_chars():
    assert preprocess("\x01\x02good \x03product\x04") == "good product"


def test_preserves_tab_as_whitespace():
    assert preprocess("hello\tworld") == "hello world"


def test_preserves_newline_as_whitespace():
    assert preprocess("line1\nline2") == "line1 line2"


def test_multiple_urls_replaced():
    result = preprocess("see https://a.com and https://b.com here")
    assert result == "see [URL] and [URL] here"


def test_url_at_start_of_text():
    assert preprocess("https://example.com is great") == "[URL] is great"


def test_url_at_end_of_text():
    assert preprocess("visit https://example.com") == "visit [URL]"


def test_all_html_input():
    assert preprocess("<div><p><span></span></p></div>") == ""


def test_self_closing_tags():
    assert preprocess("line<br/>break<hr/>done") == "line break done"


def test_carriage_return_collapsed():
    assert preprocess("hello\r\nworld") == "hello world"


def test_preserves_emoji_characters():
    assert preprocess("I love this product! 😍") == "I love this product! 😍"


def test_preserves_accented_characters():
    assert preprocess("Très bien, merci!") == "Très bien, merci!"


def test_preserves_cjk_characters():
    assert preprocess("この製品は素晴らしい") == "この製品は素晴らしい"


def test_html_with_url_combined():
    result = preprocess("<a href='https://example.com'>Click here</a>")
    assert "href" not in result
    assert "Click here" in result
