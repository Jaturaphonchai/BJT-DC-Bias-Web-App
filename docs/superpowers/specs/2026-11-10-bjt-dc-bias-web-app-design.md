# BJT DC Bias Web App — Design

- **วันที่:** 2026-11-10
- **รายวิชา:** ENG29 2121 Computer Programming for Electrical Engineers (2/2569)
- **Lab:** 02 — First DC Bias Web App
- **สถานะ:** อนุมัติแนวทาง A (Server-rendered form + POST /calculate)

## 1. Intent และเหตุผล

สร้าง Web Application จริงชิ้นแรกของรายวิชา: Flask multi-file app ที่รับค่าอุปกรณ์ของวงจร
BJT Common-Emitter แบบ Voltage-Divider Bias แล้วให้ **Python backend** คำนวณ DC Operating Point
ส่งกลับมาแสดงใน Browser พร้อมหน่วย, validation และ warning เมื่อแบบจำลอง Forward-Active ใช้ไม่ได้

ชิ้นงานนี้เป็น vertical slice แรกของเป้าหมายปลายภาค (Virtual Transistor Laboratory)
จึงต้องมีโครงสร้างที่ต่อยอดได้ในสัปดาห์ถัดไป โดยไม่ต้องรื้อใหม่

## 2. Goals

- G1 เปิดใช้งานได้จริงที่ `http://127.0.0.1:5000/` ผ่าน Flask dev server
- G2 แยกความรับผิดชอบ: `app.py` (HTTP) / `dc_bias.py` (สมการ) / template / CSS / tests
- G3 รับ `VCC, R1, R2, RC, RE, β, VBE` และคำนวณ `VB, VE, VC, VCE, IC` (แสดง `IB, IE` เพิ่ม)
- G4 Validation: ค่าขาด, ไม่ใช่ตัวเลข, R ≤ 0, β ≤ 0, VCC ≤ 0, VBE ไม่สมเหตุสมผล
- G5 Region warning: Cutoff (`VTH ≤ VBE`) และ Saturation (`VCE ≤ 0.2 V`)
- G6 Automated tests: unit tests ของสมการ ≥ 3 และ Flask test client ≥ 1
- G7 README ที่ clone แล้วติดตั้ง/รัน/ทดสอบได้จริง และ commit ผ่าน GitHub Desktop

## 3. Non-goals (ไม่ทำในคาบนี้)

- AC small-signal, Bode plot, Transient, Signal generator, Overlay animation
- Bias types อื่น (Fixed, Emitter bias), FET, SPICE/ngspice
- Database, authentication, deployment, JavaScript framework
- Interactive knob / real-time update (เป็นงาน Week 6–7)

## 4. Anti-goals (ถือว่าล้มเหลวแม้โปรแกรมจะรันได้)

- ตัวเลขผลลัพธ์ hardcode อยู่ใน HTML แทนการคำนวณจริง
- ประกาศว่า "tests ผ่าน" โดยไม่ได้รันจริง
- แสดงผลในย่านที่แบบจำลองใช้ไม่ได้ โดยไม่มี warning
- Commit `.venv/`, `.env`, credential หรือไฟล์ขยะของ editor

## 5. Constraints

- เวลาคาบ 180 นาที, Windows 11, Python 3.15.2, Flask 3.1.3
- Repo เดิมของรายวิชา: `Jaturaphonchai/-DC-Circuit-Calculator` (มีไฟล์ Lab 1 ที่ root)
- แอปอยู่ในโฟลเดอร์ย่อย `transistor-simulator/` ไม่ทับไฟล์ Lab 1
- แบบจำลอง: β คงที่, VBE คงที่, สมมติฐาน Forward-Active
- ค่าตัวต้านทานรับเป็น **kΩ** แล้วแปลงเป็น Ω ภายใน (ตรงกับข้อมูลทดลอง 100k/22k/2.2k/1k)

## 6. Approaches ที่พิจารณา

| แนวทาง | ข้อดี | ข้อเสีย | ผล |
|---|---|---|---|
| **A. Server-rendered form + POST /calculate** | ตรง acceptance A1/A2, ไม่มี JS, test ง่าย, เสี่ยงต่ำ | ต้องกด submit ทุกครั้ง | **เลือก** |
| B. JSON API + fetch (AJAX) | ต่อยอด interactive ได้ลื่น | โค้ดเพิ่มเกือบเท่าตัว, ต้องเทสต์ 2 ชั้น | ไม่เลือก (เกินเวลา, ไม่เพิ่มคะแนน) |
| C. POST / route เดียว | สั้นที่สุด | route ทำหลายหน้าที่, แยกความรับผิดชอบไม่ชัด | ไม่เลือก |

## 7. Design

### 7.1 โครงสร้างไฟล์

