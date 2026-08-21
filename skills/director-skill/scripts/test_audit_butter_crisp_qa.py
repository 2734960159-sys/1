#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("audit_butter_crisp_qa.py")
SPEC = importlib.util.spec_from_file_location("audit_butter_crisp_qa", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ButterCrispAuditTests(unittest.TestCase):
    def test_complete_manifest_passes(self) -> None:
        self.assertEqual(MODULE.audit_manifest(MODULE.example_manifest()), [])

    def test_rounded_cross_section_fails(self) -> None:
        data = MODULE.example_manifest()
        geometry = data["product_instances"][0]["geometry"]
        geometry.update(
            cross_section_visible=True,
            cross_section_shape="round",
            cross_section_measurable=True,
            cross_section_width_px=50,
            cross_section_thickness_px=48,
        )
        issues = MODULE.audit_manifest(data)
        self.assertTrue(any("PRODUCT_CROSS_SECTION_ROUNDED" in issue for issue in issues))

    def test_thin_product_fails(self) -> None:
        data = MODULE.example_manifest()
        data["product_instances"][0]["geometry"]["thickness_px"] = 12
        issues = MODULE.audit_manifest(data)
        self.assertTrue(any("PRODUCT_THICKNESS_COLLAPSED" in issue for issue in issues))

    def test_generative_package_text_fails(self) -> None:
        data = MODULE.example_manifest()
        data["package_instances"][0]["print_review"]["artwork_method"] = "generative_text"
        issues = MODULE.audit_manifest(data)
        self.assertTrue(any("PACKAGE_PRINT_IDENTITY_MISMATCH" in issue for issue in issues))

    def test_flat_box_fails(self) -> None:
        data = MODULE.example_manifest()
        data["package_instances"][0]["geometry"]["depth_px"] = 25
        issues = MODULE.audit_manifest(data)
        self.assertTrue(any("PACKAGE_DEPTH_COLLAPSED" in issue for issue in issues))

    def test_every_visible_box_needs_own_record(self) -> None:
        data = MODULE.example_manifest()
        data["inventory_complete"] = False
        issues = MODULE.audit_manifest(data)
        self.assertIn("OBJECT_INVENTORY_INCOMPLETE", issues)


if __name__ == "__main__":
    unittest.main()
