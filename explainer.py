"""Explainer: Ollama client with graceful degradation.

Calls a local Ollama service to produce a plain-English explanation of a
trigonometry concept. Every failure mode (timeout, connection error, non-200
response, or malformed body) is absorbed and mapped to a friendly fallback so
the core figure/formula/download experience always keeps working.
"""

import os
from dataclasses import dataclass

import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
TIMEOUT_SECONDS = 30

# Shown whenever the AI explanation cannot be produced for any reason.
FRIENDLY_UNAVAILABLE_MESSAGE = (
    "The AI explanation is unavailable right now, but the figure, formula, and "
    "PNG download still work. Please try the explanation again in a moment."
)

# Defensive truncation window for the returned explanation text (Req 4.4).
MIN_EXPLANATION_LENGTH = 1
MAX_EXPLANATION_LENGTH = 2000


@dataclass
class Explanation:
    """Result of an explanation request.

    Attributes:
        available: True when the Explainer_Service returned a usable explanation.
        explanation: The plain-English explanation, or the friendly fallback
            message when ``available`` is False.
    """

    available: bool
    explanation: str


def _build_prompt(concept_name: str, formula: str) -> str:
    """Build a short prompt from the concept name and its formula."""
    return (
        "Explain the trigonometry concept "
        f'"{concept_name}" (formula: {formula}) in plain English for a student '
        "who is just starting to learn trigonometry. Keep it short and friendly."
    )


def explain(concept_name: str, formula: str) -> Explanation:
    """Call Ollama ``/api/generate`` and return an :class:`Explanation`.

    On success (HTTP 200 with a valid JSON body containing a ``response``
    field), returns ``Explanation(available=True, text)`` with the text
    truncated to the 1-2000 character window. On any failure mode — timeout,
    connection error, other request error, non-200 status, or JSON/parse
    error — returns ``Explanation(available=False, FRIENDLY_UNAVAILABLE_MESSAGE)``.

    This function never raises.
    """
    prompt = _build_prompt(concept_name, formula)
    payload = {"model": MODEL, "prompt": prompt, "stream": False}

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        return _fallback()
    except requests.exceptions.ConnectionError:
        return _fallback()
    except requests.exceptions.RequestException:
        return _fallback()

    if response.status_code != 200:
        return _fallback()

    try:
        body = response.json()
        text = body["response"]
    except (ValueError, KeyError, TypeError):
        return _fallback()

    if not isinstance(text, str) or len(text) < MIN_EXPLANATION_LENGTH:
        return _fallback()

    return Explanation(available=True, explanation=text[:MAX_EXPLANATION_LENGTH])


def _fallback() -> Explanation:
    """Return the graceful-degradation fallback explanation."""
    return Explanation(available=False, explanation=FRIENDLY_UNAVAILABLE_MESSAGE)
