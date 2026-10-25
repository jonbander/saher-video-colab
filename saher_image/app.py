from pathlib import Path
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from saher_image.config import Settings
from saher_image.providers.comfyui import ComfyUIProvider, ProviderError

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web" / "static"
settings = Settings.from_env()
provider = None
if settings.workflow_path.is_file():
    provider = ComfyUIProvider(
        base_url=settings.comfyui_base_url,
        workflow_path=settings.workflow_path,
        prompt_node_id=settings.prompt_node_id,
        prompt_input=settings.prompt_input,
        timeout_seconds=settings.timeout_seconds,
    )

app = FastAPI(title="Saher Image API", version="0.2.0")
JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)


def get_provider() -> ComfyUIProvider:
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="لم يتم إعداد ملف workflow API صالح لتوليد الصور. راجع docs/quickstart-ar.md.",
        )
    return provider


def validate_job_id(job_id: str) -> str:
    if not JOB_ID_PATTERN.fullmatch(job_id):
        raise HTTPException(status_code=404, detail="معرّف المهمة غير صالح")
    return job_id


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return (WEB / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "provider_configured": provider is not None}


@app.post("/api/v1/jobs", status_code=202)
def submit_job(request: GenerateRequest) -> dict:
    engine = get_provider()
    try:
        job_id = engine.submit(request.prompt.strip())
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"job_id": job_id, "state": "queued"}


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    engine = get_provider()
    try:
        result = engine.status(validate_job_id(job_id))
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "job_id": result.job_id,
        "state": result.state.value,
        "error": result.error,
        "outputs": [
            {"index": i, "filename": item.filename, "content_type": item.content_type,
             "url": f"/api/v1/jobs/{result.job_id}/outputs/{i}"}
            for i, item in enumerate(result.outputs)
        ],
    }


@app.get("/api/v1/jobs/{job_id}/outputs/{output_index}")
def get_output(job_id: str, output_index: int) -> Response:
    engine = get_provider()
    try:
        content, content_type = engine.fetch_output(validate_job_id(job_id), output_index)
    except ProviderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(content=content, media_type=content_type,
                    headers={"Content-Disposition": "inline", "X-Content-Type-Options": "nosniff"})


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)
