import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    return tmp_path


@pytest.fixture
def client(data_dir):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def slither_raw() -> dict:
    path = Path(__file__).parent / "fixtures" / "slither_output.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def example_zip() -> Path:
    path = Path(__file__).resolve().parents[2] / "examples" / "reentrancy-example.zip"
    if not path.exists():
        pytest.skip("examples/reentrancy-example.zip not found")
    return path
