# Validation — การตรวจสอบผลลัพธ์ DC Bias

## 1. ชุดข้อมูลอ้างอิงจากใบงาน

`VCC = 12 V`, `R1 = 100 kΩ`, `R2 = 22 kΩ`, `RC = 2.2 kΩ`, `RE = 1 kΩ`, `β = 100`, `VBE = 0.70 V`

### คำนวณมือ

```
R1 = 100 000 Ω, R2 = 22 000 Ω, RC = 2 200 Ω, RE = 1 000 Ω

VTH = 12 × 22 000 / (100 000 + 22 000) = 2.1639 V
RTH = (100 000 × 22 000) / 122 000    = 18 032.79 Ω = 18.0328 kΩ
IB  = (2.1639 − 0.70) / (18 032.79 + 101 × 1 000)
    = 1.4639 / 119 032.79
    = 12.299 µA
IC  = 100 × 12.299 µA      = 1.2299 mA
IE  = 101 × 12.299 µA      = 1.2422 mA
VE  = 1.2422 mA × 1 kΩ     = 1.2422 V
VB  = 1.2422 + 0.70        = 1.9422 V
VC  = 12 − 1.2299 mA × 2.2 kΩ = 12 − 2.7057 = 9.2943 V
VCE = 9.2943 − 1.2422      = 8.0521 V
```

### เทียบกับผลจากเว็บ

| ปริมาณ | คำนวณมือ | เว็บแสดง |
|---|---|---|
| VTH | 2.1639 V | 2.164 V |
| RTH | 18.0328 kΩ | 18.03 kΩ |
| VB | 1.9422 V | 1.942 V |
| VE | 1.2422 V | 1.242 V |
| VC | 9.2943 V | 9.294 V |
| VCE | 8.0521 V | 8.052 V |
| IB | 12.299 µA | 12.3 µA |
| IC | 1.2299 mA | 1.230 mA |
| IE | 1.2422 mA | 1.242 mA |
| Region | Active | Active (Forward-Active) |

ทุกค่าตรงกับที่คำนวณมือในข้อ 1

## 2. กรณีขอบเขตแบบจำลอง

| กรณี | อินพุตที่เปลี่ยน | ผลที่ได้ | ตรงตามข้อกำหนด |
|---|---|---|---|
| Cutoff | `R2 = 1 kΩ` → VTH = 0.119 V ≤ VBE | Region = Cutoff, IC = IE = 0, มี warning | ✅ A5 |
| Saturation | `RC = 20 kΩ` → VCE = −13.839 V | Region = Saturation, มี warning ว่า Forward-Active ใช้ไม่ได้ | ✅ A5 |
| ค่าตัวต้านทานเป็นศูนย์ | `R1 = 0` | Error "ต้องมากกว่า 0 kΩ" ใต้ช่อง R1, หน้าเว็บไม่ล่ม | ✅ A4 |
| ค่าไม่ใช่ตัวเลข | `R1 = abc` | Error "ต้องเป็นตัวเลข" | ✅ A4 |
| ค่าหาย | ลบ HTML attribute ออกแล้ว submit | Error "กรุณากรอกค่านี้" | ✅ A4 |
| VBE ≥ VCC | `VBE = 12` | Error "ต้องน้อยกว่า VCC" | ✅ A4 |

## 3. Automated tests

```bash
python -m unittest discover -s tests -v
```

ผลล่าสุด: `Ran 16 tests ... OK`

- `tests/test_dc_bias.py` — 10 tests (validation 6, สมการ/region 4)
- `tests/test_web.py` — 6 tests (GET form, GET schematic, GET static SVG, POST ค่าจริง, POST ค่าผิด, POST cutoff)

## 4. วิธีทำซ้ำด้วยตนเอง

1. `python -m flask --app app run --debug`
2. เปิด <http://127.0.0.1:5000/>
3. กรอกค่าชุดอ้างอิง → กด **Calculate DC Bias**
4. เทียบค่าที่ได้กับตารางข้อ 1
5. ลองกรอก `R1 = 0` และ `R2 = 1` เพื่อดู error และ warning
