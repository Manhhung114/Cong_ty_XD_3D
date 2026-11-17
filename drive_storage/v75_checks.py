"""Bounded V7.5 draft checks for registered spreadsheets with explicit SI headers."""
from datetime import datetime
from math import isfinite, sqrt
from zoneinfo import ZoneInfo
from graphlib import CycleError, TopologicalSorter


def _number(raw):
    if isinstance(raw, bool):
        raise ValueError
    value = float(raw)
    if not isfinite(value):
        raise ValueError
    return value


def _voltage_drop(current, length, r, x, pf, voltage):
    delta = sqrt(3) * current * length * (r * pf + x * sqrt(1 - pf ** 2))
    return {"voltage_drop_V": delta, "voltage_drop_percent": 100 * delta / voltage}


# Bounds screen out values likely to overflow or reflect wrong input units.
# They are computational bounds, not design or compliance limits.
NUMERIC = {
    "ELE": (
        ("three_phase_voltage_drop", "ΔU = √3 I L (R cosφ + X sinφ), tải trễ",
         {"current_a": (0, 1e6), "length_km": (0, 1000), "r_ohm_km": (0, 1e4),
          "x_ohm_km": (0, 1e4), "pf": (1e-6, 1), "v_ll_v": (1e-3, 1e6)},
         _voltage_drop),
        ("adiabatic_section", "S_min = I_k √t / k, phép kiểm nhiệt đoạn nhiệt sơ bộ",
         {"fault_current_a": (1e-6, 1e6), "clearing_time_s": (1e-6, 5),
          "k_a_sqrt_s_per_mm2": (1e-6, 1000)},
         lambda i, t, k: {"min_section_mm2": i * sqrt(t) / k}),
    ),
    "HVA": (
        ("sensible_air_load", "Q_s = ρ c_p Q ΔT, chỉ tính nhiệt hiện",
         {"air_density_kg_m3": (.01, 10), "air_cp_kj_kg_k": (.01, 10),
          "air_flow_m3s": (0, 1e4), "delta_temp_k": (0, 500)},
         lambda rho, cp, flow, delta: {"sensible_load_kw": rho * cp * flow * delta}),
        ("duct_velocity", "v = Q / A, tiết diện hữu dụng",
         {"air_flow_m3s": (0, 1e4), "duct_area_m2": (1e-6, 1e4)},
         lambda flow, area: {"velocity_m_s": flow / area}),
    ),
    "PLU": (
        ("hazen_williams_loss", "h_f = 10.67 L Q^1.852 / (C^1.852 d^4.87), ống đầy",
         {"pipe_length_m": (0, 1e6), "water_flow_m3s": (0, 1e3),
          "hazen_c": (1, 300), "pipe_internal_diameter_m": (.001, 100)},
         lambda length, flow, c, diameter: {"friction_head_m":
             10.67 * length * flow ** 1.852 / (c ** 1.852 * diameter ** 4.87)}),
    ),
    "STR": (
        ("uniform_load_reaction", "Hai phản lực wL/2 và M_max=wL²/8, dầm giản đơn tải đều",
         {"uniform_load_kn_m": (0, 1e6), "span_m": (.001, 1e4)},
         lambda load, span: {"reaction_each_kn": load * span / 2,
                             "midspan_moment_kn_m": load * span ** 2 / 8}),
    ),
}
PUMP = ("pump_input_power", "P = ρ g Q H / η, g = 9.80665 m/s²",
        {"water_flow_m3s": (0, 1e3), "total_head_m": (0, 1e4),
         "water_density_kg_m3": (100, 2000), "pump_efficiency": (.001, 1)},
        lambda flow, head, density, eta: {"shaft_power_kw":
            density * 9.80665 * flow * head / (1000 * eta)})
NUMERIC["PLU"] += (PUMP,)
NUMERIC["FIR"] = (PUMP,)


def _finding(rule, level, message, sources=(), values=None):
    return {"rule": rule, "level": level, "message": message, "sources": list(sources),
            "values": values or {}, "standardCheck": "not_assessed",
            "methodVersion": "7.5.0", "reviewStatus": "DRAFT"}


def _source(row, columns):
    return f'{row["sheet"]}!row{row["row"]}:{columns}'


