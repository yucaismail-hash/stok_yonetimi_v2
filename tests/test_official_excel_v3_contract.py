"""Focused, database-free Official Excel V3 contract tests."""
import io
import unittest

from openpyxl import load_workbook

from app.application.canonical_excel_ingestion import (
    OFFICIAL_V3_HEADERS,
    OFFICIAL_V3_SHEET,
    parse_workbook,
    template_bytes,
)


class OfficialExcelV3ContractTests(unittest.TestCase):
    def test_template_has_official_sheets_and_wide_iso_headers(self):
        book = load_workbook(io.BytesIO(template_bytes()), read_only=True, data_only=True)
        self.assertEqual(book.sheetnames, [OFFICIAL_V3_SHEET, "Malzeme_Tedarikciler", "Tedarikciler", "Events", "Data_Requirement_Matrix"])
        headers = list(next(book[OFFICIAL_V3_SHEET].iter_rows(max_row=1, values_only=True)))
        self.assertEqual(tuple(headers[:len(OFFICIAL_V3_HEADERS)]), OFFICIAL_V3_HEADERS)
        self.assertEqual(headers[len(OFFICIAL_V3_HEADERS):], [f"2026-W{week:02d}" for week in range(1, 53)])

    def test_template_normalizes_wide_rows_to_weekly_canonical_rows(self):
        rows, errors = parse_workbook(template_bytes())
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 52)
        self.assertEqual(rows[0]["material_code"], "SKU-001")
        self.assertEqual(rows[0]["product_level"], "finished_good")
        self.assertEqual(rows[0]["period"], "2026-W01")
        self.assertEqual(rows[-1]["period"], "2026-W52")
        self.assertNotIn("demand_type", rows[0])
