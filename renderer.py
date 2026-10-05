"""Renderer: matplotlib (Agg) drawing + PNG serialization.

Pure drawing + PNG serialization for the five supported trigonometry
concepts. The matplotlib ``Agg`` backend is selected before importing
``pyplot`` so the module works headless (e.g. inside a container) with no
display server.

Each draw function returns a matplotlib ``Figure`` with the concept's formula
embedded as a visible text artist (via ``ax.set_title`` and/or ``fig.text``).
The embedded formula strings match the ones in ``concepts.py`` exactly:

- sine           -> "y = sin(x)"
- cosine         -> "y = cos(x)"
- tangent        -> "y = tan(x)"
- right triangle -> "a\u00b2 + b\u00b2 = c\u00b2"
- unit circle    -> "x\u00b2 + y\u00b2 = 1"
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import matplotlib

# Select a non-interactive backend BEFORE importing pyplot (headless-safe).
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow matplotlib.use)
import numpy as np  # noqa: E402

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.figure import Figure

    from concepts import Concept


# Formula text per concept. Kept in sync with ``concepts._FORMULAS`` so the
# formula visible in the figure matches the registry's formula exactly.
_SINE_FORMULA = "y = sin(x)"
_COSINE_FORMULA = "y = cos(x)"
_TANGENT_FORMULA = "y = tan(x)"
_RIGHT_TRIANGLE_FORMULA = "a\u00b2 + b\u00b2 = c\u00b2"
_UNIT_CIRCLE_FORMULA = "x\u00b2 + y\u00b2 = 1"


def draw_sine() -> "Figure":
    """Plot ``y = sin(x)`` and embed the formula as the title."""
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.linspace(-2 * np.pi, 2 * np.pi, 1000)
    ax.plot(x, np.sin(x), color="#1f77b4")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(0, color="gray", linewidth=0.8)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(_SINE_FORMULA)
    fig.tight_layout()
    return fig


def draw_cosine() -> "Figure":
    """Plot ``y = cos(x)`` and embed the formula as the title."""
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.linspace(-2 * np.pi, 2 * np.pi, 1000)
    ax.plot(x, np.cos(x), color="#ff7f0e")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(0, color="gray", linewidth=0.8)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(_COSINE_FORMULA)
    fig.tight_layout()
    return fig


def draw_tangent() -> "Figure":
    """Plot ``y = tan(x)`` (clipping extreme values near asymptotes)."""
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.linspace(-2 * np.pi, 2 * np.pi, 2000)
    y = np.tan(x)
    # Clip the near-vertical spikes around the asymptotes so the plot stays
    # readable; break the line where it would otherwise jump across the axis.
    clip = 10.0
    y = np.where(np.abs(y) > clip, np.nan, y)
    ax.plot(x, y, color="#2ca02c")
    ax.set_ylim(-clip, clip)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(0, color="gray", linewidth=0.8)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(_TANGENT_FORMULA)
    fig.tight_layout()
    return fig


def draw_right_triangle() -> "Figure":
    """Draw a labeled right triangle and embed ``a\u00b2 + b\u00b2 = c\u00b2``."""
    fig, ax = plt.subplots(figsize=(6, 4))

    # Right angle at the origin; legs along the axes.
    a = 4.0  # horizontal leg
    b = 3.0  # vertical leg
    vertices = [(0.0, 0.0), (a, 0.0), (0.0, b), (0.0, 0.0)]
    xs, ys = zip(*vertices)
    ax.plot(xs, ys, color="#9467bd", linewidth=2)

    # Right-angle marker at the origin.
    m = 0.4
    ax.plot([m, m, 0.0], [0.0, m, m], color="gray", linewidth=1)

    # Side labels.
    ax.text(a / 2, -0.35, "a", ha="center", va="top", fontsize=12)
    ax.text(-0.35, b / 2, "b", ha="right", va="center", fontsize=12)
    ax.text(a / 2 + 0.15, b / 2 + 0.15, "c", ha="left", va="bottom", fontsize=12)

    ax.set_xlim(-1, a + 1)
    ax.set_ylim(-1, b + 1)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title(_RIGHT_TRIANGLE_FORMULA)
    fig.tight_layout()
    return fig


def draw_unit_circle() -> "Figure":
    """Draw the unit circle and embed ``x\u00b2 + y\u00b2 = 1``."""
    fig, ax = plt.subplots(figsize=(5, 5))
    theta = np.linspace(0, 2 * np.pi, 1000)
    ax.plot(np.cos(theta), np.sin(theta), color="#d62728")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(0, color="gray", linewidth=0.8)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(_UNIT_CIRCLE_FORMULA)
    fig.tight_layout()
    return fig


def render_png(concept: "Concept") -> bytes:
    """Build the figure for ``concept`` and return non-empty PNG bytes.

    Calls the concept's draw function, serializes the resulting figure to PNG
    bytes via an in-memory buffer, and closes the figure afterwards to avoid
    leaking matplotlib resources.
    """
    fig = concept.draw()
    try:
        buffer = BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight")
        return buffer.getvalue()
    finally:
        plt.close(fig)