def _numeric_checks(agent_id, rows):
    groups = {}
    for row in rows:
        cells = row["cells"]
        key = str(cells.get("1", "")).strip().casefold()
        groups.setdefault(row["sheet"], {}).setdefault(key, []).append(row)
    for tool, method, parameters, calculate in NUMERIC.get(agent_id, ()):
        candidates = [group for group in groups.values() if parameters.keys() <= group.keys()]
        if len(candidates) != 1 or any(len(candidates[0][key]) != 1 for key in parameters):
            yield _finding(tool, "insufficient", "Cần một bảng có khóa đơn vị duy nhất: " +
                           ", ".join(parameters))
            continue
        selected = [candidates[0][key][0] for key in parameters]
        sources = [_source(row, "col1-col2") for row in selected]
        try:
            values = [_number(row["cells"].get("2")) for row in selected]
            if any(not lower <= value <= upper
                   for value, (lower, upper) in zip(values, parameters.values())):
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            yield _finding(tool, "invalid_input", "Số liệu ngoài phạm vi hoặc sai định dạng đơn vị", sources)
            continue
        yield _finding(tool, "calculated", method, sources,
                       {key: round(value, 6) for key, value in calculate(*values).items()})


def _table(rows, headers):
    for index, row in enumerate(rows):
        columns = {str(value).strip().casefold(): col for col, value in row["cells"].items()}
        if not set(headers) <= columns.keys():
            continue
        for item in rows[index + 1:]:
            if item["sheet"] != row["sheet"]:
                break
            yield ([str(item["cells"].get(columns[key], "")).strip() for key in headers],
                   _source(item, "cols" + ",".join(columns[key] for key in headers)))
        break


def _critical_path(rows, incomplete):
    tool = "critical_path"
    headers = ("task_id", "duration_days", "predecessors")
    tasks = {}
    sources = {}
    for (key, duration, parents), source in _table(rows, headers):
        if not key and not duration and not parents:
            continue
        try:
            days = _number(duration)
            if not key or key in tasks or not 0 <= days <= 10000:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            return _finding(tool, "invalid_input", "ID trùng/thiếu hoặc thời lượng ngày không hợp lệ", [source])
        tasks[key] = (days, tuple(p.strip() for p in parents.split(",") if p.strip()))
        sources[key] = source
    if not tasks or incomplete:
        return _finding(tool, "insufficient", "Cần bảng WBS đầy đủ: " + ", ".join(headers))
    if any(p not in tasks for _, parents in tasks.values() for p in parents):
        return _finding(tool, "invalid_input", "Quan hệ phụ thuộc chứa ID chưa có trong bảng")
    try:
        order = list(TopologicalSorter({k: v[1] for k, v in tasks.items()}).static_order())
    except CycleError as exc:
        return _finding(tool, "invalid_input", "Có vòng phụ thuộc trong WBS",
                        [sources[key] for key in exc.args[1]][:8])
    finished, paths = {}, {}
    for key in order:
        duration, parents = tasks[key]
        predecessor = max(parents, key=finished.__getitem__, default=None)
        finished[key] = finished.get(predecessor, 0) + duration
        paths[key] = [*paths.get(predecessor, []), key]
    last = max(order, key=finished.__getitem__)
    return _finding(tool, "calculated", "CPM theo ngày, quan hệ kết thúc–bắt đầu, không có độ trễ",
                    [sources[key] for key in paths[last]][:8],
                    {"duration_days": finished[last], "critical_path_example": paths[last][:20]})


def _itp(rows):
    headers = ("work_package", "drawing_revision", "sample_id", "test_report", "ncr_id", "closure_evidence")
    entries = list(_table(rows, headers))
    if not entries:
        yield _finding("itp_register_sample", "insufficient", "Cần bảng ITP: " + ", ".join(headers))
        return
    for index, (values, source) in enumerate(entries[:10]):
        work, revision, sample, report, ncr, closure = values
        if not all((work, revision, sample, report)) or (ncr and not closure):
            yield _finding("itp_register_sample", "insufficient",
                           "Thiếu công tác, revision, ID mẫu, phiếu thử hoặc bằng chứng đóng NCR", [source])
        else:
            yield _finding("itp_register_sample", "sampled",
                           "Có trường đối chiếu cho mẫu ITP; cần kỹ sư đọc chứng từ gốc", [source],
                           {"sample_row": index + 1})


def checks(agent_id, parsed):
    stats = parsed.get("stats") or {}
    rows = stats.get("table_rows", [])[:100]
    if agent_id in NUMERIC:
        yield from _numeric_checks(agent_id, rows)
    if agent_id in {"PM", "PLN"}:
        complete = stats.get("table_complete", not parsed.get("warnings"))
        yield _critical_path(rows, not complete)
    if agent_id == "QCX":
        yield from _itp(rows)

    from drive_storage.v75_registers import REGISTER_TOOLS, check_register
    if agent_id in REGISTER_TOOLS and parsed["type"] in {"csv", "xlsx"}:
        today = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()
        yield from check_register(REGISTER_TOOLS[agent_id], rows, _finding, today)
