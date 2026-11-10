# AGENTS.md — ข้อตกลงการแก้โค้ดในโปรเจกต์นี้

ไฟล์นี้อ่านโดย AI coding agent ทุกครั้งที่ทำงานในโปรเจกต์

## หลักการแยกความรับผิดชอบ

- `dc_bias.py` = สมการฟิสิกส์ + validation เท่านั้น **ห้าม import Flask**
- `app.py` = HTTP routing + แปลง request เป็น model **ห้ามเขียนสมการเอง**
- `templates/` = การแสดงผลเท่านั้น **ห้ามคำนวณค่าทางไฟฟ้าใน template**
- `static/` = หน้าตาเท่านั้น

## กฎที่ต้องปฏิบัติ

1. **ห้าม hardcode ผลลัพธ์** ตัวเลขทุกตัวที่แสดงต้องมาจาก `calculate_dc_bias()`
2. **ทุกการแก้สมการต้องมี test** ใน `tests/test_dc_bias.py` และรัน
   `python -m unittest discover -s tests -v` ให้ผ่านก่อนส่งงาน
3. **ทุกการแก้ route ต้องมี HTTP test** ใน `tests/test_web.py`
4. ค่าความต้านทานรับเป็น kΩ และแปลงเป็น Ω ที่จุดเดียวใน `calculate_dc_bias()`
5. ข้อความ error/warning ต้องเป็นภาษาไทยที่ผู้ใช้เข้าใจ ไม่ใช่ exception ดิบ
6. ห้ามใส่ JavaScript หรือ dependency ใหม่โดยไม่จำเป็น
7. ห้าม commit `.venv/`, `__pycache__/`, `.env` หรือ credential
8. รักษาสมมติฐาน Forward-Active ให้ชัดเจน ทั้งใน UI และเอกสาร

## สไตล์โค้ด

- Python ตาม PEP 8, ใช้ type hints, ฟังก์ชันสั้นและมี docstring
- ใช้ `unittest` (stdlib) ไม่เพิ่ม pytest
- ชื่อตัวแปรใช้ภาษาอังกฤษ, ข้อความที่ผู้ใช้เห็นเป็นภาษาไทย

## คำสั่งที่ใช้บ่อย

```bash
python -m unittest discover -s tests -v
python -m flask --app app run --debug
```
