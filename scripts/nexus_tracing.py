"""Tracing mínimo do NEXUS·AI.

Cada span registra tempos MEDIDOS (time.perf_counter), hierarquia pai/filho, atributos
e status. O resultado é salvo em JSON (lido pelo painel / gerador de relatórios).

Opcional: se `opentelemetry-sdk` e `opentelemetry-exporter-otlp-proto-http` estiverem
instalados e houver um coletor (ex.: Phoenix local em http://localhost:6006), o mesmo
trace também é enviado via OTLP com `export_otlp()`.
"""
from __future__ import annotations

import contextlib
import functools
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


class Tracer:
    def __init__(self, service: str = "nexus-ai"):
        self.service = service
        self.trace_id = uuid.uuid4().hex
        self.spans: list[dict] = []
        self._t0 = time.perf_counter()
        self._epoch_ns0 = time.time_ns()
        self._started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._local = threading.local()

    def _stack(self) -> list:
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        return self._local.stack

    @contextlib.contextmanager
    def span(self, name: str, **attributes):
        stack = self._stack()
        span = {
            "span_id": uuid.uuid4().hex[:16],
            "parent_id": stack[-1] if stack else None,
            "name": name,
            "attributes": dict(attributes),
            "status": "ok",
            "error": None,
        }
        start = time.perf_counter()
        span["start_ms"] = round((start - self._t0) * 1000, 3)
        stack.append(span["span_id"])
        try:
            yield span
        except BaseException as exc:  # registra e propaga
            span["status"] = "error"
            span["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            span["duration_ms"] = round((time.perf_counter() - start) * 1000, 3)
            stack.pop()
            self.spans.append(span)

    def trace(self, name: str | None = None):
        """Decorator: @tracer.trace("nome") registra cada chamada como um span."""

        def deco(fn):
            @functools.wraps(fn)
            def wrapper(*a, **kw):
                with self.span(name or fn.__name__):
                    return fn(*a, **kw)

            return wrapper

        return deco

    def to_dict(self) -> dict:
        spans = sorted(self.spans, key=lambda s: s["start_ms"])
        total = max((s["start_ms"] + s["duration_ms"] for s in spans), default=0.0)
        return {
            "trace_id": self.trace_id,
            "service": self.service,
            "started_at_utc": self._started_at,
            "total_ms": round(total, 3),
            "spans": spans,
        }

    def save(self, path: str | os.PathLike) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    def export_otlp(self, endpoint: str | None = None, project: str = "nexus-ai") -> bool:
        """Reenvia os spans já medidos para um coletor OTLP (ex.: Phoenix).

        Retorna False (sem erro) se não houver endpoint ou se as bibliotecas OpenTelemetry
        não estiverem instaladas.
        """
        endpoint = endpoint or os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
        if not endpoint:
            return False
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        except ImportError:
            return False

        endpoint = endpoint.rstrip("/")
        if not endpoint.endswith("/v1/traces"):
            endpoint += "/v1/traces"
        provider = TracerProvider(
            resource=Resource.create(
                {"service.name": self.service, "openinference.project.name": project}
            )
        )
        provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        tracer = provider.get_tracer("nexus")
        made: dict = {}
        for s in sorted(self.spans, key=lambda x: x["start_ms"]):
            ctx = trace.set_span_in_context(made[s["parent_id"]]) if s["parent_id"] in made else None
            start_ns = self._epoch_ns0 + int(s["start_ms"] * 1e6)
            end_ns = start_ns + int(s["duration_ms"] * 1e6)
            attrs = {
                k: (v if isinstance(v, (str, int, float, bool)) else str(v))
                for k, v in s["attributes"].items()
            }
            sp = tracer.start_span(s["name"], context=ctx, start_time=start_ns, attributes=attrs)
            sp.end(end_time=end_ns)
            made[s["span_id"]] = sp
        provider.force_flush()
        return True
