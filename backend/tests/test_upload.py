import io
import zipfile
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def _make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


@patch("app.api.routes.audit.run_audit_pipeline", new_callable=AsyncMock)
def test_upload_valid_zip(_mock_pipeline, client: TestClient, example_zip):
    with open(example_zip, "rb") as f:
        response = client.post(
            "/api/v1/audits",
            files={"file": ("reentrancy-example.zip", f, "application/zip")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data

    status = client.get(f"/api/v1/audits/{data['task_id']}")
    assert status.status_code == 200
    assert status.json()["filename"] == "reentrancy-example.zip"


def test_upload_rejects_non_zip(client: TestClient):
    response = client.post(
        "/api/v1/audits",
        files={"file": ("contract.sol", b"pragma solidity ^0.8.0;", "text/plain")},
    )
    assert response.status_code == 400
    assert "zip" in response.json()["detail"].lower()


def test_upload_rejects_empty_zip(client: TestClient):
    empty_zip = _make_zip({})
    response = client.post(
        "/api/v1/audits",
        files={"file": ("empty.zip", empty_zip, "application/zip")},
    )
    assert response.status_code == 400


def test_upload_rejects_zip_without_sol(client: TestClient):
    zip_bytes = _make_zip({"readme.txt": "no solidity here"})
    response = client.post(
        "/api/v1/audits",
        files={"file": ("no-sol.zip", zip_bytes, "application/zip")},
    )
    assert response.status_code == 400
    assert ".sol" in response.json()["detail"]


def test_upload_rejects_path_traversal(client: TestClient):
    zip_bytes = _make_zip({"../evil.sol": "pragma solidity ^0.8.0; contract X {}"})
    response = client.post(
        "/api/v1/audits",
        files={"file": ("evil.zip", zip_bytes, "application/zip")},
    )
    assert response.status_code == 400
