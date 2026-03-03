# app/pricing.py
from __future__ import annotations

from typing import Dict, List, Tuple


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return float(default)


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return int(default)


def _floor_break_price(part_spec: Dict, *, program_qty: int) -> float:
    """
    Returns per-unit price for a part at a given program quantity using FLOOR breakpoint.

    - If `part_spec.breaks` exists: choose largest break_qty <= program_qty.
      If program_qty is below smallest breakpoint, use the smallest breakpoint.
    - Else fall back to `part_spec.base_value`.

    Expected breaks shape:
      {"1": 97.17, "100": 33.95, ...} (keys may be str or int)
    """
    qty = max(_as_int(program_qty, 0), 0)
    breaks = part_spec.get("breaks")

    if isinstance(breaks, dict) and breaks:
        parsed: List[Tuple[int, float]] = []
        for k, v in breaks.items():
            try:
                bq = int(k)
            except Exception:
                continue
            parsed.append((bq, _as_float(v, 0.0)))

        if parsed:
            parsed.sort(key=lambda x: x[0])

            floor_price = None
            for bq, price in parsed:
                if bq <= qty:
                    floor_price = price
                else:
                    break

            if floor_price is not None:
                return float(floor_price)

            # qty below smallest break -> use smallest
            return float(parsed[0][1])

    return _as_float(part_spec.get("base_value", 0.0), 0.0)


def parts_value(catalog: Dict, part_key: str, *, program_qty: int | None = None, **_ignored) -> float:
    """
    Break-aware part pricing:
      - Uses per-part `breaks` (FLOOR selection) when present.
      - Falls back to `base_value`.
    `program_qty` is the order quantity; required for `breaks`.
    """
    try:
        part_spec = (catalog.get("parts", {}) or {}).get(part_key, {}) or {}
        if not isinstance(part_spec, dict):
            return 0.0

        qty = int(program_qty or 1)

        breaks = part_spec.get("breaks")
        if isinstance(breaks, dict) and breaks:
            parsed: List[Tuple[int, float]] = []
            for k, v in breaks.items():
                try:
                    bq = int(k)
                except Exception:
                    continue
                try:
                    price = float(v or 0)
                except Exception:
                    price = 0.0
                parsed.append((bq, price))

            if parsed:
                parsed.sort(key=lambda x: x[0])
                floor_price = None
                for bq, price in parsed:
                    if bq <= qty:
                        floor_price = price
                    else:
                        break
                if floor_price is not None:
                    return float(floor_price)
                return float(parsed[0][1])

        return float(part_spec.get("base_value", 0) or 0)
    except Exception:
        return 0.0


def matrix_markup_pct(policy: Dict, rc: Tuple[int, int]) -> float:
    """
    Reads markup strictly from policy.matrix_markups[r][c].
    Expects decimals (0.35 == 35%).
    """
    grid = policy.get("matrix_markups")
    if not (
        isinstance(grid, list)
        and len(grid) == 3
        and all(isinstance(r, list) and len(r) == 3 for r in grid)
    ):
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
        dqty = _as_int(form.get(qty_ctrl, 0), 0)
        if dqty > 0 and r.get("match_on_dim") == "depth_in" and depth_in is not None:
            part = (r.get("map", {}) or {}).get(str(depth_in), r.get("else"))
            if part:
                resolved.append((part, int(dqty)))

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
            tqty = _as_int(form.get(tq_ctrl, 0), 0)
            if tqty >= _as_int(r.get("min_quantity", 1), 1):
                part = r.get("part")
                if part:
                    resolved.append((part, int(tqty)))

    # printed inside (sidekick-only; PDQ unaffected unless rule exists)
    if "resolve_printed_inside" in rules:
        r = rules["resolve_printed_inside"]
        ctrl_id = r.get("based_on_control")
        selected = form.get(ctrl_id)
        part = (r.get("map", {}) or {}).get(selected)
        if part:
            resolved.append((part, 1))

    return resolved