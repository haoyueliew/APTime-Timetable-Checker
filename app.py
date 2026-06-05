from flask import Flask, render_template, request, jsonify
import requests
import re
from datetime import datetime, timedelta

app = Flask(__name__)

API_URL = "https://s3-ap-southeast-1.amazonaws.com/open-ws/weektimetable"
DAYS = ["MON", "TUE", "WED", "THU", "FRI"]

# ── Fetch timetable data from APSpace ─────────────────────────────────────────
def fetch_timetable():
    response = requests.get(API_URL, timeout=30)
    return response.json()

# ── Convert time string like "08:30 AM" into minutes since midnight ───────────
def to_minutes(time_str):
    if not time_str:
        return None
    time_str = time_str.strip()
    match = re.match(r'^(\d{1,2}):(\d{2})\s*(AM|PM)?$', time_str, re.IGNORECASE)
    if not match:
        return None
    h, m = int(match.group(1)), int(match.group(2))
    ampm = match.group(3).upper() if match.group(3) else None
    if ampm == "PM" and h != 12:
        h += 12
    if ampm == "AM" and h == 12:
        h = 0
    return h * 60 + m

# ── Parse DATESTAMP like "30-MAR-26" into a datetime object ──────────────────
def parse_datestamp(ds):
    try:
        return datetime.strptime(ds.strip(), "%d-%b-%y")
    except:
        return None

# ── Get the Monday of the week for a given date ──────────────────────────────
def get_week_monday(dt):
    return dt - timedelta(days=dt.weekday())  # Monday = 0

# ── Format datetime to a friendly label matching APSpace style: "Apr 27, 2026" ─
def format_week_label(monday_dt, all_mondays_sorted):
    label = monday_dt.strftime('%b %d, %Y').replace(' 0', ' ')
    if monday_dt == all_mondays_sorted[0]:
        label += "  —  This Week"
    elif len(all_mondays_sorted) > 1 and monday_dt == all_mondays_sorted[1]:
        label += "  —  Next Week"
    return label

# ── Strip L/T lecture/tutorial suffix from module code ───────────────────────
def base_modid(modid):
    modid = modid.upper().strip()
    modid = re.sub(r'-\d+$', '', modid)
    modid = re.sub(r'-(L|T|LAB)$', '', modid)
    return modid

# ── Get busy intervals, with optional group, week and ignored module filters ──
def get_busy_intervals(data, intake_code, group=None, ignored_modules=None, datestamp=None):
    intake_code = intake_code.upper().strip()
    ignored_modules = [m.upper().strip() for m in (ignored_modules or [])]
    busy = {day: [] for day in DAYS}
    found = False

    # Convert datestamp (Monday) to a week range for filtering
    week_monday = None
    week_friday = None
    if datestamp:
        dt = parse_datestamp(datestamp)
        if dt:
            week_monday = get_week_monday(dt)
            week_friday = week_monday + timedelta(days=4)

    for entry in data:
        if entry.get("INTAKE", "").upper().strip() != intake_code:
            continue
        found = True

        # Filter by selected week — match any date within Mon–Fri of that week
        if week_monday:
            entry_dt = parse_datestamp(entry.get("DATESTAMP", ""))
            if not entry_dt or not (week_monday <= entry_dt <= week_friday):
                continue

        # Filter by group if specified
        if group:
            entry_group = entry.get("GROUPING", "").upper().strip()
            if entry_group and entry_group != group.upper().strip():
                continue

        # Skip ignored CT elective modules — match by base code (ignores L/T suffix)
        modid = entry.get("MODID", "").upper().strip()
        if any(base_modid(modid) == base_modid(ig) for ig in ignored_modules):
            continue

        day = entry.get("DAY", "").upper().strip()
        if day not in DAYS:
            continue
        start = to_minutes(entry.get("TIME_FROM", ""))
        end   = to_minutes(entry.get("TIME_TO", ""))
        if start is not None and end is not None:
            busy[day].append([start, end])

    return busy, found

# ── Merge overlapping intervals ───────────────────────────────────────────────
def merge_intervals(intervals):
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged = [list(sorted_intervals[0])]
    for start, end in sorted_intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged

# ── Find common free slots across all intakes ─────────────────────────────────
def find_free_slots(all_busy, min_gap_mins):
    DAY_START = 8 * 60
    DAY_END   = 18 * 60
    free_slots = {}

    for day in DAYS:
        combined = []
        for busy in all_busy:
            combined.extend(busy[day])
        merged = merge_intervals(combined)

        free = []
        current = DAY_START

        for start, end in merged:
            if current < start and (start - current) >= min_gap_mins:
                free.append({"start": current, "end": start, "rest_of_day": False})
            if end > current:
                current = end

        if current < DAY_END:
            free.append({"start": current, "end": None, "rest_of_day": True})

        free_slots[day] = free

    return free_slots

