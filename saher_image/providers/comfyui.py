from __future__ import annotations

import json
import secrets
from pathlib import Path
from urllib.parse import urljoin

import httpx

from saher_image.contracts import JobState, JobStatus, OutputAsset


class ProviderError(RuntimeError):
    pass


class ComfyUIProvider:
    """Thin adapter for a private ComfyUI server using its documented HTTP API."""

    def __init__(
        self,
        base_url: str,
        workflow_path: str | Path,
        prompt_node_id: str,
        prompt_input: str = "text",
        timeout_seconds: float = 30,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.workflow_path = Path(workflow_path)
        self.prompt_node_id = str(prompt_node_id)
        self.prompt_input = prompt_input
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def _url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = self.client.request(method, self._url(path), **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            raise ProviderError(f"ComfyUI request failed: {exc}") from exc

    def _workflow(self, prompt: str) -> dict:
        try:
            workflow = json.loads(self.workflow_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ProviderError("Configured ComfyUI API workflow file is unavailable") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("Configured workflow is not valid JSON") from exc

        node = workflow.get(self.prompt_node_id)
        if not isinstance(node, dict):
            raise ProviderError("Prompt node ID is not present in the configured workflow")
        inputs = node.get("inputs")
        if not isinstance(inputs, dict) or self.prompt_input not in inputs:
            raise ProviderError("Prompt input is not present in the configured workflow node")
        inputs[self.prompt_input] = prompt
        for candidate in workflow.values():
            if not isinstance(candidate, dict) or candidate.get("class_type") != "KSampler":
                continue
            sampler_inputs = candidate.get("inputs")
            if isinstance(sampler_inputs, dict) and "seed" in sampler_inputs:
                sampler_inputs["seed"] = secrets.randbelow(2**53)
        return workflow

    def submit(self, prompt: str) -> str:
        workflow = self._workflow(prompt)
        payload = self._request("POST", "/prompt", json={"prompt": workflow}).json()
        prompt_id = payload.get("prompt_id")
        if not prompt_id:
            raise ProviderError("ComfyUI did not return a prompt_id")
        return str(prompt_id)

    @staticmethod
    def _assets(history_entry: dict) -> list[OutputAsset]:
        assets: list[OutputAsset] = []
        for node_output in history_entry.get("outputs", {}).values():
            for field in ("videos", "gifs", "images", "audio"):
                for item in node_output.get(field, []) or []:
                    filename = item.get("filename")
                    if not filename:
                        continue
                    ext = Path(filename).suffix.lower()
                    content_type = {
                        ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime",
                        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                        ".wav": "audio/wav", ".mp3": "audio/mpeg",
                    }.get(ext, "application/octet-stream")
                    assets.append(OutputAsset(
                        filename=filename,
                        subfolder=str(item.get("subfolder", "")),
                        media_type=str(item.get("type", "output")),
                        content_type=content_type,
                    ))
        return assets

    def status(self, job_id: str) -> JobStatus:
        history = self._request("GET", f"/history/{job_id}").json()
        entry = history.get(job_id)
        if entry:
            status_data = entry.get("status", {})
            status_text = str(status_data.get("status_str", "")).lower()
            if status_text == "error":
                return JobStatus(job_id, JobState.FAILED, error="ComfyUI reported a failed job")
            if status_data.get("completed") or status_text == "success" or entry.get("outputs"):
                return JobStatus(job_id, JobState.COMPLETED, self._assets(entry))
            return JobStatus(job_id, JobState.RUNNING)

        queue = self._request("GET", "/queue").json()
        if any(str(item[1]) == job_id for item in queue.get("queue_running", [])):
            return JobStatus(job_id, JobState.RUNNING)
        if any(str(item[1]) == job_id for item in queue.get("queue_pending", [])):
            return JobStatus(job_id, JobState.QUEUED)
        return JobStatus(job_id, JobState.UNKNOWN)

    def fetch_output(self, job_id: str, output_index: int) -> tuple[bytes, str]:
        status = self.status(job_id)
        if status.state != JobState.COMPLETED:
            raise ProviderError("Outputs are available only after successful completion")
        if output_index < 0 or output_index >= len(status.outputs):
            raise ProviderError("Output index is out of range")
        asset = status.outputs[output_index]
        response = self._request("GET", "/view", params={
            "filename": asset.filename,
            "subfolder": asset.subfolder,
            "type": asset.media_type,
        })
        return response.content, asset.content_type

    def close(self) -> None:
        self.client.close()
