"""Concepts registry: single source of truth for the Supported_Scope.

Maps each supported concept to its formula and matplotlib draw function.
The draw functions live in ``renderer`` and are imported lazily so that this
module stays importable even before ``renderer`` implements them (task 3).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.figure import Figure


@dataclass(frozen=True)
class Concept:
    """A supported trigonometry concept.

    Attributes:
        name: Canonical name, e.g. ``"sine"``.
        formula: Formula text, e.g. ``"y = sin(x)"``.
        draw: Callable building a matplotlib ``Figure`` that embeds the formula.
    """

    name: str
    formula: str
    draw: "Callable[[], Figure]"


# Canonical scope. Order matches the five supported concepts.
SUPPORTED = ["sine", "cosine", "tangent", "right triangle", "unit circle"]

# Formula text per canonical concept name.
_FORMULAS = {
    "sine": "y = sin(x)",
    "cosine": "y = cos(x)",
    "tangent": "y = tan(x)",
    "right triangle": "a\u00b2 + b\u00b2 = c\u00b2",
    "unit circle": "x\u00b2 + y\u00b2 = 1",
}

# Canonical concept name -> name of the draw function in ``renderer``.
_DRAW_FUNCS = {
    "sine": "draw_sine",
    "cosine": "draw_cosine",
    "tangent": "draw_tangent",
    "right triangle": "draw_right_triangle",
    "unit circle": "draw_unit_circle",
}


def _make_lazy_draw(func_name: str) -> "Callable[[], Figure]":
    """Return a thunk that imports ``renderer.<func_name>`` on first call.

    Deferring the import keeps ``concepts.py`` importable even if ``renderer``
    does not yet define the draw functions. The lookup happens only when the
    figure is actually requested.
    """

    def _draw() -> "Figure":
        import renderer

        try:
            func = getattr(renderer, func_name)
        except AttributeError as exc:  # pragma: no cover - defensive
            raise NotImplementedError(
                f"renderer.{func_name} is not implemented yet"
            ) from exc
        return func()

    _draw.__name__ = func_name
    _draw.__qualname__ = func_name
    return _draw


# Canonical name -> Concept.
REGISTRY: dict[str, Concept] = {
    name: Concept(
        name=name,
        formula=_FORMULAS[name],
        draw=_make_lazy_draw(_DRAW_FUNCS[name]),
    )
    for name in SUPPORTED
}


def normalize(raw: str) -> str | None:
    """Trim, lowercase, and collapse internal spaces; return canonical name or None.

    Rules (Req 1.3, 1.4, 1.5):
    - Strip leading/trailing whitespace, lowercase, and collapse runs of
      internal whitespace to a single space before matching.
    - Reject empty/whitespace-only input and input longer than 100 characters
      (measured on the raw input) by returning ``None``.
    - Return the canonical name when it matches a supported concept, else None.
    """

    if not isinstance(raw, str):
        return None

    if len(raw) > 100:
        return None

    cleaned = re.sub(r"\s+", " ", raw.strip()).lower()
    if not cleaned:
        return None

    return cleaned if cleaned in REGISTRY else None


def get(raw: str) -> Concept | None:
    """Return the Concept for a raw input, or None if out of scope / invalid."""

    canonical = normalize(raw)
    if canonical is None:
        return None
    return REGISTRY[canonical]
