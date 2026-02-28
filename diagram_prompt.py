"""Diagram prompt builder -- creates image generation prompts from plans."""

from __future__ import annotations

from diagram_planner import DiagramPlan


def build_diagram_prompt(plan: DiagramPlan, title: str = "") -> str:
    """Build a text prompt for generating a clean educational diagram.

    Parameters
    ----------
    plan : DiagramPlan
        Structured plan with inputs, processes, and outputs.
    title : str
        Optional paper/post title for additional context.

    Returns
    -------
    str
        A fully-formed prompt suitable for image generation APIs.
    """
    flow = plan.flow_description

    prompt_parts = [
        "A clean educational scientific diagram showing the following concept flow:",
        f"  {flow}",
        "",
        "Style requirements:",
        "- White background",
        "- Minimalistic design",
        "- Labeled boxes or circles for each component",
        "- Clear arrows connecting components left to right",
        "- Textbook-style illustration",
        "- Use simple, readable sans-serif font for labels",
        "- Each component clearly labeled with its name",
        "- No artistic embellishments, no gradients",
        "- No logos, no watermarks",
        "- No photographs of people or faces",
        "- No copied figures from papers",
        "- Professional scientific infographic style",
        "- Suitable for email at 500px width",
    ]

    if title:
        prompt_parts.insert(2, f"  Topic: {title[:80]}")

    return "\n".join(prompt_parts)
