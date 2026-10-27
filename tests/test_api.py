from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

JOB = "Looking for a Python developer with FastAPI, Docker and SQL experience. 2+ years required."


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_screen_ranks_uploaded_resumes():
    files = [
        ("resumes", ("a.txt", b"Sam Lee\nPython FastAPI Docker SQL developer, 3 years", "text/plain")),
        ("resumes", ("b.txt", b"Kim Park\nPainter and illustrator", "text/plain")),
    ]
    response = client.post("/api/screen", data={"job_description": JOB}, files=files)

    assert response.status_code == 200
    results = response.json()["results"]
    assert [r["filename"] for r in results] == ["a.txt", "b.txt"]


def test_screen_rejects_unsupported_files():
    files = [("resumes", ("photo.png", b"fake", "image/png"))]
    response = client.post("/api/screen", data={"job_description": JOB}, files=files)

    assert response.status_code == 400
    assert "photo.png" in response.json()["detail"]
