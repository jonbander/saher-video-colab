import json

import httpx
import pytest

from saher_video.contracts import JobState
from saher_video.providers.comfyui import ComfyUIProvider, ProviderError


def make_provider(tmp_path, handler):
    workflow = tmp_path / "workflow.json"
    workflow.write_text(json.dumps({"6": {"inputs": {"text": "placeholder"}}}))
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return ComfyUIProvider("http://comfy.test", workflow, "6", "text", client=client)


def test_submit_injects_prompt_into_selected_api_node(tmp_path):
    def handler(request):
        assert request.method == "POST"
        payload = json.loads(request.content)
        assert payload["prompt"]["6"]["inputs"]["text"] == "a lighthouse at dusk"
        return httpx.Response(200, json={"prompt_id": "0123456789abcdef0123456789abcdef"})

    provider = make_provider(tmp_path, handler)
    assert provider.submit("a lighthouse at dusk") == "0123456789abcdef0123456789abcdef"


def test_missing_prompt_node_is_reported(tmp_path):
    workflow = tmp_path / "workflow.json"
    workflow.write_text('{"3":{"inputs":{}}}')
    provider = ComfyUIProvider("http://comfy.test", workflow, "6", client=httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200))))
    with pytest.raises(ProviderError, match="node ID"):
        provider.submit("prompt")


def test_completed_job_extracts_video_output(tmp_path):
    job_id = "0123456789abcdef0123456789abcdef"
    def handler(request):
        if request.url.path == f"/history/{job_id}":
            return httpx.Response(200, json={job_id: {"status": {"completed": True, "status_str": "success"}, "outputs": {"9": {"videos": [{"filename": "result.mp4", "subfolder": "", "type": "output"}]}}}})
        return httpx.Response(200, content=b"video-data")

    provider = make_provider(tmp_path, handler)
    status = provider.status(job_id)
    assert status.state == JobState.COMPLETED
    assert status.outputs[0].filename == "result.mp4"
    assert provider.fetch_output(job_id, 0) == (b"video-data", "video/mp4")


def test_queued_job_is_found_in_queue(tmp_path):
    job_id = "0123456789abcdef0123456789abcdef"
    def handler(request):
        if request.url.path == f"/history/{job_id}":
            return httpx.Response(200, json={})
        return httpx.Response(200, json={"queue_running": [], "queue_pending": [[1, job_id]]})

    provider = make_provider(tmp_path, handler)
    assert provider.status(job_id).state == JobState.QUEUED
