#!/usr/bin/env python3
"""Validate recorded per-object QA evidence for butter crisp stick frames.

This checks manifest completeness and numeric gates. It does not inspect image
semantics and therefore never replaces original-resolution visual review.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PRODUCT_THICKNESS_RATIO = (0.30, 0.50)
PRODUCT_LENGTH_WIDTH_RATIO = (4.0, 5.0)
PACKAGE_FRONT_RATIO = (0.90, 1.10)
PACKAGE_DEPTH_RATIO = (0.24, 0.36)
ALLOWED_ARTWORK_METHODS = {"deterministic_reference_composite", "verified_reference_pixels"}


def _ratio(numerator: Any, denominator: Any) -> float | None:
    try:
        n = float(numerator)
        d = float(denominator)
    except (TypeError, ValueError):
        return None
    return None if d <= 0 else n / d


def _in_range(value: float | None, bounds: tuple[float, float]) -> bool:
    return value is not None and bounds[0] <= value <= bounds[1]


def audit_manifest(data: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    shot_id = data.get("shot_id", "UNKNOWN")

    if data.get("full_resolution_review") is not True:
        issues.append("FULL_RESOLUTION_REVIEW_MISSING")
    if data.get("contact_sheet_used_for_approval") is not False:
        issues.append("CONTACT_SHEET_CANNOT_APPROVE")
    if data.get("inventory_complete") is not True:
        issues.append("OBJECT_INVENTORY_INCOMPLETE")

    products = data.get("product_instances")
    packages = data.get("package_instances")
    if not isinstance(products, list):
        issues.append("PRODUCT_INSTANCE_LIST_MISSING")
        products = []
    if not isinstance(packages, list):
        issues.append("PACKAGE_INSTANCE_LIST_MISSING")
        packages = []

    seen: set[str] = set()
    for index, item in enumerate(products, 1):
        prefix = f"product[{index}]"
        object_id = item.get("id")
        if not object_id or object_id in seen:
            issues.append(f"{prefix}:OBJECT_ID_MISSING_OR_DUPLICATE")
        else:
            seen.add(object_id)
        if not item.get("bbox") or len(item.get("bbox", [])) != 4:
            issues.append(f"{prefix}:BBOX_MISSING")
        if item.get("original_size_crop_reviewed") is not True:
            issues.append(f"{prefix}:ORIGINAL_SIZE_CROP_NOT_REVIEWED")
        if item.get("reference_crop_compared") is not True:
            issues.append(f"{prefix}:PRODUCT_REFERENCE_NOT_COMPARED")
        if item.get("microstructure_review") != "pass":
            issues.append(f"{prefix}:PRODUCT_MICROSTRUCTURE_FLATTENED")

        geometry = item.get("geometry", {})
        if geometry.get("cross_section_visible") is True:
            if geometry.get("cross_section_shape") != "rectangular_with_small_corner_radius":
                issues.append(f"{prefix}:PRODUCT_CROSS_SECTION_ROUNDED")
            ratio = _ratio(geometry.get("cross_section_thickness_px"), geometry.get("cross_section_width_px"))
            if geometry.get("cross_section_measurable") is True and not _in_range(ratio, PRODUCT_THICKNESS_RATIO):
                issues.append(f"{prefix}:PRODUCT_THICKNESS_COLLAPSED")

        if geometry.get("length_width_measurable") is True:
            ratio = _ratio(geometry.get("length_px"), geometry.get("width_px"))
            if not _in_range(ratio, PRODUCT_LENGTH_WIDTH_RATIO):
                issues.append(f"{prefix}:PRODUCT_LENGTH_WIDTH_OUT_OF_RANGE")

        if geometry.get("side_thickness_measurable") is True:
            ratio = _ratio(geometry.get("thickness_px"), geometry.get("width_px"))
            if not _in_range(ratio, PRODUCT_THICKNESS_RATIO):
                issues.append(f"{prefix}:PRODUCT_THICKNESS_COLLAPSED")

        if not any(
            geometry.get(flag) is True
            for flag in ("cross_section_measurable", "length_width_measurable", "side_thickness_measurable")
        ):
            if geometry.get("manual_perspective_review") != "pass" or not geometry.get("manual_review_reason"):
                issues.append(f"{prefix}:PRODUCT_GEOMETRY_EVIDENCE_MISSING")

    for index, item in enumerate(packages, 1):
        prefix = f"package[{index}]"
        object_id = item.get("id")
        if not object_id or object_id in seen:
            issues.append(f"{prefix}:OBJECT_ID_MISSING_OR_DUPLICATE")
        else:
            seen.add(object_id)
        if not item.get("bbox") or len(item.get("bbox", [])) != 4:
            issues.append(f"{prefix}:BBOX_MISSING")
        if item.get("original_size_crop_reviewed") is not True:
            issues.append(f"{prefix}:ORIGINAL_SIZE_CROP_NOT_REVIEWED")
        if item.get("scale_review") != "pass":
            issues.append(f"{prefix}:PACKAGE_SCALE_MISMATCH")

        geometry = item.get("geometry", {})
        if geometry.get("front_aspect_measurable") is True:
            ratio = _ratio(geometry.get("front_width_px"), geometry.get("front_height_px"))
            if not _in_range(ratio, PACKAGE_FRONT_RATIO):
                issues.append(f"{prefix}:PACKAGE_FRONT_ASPECT_MISMATCH")
        if geometry.get("depth_measurable") is True:
            ratio = _ratio(geometry.get("depth_px"), geometry.get("perspective_corrected_front_edge_px"))
            if not _in_range(ratio, PACKAGE_DEPTH_RATIO):
                issues.append(f"{prefix}:PACKAGE_DEPTH_COLLAPSED")
        elif geometry.get("manual_depth_review") != "pass" or not geometry.get("manual_depth_reason"):
            issues.append(f"{prefix}:PACKAGE_DEPTH_EVIDENCE_MISSING")

        print_review = item.get("print_review", {})
        if print_review.get("front_legible") is True:
            if print_review.get("artwork_method") not in ALLOWED_ARTWORK_METHODS:
                issues.append(f"{prefix}:PACKAGE_PRINT_IDENTITY_MISMATCH")
            for field in ("brand_exact", "product_name_exact", "net_weight_exact", "layout_exact"):
                if print_review.get(field) is not True:
                    issues.append(f"{prefix}:PACKAGE_PRINT_IDENTITY_MISMATCH:{field}")
        elif print_review.get("layout_color_block_review") != "pass":
            issues.append(f"{prefix}:PACKAGE_PRINT_REVIEW_MISSING")

    if data.get("declared_status") == "approved" and issues:
        issues.insert(0, f"{shot_id}:APPROVAL_REVOKED")
    return issues


def example_manifest() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "shot_id": "F000",
        "declared_status": "approved",
        "full_resolution_review": True,
        "contact_sheet_used_for_approval": False,
        "inventory_complete": True,
        "product_instances": [
            {
                "id": "P1",
                "bbox": [100, 100, 580, 200],
                "original_size_crop_reviewed": True,
                "reference_crop_compared": True,
                "microstructure_review": "pass",
                "geometry": {
                    "cross_section_visible": False,
                    "length_width_measurable": True,
                    "length_px": 480,
                    "width_px": 100,
                    "side_thickness_measurable": True,
                    "thickness_px": 40,
                },
            }
        ],
        "package_instances": [
            {
                "id": "B1",
                "bbox": [600, 100, 900, 490],
                "original_size_crop_reviewed": True,
                "scale_review": "pass",
                "geometry": {
                    "front_aspect_measurable": True,
                    "front_width_px": 300,
                    "front_height_px": 300,
                    "depth_measurable": True,
                    "depth_px": 90,
                    "perspective_corrected_front_edge_px": 300,
                },
                "print_review": {
                    "front_legible": True,
                    "artwork_method": "deterministic_reference_composite",
                    "brand_exact": True,
                    "product_name_exact": True,
                    "net_weight_exact": True,
                    "layout_exact": True,
                },
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--write-example", type=Path)
    args = parser.parse_args()
    if args.write_example:
        args.write_example.parent.mkdir(parents=True, exist_ok=True)
        args.write_example.write_text(json.dumps(example_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote example manifest: {args.write_example}")
        return 0
    if not args.manifest:
        parser.error("one of --manifest or --write-example is required")
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    issues = audit_manifest(data)
    if issues:
        print(json.dumps({"status": "failed", "issues": issues}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": "passed", "issues": []}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
