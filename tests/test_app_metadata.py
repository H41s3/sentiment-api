from app.main import app


def test_app_title():
    assert app.title == "Sentiment Analysis API"


def test_app_version():
    assert app.version == "0.1.0"


def test_app_description_is_nonempty():
    assert app.description
    assert len(app.description) > 10


def test_app_has_openapi_tags():
    tag_names = [t["name"] for t in app.openapi_tags]
    assert "sentiment" in tag_names
    assert "meta" in tag_names


def test_app_has_lifespan():
    assert app.router.lifespan_context is not None


def test_app_has_rate_limiter_state():
    assert hasattr(app.state, "limiter")
    assert app.state.limiter is not None
