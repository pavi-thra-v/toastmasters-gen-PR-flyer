import io
from pathlib import Path
from datetime import date
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ============================================================
# AL NextGen Toastmasters - Personal VPPR Flyer Generator
# ============================================================
# Run:
#   pip install -r requirements.txt
#   streamlit run app.py
#
# The app creates a 1080 x 1350 PNG/PDF flyer in a layout
# inspired by the club flyers supplied by the user.
# ============================================================

W, H = 1080, 1350

BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"

# Club palette sampled/approximated from the supplied flyers.
BG = (250, 250, 250)
NAVY = (0, 65, 101)
FOOTER = (0, 79, 122)
WHITE = (250, 250, 250)
BLACK = (15, 15, 15)
YELLOW = (255, 213, 45)
MAROON = (105, 8, 20)

st.set_page_config(
    page_title="AL NextGen VPPR Flyer Generator",
    page_icon="📰",
    layout="wide",
)

# -----------------------------
# Font handling
# -----------------------------
def find_font(bold=False, italic=False):
    candidates = []
    if bold and italic:
        candidates += [
            ASSET_DIR / "Montserrat-BoldItalic.ttf",
            ASSET_DIR / "Montserrat-SemiBoldItalic.ttf",
        ]
    elif bold:
        candidates += [
            ASSET_DIR / "Montserrat-Bold.ttf",
            ASSET_DIR / "Montserrat-SemiBold.ttf",
        ]
    elif italic:
        candidates += [
            ASSET_DIR / "Montserrat-Italic.ttf",
        ]
    else:
        candidates += [
            ASSET_DIR / "Montserrat-Regular.ttf",
        ]

    # Common Linux / Windows locations.
    candidates += [
        Path("/usr/share/fonts/truetype/montserrat/Montserrat-Regular.ttf"),
        Path("/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf"),
        Path("C:/Windows/Fonts/montserrat.ttf"),
        Path("C:/Windows/Fonts/Montserrat-Bold.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]

    for p in candidates:
        if p.exists():
            return p

    # Pillow's bundled DejaVu fonts are a reliable fallback.
    if bold and italic:
        return "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
    if bold:
        return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if italic:
        return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(size, bold=False, italic=False):
    try:
        return ImageFont.truetype(str(find_font(bold, italic)), size=size)
    except Exception:
        return ImageFont.load_default()


def text_bbox(draw, text, f):
    return draw.textbbox((0, 0), text, font=f)


def fit_font(draw, text, max_width, start_size, min_size=12, bold=False, italic=False):
    size = start_size
    while size >= min_size:
        f = font(size, bold=bold, italic=italic)
        if text_bbox(draw, text, f)[2] <= max_width:
            return f
        size -= 1
    return font(min_size, bold=bold, italic=italic)


def centered_text(draw, text, box, f, fill=WHITE, spacing=4):
    x1, y1, x2, y2 = box
    bb = draw.multiline_textbbox((0, 0), text, font=f, spacing=spacing, align="center")
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    x = x1 + (x2 - x1 - tw) / 2
    y = y1 + (y2 - y1 - th) / 2 - bb[1]
    draw.multiline_text((x, y), text, font=f, fill=fill, spacing=spacing, align="center")


def rounded_photo(img, size, radius=26):
    """Crop image to exact size and add rounded corners."""
    img = ImageOps.exif_transpose(img).convert("RGB")
    img = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.4))
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, size[0]-1, size[1]-1), radius=radius, fill=255)
    out = Image.new("RGB", size, WHITE)
    out.paste(img, (0, 0), mask)
    return out


def draw_card(canvas, role_data, x, y, card_w, card_h):
    d = ImageDraw.Draw(canvas)

    # Outer navy card.
    d.rounded_rectangle(
        (x, y, x + card_w, y + card_h),
        radius=28,
        fill=NAVY,
    )

    photo_x = x + 28
    photo_y = y + 28
    photo_w = card_w - 56
    photo_h = 270

    photo = role_data.get("photo")
    if photo is not None:
        photo = rounded_photo(photo, (photo_w, photo_h), radius=25)
    else:
        photo = Image.new("RGB", (photo_w, photo_h), (205, 210, 210))
        pd = ImageDraw.Draw(photo)
        f = font(30, bold=True)
        centered_text(pd, "PHOTO", (0, 0, photo_w, photo_h), f, fill=(90, 95, 95))

    canvas.paste(photo, (photo_x, photo_y))

    name = (role_data.get("name") or "Name").strip()
    role = (role_data.get("role") or "ROLE").strip()

    name_f = fit_font(d, name, card_w - 45, 27, 18, bold=False)
    role_f = fit_font(d, role.upper(), card_w - 40, 31, 17, bold=True)

    name_bb = d.textbbox((0, 0), name, font=name_f)
    name_w = name_bb[2] - name_bb[0]
    d.text(
        (x + (card_w - name_w) / 2, y + 322),
        name,
        font=name_f,
        fill=WHITE,
    )

    # Role can be two lines for GENERAL EVALUATOR, etc.
    role_text = role.upper()
    if len(role_text) > 15:
        words = role_text.split()
        if len(words) >= 2:
            role_text = " ".join(words[:-1]) + "\n" + words[-1]

    centered_text(
        d,
        role_text,
        (x + 18, y + 365, x + card_w - 18, y + card_h - 15),
        role_f,
        fill=WHITE,
        spacing=2,
    )


