"""仅用于本地无 PostgreSQL 环境下运行 scripts/verify_paper_rules.py 的配置。"""

from config.settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
