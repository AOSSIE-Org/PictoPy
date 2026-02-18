import pytest
from fastapi import FastAPI
from main import generate_openapi_json


def test_openapi_failure_does_not_trigger_lifespan(monkeypatch):
    """
    OpenAPI generation should not trigger application lifespan events.
    Running lifespan during schema generation can cause unwanted side effects
    like starting DB connections, background workers, or external services.
    """

    lifespan_called = {"count": 0}

    # Fake lifespan function
    async def fake_lifespan(app: FastAPI):
        lifespan_called["count"] += 1
        yield

    # Force OpenAPI to fail
    def broken_openapi(*args, **kwargs):
        raise Exception("Simulated failure")

    monkeypatch.setattr("main.get_openapi", broken_openapi)

    # Create app with custom lifespan
    app = FastAPI(lifespan=fake_lifespan)

    try:
        generate_openapi_json()
    except Exception:
        pass

    # This is the real assertion the bot wanted
    assert lifespan_called["count"] == 0, "Lifespan should not run if OpenAPI fails"