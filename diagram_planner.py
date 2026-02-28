"""Diagram planner -- converts a summary into conceptual components."""

from __future__ import annotations

from dataclasses import dataclass
from llm_client import generate_completion
from logger import setup_logger

log = setup_logger()

_PLANNER_SYSTEM = (
    "You are a scientific diagram planner. Given a research summary, "
    "identify the key conceptual stages for a simple explanatory diagram. "
    "Output ONLY the components in the exact format specified."
)

_PLANNER_PROMPT = (
    "Read this research summary and extract 3-6 conceptual components for "
    "a simple educational diagram.\n"
    "\n"
    "Identify:\n"
    "• Input(s): What goes in (data, signals, stimuli)?\n"
    "• Process(es): What transformation or method is applied?\n"
    "• Output(s): What is the result or prediction?\n"
    "\n"
    "Respond ONLY in this format, one component per line:\n"
    "Input: <description>\n"
    "Process: <description>\n"
    "Output: <description>\n"
    "\n"
    "You may include up to 2 Process steps if the research involves "
    "multiple stages. Keep each description under 6 words.\n"
    "\n"
    "Summary:\n"
    "{summary}\n"
)


@dataclass
class DiagramPlan:
    """Structured plan for generating a concept diagram."""
    inputs: list[str]
    processes: list[str]
    outputs: list[str]

    @property
    def components(self) -> list[str]:
        """Return all components as a flat list."""
        return self.inputs + self.processes + self.outputs

    @property
    def flow_description(self) -> str:
        """Return a human-readable flow description for prompt building."""
        parts = []
        for inp in self.inputs:
            parts.append(inp)
        for proc in self.processes:
            parts.append(proc)
        for out in self.outputs:
            parts.append(out)
        return " → ".join(parts)


def _parse_plan(raw_text: str) -> DiagramPlan | None:
    """Parse the LLM output into a structured DiagramPlan."""
    inputs: list[str] = []
    processes: list[str] = []
    outputs: list[str] = []

    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        lower = line.lower()
        if lower.startswith("input:"):
            val = line.split(":", 1)[1].strip()
            if val:
                inputs.append(val)
        elif lower.startswith("process:"):
            val = line.split(":", 1)[1].strip()
            if val:
                processes.append(val)
        elif lower.startswith("output:"):
            val = line.split(":", 1)[1].strip()
            if val:
                outputs.append(val)

    # Must have at least one of each
    if not inputs or not processes or not outputs:
        return None

    total = len(inputs) + len(processes) + len(outputs)
    if total < 3 or total > 6:
        return None

    return DiagramPlan(inputs=inputs, processes=processes, outputs=outputs)


def create_diagram_plan(summary_text: str) -> DiagramPlan | None:
    """Convert a summary into a structured diagram plan.

    Parameters
    ----------
    summary_text : str
        The (possibly refined) summary text.

    Returns
    -------
    DiagramPlan | None
        A structured plan, or ``None`` if the LLM output can't be parsed.
    """
    if not summary_text or not summary_text.strip():
        return None

    prompt = _PLANNER_PROMPT.format(summary=summary_text)

    try:
        raw = generate_completion(prompt, system_prompt=_PLANNER_SYSTEM)
        if not raw:
            log.warning("Diagram planner returned no output")
            return None

        plan = _parse_plan(raw)
        if plan:
            log.debug("Diagram plan created: %s", plan.flow_description)
        else:
            log.warning("Failed to parse diagram plan from LLM output")
        return plan

    except Exception as exc:
        log.warning("Diagram planning failed: %s", exc)
        return None
