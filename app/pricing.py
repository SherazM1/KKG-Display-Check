from __future__ import annotations

from typing import Dict, List, Tuple


def parts_value(catalog: Dict, part_key: str) -> float:
    try:
        return float(catalog.get("parts", {}).get(part_key, {}).get("base_value", 0) or 0)
    except Exception:
        return 0.0


def unit_factor(policy: Dict, qty: int) -> float:
    """
    Computes per-unit factor based on policy.unit_tiers.
    tier_boundary: "inclusive" means min<=qty<=max, else min<=qty<max.
    """
    uf = 1.0
    tiers = policy.get("unit_tiers", []) or []
    inclusive = (policy.get("tier_boundary", "inclusive") == "inclusive")

    for band in tiers:
        min_q = int(band.get("min_qty", 0) or 0)
        max_q = band.get("max_qty")
        factor = float(band.get("factor", 1.0) or 1.0)

        if max_q is None:
            if qty >= min_q:
                uf = factor
            continue

        max_q_i = int(max_q)
        if inclusive:
            if qty >= min_q and qty <= max_q_i:
                uf = factor
        else:
            if qty >= min_q and qty < max_q_i:
                uf = factor

    return float(uf)


def matrix_markup_pct(policy: Dict, rc: Tuple[int, int]) -> float:
    """
    Reads markup strictly from policy.matrix_markups[r][c].
    Expects decimals (0.35 == 35%).
    """
    grid = policy.get("matrix_markups")
    if not (isinstance(grid, list) and len(grid) == 3 and all(isinstance(r, list) and len(r) == 3 for r in grid)):
        raise ValueError("Missing/invalid policy.matrix_markups (expected 3x3 list).")
    r, c = rc
    return float(grid[r][c])


def resolve_parts_per_unit(
    catalog: Dict,
    form: Dict,
    *,
    footprint_dims: Tuple[int | None, int | None],
) -> List[Tuple[str, int]]:
    """
    Applies catalog rules to produce a list of (part_key, qty_per_unit).
    """
    rules = catalog.get("rules", {}) or {}
    resolved: List[Tuple[str, int]] = []

    fp_key = form.get("footprint")
    width_in, depth_in = footprint_dims

    # footprint base
    if fp_key and "resolve_footprint_base" in rules:
        r = rules["resolve_footprint_base"]
        base_part = (r.get("map", {}) or {}).get(fp_key)
        if base_part:
            resolved.append((base_part, 1))

    # header
    if "resolve_header" in rules:
        r = rules["resolve_header"]
        part = r.get("else")
        if form.get(r.get("when_control")) == r.get("when_value"):
            if r.get("match_on_dim") == "width_in" and width_in is not None:
                part = (r.get("map", {}) or {}).get(str(width_in), r.get("else"))
        if part:
            resolved.append((part, 1))

    # dividers (also used for sidekick pegs via quantity_control)
    if "resolve_dividers" in rules:
        r = rules["resolve_dividers"]
        qty_ctrl = r.get("quantity_control")
        dqty = int(form.get(qty_ctrl, 0) or 0)
        if dqty > 0 and r.get("match_on_dim") == "depth_in" and depth_in is not None:
            part = (r.get("map", {}) or {}).get(str(depth_in), r.get("else"))
            if part:
                resolved.append((part, dqty))

    # shipper
    if "resolve_shipper" in rules:
        r = rules["resolve_shipper"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            part = (r.get("map", {}) or {}).get(fp_key, r.get("else"))
            if part:
                resolved.append((part, 1))

    # assembly touches
    if "resolve_assembly_touches" in rules:
        r = rules["resolve_assembly_touches"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            tq_ctrl = r.get("quantity_control")
            tqty = int(form.get(tq_ctrl, 0) or 0)
            if tqty >= int(r.get("min_quantity", 1) or 1):
                part = r.get("part")
                if part:
                    resolved.append((part, tqty))

    # printed inside (sidekick-only; PDQ unaffected unless rule exists)
    if "resolve_printed_inside" in rules:
        r = rules["resolve_printed_inside"]
        ctrl_id = r.get("based_on_control")
        selected = form.get(ctrl_id)
        part = (r.get("map", {}) or {}).get(selected)
        if part:
            resolved.append((part, 1))

    return resolved
