"""Optional tracing to Langfuse Cloud over OpenTelemetry.

Off unless LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set (and the ``tracing`` extra is
installed). When on, every meal check becomes one trace:

- a ``meal_check`` span with what the flow did and how long each step took (an event per step),
  the verdict, the engine version and whether the explanation came from the model or the template;
- under it, the AI model calls (perception and explanation) as recorded by Pydantic AI, with
  token counts and latency.

What is sent: the de-identified text the models already receive, and the model's answers.
What is never sent: photos (binary content is left out), names (PII is scrubbed before any model
call, so traces only ever contain scrubbed text) and the patient's id (a one-way hash is used to
group a patient's traces).
"""

from __future__ import annotations

import base64
import hashlib
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

log = logging.getLogger("happygut.tracing")

_tracer: Any = None
_provider: Any = None


def enabled() -> bool:
    return _tracer is not None


def endpoint(host: str) -> str:
    """Langfuse's OpenTelemetry endpoint for traces."""
    return f"{host.rstrip('/')}/api/public/otel/v1/traces"


def auth_header(public_key: str, secret_key: str) -> str:
    return "Basic " + base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()


def setup(public_key: str, secret_key: str, host: str, *, environment: str, version: str, exporter: Any = None) -> bool:
    """Start exporting traces. ``exporter`` replaces the Langfuse exporter (tests)."""
    global _tracer, _provider
    if exporter is None and not (public_key and secret_key):
        return False
    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            SimpleSpanProcessor,
        )
        from pydantic_ai import Agent
        from pydantic_ai.models.instrumented import InstrumentationSettings
    except ImportError:
        log.warning("LANGFUSE keys are set but the tracing extra isn't installed: uv sync --extra tracing")
        return False
    provider = TracerProvider(resource=Resource.create({
        "service.name": "happygut-api", "service.version": version, "deployment.environment": environment,
    }))
    if exporter is None:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        exporter = OTLPSpanExporter(endpoint=endpoint(host), headers={"Authorization": auth_header(public_key, secret_key)})
        provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    Agent.instrument_all(InstrumentationSettings(tracer_provider=provider, include_binary_content=False))
    _provider, _tracer = provider, provider.get_tracer("happygut")
    log.info("tracing to %s", "test exporter" if exporter is not None and not public_key else endpoint(host))
    return True


def shutdown() -> None:
    """Flush and stop (tests, and process exit)."""
    global _tracer, _provider
    if _provider is not None:
        _provider.shutdown()
    _tracer = _provider = None
    try:
        from pydantic_ai import Agent

        Agent.instrument_all(False)
    except ImportError:
        pass


def pseudonym(patient_id: str) -> str:
    """A stable one-way id for grouping one patient's traces; the real id never leaves the backend."""
    return hashlib.sha256(f"happygut:{patient_id}".encode()).hexdigest()[:16]


class _NoSpan:
    def set_attribute(self, key: str, value: Any) -> None: ...
    def add_event(self, name: str, attributes: dict | None = None) -> None: ...


@contextmanager
def meal_check_span(**attributes: Any) -> Iterator[Any]:
    """The root span of one meal check; a no-op when tracing is off. Model calls made inside nest under it."""
    if _tracer is None:
        yield _NoSpan()
        return
    from opentelemetry import context, trace

    span = _tracer.start_span("meal_check", attributes={k: v for k, v in attributes.items() if v is not None})
    token = context.attach(trace.set_span_in_context(span))
    try:
        yield span
    except Exception as exc:
        span.record_exception(exc)
        span.set_status(trace.Status(trace.StatusCode.ERROR))
        raise
    finally:
        try:
            context.detach(token)
        except ValueError:  # the stream was closed from another context; the span still ends
            log.debug("trace context detached from another context")
        span.end()
