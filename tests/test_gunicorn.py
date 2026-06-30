import importlib
import types


def _load_config() -> types.ModuleType:
    """Import gunicorn.conf as a module so we can inspect its top-level vars."""
    spec = importlib.util.spec_from_file_location("gunicorn_conf", "gunicorn.conf.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_default_workers_is_two():
    mod = _load_config()
    assert mod.workers == 2


def test_workers_reads_web_concurrency(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "4")
    mod = _load_config()
    assert mod.workers == 4


def test_worker_class_is_uvicorn():
    mod = _load_config()
    assert mod.worker_class == "uvicorn.workers.UvicornWorker"


def test_timeout_is_set():
    mod = _load_config()
    assert mod.timeout == 120


def test_graceful_timeout_is_set():
    mod = _load_config()
    assert mod.graceful_timeout == 30


def test_preload_app_enabled():
    mod = _load_config()
    assert mod.preload_app is True


def test_keepalive_is_set():
    mod = _load_config()
    assert mod.keepalive == 5
