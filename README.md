# BJT DC Bias Web App

**ENG29 2121 — Computer Programming for Electrical Engineers (2/2569)**
Lab 02 · Flask Web Application สำหรับคำนวณ DC Bias ของวงจร BJT Common-Emitter
แบบ Voltage-Divider Bias

> Repository นี้เป็น Public แล้ว — เปิดดูได้ที่
> <https://github.com/Jaturaphonchai/BJT-DC-Bias-Web-App>

## ชิ้นงานหลัก

| ส่วน | ที่อยู่ |
|---|---|
| Web Application (Lab 02) | [`transistor-simulator/`](transistor-simulator/) |
| คู่มือติดตั้งและรัน | [`transistor-simulator/README.md`](transistor-simulator/README.md) |
| เอกสารออกแบบ | [`docs/superpowers/specs/`](docs/superpowers/specs/) |
| แผนการพัฒนา | [`docs/superpowers/plans/`](docs/superpowers/plans/) |
| ผลตรวจสอบค่า | [`transistor-simulator/docs/validation.md`](transistor-simulator/docs/validation.md) |
| ข้อตกลงการแก้โค้ด | [`transistor-simulator/AGENTS.md`](transistor-simulator/AGENTS.md) |

## เริ่มใช้งานเร็ว

```bash
cd transistor-simulator
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
python -m pip install -r requirements.txt
python -m flask --app app run --debug
# เปิด http://127.0.0.1:5000/
```

ทดสอบ:

```bash
python -m unittest discover -s tests -v
```

## ไฟล์อื่นใน Repository

`electrical.py`, `test_electrical.py`, `test_electricalBranch.py`
เป็นงานจาก Lab 01 ที่เก็บไว้ต่อเนื่องใน repo เดียวกัน

## ข้อจำกัดของแบบจำลอง

- ใช้ β คงที่และ VBE คงที่ (Forward-Active Approximation)
- ไม่ใช่ SPICE solver — ผลในย่าน Cutoff/Saturation มี warning กำกับ
- ยังไม่รองรับ AC, Transient, Bode plot หรือ Bias ชนิดอื่น (อยู่ระหว่าง Week 3–7)
