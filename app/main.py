from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.keep_alive import start_keep_alive
from app.parser import UnsupportedFileError, extract_text
from app.scorer import WEIGHTS, rank_resumes

STATIC_DIR = Path(__file__).parent / "static"
MAX_FILES = 20
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = start_keep_alive()
    yield
    if task:
        task.cancel()


app = FastAPI(title="AI Resume Screener", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/screen")
async def screen(
    job_description: str = Form(...),
    resumes: list[UploadFile] = File(...),
):
    if len(job_description.strip()) < 30:
        raise HTTPException(400, "Job description is too short to compare against.")
    if len(resumes) > MAX_FILES:
        raise HTTPException(400, f"Upload at most {MAX_FILES} resumes at a time.")

    texts: dict[str, str] = {}
    for upload in resumes:
        data = await upload.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(400, f"{upload.filename} is larger than 5 MB.")
        try:
            texts[upload.filename] = extract_text(upload.filename, data)
        except UnsupportedFileError as error:
            raise HTTPException(400, str(error))
        except Exception:
            raise HTTPException(400, f"Could not read {upload.filename}.")

    results = rank_resumes(job_description, texts)
    return {"weights": WEIGHTS, "results": [asdict(result) for result in results]}
