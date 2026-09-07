"""
Lab 5 - Auditing & Observability for Agents (SKELETON)

A REAL model drives the agent: for each natural-language request it picks a
tool to call. Instrument every tool call with REAL OpenTelemetry spans (trace
id, span id, attributes, status) under one session trace, then run an anomaly
detector over the captured spans to surface suspicious patterns.

NOTE: incomplete. Merge in instrument_call() and detect_anomalies() from
extra/observable_agent_complete.txt before running.
"""
import json
import os
import re
import sys

# Real OpenTelemetry: a TracerProvider makes spans, an in-memory exporter
# collects them so the anomaly detector can read them back at the end.
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status, StatusCode

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
import llm


# ===========================================================================
#  HOW ONE REQUEST FLOWS THROUGH THIS FILE
#
#      (user, request) -> instrument_call()     opens a "tool.call" span
#                           -> choose_tool()     the real model picks a tool
#                           -> authorize()       allowed / denied
#                           -> span attributes   user, tool, sensitive, status
#                           -> [AUDIT] line      trace_id / span_id printed
#      ...after all 7 requests:
#      detect_anomalies(spans) -> denied calls, sensitive-tool bursts, review list
#
#  Nothing here PREVENTS a bad call - this lab is the detective layer.
# ===========================================================================

# ---------------------------------------------------------------------------
#  THE AGENT (provided) - tools, the model's tool-picking prompt, a scripted
#  session of 7 requests (mallory's three exports are the burst to catch)
# ---------------------------------------------------------------------------
TOOLS = ["lookup_benefits", "check_pto", "export_employee_data", "send_company_email"]
SENSITIVE_TOOLS = {"export_employee_data", "send_company_email", "update_salary"}

TOOL_SYSTEM = (
    "You are an HR agent that selects exactly ONE tool to handle each request. "
    "Available tools: lookup_benefits, check_pto, export_employee_data, "
    "send_company_email. Respond with ONLY a JSON object of the form "
    '{"tool": "<tool_name>", "args": {...}} and no other text.'
)

REQUESTS = [
    ("alice", "What are my dental benefits?"),
    ("alice", "How many PTO days does employee E1001 have?"),
    ("mallory", "Export all employee records from the Engineering department."),
    ("mallory", "Now export the Sales team's records too."),
    ("mallory", "And export the Finance department records as well."),
    ("bob", "Send an email to all-staff announcing a mandatory password reset."),
    ("alice", "What benefits does employee E1002 have?"),
]


def choose_tool(request):
    """Ask the real model which tool to call; parse its JSON answer."""
    raw = llm.complete(request, system=TOOL_SYSTEM, prefer="strong", max_tokens=200)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        obj = json.loads(m.group(0))
        return obj.get("tool", "unknown"), obj.get("args", {})
    except Exception:
        return "unknown", {"raw": raw[:40]}


def authorize(user, tool):
    """Simple policy stub: only alice may invoke sensitive tools."""
    return not (tool in SENSITIVE_TOOLS and user != "alice")


# ---------------------------------------------------------------------------
#  WHAT YOU BUILD - instrument_call() records; detect_anomalies() reviews
# ---------------------------------------------------------------------------
def instrument_call(tracer, user, request):
    """Run one agent turn inside an OpenTelemetry span with rich attributes."""
    # TODO (merge): open a span, call choose_tool(), set attributes
    # (user, tool, args, sensitive, status), mark denied calls ERROR, and
    # print a compact [AUDIT] line with the span's trace_id / span_id.
    raise NotImplementedError("instrument_call not implemented yet")


def detect_anomalies(spans):
    """Flag suspicious patterns in the captured spans."""
    # TODO (merge): denied calls, sensitive-tool bursts (3+), review list
    raise NotImplementedError("detect_anomalies not implemented yet")


# ---------------------------------------------------------------------------
#  TRACER SETUP + MAIN (provided)
# ---------------------------------------------------------------------------
def build_tracer():
    """Provided: set up a real OTel tracer with an in-memory span exporter."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer("omnitech.agent"), exporter


def main():
    tracer, exporter = build_tracer()
    print(f"=== OBSERVABLE AGENT (OpenTelemetry; model {llm.active_backend('strong')}) ===\n")
    with tracer.start_as_current_span("agent.session") as session:
        tid = format(session.get_span_context().trace_id, "032x")[:12]
        print(f"session trace_id = {tid}\n")
        for user, request in REQUESTS:
            instrument_call(tracer, user, request)

    spans = [s for s in exporter.get_finished_spans() if "tool" in s.attributes]
    print("\n=== TELEMETRY SUMMARY ===")
    print(f"  tool spans      : {len(spans)}")
    print(f"  sensitive calls : {sum(bool(s.attributes.get('sensitive')) for s in spans)}")
    print(f"  denied calls    : {sum(s.attributes.get('status') == 'denied' for s in spans)}")

    print("\n=== ANOMALY DETECTION ===")
    for f in detect_anomalies(spans):
        print(f"  [!] {f}")
    print()


if __name__ == "__main__":
    main()
