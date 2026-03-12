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
    Returns an effective breaks dict for pricing selection (production parts only).

    - If qty < 100 and smoothing enabled: uses {1,25,50,75,100} where:
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

    for k in ("25", "50", "75"):
        if k in tiers:
            effective[k] = _as_float(tiers.get(k), 0.0)

    if not any(k in effective for k in ("25", "50", "75")):
        return raw_breaks

    return effective


def _fulfillment_effective_qty(catalog: Dict, program_qty: int) -> int:
    """Fulfillment tiering starts at 200. For qty < 200, use 200-tier pricing."""
    policy = catalog.get("policy", {}) or {}
    fp = policy.get("fulfillment_pricing", {}) or {}
    min_qty = _as_int(fp.get("min_qty", 200), 200)
    return max(_as_int(program_qty, 1), min_qty)


def _fulfillment_fixed_per_display_price(catalog: Dict, part_spec: Dict, program_qty: int) -> float:
    """
    Fixed per-display fulfillment line (AssembleTray / Pack out Tray / Pack out Header):
    price is selected by program qty tiers (floor), with qty < 200 treated as 200.
    """
    breaks = part_spec.get("breaks")
    parsed = _parse_breaks_map(breaks)
    if not parsed:
        return _round_money(_as_float(part_spec.get("base_value", 0.0), 0.0))
    eff_qty = _fulfillment_effective_qty(catalog, program_qty)
    return _round_money(_floor_from_parsed_breaks(parsed, eff_qty))


def _fulfillment_adder_cap_total_per_display(
    catalog: Dict,
    part_spec: Dict,
    *,
    count: int,
    program_qty: int,
) -> float:
    """
    Adder-with-cap fulfillment (Assemble Dividers / Product fill):
    - count <= 0 -> 0
    - total per display = base_for_1 + sum(adders 2..count)
    - for count > cap, repeat the cap adder for additional items
    """
    n = _as_int(count, 0)
    if n <= 0:
        return 0.0

    base_breaks = part_spec.get("base_for_1_breaks")
    base_parsed = _parse_breaks_map(base_breaks)
    if not base_parsed:
        return 0.0

    eff_qty = _fulfillment_effective_qty(catalog, program_qty)
    base = _floor_from_parsed_breaks(base_parsed, eff_qty)
    if n == 1:
        return _round_money(base)

    adder_breaks = part_spec.get("adder_breaks")
    if not isinstance(adder_breaks, dict) or not adder_breaks:
        return _round_money(base)

    cap = _as_int(part_spec.get("adder_cap", 0), 0)
    if cap <= 0:
        cap = n

    available_rows: List[int] = []
    for k in adder_breaks.keys():
        try:
            available_rows.append(int(k))
        except Exception:
            continue
    if not available_rows:
        return _round_money(base)

    max_row = max(available_rows)
    last_row = min(cap, max_row)

    def _adder_for_row(row_n: int) -> float:
        row = adder_breaks.get(str(row_n))
        parsed = _parse_breaks_map(row)
        if not parsed:
            return 0.0
        return _floor_from_parsed_breaks(parsed, eff_qty)

    total_adders = 0.0
    upto = min(n, last_row)
    for row_n in range(2, upto + 1):
        if str(row_n) in adder_breaks:
            total_adders += _adder_for_row(row_n)
        else:
            total_adders += _adder_for_row(last_row)

    if n > last_row:
        last_adder = _adder_for_row(last_row)
        total_adders += float(n - last_row) * last_adder

    return _round_money(base + total_adders)


def parts_value(
    catalog: Dict,
    part_key: str,
    *,
    program_qty: int | None = None,
    item_qty: int | None = None,
    **_ignored,
) -> float:
    """
    Returns a per-display unit price for a part at the given program quantity.

    Production parts:
    - qty < 100 uses derived tiers when enabled and present
    - qty >= 100 uses raw breaks (floor)

    Fulfillment parts (PDQ):
    - tiers start at 200 (qty < 200 treated as 200)
    - fixed-per-display lines use part_spec.breaks
    - adder-cap lines (dividers/touches) require item_qty to compute the per-display total
    """
    try:
        parts = catalog.get("parts", {}) or {}
        part_spec = parts.get(part_key, {}) or {}
        if not isinstance(part_spec, dict):
            return 0.0

        pq = max(_as_int(program_qty or 1, 1), 1)
        pricing_family = str(part_spec.get("pricing_family") or "").strip()

        if pricing_family == "fulfillment_fixed_per_display":
            return _fulfillment_fixed_per_display_price(catalog, part_spec, pq)

        if pricing_family == "fulfillment_adder_cap":
            n = _as_int(item_qty, 0)
            if n <= 0:
                return 0.0
            return _fulfillment_adder_cap_total_per_display(
                catalog, part_spec, count=n, program_qty=pq
            )

        qty = pq
        effective_breaks = _effective_breaks_for_part(catalog, part_spec, qty)
        if effective_breaks is not None:
            parsed = _parse_breaks_map(effective_breaks)
            if parsed:
                return _round_money(_floor_from_parsed_breaks(parsed, qty))

        return _round_money(_as_float(part_spec.get("base_value", 0.0), 0.0))
    except Exception:
        return 0.0


