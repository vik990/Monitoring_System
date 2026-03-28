# bootstrap for PyMySQL on Windows
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    pass

# Import Celery app to ensure tasks are discovered when Django starts
try:
    from .celery import app as celery_app  # noqa
except Exception:
    # Celery may not be installed or configured in some dev environments
    pass