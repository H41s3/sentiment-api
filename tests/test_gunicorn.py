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


def test_max_requests_enables_worker_recycling():
    mod = _load_config()
    assert mod.max_requests == 1000


def test_max_requests_jitter_is_set():
    mod = _load_config()
    assert mod.max_requests_jitter == 50


def test_loglevel_defaults_to_info():
    mod = _load_config()
    assert mod.loglevel == "info"


def test_loglevel_reads_log_level_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    mod = _load_config()
    assert mod.loglevel == "debug"


def test_worker_tmp_dir_uses_tmpfs():
    mod = _load_config()
    assert mod.worker_tmp_dir == "/dev/shm"


def test_accesslog_writes_to_stdout():
    mod = _load_config()
    assert mod.accesslog == "-"


def test_errorlog_writes_to_stderr():
    mod = _load_config()
    assert mod.errorlog == "-"
