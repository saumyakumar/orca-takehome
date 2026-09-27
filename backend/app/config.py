import os

DATABASE_URL = os.environ.get("ORCA_DATABASE_URL", "sqlite:///./orca.db")
