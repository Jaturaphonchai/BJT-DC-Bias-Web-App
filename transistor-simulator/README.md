# BJT DC Bias Web App

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจร BJT NPN Common-Emitter
แบบ **Voltage-Divider Bias** ด้วย Forward-Active Approximation

> ENG29 2121 Computer Programming for Electrical Engineers · Lab 02 · 2/2569

## โครงสร้างโปรเจกต์

```
transistor-simulator/
├── app.py                  # Flask routes (GET /, POST /calculate)
├── dc_bias.py              # สมการ + validation (ไม่รู้จัก HTTP)
├── templates/index.html    # ฟอร์มและตารางผลลัพธ์ (Jinja)
├── static/style.css        # การจัดหน้าและหน้าตา
├── tests/
│   ├── test_dc_bias.py     # unit tests ของสมการ
│   └── test_web.py         # HTTP tests ด้วย Flask test client
├── requirements.txt
├── AGENTS.md               # ข้อตกลงการแก้โค้ดด้วย AI
├── docs/
│   ├── design-note.md
│   ├── validation.md
│   └── reflection.md
└── README.md
```

## สิ่งที่ต้องมี

- Python 3.10 ขึ้นไป (พัฒนาบน 3.15.2)
- Flask 3.1.3 (อยู่ใน `requirements.txt`)
- ไม่ต้องใช้ Node.js หรือ JavaScript ใด ๆ

## ติดตั้ง

```bash
cd transistor-simulator

python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

python -m pip install -r requirements.txt
```

## รันเว็บแอป

```bash
python -m flask --app app run --debug
```

เปิด Browser ที่ <http://127.0.0.1:5000/>

> ต้องเปิดผ่าน Flask Server เท่านั้น — การ double-click ไฟล์ `templates/index.html`
> จะไม่ทำงาน เพราะไม่มี Python backend มาคำนวณ และ Jinja template ยังไม่ถูก render

## รันการทดสอบ

```bash
python -m unittest discover -s tests -v
```

ผลที่คาดหวัง: `Ran 17 tests ... OK`

## ค่าอุปกรณ์ที่รับเข้า

| ช่อง | ความหมาย | หน่วย |
|---|---|---|
| `VCC` | แรงดันไฟเลี้ยง | V |
| `R1` | ตัวต้านทาน VCC–Base | kΩ |
| `R2` | ตัวต้านทาน Base–Ground | kΩ |
| `RC` | ตัวต้านทาน VCC–Collector | kΩ |
| `RE` | ตัวต้านทาน Emitter–Ground | kΩ |
| `β` | อัตราขยายกระแส | – |
| `VBE` | แรงดัน Base–Emitter | V |

ค่าที่กรอกเป็น kΩ จะถูกแปลงเป็น Ω ก่อนคำนวณ

## ผลลัพธ์ที่คำนวณ

`VTH`, `RTH`, `VB`, `VE`, `VC`, `VCE` (V) และ `IB`, `IC`, `IE` (mA)
พร้อมป้าย Operating Region และคำเตือนเมื่อแบบจำลองใช้ไม่ได้

## แบบจำลองและสมการ

### วิธีประมาณ (ละ IB) — ผลหลักที่แสดง

```
VTH ≈ VB
VE  = VTH − VBE
IE  = VE / RE
IC  ≈ IE
IB  = IC / β
VC  = VCC − IC · RC
VCE = VC − VE
```

ใช้ได้ดีเมื่อ `RTH ≪ (β+1)·RE` เท่านั้น

### สมการเต็ม (คิด IB) — ผลตรวจสอบ

```
VTH = VCC · R2 / (R1 + R2)
RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1) · RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

> ชุดค่าอ้างอิงในใบงานให้ผลต่างกันประมาณ 18% ที่ VE เพราะ `RTH (18 kΩ)`
> ไม่ได้เล็กกว่า `(β+1)·RE (101 kΩ)` มากนัก — แอปจึงแสดงทั้งสองวิธีคู่กัน
> และใช้สมการเต็มเป็นตัวตัดสิน Operating Region

### ย่านการทำงานที่รายงาน

| Region | เงื่อนไข | สิ่งที่แอปแจ้ง |
|---|---|---|
| Active | `VTH > VBE` และ `VCE > 0.2 V` | แบบจำลอง Forward-Active ใช้ได้ |
| Cutoff | `VTH ≤ VBE` | IB ≤ 0, IC = IE = 0 + warning |
| Saturation | `VCE ≤ 0.2 V` | warning ว่าแบบจำลองใช้ไม่ได้ |

## ข้อจำกัด

- ใช้ β คงที่และ VBE คงที่ (ไม่จำลองการเปลี่ยนแปลงตามอุณหภูมิ/กระแส)
- เป็น Forward-Active Approximation ไม่ใช่ ngspice/SPICE solver
- ผลในย่าน Cutoff/Saturation ใช้เพื่อการเรียนรู้เท่านั้น ไม่ใช่ค่าที่แม่นยำ
- ยังไม่รองรับ AC, Transient, Bode plot หรือ Bias แบบอื่น

## เอกสารประกอบ

- `docs/design-note.md` — เหตุผลการออกแบบและทางเลือกที่ตัดทิ้ง
- `docs/validation.md` — การตรวจสอบผลกับคำนวณมือและกรณีทดสอบ
- `docs/reflection.md` — คำถามสะท้อนคิดรายบุคคล
