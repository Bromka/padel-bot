"""Generates the schedule infographic as a PNG image."""
import datetime
import io
import textwrap

from PIL import Image, ImageDraw, ImageFont
import pytz

# ── Colours ───────────────────────────────────────────────
BG = (18, 18, 30)           # dark background
HEADER_BG = (30, 30, 50)
CLUB_HEADER_BG = (40, 40, 65)
FREE_BG = (34, 139, 70)     # green
BUSY_BG = (60, 60, 80)      # dark grey
RAIN_WARN_BG = (160, 60, 60)
TEXT_MAIN = (240, 240, 255)
TEXT_DIM = (150, 150, 180)
TEXT_FREE = (255, 255, 255)
TEXT_BUSY = (100, 100, 130)
GRID_LINE = (50, 50, 75)
OUTDOOR_BADGE = (200, 120, 30)

# ── Sizes ─────────────────────────────────────────────────
CELL_W = 110
CELL_H = 34
TIME_COL_W = 70
WEATHER_COL_W = 90
ROW_HEADER_H = 40
SECTION_GAP = 16
PADDING = 20
FONT_SIZE_MAIN = 15
FONT_SIZE_SMALL = 12
FONT_SIZE_HEADER = 18


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["/System/Library/Fonts/Helvetica.ttc",
         "/System/Library/Fonts/Arial.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
        if bold else
        ["/System/Library/Fonts/Helvetica.ttc",
         "/System/Library/Fonts/Arial.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _text_w(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _centered(draw, text, font, x, y, w, h, color):
    tw = _text_w(draw, text, font)
    th = font.size
    draw.text((x + (w - tw) // 2, y + (h - th) // 2), text, font=font, fill=color)


def _make_time_slots(start_h: int, end_h: int) -> list[str]:
    slots = []
    h, m = start_h, 0
    while h < end_h or (h == end_h and m == 0):
        slots.append(f"{h:02d}:{m:02d}")
        m += 30
        if m >= 60:
            m = 0
            h += 1
    return slots


def render_schedule(
    clubs_data: list[dict],
    forecast: dict,
    hours_after_rain: int,
    start_h: int,
    end_h: int,
    timezone: str,
) -> bytes:
    """
    clubs_data: list of {name, outdoor, booking_url, slots_by_court, error?}
    forecast: {HH:MM: {temp, rain, icon, ...}}
    Returns PNG bytes.
    """
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz)
    time_slots = _make_time_slots(start_h, end_h)

    font_hdr = _load_font(FONT_SIZE_HEADER, bold=True)
    font_main = _load_font(FONT_SIZE_MAIN, bold=True)
    font_sm = _load_font(FONT_SIZE_SMALL)
    font_sm_bold = _load_font(FONT_SIZE_SMALL, bold=True)

    # ── Calculate canvas width ─────────────────────────────
    max_courts = max(
        (len(c.get("slots_by_court", {})) for c in clubs_data if "error" not in c),
        default=1,
    )
    grid_w = TIME_COL_W + WEATHER_COL_W + max_courts * CELL_W
    canvas_w = PADDING * 2 + grid_w

    # ── Calculate canvas height ────────────────────────────
    total_h = PADDING  # top padding
    total_h += ROW_HEADER_H + 4  # global header
    for club in clubs_data:
        total_h += SECTION_GAP + ROW_HEADER_H  # club header
        if "error" not in club:
            total_h += ROW_HEADER_H  # column headers
            total_h += len(time_slots) * CELL_H
    total_h += PADDING  # bottom padding

    img = Image.new("RGB", (canvas_w, total_h), BG)
    draw = ImageDraw.Draw(img)

    y = PADDING

    # ── Global header ──────────────────────────────────────
    date_str = now.strftime("%-d %B %Y, %A").capitalize()
    updated_str = now.strftime("обновлено %H:%M")
    header_text = f"🏓 Падел-корты Казани  •  {date_str}"

    draw.rectangle([PADDING, y, canvas_w - PADDING, y + ROW_HEADER_H], fill=HEADER_BG)
    draw.text((PADDING + 10, y + 8), header_text, font=font_hdr, fill=TEXT_MAIN)
    draw.text(
        (canvas_w - PADDING - _text_w(draw, updated_str, font_sm) - 8, y + 12),
        updated_str, font=font_sm, fill=TEXT_DIM,
    )
    y += ROW_HEADER_H + 4

    # ── Per-club sections ──────────────────────────────────
    for club in clubs_data:
        y += SECTION_GAP
        court_names = list(club.get("slots_by_court", {}).keys())
        n_courts = len(court_names)
        section_w = TIME_COL_W + WEATHER_COL_W + n_courts * CELL_W

        # Club header row
        club_type_label = "🌤 уличные" if club["outdoor"] else "🏢 крытые"
        club_label = f"  {club['name']}  ({club_type_label})"
        draw.rectangle(
            [PADDING, y, PADDING + section_w, y + ROW_HEADER_H],
            fill=CLUB_HEADER_BG,
        )
        draw.text((PADDING + 10, y + 10), club_label, font=font_main, fill=TEXT_MAIN)

        url_text = club.get("booking_url", "")
        url_x = PADDING + section_w - _text_w(draw, url_text, font_sm) - 10
        draw.text((url_x, y + 14), url_text, font=font_sm, fill=(100, 160, 255))
        y += ROW_HEADER_H

        if "error" in club:
            draw.text((PADDING + 16, y + 8), f"⚠ {club['error']}", font=font_sm, fill=(255, 100, 100))
            y += CELL_H
            continue

        # Column header row
        x = PADDING
        _centered(draw, "Время", font_sm_bold, x, y, TIME_COL_W, ROW_HEADER_H, TEXT_DIM)
        x += TIME_COL_W
        _centered(draw, "Погода", font_sm_bold, x, y, WEATHER_COL_W, ROW_HEADER_H, TEXT_DIM)
        x += WEATHER_COL_W
        for cname in court_names:
            short = cname if len(cname) <= 12 else cname[:11] + "…"
            _centered(draw, short, font_sm_bold, x, y, CELL_W, ROW_HEADER_H, TEXT_DIM)
            x += CELL_W

        # Divider
        draw.line([(PADDING, y + ROW_HEADER_H - 1), (PADDING + section_w, y + ROW_HEADER_H - 1)],
                  fill=GRID_LINE, width=1)
        y += ROW_HEADER_H

        # Time slot rows
        for slot in time_slots:
            x = PADDING
            w_data = _get_weather_approx(slot, forecast)

            # Check rain warning for outdoor court
            rain_warning = club["outdoor"] and _rain_within(slot, forecast, hours_after_rain)

            row_bg = RAIN_WARN_BG if rain_warning else BG

            draw.rectangle([PADDING, y, PADDING + section_w, y + CELL_H - 1], fill=row_bg)

            # Time cell
            time_color = (255, 180, 60) if rain_warning else TEXT_MAIN
            _centered(draw, slot, font_main, x, y, TIME_COL_W, CELL_H, time_color)
            x += TIME_COL_W

            # Weather cell
            if w_data:
                icon = w_data["icon"]
                temp = f"{w_data['temp']:+d}°"
                weather_str = f"{icon} {temp}"
                rain_str = f"☔ {w_data['rain_mm']:.1f}мм" if w_data["rain_mm"] > 0 else ""
                wx = x + (WEATHER_COL_W - _text_w(draw, weather_str, font_sm)) // 2
                draw.text((wx, y + 4), weather_str, font=font_sm, fill=TEXT_MAIN)
                if rain_str:
                    rw = _text_w(draw, rain_str, font_sm)
                    draw.text((x + (WEATHER_COL_W - rw) // 2, y + 18), rain_str, font=font_sm, fill=(255, 150, 100))
            x += WEATHER_COL_W

            # Court cells
            for cname in court_names:
                available = club["slots_by_court"].get(cname, {}).get(slot, False)
                cell_bg = FREE_BG if available else BUSY_BG
                if rain_warning and club["outdoor"]:
                    cell_bg = RAIN_WARN_BG
                cell_text = "СВОБОДНО" if available else "—"
                cell_color = TEXT_FREE if available else TEXT_BUSY
                if rain_warning and club["outdoor"]:
                    cell_text = "☔ ДОЖДЬ"
                    cell_color = (255, 200, 150)
                draw.rectangle([x + 2, y + 2, x + CELL_W - 3, y + CELL_H - 3], fill=cell_bg)
                _centered(draw, cell_text, font_sm_bold, x, y, CELL_W, CELL_H, cell_color)
                x += CELL_W

            # Row separator
            draw.line([(PADDING, y + CELL_H - 1), (PADDING + section_w, y + CELL_H - 1)],
                      fill=GRID_LINE, width=1)
            y += CELL_H

    # ── Export ────────────────────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _get_weather_approx(slot: str, forecast: dict) -> dict | None:
    if not forecast:
        return None
    sh, sm = map(int, slot.split(":"))
    slot_min = sh * 60 + sm
    best, best_diff = None, float("inf")
    for key, val in forecast.items():
        h, m = map(int, key.split(":"))
        diff = abs(h * 60 + m - slot_min)
        if diff < best_diff:
            best_diff = diff
            best = val
    return best if best_diff <= 150 else None


def _rain_within(slot: str, forecast: dict, hours: int) -> bool:
    """True if rain is forecast within `hours` hours before or at this slot."""
    sh, sm = map(int, slot.split(":"))
    slot_min = sh * 60 + sm
    for key, val in forecast.items():
        h, m = map(int, key.split(":"))
        entry_min = h * 60 + m
        # rain in this slot or in the previous N hours
        if 0 <= slot_min - entry_min <= hours * 60 and val.get("rain"):
            return True
    return False
