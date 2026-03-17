from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from .config import DEFAULT_CONFIG
from .enrollment import enroll_speaker
from .pipeline import process_meeting
from .storage import ProfileStore


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = DEFAULT_CONFIG.workspace_dir / "uploads"


@dataclass
class JobState:
    job_id: str
    status: str
    filename: str
    language: str | None
    report_path: str | None = None
    segment_count: int | None = None
    error: str | None = None


app = FastAPI(title="SAMAudio Web")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
jobs: dict[str, JobState] = {}


def _workspace_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def _copy_upload(upload: UploadFile, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    upload.file.seek(0)
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return destination


def _list_reports() -> list[dict]:
    if not DEFAULT_CONFIG.export_dir.exists():
        return []

    reports: list[dict] = []
    for report_path in sorted(DEFAULT_CONFIG.export_dir.glob("*/meeting_report.json"), reverse=True):
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        reports.append(
            {
                "id": report_path.parent.name,
                "report_path": str(report_path),
                "meeting_audio": payload.get("meeting_audio"),
                "generated_at": payload.get("generated_at"),
                "segment_count": len(payload.get("segments", [])),
                "segments": payload.get("segments", []),
                "markdown_path": str(report_path.with_name("meeting_report.md")),
            }
        )
    return reports


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/speakers")
async def speakers() -> list[dict]:
    profiles = ProfileStore(DEFAULT_CONFIG).load_all_profiles()
    return [
        {
            "speaker_id": profile.speaker_id,
            "display_name": profile.display_name,
            "sample_count": len(profile.samples),
            "samples": [asdict(sample) for sample in profile.samples],
        }
        for profile in profiles
    ]


@app.post("/api/speakers")
async def create_speaker(
    speaker_id: str = Form(...),
    name: str = Form(...),
    files: list[UploadFile] = File(...),
) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="At least one audio file is required.")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        saved_files: list[str] = []
        for upload in files:
            filename = upload.filename or f"{uuid.uuid4()}.wav"
            saved = _copy_upload(upload, temp_root / filename)
            saved_files.append(str(saved))

        profile = enroll_speaker(
            speaker_id=speaker_id,
            display_name=name,
            audio_paths=saved_files,
            store=ProfileStore(DEFAULT_CONFIG),
        )

    return {
        "speaker_id": profile.speaker_id,
        "display_name": profile.display_name,
        "sample_count": len(profile.samples),
    }


def _run_meeting_job(job_id: str, audio_path: str, language: str | None) -> None:
    job = jobs[job_id]
    job.status = "running"
    try:
        report_path, segments = process_meeting(audio_path, language=language)
        job.status = "completed"
        job.report_path = str(report_path)
        job.segment_count = len(segments)
    except Exception as exc:  # pragma: no cover
        job.status = "failed"
        job.error = str(exc)


@app.post("/api/meetings")
async def create_meeting_job(
    file: UploadFile = File(...),
    language: str = Form("ja"),
) -> dict:
    filename = file.filename or f"{uuid.uuid4()}.wav"
    job_id = uuid.uuid4().hex
    destination = _copy_upload(file, _workspace_upload_dir() / f"{job_id}_{filename}")
    jobs[job_id] = JobState(
        job_id=job_id,
        status="queued",
        filename=filename,
        language=language,
    )
    asyncio.create_task(asyncio.to_thread(_run_meeting_job, job_id, str(destination), language))
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return asdict(job)


@app.get("/api/reports")
async def reports() -> list[dict]:
    return _list_reports()


@app.get("/api/reports/{report_id}")
async def report_detail(report_id: str) -> dict:
    report_path = DEFAULT_CONFIG.export_dir / report_id / "meeting_report.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")
    return json.loads(report_path.read_text(encoding="utf-8"))


def run() -> None:
    uvicorn.run("samaudio.webapp:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
