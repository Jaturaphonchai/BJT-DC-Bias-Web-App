"""Flask application — รับ HTTP request แล้วเรียกสมการจาก dc_bias.py"""

from flask import Flask, render_template, request

from dc_bias import (
    ValidationError,
    calculate_dc_bias,
    calculate_dc_bias_approx,
    parse_inputs,
)

app = Flask(__name__)

REGION_LABELS = {
    "active": "Active (Forward-Active)",
    "cutoff": "Cutoff",
    "saturation": "Saturation",
}

DEFAULT_VALUES = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}


@app.get("/")
def index():
    return render_template(
        "index.html",
        values=DEFAULT_VALUES,
        errors={},
        result=None,
        approx=None,
    )


@app.post("/calculate")
def calculate():
    values = {field: request.form.get(field, "") for field in DEFAULT_VALUES}

    try:
        inputs = parse_inputs(request.form)
    except ValidationError as exc:
        return render_template(
            "index.html",
            values=values,
            errors=exc.errors,
            result=None,
        )

    return render_template(
        "index.html",
        values=values,
        errors={},
        result=calculate_dc_bias(inputs),
        approx=calculate_dc_bias_approx(inputs),
        beta_re_kohm=(inputs.beta + 1.0) * inputs.re,
        region_labels=REGION_LABELS,
    )


if __name__ == "__main__":
    app.run(debug=True)
