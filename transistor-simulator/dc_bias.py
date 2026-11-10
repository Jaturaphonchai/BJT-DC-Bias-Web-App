"""สมการและ validation สำหรับ DC Bias ของ BJT Common-Emitter (Voltage Divider)

โมดูลนี้ไม่รู้จัก Flask, HTTP หรือ HTML เลย — รับค่าตัวเลขเข้าและคืนผลลัพธ์เป็น object
ค่าความต้านทานที่รับเข้ามีหน่วยเป็น kΩ และแปลงเป็น Ω ภายในฟังก์ชันเดียว
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

VCE_SAT = 0.2  # V — ขอบ Saturation ที่ใช้ในแบบจำลองนี้

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")


class ValidationError(Exception):
    """ข้อมูลเข้าผิดรูปแบบหรือผิดหลักไฟฟ้า — เก็บข้อความแยกตามชื่อช่อง"""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("; ".join(errors.values()))
        self.errors = errors


@dataclass(frozen=True)
class BiasInputs:
    """ค่าอุปกรณ์ของวงจร (R เป็น kΩ, V เป็น V, β ไม่มีหน่วย)"""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


@dataclass(frozen=True)
class BiasResult:
    """ผลการคำนวณ DC Operating Point (V เป็น V, I เป็น mA)"""

    vth: float
    rth_kohm: float
    ib_ma: float
    ic_ma: float
    ie_ma: float
    ve: float
    vb: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ApproxResult:
    """ผลจากวิธีประมาณ (ละ IB) — VB ≈ VTH, IE ≈ VE/RE, IC ≈ IE"""

    vth: float
    vb: float
    ve: float
    vc: float
    vce: float
    ib_ma: float
    ic_ma: float
    ie_ma: float


def parse_inputs(form: Mapping[str, str]) -> BiasInputs:
    """แปลงข้อมูลจากฟอร์มเป็น BiasInputs หรือโยน ValidationError"""

    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    for field in FIELDS:
        raw = (form.get(field) or "").strip()
        if not raw:
            errors[field] = "กรุณากรอกค่านี้"
            continue
        try:
            values[field] = float(raw)
        except ValueError:
            errors[field] = "ต้องเป็นตัวเลข"

    if "vcc" in values and values["vcc"] <= 0:
        errors["vcc"] = "ต้องมากกว่า 0 V"

    for field in ("r1", "r2", "rc", "re"):
        if field in values and values[field] <= 0:
            errors[field] = "ต้องมากกว่า 0 kΩ"

    if "beta" in values and values["beta"] <= 0:
        errors["beta"] = "ต้องมากกว่า 0"

    if "vbe" in values:
        if values["vbe"] < 0:
            errors["vbe"] = "ต้องไม่ติดลบ"
        elif "vcc" in values and values["vcc"] > 0 and values["vbe"] >= values["vcc"]:
            errors["vbe"] = "ต้องน้อยกว่า VCC"

    if errors:
        raise ValidationError(errors)

    return BiasInputs(**values)


def calculate_dc_bias(inputs: BiasInputs) -> BiasResult:
    """คำนวณ DC Operating Point ด้วย Forward-Active Approximation (β และ VBE คงที่)"""

    r1 = inputs.r1 * 1000.0
    r2 = inputs.r2 * 1000.0
    rc = inputs.rc * 1000.0
    re = inputs.re * 1000.0

    vth = inputs.vcc * r2 / (r1 + r2)
    rth_ohm = (r1 * r2) / (r1 + r2)

    if vth <= inputs.vbe:
        return BiasResult(
            vth=vth,
            rth_kohm=rth_ohm / 1000.0,
            ib_ma=0.0,
            ic_ma=0.0,
            ie_ma=0.0,
            ve=0.0,
            vb=vth,
            vc=inputs.vcc,
            vce=inputs.vcc,
            region="cutoff",
            warnings=(
                "VTH ≤ VBE ทำให้ IB ≤ 0: ทรานซิสเตอร์อยู่ในย่าน Cutoff "
                "แบบจำลอง Forward-Active ใช้ไม่ได้ ผลลัพธ์นี้ไม่ควรใช้เป็นค่าจำลองที่แม่นยำ",
            ),
        )

    ib = (vth - inputs.vbe) / (rth_ohm + (inputs.beta + 1.0) * re)
    ic = inputs.beta * ib
    ie = (inputs.beta + 1.0) * ib

    ve = ie * re
    vb = ve + inputs.vbe
    vc = inputs.vcc - ic * rc
    vce = vc - ve

    warnings: list[str] = []
    if vce <= VCE_SAT:
        region = "saturation"
        warnings.append(
            "VCE ≤ 0.2 V: ทรานซิสเตอร์อยู่ในย่าน Saturation "
            "แบบจำลอง Forward-Active ใช้ไม่ได้ ผลลัพธ์นี้ไม่ควรใช้เป็นค่าจำลองที่แม่นยำ"
        )
    else:
        region = "active"
        if vce < 1.0:
            warnings.append(
                "VCE ใกล้ขอบ Saturation (ต่ำกว่า 1 V) — ตรวจสอบจุดทำงานก่อนใช้ผลลัพธ์"
            )

    return BiasResult(
        vth=vth,
        rth_kohm=rth_ohm / 1000.0,
        ib_ma=ib * 1000.0,
        ic_ma=ic * 1000.0,
        ie_ma=ie * 1000.0,
        ve=ve,
        vb=vb,
        vc=vc,
        vce=vce,
        region=region,
        warnings=tuple(warnings),
    )


def calculate_dc_bias_approx(inputs: BiasInputs) -> ApproxResult:
    """วิธีประมาณแบบละ IB (ใช้เมื่อ RTH ≪ (β+1)·RE)

    VB ≈ VTH, VE = VTH − VBE, IE = VE/RE, IC ≈ IE, IB = IC/β
    เป็นการประมาณที่ใช้กันในตำราเบื้องต้น — คลาดเคลื่อนมากเมื่อ RTH ไม่ได้เล็กกว่า (β+1)·RE
    """

    r1 = inputs.r1 * 1000.0
    r2 = inputs.r2 * 1000.0
    rc = inputs.rc * 1000.0
    re = inputs.re * 1000.0

    vth = inputs.vcc * r2 / (r1 + r2)
    vb = vth
    ve = max(vth - inputs.vbe, 0.0)

    ie = ve / re
    ic = ie
    ib = ic / inputs.beta

    vc = inputs.vcc - ic * rc
    vce = vc - ve

    return ApproxResult(
        vth=vth,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        ib_ma=ib * 1000.0,
        ic_ma=ic * 1000.0,
        ie_ma=ie * 1000.0,
    )
