import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def get_temp_file() -> Path:
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    temp_path = Path(temp_file.name)
    try:
        yield temp_path
    finally:
        temp_file.close()
        temp_path.unlink(missing_ok=True)


@contextmanager
def get_temp_dir() -> Path:
    temp_dir = tempfile.mkdtemp(prefix="pyodk_tmp_")
    temp_path = Path(temp_dir)
    try:
        yield temp_path
    finally:
        if temp_path.exists():
            shutil.rmtree(temp_dir)
