# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Flask multi-file web app ที่คำนวณ DC Operating Point ของวงจร BJT Common-Emitter Voltage-Divider Bias และแสดงผลพร้อมหน่วย/validation/warning

**Architecture:** `dc_bias.py` เป็น pure Python (ไม่รู้จัก HTTP) เก็บสมการ + validation; `app.py` ทำ routing และแปลง form → model; `templates/index.html` แสดงผลด้วย Jinja; `static/style.css` ดูแลหน้าตา; `tests/` ตรวจทั้งสมการและ HTTP ด้วย `unittest`

**Tech Stack:** Python 3.15.2, Flask 3.1.3, Jinja2, `unittest` (stdlib), HTML/CSS ไม่มี JavaScript

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-web-app-design.md`

## Global Constraints

- ทุก path ของแอปอยู่ใต้ `transistor-simulator/`
- ค่าตัวต้านทานรับเป็น kΩ และคูณ 1000 ก่อนใช้ในสมการ
- ค่าคงที่ `VCE_SAT = 0.2` (V)
- ห้ามมีตัวเลขผลลัพธ์ hardcode ใน template
- ห้ามใช้ JavaScript
- การทดสอบใช้ `python -m unittest discover -s tests -v` จากโฟลเดอร์ `transistor-simulator/`
- ห้าม commit `.venv/`, `__pycache__/`, `.env`

## Review Focus

- ผู้ใช้กรอกค่าว่างหรือช่องว่างล้วน → ต้องได้ error ภาษาไทย ไม่ใช่ 500
- ผู้ใช้กรอกตัวเลขแต่ผิดหลักไฟฟ้า (R1=0, VBE > VCC) → ต้องถูกปฏิเสธพร้อมชี้ช่อง
- ผู้ใช้กรอกค่าที่ทำให้ VCE ติดลบ → ต้องรายงาน saturation ไม่ใช่โชว์เลขติดลบเฉย ๆ
- ผู้ใช้กรอก VTH ≤ VBE → ต้องได้ cutoff และไม่มีการคำนวณ IC ที่ทำให้เข้าใจผิด
- ผู้ใช้กด refresh หลัง POST → ต้องไม่ error และคงค่าที่กรอก (ไม่ใช้ session)

---

### Task 1: Validation layer ของ `dc_bias.py`

**Files:**
- Create: `transistor-simulator/dc_bias.py`
- Test: `transistor-simulator/tests/test_dc_bias.py`

**Interfaces:**
- Produces: `BiasInputs` (frozen dataclass: `vcc, r1, r2, rc, re, beta, vbe`), `ValidationError(errors: dict[str, str])`, `parse_inputs(form: Mapping[str, str]) -> BiasInputs`

- [ ] **Step 1: เขียน test ที่ยังไม่ผ่าน**

```python
class TestParseInputs(unittest.TestCase):
    def test_valid_form_is_parsed(self):
        inputs = parse_inputs({"vcc": "12", "r1": "100", "r2": "22",
                               "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7"})
        self.assertAlmostEqual(inputs.vcc, 12.0)
        self.assertAlmostEqual(inputs.r1, 100.0)

    def test_non_numeric_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({... "r1": "abc" ...})
        self.assertIn("r1", ctx.exception.errors)

    def test_zero_resistance_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({... "r2": "0" ...})
        self.assertIn("r2", ctx.exception.errors)

    def test_missing_field_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_inputs({"vcc": "12"})
        self.assertIn("r1", ctx.exception.errors)
```

- [ ] **Step 2: รัน test ให้เห็นว่าล้มเหลว**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 3: เขียน `dc_bias.py` ให้ผ่าน**

สร้าง dataclass `BiasInputs`, `ValidationError`, `parse_inputs` ที่ตรวจ: ครบทุกช่อง, แปลง float ได้, `vcc > 0`, `r1/r2/rc/re > 0`, `beta > 0`, `0 <= vbe < vcc` — ข้อความ error เป็นภาษาไทยรายช่อง

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: PASS ทุกกรณีของ `TestParseInputs`

---

### Task 2: สมการ DC Bias และ Region

**Files:**
- Modify: `transistor-simulator/dc_bias.py`
- Test: `transistor-simulator/tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `BiasInputs`
- Produces: `BiasResult` (frozen dataclass: `vth, rth_kohm, ib_ma, ic_ma, ie_ma, ve, vb, vc, vce, region, warnings`), `calculate_dc_bias(inputs: BiasInputs) -> BiasResult`

- [ ] **Step 1: เขียน test ค่าอ้างอิงและ region**

```python
def ref_inputs(**overrides):
    base = dict(vcc=12.0, r1=100.0, r2=22.0, rc=2.2, re=1.0, beta=100.0, vbe=0.7)
    base.update(overrides)
    return BiasInputs(**base)

class TestCalculate(unittest.TestCase):
    def test_reference_operating_point(self):
        r = calculate_dc_bias(ref_inputs())
        self.assertAlmostEqual(r.vth, 2.1639, places=3)
        self.assertAlmostEqual(r.rth_kohm, 18.0328, places=3)
        self.assertAlmostEqual(r.ib_ma, 0.0123, places=4)
        self.assertAlmostEqual(r.ic_ma, 1.2299, places=3)
        self.assertAlmostEqual(r.ie_ma, 1.2422, places=3)
        self.assertAlmostEqual(r.ve, 1.2422, places=3)
        self.assertAlmostEqual(r.vb, 1.9422, places=3)
        self.assertAlmostEqual(r.vc, 9.2942, places=3)
        self.assertAlmostEqual(r.vce, 8.0520, places=3)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())

    def test_cutoff_when_vth_below_vbe(self):
        r = calculate_dc_bias(ref_inputs(r2=1.0))
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ic_ma, 0.0)
        self.assertTrue(r.warnings)

    def test_saturation_when_vce_negative(self):
        r = calculate_dc_bias(ref_inputs(rc=20.0))
        self.assertEqual(r.region, "saturation")
        self.assertLessEqual(r.vce, 0.2)
        self.assertTrue(any("Forward-Active" in w for w in r.warnings))
```

