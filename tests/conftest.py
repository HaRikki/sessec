import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["ADMIN_TOKEN"] = "test-admin-token"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"
