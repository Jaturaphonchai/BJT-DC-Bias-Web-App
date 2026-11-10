"""HTTP tests ผ่าน Flask test client"""

import unittest

from app import app

VALID_FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}


class TestWeb(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_get_index_shows_form(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"VCC", response.data)
        self.assertIn("Calculate DC Bias".encode(), response.data)

    def test_get_index_shows_schematic(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"schematic.svg", response.data)
        self.assertIn("แผนผังวงจร".encode(), response.data)

    def test_schematic_file_is_served(self):
        response = self.client.get("/static/schematic.svg")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<svg", response.data)
        response.close()

    def test_post_valid_input_calculates_on_backend(self):
        response = self.client.post("/calculate", data=VALID_FORM)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.942", response.data)  # VB จากสมการเต็ม
        self.assertIn(b"8.052", response.data)  # VCE
        self.assertIn("Active".encode(), response.data)
        self.assertNotIn(b"8.779", response.data)  # ไม่แสดงผลวิธีประมาณแล้ว

    def test_post_invalid_input_shows_error_without_crashing(self):
        response = self.client.post("/calculate", data={**VALID_FORM, "r1": "0"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("มากกว่า 0".encode(), response.data)
        self.assertNotIn(b"8.052", response.data)

    def test_post_cutoff_input_shows_warning(self):
        response = self.client.post("/calculate", data={**VALID_FORM, "r2": "1"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("Cutoff".encode(), response.data)
        self.assertIn("Forward-Active".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
