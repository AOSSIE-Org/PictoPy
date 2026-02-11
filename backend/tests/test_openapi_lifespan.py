import pytest
from fastapi import FastAPI
from main import generate_openapi_json


def test_openapi_failure_does_not_crash_app(monkeypatch):
    def broken_openapi(*args, **kwargs):
        raise Exception("Simulated failure")

    monkeypatch.setattr(
        "main.get_openapi",
        broken_openapi
    )

    app = FastAPI()

    try:
        generate_openapi_json()
        started = True
    except Exception:
        started = False

    assert started, "App should not crash if OpenAPI generation fails"

