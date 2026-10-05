"""Flask application for Trigonometry Visualizer.

Wires together the concepts registry, renderer, explainer, and docs modules
into three HTTP routes:

- ``GET /``                         serve the single HTML page in its empty state
- ``GET /render?concept=X``         return a PNG for the concept (download toggle)
- ``GET /explain?concept=X``        return a JSON plain-English explanation

The render path validates input through ``concepts.get`` and returns a 400 JSON
error listing the five supported concepts on invalid/out-of-scope input. The
explain path always returns HTTP 200 and delegates graceful degradation to
``explainer.explain`` so an unavailable AI service never breaks the response.
"""

from __future__ import annotations

from flask import Flask, Response, jsonify, render_template, request

import concepts
import explainer
import renderer

app = Flask(__name__)


def _invalid_concept_response() -> tuple[Response, int]:
    """Build the standard 400 JSON error listing the five supported concepts.

    Used for empty, over-length, and out-of-scope input (Req 1.4, 1.5, 2.2).
    """
    payload = {
        "error": (
            "Unsupported concept. Choose one of the supported concepts: "
            + ", ".join(concepts.SUPPORTED)
            + "."
        ),
        "supported": list(concepts.SUPPORTED),
    }
    return jsonify(payload), 400


@app.route("/", methods=["GET"])
def index() -> str:
    """Serve the single HTML page in its empty state (Req 6.1, 6.2).

    The template renders with no figure, formula, download control, or
    explanation until the Learner selects a concept client-side. The supported
    concepts and their formulas are passed so the page can show the formula
    adjacent to the figure once one is rendered (Req 2.5).
    """
    formulas = {
        name: concepts.REGISTRY[name].formula for name in concepts.SUPPORTED
    }
    return render_template(
        "index.html", supported=concepts.SUPPORTED, formulas=formulas
    )


@app.route("/render", methods=["GET"])
def render():
    """Return a PNG for ``?concept=X`` or a 400 JSON error on invalid input.

    On a supported concept, returns 200 ``image/png`` with the rendered figure.
    When ``?download=1`` is present, sets ``Content-Disposition: attachment`` so
    the browser downloads the file instead of displaying it inline (Req 3.2).
    Invalid, empty, over-length, or out-of-scope input yields the standard 400
    JSON error listing the five supported concepts (Req 2.2, 2.3).
    """
    raw = request.args.get("concept", "")
    concept = concepts.get(raw)
    if concept is None:
        return _invalid_concept_response()

    png_bytes = renderer.render_png(concept)

    download = request.args.get("download") == "1"
    filename = concept.name.replace(" ", "_") + ".png"
    disposition = "attachment" if download else "inline"

    response = Response(png_bytes, mimetype="image/png")
    response.headers["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    return response


@app.route("/explain", methods=["GET"])
def explain():
    """Return a JSON explanation for ``?concept=X`` (always HTTP 200).

    Looks up the concept's formula and delegates to ``explainer.explain``, which
    never raises and degrades gracefully to a friendly fallback when the AI
    service is slow, erroring, or unreachable (Req 4.1, 4.5, 5.5). Returns
    ``{"available": bool, "explanation": str}``.

    When the concept is out of scope there is no formula to explain, so the
    response reports ``available=False`` with a guidance message while still
    returning HTTP 200.
    """
    raw = request.args.get("concept", "")
    concept = concepts.get(raw)
    if concept is None:
        message = (
            "No explanation is available for that input. Choose a supported "
            "concept: " + ", ".join(concepts.SUPPORTED) + "."
        )
        return jsonify({"available": False, "explanation": message}), 200

    result = explainer.explain(concept.name, concept.formula)
    return (
        jsonify({"available": result.available, "explanation": result.explanation}),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