def matrix_markup_pct(policy: Dict, rc: Tuple[int, int]) -> float:
    """Reads markup strictly from policy.matrix_markups[r][c]. Expects decimals (0.35 == 35%)."""
    grid = policy.get("matrix_markups")
    if not (
        isinstance(grid, list)
        and len(grid) == 3
        and all(isinstance(r, list) and len(r) == 3 for r in grid)
    ):
        raise ValueError("Missing/invalid policy.matrix_markups (expected 3x3 list).")
    r, c = rc
    return float(grid[r][c])


def _when_matches(form: Dict, rule: Dict) -> bool:
    """
    Supports:
    - when_control + when_value
    - when_all: [{control, value}, ...]

    If no condition keys exist, returns True.
    """
    if not isinstance(rule, dict):
        return False

    when_all = rule.get("when_all")
    if isinstance(when_all, list) and when_all:
        for cond in when_all:
            if not isinstance(cond, dict):
                return False
            if form.get(cond.get("control")) != cond.get("value"):
                return False
        return True

    wc = rule.get("when_control")
    wv = rule.get("when_value")
    if wc is not None and wv is not None:
        return form.get(wc) == wv

    return True


def resolve_parts_per_unit(
    catalog: Dict,
    form: Dict,
    *,
    footprint_dims: Tuple[int | None, int | None],
) -> List[Tuple[str, int]]:
    """
    Applies catalog rules to produce a list of (part_key, qty_per_display).

    Note: for fulfillment adder-cap parts, qty_per_display is the entered count
    (divider_count or product_touches). The caller should pass that qty into
    parts_value(..., item_qty=qty_per_display) and NOT multiply again.
    """
    rules = catalog.get("rules", {}) or {}
    resolved: List[Tuple[str, int]] = []

    fp_key = form.get("footprint")
    width_in, depth_in = footprint_dims

    if fp_key and "resolve_footprint_base" in rules:
        r = rules["resolve_footprint_base"]
        base_part = (r.get("map", {}) or {}).get(fp_key)
        if base_part:
            resolved.append((base_part, 1))

    if "resolve_header" in rules:
        r = rules["resolve_header"]
        part = r.get("else")
        if form.get(r.get("when_control")) == r.get("when_value"):
            if r.get("match_on_dim") == "width_in" and width_in is not None:
                part = (r.get("map", {}) or {}).get(str(width_in), r.get("else"))
        if part:
            resolved.append((part, 1))

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

    if "resolve_shipper" in rules:
        r = rules["resolve_shipper"]
        if form.get(r.get("when_control")) == r.get("when_value"):
            part = (r.get("map", {}) or {}).get(fp_key, r.get("else"))
            if part:
                resolved.append((part, 1))

    if "resolve_assembly_touches" in rules:
        r = rules["resolve_assembly_touches"]
        if _when_matches(form, r):
            tq_ctrl = r.get("quantity_control")
            tqty = _as_int(form.get(tq_ctrl, 0), 0)
            if tqty >= _as_int(r.get("min_quantity", 1), 1):
                part = None
                if r.get("map_by") == "footprint" and fp_key:
                    part = (r.get("map", {}) or {}).get(fp_key, r.get("else"))
                else:
                    part = r.get("part")
                if part:
                    resolved.append((part, int(tqty)))

    if "resolve_fulfillment_assemble_tray" in rules:
        r = rules["resolve_fulfillment_assemble_tray"]
        if _when_matches(form, r) and fp_key:
            part = (r.get("map", {}) or {}).get(fp_key, r.get("else"))
            if part:
                resolved.append((part, 1))

    if "resolve_fulfillment_packout_tray" in rules:
        r = rules["resolve_fulfillment_packout_tray"]
        if _when_matches(form, r) and fp_key:
            part = (r.get("map", {}) or {}).get(fp_key, r.get("else"))
            if part:
                resolved.append((part, 1))

    if "resolve_fulfillment_packout_header" in rules:
        r = rules["resolve_fulfillment_packout_header"]
        if _when_matches(form, r) and fp_key:
            part = (r.get("map", {}) or {}).get(fp_key, r.get("else"))
            if part:
                resolved.append((part, 1))

    if "resolve_fulfillment_divider_assembly" in rules:
        r = rules["resolve_fulfillment_divider_assembly"]
        if _when_matches(form, r) and fp_key:
            qty_ctrl = r.get("quantity_control")
            dqty = _as_int(form.get(qty_ctrl, 0), 0)
            if dqty >= _as_int(r.get("min_quantity", 1), 1):
                part = (r.get("map", {}) or {}).get(fp_key, r.get("else"))
                if part:
                    resolved.append((part, int(dqty)))

    if "resolve_printed_inside" in rules:
        r = rules["resolve_printed_inside"]
        ctrl_id = r.get("based_on_control")
        selected = form.get(ctrl_id)
        part = (r.get("map", {}) or {}).get(selected)
        if part:
            resolved.append((part, 1))

    return resolved