- [ ] **Step 2: รัน test ให้เห็นว่าล้มเหลว**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: FAIL — `AttributeError: module 'dc_bias' has no attribute 'calculate_dc_bias'`

- [ ] **Step 3: เขียน `calculate_dc_bias` ตามสมการใน spec ข้อ 7.3–7.4**

ตัดสิน region ตามลำดับ cutoff → saturation → active และสร้างข้อความ warning ภาษาไทยที่ระบุว่าแบบจำลอง Forward-Active ใช้ไม่ได้

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `python -m unittest tests.test_dc_bias -v`
Expected: PASS ทั้ง `TestParseInputs` และ `TestCalculate`

---

### Task 3: Flask routes และ template

**Files:**
- Create: `transistor-simulator/app.py`, `transistor-simulator/templates/index.html`
- Test: `transistor-simulator/tests/test_web.py`

**Interfaces:**
- Consumes: `parse_inputs`, `calculate_dc_bias`, `ValidationError`, `BiasInputs`
- Produces: Flask app object `app` ใน `app.py`; route `GET /` และ `POST /calculate`

- [ ] **Step 1: เขียน test ของ HTTP**

```python
class TestWeb(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_index_shows_form(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"VCC", resp.data)

    def test_post_valid_calculates(self):
        resp = self.client.post("/calculate", data={... ค่าอ้างอิง ...})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"1.942", resp.data)
        self.assertIn(b"8.052", resp.data)
        self.assertIn("Active".encode(), resp.data)

    def test_post_invalid_shows_error(self):
        resp = self.client.post("/calculate", data={... "r1": "0" ...})
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b"8.052", resp.data)
        self.assertIn("มากกว่า 0".encode(), resp.data)
```

- [ ] **Step 2: รัน test ให้เห็นว่าล้มเหลว**

Run: `python -m unittest tests.test_web -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: เขียน `app.py` + `templates/index.html`**

`GET /` ส่งค่าเริ่มต้นของใบงาน; `POST /calculate` เรียก `parse_inputs` แล้ว `calculate_dc_bias`; ถ้า `ValidationError` ให้ re-render ฟอร์มพร้อม `errors` และคงค่าที่กรอก (HTTP 200); template แสดงตารางผล 3 ตำแหน่งทศนิยม + ป้าย region + warning

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS ทั้งหมด ≥ 8 tests

---

### Task 4: CSS และการจัดหน้า

**Files:**
- Create: `transistor-simulator/static/style.css`
- Modify: `transistor-simulator/templates/index.html` (ลิงก์ CSS, class)

- [ ] **Step 1: เพิ่ม `url_for('static', filename='style.css')` และ class ให้ template**
- [ ] **Step 2: เขียน CSS: 2 คอลัมน์บนจอกว้าง (ฟอร์ม | ผลลัพธ์), 1 คอลัมน์ใต้ 860px, ป้าย region มีสีแยกตามสถานะ**
- [ ] **Step 3: เปิดเว็บตรวจด้วยตา**

Run: `python -m flask --app app run --debug`
Expected: หน้าโหลดที่ `http://127.0.0.1:5000/` ไม่มี 404 ของ CSS

---

### Task 5: README, AGENTS.md และเอกสารประกอบ

**Files:**
- Create: `transistor-simulator/README.md`, `transistor-simulator/AGENTS.md`
- Create: `transistor-simulator/docs/design-note.md`, `validation.md`, `reflection.md`

- [ ] **Step 1: เขียน README (ติดตั้ง/รัน/ทดสอบ/โครงสร้าง/สมมติฐาน/ข้อจำกัด)**
- [ ] **Step 2: เขียน AGENTS.md (convention: สมการอยู่ใน `dc_bias.py` เท่านั้น, ห้าม hardcode ผล, ต้องมี test ใหม่ทุกครั้งที่แก้สมการ)**
- [ ] **Step 3: เขียน `validation.md` แสดงการเทียบผลกับคำนวณมือ + กรณี cutoff/saturation/invalid**
- [ ] **Step 4: เขียน `reflection.md` เป็นโครงให้เจ้าของงานเติมเอง (ห้ามแต่งแทน)**

---

### Task 6: ตรวจรับปลายทาง (A1–A7)

**Files:** ไม่สร้างไฟล์ใหม่

- [ ] **Step 1: รัน tests ทั้งหมดและบันทึกผล**

Run: `python -m unittest discover -s tests -v`
Expected: `OK` และมี ≥ 9 tests

- [ ] **Step 2: รันเซิร์ฟเวอร์และตรวจด้วย Browser**
  - A1 `GET /` = 200 เห็นฟอร์ม
  - A2 กรอกค่าอ้างอิง → เห็นผลคำนวณ
  - A3 ค่า VB/VE/VC/VCE/IC ตรงกับ `docs/validation.md`
  - A4 กรอก R1 = 0 → เห็น error ไม่ล่ม
  - A5 ตั้ง R2 = 1 → เห็น warning cutoff
- [ ] **Step 3: ตรวจ `git status` ว่าไม่มี `.venv/` หรือไฟล์ขยะ**
- [ ] **Step 4: ส่งมอบให้เจ้าของ commit ผ่าน GitHub Desktop**

Expected: GitHub Desktop แสดงเฉพาะไฟล์ source ที่ตั้งใจ, ไม่มี `.venv`
