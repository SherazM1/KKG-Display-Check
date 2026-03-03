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


def _round_money(value: float) -> float:
    # Prevents float artifacts; rounds to cents as required.
    return round(float(value) + 1e-9, 2)


def _parse_breaks_map(breaks: object) -> List[Tuple[int, float]]:
    if not isinstance(breaks, dict):
        return []
    parsed: List[Tuple[int, float]] = []
    for k, v in breaks.items():
        try:
            bq = int(k)
        except Exception:
            continue
        parsed.append((bq, _as_float(v, 0.0)))
    parsed.sort(key=lambda x: x[0])
    return parsed


def _floor_from_parsed_breaks(parsed: List[Tuple[int, float]], qty: int) -> float:
    if not parsed:
        return 0.0

    qty_i = max(_as_int(qty, 0), 0)
    floor_price = None
    for bq, price in parsed:
        if bq <= qty_i:
            floor_price = price
        else:
            break

    if floor_price is not None:
        return float(floor_price)

    return float(parsed[0][1])


def _sub100_smoothing_enabled(catalog: Dict) -> bool:
    policy = catalog.get("policy", {}) or {}
    bp = policy.get("break_pricing", {}) or {}
    sub = bp.get("sub_100_smoothing", {}) or {}
    return bool(sub.get("enabled", False))


def _effective_breaks_for_part(catalog: Dict, part_spec: Dict, qty: int) -> Dict | None:
    """
    Returns an effective breaks dict for pricing selection.

    - If qty < 100 and smoothing enabled:
        uses {1,25,50,75,100} where:
          1 & 100 come from raw breaks
          25/50/75 come from derived_breaks.tiers
      Guardrail: raw breaks must include both "1" and "100".
    - Else: returns raw breaks.
    """
    raw_breaks = part_spec.get("breaks")
    if not isinstance(raw_breaks, dict) or not raw_breaks:
        return None

    if qty >= 100:
        return raw_breaks

    if not _sub100_smoothing_enabled(catalog):
        return raw_breaks

    # Guardrail: require real anchors
    if "1" not in raw_breaks or "100" not in raw_breaks:
        return raw_breaks

    derived = part_spec.get("derived_breaks", {}) or {}
    tiers = (derived.get("tiers", {}) or {}) if isinstance(derived, dict) else {}
    if not isinstance(tiers, dict) or not tiers:
        return raw_breaks

    effective: Dict[str, float] = {
        "1": _as_float(raw_breaks.get("1"), 0.0),
        "100": _as_float(raw_breaks.get("100"), 0.0),
    }

    # Only include defined tiers; missing ones won't break selection.
    for k in ("25", "50", "75"):
        if k in tiers:
            effective[k] = _as_float(tiers.get(k), 0.0)

    # If we didn't add any mid-tiers, there's nothing to smooth.
    if not any(k in effective for k in ("25", "50", "75")):
        return raw_breaks

    return effective


def parts_value(catalog: Dict, part_key: str, *, program_qty: int | None = None, **_ignored) -> float:
    """
    Per-unit part price at program quantity.

    - Uses derived exponential tiers for qty < 100 when enabled in policy and available on part.
    - Uses raw breaks (floor) for qty >= 100.
    - Falls back to base_value when no breaks exist.
    - Always returns dollars rounded to cents.
    """
    try:
        parts = catalog.get("parts", {}) or {}
        part_spec = parts.get(part_key, {}) or {}
        if not isinstance(part_spec, dict):
            return 0.0

        qty = max(_as_int(program_qty or 1, 1), 1)

        effective_breaks = _effective_breaks_for_part(catalog, part_spec, qty)
        if effective_breaks is not None:
            parsed = _parse_breaks_map(effective_breaks)
            if parsed:
                return _round_money(_floor_from_parsed_breaks(parsed, qty))

        return _round_money(_as_float(part_spec.get("base_value", 0.0), 0.0))
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

    # dividers (PDQ: optionally map by footprint; Sidekick: still maps by depth_in)
    if "resolve_dividers" in rules:
        r = rules["resolve_dividers"]
        qty_ctrl = r.get("quantity_control")
        dqty = _as_int(form.get(qty_ctrl, 0), 0)

        if dqty > 0:
            part = None
            if r.get("map_by") == "footprint" and fp_key:
                part = (r.get("map", {}) or {}).get(fp_key, r.get("else"))
            else:
                if r.get("match_on_dim") == "depth_in" and depth_in is not None:
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