def draw_flyer(
    meeting_no,
    meeting_date,
    meeting_time,
    venue,
    theme,
    word,
    idiom,
    cards,
    logo,
    teams_block,
):
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)

    # Header
    if logo:
        logo = ImageOps.contain(ImageOps.exif_transpose(logo).convert("RGB"), (205, 165))
        canvas.paste(logo, (65, 25))

    header_x = 292
    d.text(
        (header_x, 57),
        "AL NextGen Toastmasters Club",
        font=fit_font(d, "AL NextGen Toastmasters Club", 710, 42, 28, bold=True),
        fill=NAVY,
    )
    d.text(
        (header_x, 118),
        "AREA C01 | DIVISION C | DISTRICT 229",
        font=fit_font(d, "AREA C01 | DIVISION C | DISTRICT 229", 710, 31, 20, bold=True),
        fill=NAVY,
    )

    # Main cards.
    card_w = 309
    card_h = 417
    left_x = 41
    middle_x = 366
    top_y = 222
    bottom_x = 211
    bottom_y = 673

    draw_card(canvas, cards[0], left_x, top_y, card_w, card_h)
    draw_card(canvas, cards[1], middle_x, top_y, card_w, card_h)
    draw_card(canvas, cards[2], bottom_x, bottom_y, card_w, card_h)

    # Right information panel with pointed bottom.
    px1, py1, px2 = 695, 218, 1045
    panel_bottom = 867
    d.rounded_rectangle((px1, py1, px2, panel_bottom - 80), radius=35, fill=NAVY)
    d.polygon(
        [(px1, panel_bottom - 110), (px2, panel_bottom - 110),
         ((px1 + px2) // 2, panel_bottom)],
        fill=NAVY,
    )

    centered_text(d, "DATE", (px1 + 10, 252, px2 - 10, 306),
                  font(38, bold=True), WHITE)
    centered_text(d, meeting_date, (px1 + 10, 316, px2 - 10, 370),
                  fit_font(d, meeting_date, 310, 34, 22), WHITE)

    centered_text(d, "TIME", (px1 + 10, 400, px2 - 10, 454),
                  font(38, bold=True), WHITE)
    centered_text(d, meeting_time, (px1 + 10, 464, px2 - 10, 525),
                  fit_font(d, meeting_time, 315, 32, 20), WHITE)

    centered_text(d, "VENUE", (px1 + 10, 548, px2 - 10, 603),
                  font(38, bold=True), WHITE)

    venue_lines = venue.strip()
    vf = fit_font(d, venue_lines, 310, 29, 26, bold=False)
    # Word-wrap venue to a visually useful width.
    words = venue_lines.split()
    lines, current = [], ""
    for w in words:
        trial = (current + " " + w).strip()
        if text_bbox(d, trial, vf)[2] <= 310:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    venue_text = "\n".join(lines[:5])
    centered_text(d, venue_text, (px1 + 10, 612, px2 - 10, 805),
                  vf, WHITE, spacing=7)

    # Teams QR / join block.
    if teams_block:
        tb = ImageOps.contain(ImageOps.exif_transpose(teams_block).convert("RGB"), (345, 335))
        canvas.paste(tb, (675, 875))

    # Theme
    d.text((188, 1125), "THEME OF THE DAY",
            font=font(30, bold=True, italic=True), fill=MAROON)
    theme_f = fit_font(d, theme, 470, 31, 19, bold=True)
    d.text((192, 1172), theme,
            font=theme_f, fill=NAVY)

    # Footer
    fy = 1243
    d.rectangle((0, fy, W, H), fill=FOOTER)

    d.text((40, fy + 17), "WORD OF THE DAY",
            font=font(29, bold=False, italic=True), fill=WHITE)
    word_f = fit_font(d, word, 300, 28, 18, italic=True)
    d.text((40, fy + 58), word,
            font=word_f, fill=YELLOW)

    meeting_label = f"Meeting No.{meeting_no}"
    mf = fit_font(d, meeting_label, 300, 36, 24, bold=True)
    mb = d.textbbox((0, 0), meeting_label, font=mf)
    d.text(((W - (mb[2] - mb[0])) / 2, fy + 33),
           meeting_label, font=mf, fill=WHITE)

    d.text((742, fy + 17), "IDIOM OF THE DAY",
            font=font(29, bold=False, italic=True), fill=WHITE)
    idiom_f = fit_font(d, idiom, 300, 28, 17, italic=True)
    ib = d.textbbox((0, 0), idiom, font=idiom_f)
    d.text((1020 - (ib[2] - ib[0]), fy + 58),
           idiom, font=idiom_f, fill=YELLOW)

    return canvas


# -----------------------------
# Sidebar / inputs
# -----------------------------
st.title("📰 AL NextGen VPPR Flyer Generator")
st.caption("Generate your weekly role-player flyer in seconds.")

with st.sidebar:
    st.header("Meeting details")

    meeting_no = st.number_input("Meeting number", min_value=1, value=19, step=1)
    meeting_date = st.date_input("Date", value=date.today())
    # Windows does not support the Linux "%-d" strftime format,
    # so build the ordinal date explicitly for cross-platform compatibility.
    try:
        day = meeting_date.day
        suffix = "th" if 10 <= day % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        meeting_date_str = f"{day}{suffix} {meeting_date.strftime("%b %Y")}"
    except Exception:
        meeting_date_str = str(meeting_date)

    meeting_time = st.text_input("Time", "3:00 to 4:30 PM")
    venue = st.text_area(
        "Venue",
        "NDO2 (Eagle Room)\nGP Hinduja Centre for Technology & Innovation (GPC)",
        height=100,
    )
    theme = st.text_input("Theme of the Day", "Best of Both Worlds")
    word = st.text_input("Word of the Day", "Amalgamate")
    idiom = st.text_input("Idiom of the Day", "Bridge the gap")

    st.divider()
    st.header("Flyer layout")

    layout = st.radio(
        "Choose layout",
        ["Key Roles", "Supporting Roles"],
        help="Both layouts use the same visual template; only the default role names change.",
    )

    if layout == "Key Roles":
        default_roles = ["TMOD", "General Evaluator", "TTM"]
    else:
        default_roles = ["Timer", "Ah-counter", "Grammarian"]

    st.divider()
    st.header("Brand assets")
    logo_upload = st.file_uploader("Club logo (optional)", type=["png", "jpg", "jpeg"])
    teams_upload = st.file_uploader("Teams QR block (optional)", type=["png", "jpg", "jpeg"])

# Load default assets.
default_logo = None
default_teams = None
try:
    default_logo = Image.open(ASSET_DIR / "default_logo.png").convert("RGB")
except Exception:
    pass

try:
    default_teams = Image.open(ASSET_DIR / "default_teams_qr.png").convert("RGB")
except Exception:
    pass

logo = Image.open(logo_upload).convert("RGB") if logo_upload else default_logo
teams_block = Image.open(teams_upload).convert("RGB") if teams_upload else default_teams

# -----------------------------
# Role inputs
# -----------------------------
st.subheader("Role players")

cols = st.columns(3)
role_data = []

for i in range(3):
    with cols[i]:
        st.markdown(f"### Role {i+1}")
        role = st.text_input(
            "Role",
            value=default_roles[i],
            key=f"role_{i}",
        )
        name = st.text_input(
            "Member name",
            value="",
            placeholder="e.g. TM Pavithra",
            key=f"name_{i}",
        )
        photo_file = st.file_uploader(
            "Photo",
            type=["png", "jpg", "jpeg"],
            key=f"photo_{i}",
        )
        photo = Image.open(photo_file).convert("RGB") if photo_file else None
        role_data.append({"role": role, "name": name, "photo": photo})

st.divider()

generate = st.button("🚀 Generate Flyer", type="primary", use_container_width=True)

if generate:
    if any(not x["name"].strip() for x in role_data):
        st.warning("Please enter all three member names.")
    else:
        flyer = draw_flyer(
            meeting_no=meeting_no,
            meeting_date=meeting_date_str,
            meeting_time=meeting_time,
            venue=venue,
            theme=theme,
            word=word,
            idiom=idiom,
            cards=role_data,
            logo=logo,
            teams_block=teams_block,
        )

        st.session_state["flyer"] = flyer
        st.success("Flyer generated!")

if "flyer" in st.session_state:
    flyer = st.session_state["flyer"]

    left, right = st.columns([2, 1])
    with left:
        st.image(flyer, caption="Preview", width="stretch")

    png_bytes = io.BytesIO()
    flyer.save(png_bytes, format="PNG")
    png_bytes.seek(0)

    pdf_bytes = io.BytesIO()
    flyer.save(pdf_bytes, format="PDF", resolution=150.0)
    pdf_bytes.seek(0)

    with right:
        st.subheader("Download")
        filename = f"AL_NextGen_Meeting_{meeting_no}_Flyer"

        st.download_button(
            "⬇️ Download PNG",
            data=png_bytes,
            file_name=filename + ".png",
            mime="image/png",
            use_container_width=True,
        )

        st.download_button(
            "⬇️ Download PDF",
            data=pdf_bytes,
            file_name=filename + ".pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.info(
            "Tip: Keep the same logo and Teams QR in the assets folder. "
            "Then each week you only enter meeting details and upload role-player photos."
        )

st.divider()
st.caption("Personal VPPR utility • Template-based generation • 1080 × 1350 output")
