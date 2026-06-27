import os

workers = int(os.getenv("WEB_CONCURRENCY", "2"))
timeout = 120
accesslog = "-"