# ── Format minutes back to readable time like "8:30 AM" ──────────────────────
def format_time(minutes):
    h = minutes // 60
    m = minutes % 60
    ampm = "PM" if h >= 12 else "AM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ampm}"

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# ── Get available weeks for given intakes ─────────────────────────────────────
@app.route("/get-weeks", methods=["POST"])
def get_weeks():
    try:
        body    = request.get_json()
        intakes = [i["code"].upper().strip() for i in body.get("intakes", [])]
        data    = fetch_timetable()

        # Collect all datestamps across given intakes
        datestamps = set()
        for entry in data:
            if entry.get("INTAKE", "").upper().strip() in intakes:
                ds = entry.get("DATESTAMP", "").strip()
                if ds:
                    datestamps.add(ds)

        # Map each datestamp to its Monday (start of week)
        monday_map = {}  # monday_dt -> representative datestamp (the Monday itself if exists, else earliest in week)
        for ds in datestamps:
            dt = parse_datestamp(ds)
            if not dt:
                continue
            monday = get_week_monday(dt)
            # Store the monday datetime, keep track of which datestamps belong to this week
            if monday not in monday_map:
                monday_map[monday] = ds
            else:
                # Prefer the datestamp that IS the monday
                existing_dt = parse_datestamp(monday_map[monday])
                if dt == monday:
                    monday_map[monday] = ds
                elif existing_dt != monday and dt < existing_dt:
                    monday_map[monday] = ds

        # Sort weeks chronologically
        sorted_mondays = sorted(monday_map.keys())

        weeks = []
        for monday_dt in sorted_mondays:
            # Format the monday date as a datestamp string to pass back for filtering
            monday_str = monday_dt.strftime("%d-%b-%y").upper()  # e.g. "27-APR-26"
            label = format_week_label(monday_dt, sorted_mondays)
            weeks.append({
                "datestamp": monday_str,
                "monday_dt": monday_dt.strftime("%Y-%m-%d"),
                "label": label
            })

        return jsonify({"weeks": weeks})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Fetch CT elective modules for given intakes ───────────────────────────────
@app.route("/get-modules", methods=["POST"])
def get_modules():
    try:
        body       = request.get_json()
        intakes    = [{"code": i["code"].upper().strip(), "group": i.get("group", "")} for i in body.get("intakes", [])]
        datestamp  = body.get("datestamp", "").strip()
        data       = fetch_timetable()

        ct_modules = {}

        for intake in intakes:
            code  = intake["code"]
            group = intake["group"].upper().strip() if intake["group"] else None

            # Convert datestamp to week range
            week_monday = None
            week_friday = None
            if datestamp:
                dt = parse_datestamp(datestamp)
                if dt:
                    week_monday = get_week_monday(dt)
                    week_friday = week_monday + timedelta(days=4)

            for entry in data:
                if entry.get("INTAKE", "").upper().strip() != code:
                    continue
                if week_monday:
                    entry_dt = parse_datestamp(entry.get("DATESTAMP", ""))
                    if not entry_dt or not (week_monday <= entry_dt <= week_friday):
                        continue
                if group:
                    entry_group = entry.get("GROUPING", "").upper().strip()
                    if entry_group and entry_group != group:
                        continue
                modid = entry.get("MODID", "").upper().strip()
                if modid.startswith("CT"):
                    bmod = base_modid(modid)
                    if bmod not in ct_modules:
                        ct_modules[bmod] = entry.get("MODULE_NAME", bmod)

        sorted_modules = [
            {"modid": k, "name": v}
            for k, v in sorted(ct_modules.items())
        ]

        return jsonify({"ct_modules": sorted_modules})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Find common free slots ────────────────────────────────────────────────────
@app.route("/find-slots", methods=["POST"])
def find_slots():
    try:
        body            = request.get_json()
        intakes         = [{"code": i["code"].upper().strip(), "group": i.get("group", "")} for i in body.get("intakes", [])]
        min_gap         = int(body.get("min_gap", 60))
        ignored_modules = [m.upper().strip() for m in body.get("ignored_modules", [])]
        datestamp       = body.get("datestamp", "").strip()

        if len(intakes) < 2:
            return jsonify({"error": "Please provide at least 2 intake codes."}), 400

        data      = fetch_timetable()
        all_busy  = []
        not_found = []

        for intake in intakes:
            code  = intake["code"]
            group = intake["group"].upper().strip() if intake["group"] else None
            busy, found = get_busy_intervals(
                data, code,
                group=group,
                ignored_modules=ignored_modules,
                datestamp=datestamp if datestamp else None
            )
            all_busy.append(busy)
            if not found:
                not_found.append(code)

        free_slots = find_free_slots(all_busy, min_gap)

        combined_busy = {}
        for day in DAYS:
            combined = []
            for busy in all_busy:
                combined.extend(busy[day])
            combined_busy[day] = merge_intervals(combined)

        formatted_free = {}
        formatted_busy = {}

        for day in DAYS:
            formatted_free[day] = []
            for slot in free_slots[day]:
                formatted_free[day].append({
                    "start":       format_time(slot["start"]),
                    "start_mins":  slot["start"],
                    "end":         format_time(slot["end"]) if slot["end"] else None,
                    "end_mins":    slot["end"],
                    "rest_of_day": slot["rest_of_day"],
                    "duration":    (slot["end"] - slot["start"]) if slot["end"] else None
                })

            formatted_busy[day] = [
                {"start": s, "end": e}
                for s, e in combined_busy[day]
            ]

        return jsonify({
            "free_slots":       formatted_free,
            "busy_slots":       formatted_busy,
            "not_found":        not_found,
            "intakes":          [i["code"] for i in intakes],
            "min_gap":          min_gap,
            "ignored_modules":  ignored_modules,
            "datestamp":        datestamp
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("  APU Free Slot Finder - Running!")
    print("  Open your browser and go to:")
    print("  http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True)