```
<repo root>/
├── .gitignore                      # มีแล้ว
├── docs/superpowers/specs/         # เอกสารนี้
├── docs/superpowers/plans/         # implementation plan
└── transistor-simulator/
    ├── app.py                      # Flask routes เท่านั้น
    ├── dc_bias.py                  # สมการ + validation (ไม่รู้จัก HTML/HTTP)
    ├── templates/index.html        # form + results (Jinja)
    ├── static/style.css            # presentation
    ├── tests/test_dc_bias.py       # unit tests (unittest)
    ├── tests/test_web.py           # Flask test client
    ├── requirements.txt            # Flask==3.1.3 (มีแล้ว)
    ├── README.md
    ├── AGENTS.md
    └── docs/{design-note,validation,reflection}.md
```

### 7.2 สัญญาของ `dc_bias.py`

```python
VCE_SAT = 0.2

@dataclass(frozen=True)
class BiasInputs:
    vcc: float; r1: float; r2: float; rc: float; re: float  # R เป็น kΩ
    beta: float; vbe: float                                   # V, -

@dataclass(frozen=True)
class BiasResult:
    vth: float; rth_kohm: float
    ib_ma: float; ic_ma: float; ie_ma: float
    ve: float; vb: float; vc: float; vce: float
    region: str          # "active" | "cutoff" | "saturation"
    warnings: tuple[str, ...]

class ValidationError(Exception):
    errors: dict[str, str]   # field -> ข้อความภาษาไทย

def parse_inputs(form: Mapping[str, str]) -> BiasInputs   # raises ValidationError
def calculate_dc_bias(inputs: BiasInputs) -> BiasResult
```

### 7.3 สมการ

```
r_ohm = r_kohm * 1000
VTH = VCC·R2/(R1+R2)
RTH = R1·R2/(R1+R2)
IB  = (VTH − VBE)/(RTH + (β+1)·RE)
IC  = β·IB          IE = (β+1)·IB
VE  = IE·RE         VB = VE + VBE
VC  = VCC − IC·RC   VCE = VC − VE
```

### 7.4 กติกา Region (สำคัญต่อคะแนน A5)

1. `VTH ≤ VBE` → **cutoff**: `IB = IC = IE = 0`, `VE = 0`, `VB = VTH`, `VC = VCC`, `VCE = VCC` + warning
2. `VCE ≤ VCE_SAT (0.2 V)` → คำนวณตามสมการแล้วติดป้าย **saturation** + warning ว่าแบบจำลอง Forward-Active ใช้ไม่ได้
3. นอกนั้น → **active**

Warning ต้องบอกชัดว่า "ค่าที่ได้ไม่ควรใช้เป็นผลจำลองที่แม่นยำ"

### 7.5 UI

- ภาษาไทย + ศัพท์เทคนิคอังกฤษ, หน่วยกำกับทุกช่อง (`V`, `kΩ`, `–`)
- ค่าเริ่มต้น = ข้อมูลทดลองในใบงาน (12, 100k, 22k, 2.2k, 1k, β=100, VBE=0.70 V)
- ผลลัพธ์: ตาราง V/I 3 ตำแหน่งทศนิยม + ป้าย Region + กล่อง warning/error
- Error แสดงใต้ช่องที่ผิด และคงค่าที่ผู้ใช้กรอกไว้
- Responsive 1 คอลัมน์บนจอเล็ก, ใช้งานด้วยคีย์บอร์ดได้

### 7.6 กติกาการแสดงตัวเลข
- แรงดัน: V, 3 ตำแหน่งทศนิยม
- กระแส: mA, 3 ตำแหน่งทศนิยม
- ความต้านทาน: kΩ, 2 ตำแหน่งทศนิยม
- ไม่ปัดเศษในชั้นคำนวณ (ปัดเฉพาะตอนแสดงผล)

### 7.7 สองวิธีคำนวณที่แสดงคู่กัน (ปรับปรุงระหว่างทำ)

ตรวจสอบกับผู้ใช้แล้วว่าเกณฑ์ของรายวิชาอ้างอิง **วิธีประมาณ (ละ IB)** จึงแสดงทั้งสองวิธี:

| วิธี | สมการ | บทบาทใน UI |
|---|---|---|
| ประมาณ (ละ IB) | `VB ≈ VTH`, `IE = (VTH−VBE)/RE`, `IC ≈ IE` | ค่าหลัก |
| สมการเต็ม (คิด IB) | ตามข้อ 7.3 | ค่าตรวจสอบ + ใช้ตัดสิน Region |

เหตุผล: ชุดค่าอ้างอิงให้ `RTH = 18.03 kΩ` เทียบกับ `(β+1)·RE = 101 kΩ`
ผลสองวิธีต่างกัน ≈ 18% ที่ `VE` จึงต้องแสดงคู่กันและอธิบายเงื่อนไข
`RTH ≪ (β+1)·RE` กำกับไว้

## 8. สิ่งที่เหลือให้ผู้สร้างตัดสินใจ

- รายละเอียด CSS (สี, ระยะห่าง) ให้สอดคล้องโทนเดียวกับ handout
- ถ้อยคำใน README และเอกสาร `docs/*.md`
- ค่าในชุดทดสอบนอกเหนือจากค่าอ้างอิงในใบงาน
