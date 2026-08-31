import os

# db.py raises at import if this is missing. Tests never open the pool.
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/evmbench")
