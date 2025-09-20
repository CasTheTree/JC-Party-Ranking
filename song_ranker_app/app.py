import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io, zipfile, os, math, textwrap
from pathlib import Path

st.set_page_config(page_title="Song Score Cards", layout="wide")

st.title("🎵 Song Score Cards — Transparent PNG Exporter")

st.markdown(
    "Upload your song scores CSV and (optionally) a ZIP of avatar images. "
    "We'll generate per-song cards like your example with a transparent background. "
    "Highest score = **green**, lowest = **red**, submitter shows a **yellow N**. "
    "You can also pick each person's favorite song to place a subtle star behind their score."
)

with st.sidebar:
    st.header("1) Upload your data")
    scores_file = st.file_uploader("Scores CSV", type=["csv"])
    avatars_zip = st.file_uploader("Avatars ZIP (optional)", type=["zip"])
    st.caption("Avatar filenames should match people names, e.g. `Nick.png`, `Jiho.jpg`. Matching is case-insensitive.")
    st.header("2) Layout & Style")
    card_w = st.slider("Card width (px)", 600, 1400, 1000, 50)
    card_h = st.slider("Card height (px)", 350, 900, 500, 25)
    edge_padding = st.slider("Outer padding (px)", 8, 60, 20, 2)
    chip_size = st.slider("Score chip size (px)", 36, 120, 64, 2)
    chip_gap = st.slider("Gap between chips (px)", 4, 40, 10, 1)
    columns_mode = st.selectbox("Chip layout", ["Two rails (left/right)", "Single left rail", "Single right rail"])
    st.header("3) Export options")
    show_rank = st.checkbox("Show rank number", True)
    show_avg = st.checkbox("Show average", True)
    star_opacity = st.slider("Favorite star opacity (%)", 0, 100, 35, 1)
    st.divider()

def _safe_read_csv(file):
    try:
        return pd.read_csv(file)
    except Exception:
        file.seek(0)
        return pd.read_csv(file, encoding="utf-8", engine="python")

def _load_avatars(zip_bytes):
    avatar_map = {}
    if not zip_bytes: 
        return avatar_map
    try:
        with zipfile.ZipFile(zip_bytes) as zf:
            for name in zf.namelist():
                low = Path(name).name.lower()
                if low.endswith((".png",".jpg",".jpeg",".webp",".bmp",".gif")):
                    with zf.open(name) as f:
                        avatar_map[Path(name).stem.lower()] = Image.open(io.BytesIO(f.read())).convert("RGBA")
    except Exception:
        pass
    return avatar_map

def _circle_crop(img, size):
    img = ImageOps.fit(img, (size, size), method=Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0,0,size,size), fill=255)
    out = Image.new("RGBA", (size, size), (0,0,0,0))
    out.paste(img, (0,0), mask)
    return out

def _draw_round_rect(draw, xy, radius, fill):
    x0,y0,x1,y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)

def _get_font(size, bold=False):
    # Try common system fonts; fall back to default
    try:
        # DejaVu Sans is commonly available with PIL
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

def _wrap(draw, text, font, max_w):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def render_card(row, people, avatar_map, favorites, cfg):
    W, H = cfg["card_w"], cfg["card_h"]
    img = Image.new("RGBA", (W, H), (0,0,0,0))  # transparent background
    draw = ImageDraw.Draw(img)

    pad = cfg["edge_padding"]
    chip = cfg["chip_size"]
    gap = cfg["chip_gap"]
    rail = cfg["columns_mode"]
    star_opacity = cfg["star_alpha"]
    show_rank = cfg["show_rank"]
    show_avg = cfg["show_avg"]

    # Semi-transparent panels
    panel_fill = (0,0,0,170)  # background behind content
    title_h = int(H*0.18)
    _draw_round_rect(draw, (pad, pad, W-pad, pad+title_h), 14, panel_fill)

    # Title & subtitle
    title_font = _get_font(int(title_h*0.42), bold=True)
    subtitle_font = _get_font(int(title_h*0.26), bold=False)
    title = str(row["Song"])
    artist = str(row["Artist"])
    title_y = pad + int(title_h*0.15)
    draw.text((W/2, title_y), title, font=title_font, anchor="ma", fill=(240,240,240,255))
    draw.text((W/2, title_y + int(title_h*0.48)), artist, font=subtitle_font, anchor="ma", fill=(200,200,200,255))

    # Rank / Average panel (top-right)
    box_w = int(W*0.14)
    box_h = int(title_h*0.9)
    box_x0 = W - pad - box_w
    box_y0 = pad + (title_h - box_h)//2
    _draw_round_rect(draw, (box_x0, box_y0, box_x0+box_w, box_y0+box_h), 12, (255,255,255,30))

    rnk = str(row.get("_rank",""))
    avg = row["Average"] if "Average" in row else row.get("_avg","")
    small = _get_font(int(box_h*0.22), bold=True)
    big = _get_font(int(box_h*0.44), bold=True)
    if show_rank:
        draw.text((box_x0+box_w*0.25, box_y0+box_h*0.25), f"#{rnk}", font=big, anchor="mm", fill=(230,230,230,255))
    if show_avg:
        draw.text((box_x0+box_w*0.72, box_y0+box_h*0.20), "AVG", font=small, anchor="mm", fill=(210,210,210,200))
        draw.text((box_x0+box_w*0.72, box_y0+box_h*0.60), f"{avg:.2f}" if isinstance(avg,(int,float)) else str(avg), font=big, anchor="mm", fill=(230,230,230,255))

    # Rails area panel
    rails_top = pad + title_h + gap
    _draw_round_rect(draw, (pad, rails_top, W-pad, H-pad), 14, (0,0,0,150))

    # Determine left/right rails
    if rail == "Two rails (left/right)":
        left_x = pad + gap
        right_x = W - pad - gap
        left_align = "left"
        right_align = "right"
        half = math.ceil(len(people)/2)
        left_people = people[:half]
        right_people = people[half:]
    elif rail == "Single left rail":
        left_x = pad + gap
        right_x = None
        left_people = people
        right_people = []
    else:  # Single right rail
        left_x = None
        right_x = W - pad - gap
        left_people = []
        right_people = people

    # Compute highs and lows (exclude NaN)
    scores = []
    for p in people:
        val = row.get(p, None)
        try:
            val = float(val)
            scores.append(val)
        except:
            pass
    hi = max(scores) if scores else None
    lo = min(scores) if scores else None

    def chip_color(v, is_submitter):
        if is_submitter:
            return (255,215,0,255)  # yellow
        if hi is not None and v == hi:
            return (0,200,0,255)   # green
        if lo is not None and v == lo:
            return (220,0,0,255)   # red
        return (230,230,230,255)   # neutral

    # Draw rail function
    def draw_rail(x_anchor, anchor_side, ppl):
        if not ppl: 
            return
        y = rails_top + gap
        for p in ppl:
            is_submitter = (str(row["Submitter"]).strip().lower() == str(p).strip().lower())
            score_val = row.get(p, "")
            # pick avatar if available
            av = avatar_map.get(str(p).strip().lower())
            # chip background/box
            # Avatar circle
            if av is not None:
                avatar_img = _circle_crop(av, chip)
            else:
                # placeholder
                ph = Image.new("RGBA", (chip, chip), (50,50,50,255))
                dph = ImageDraw.Draw(ph)
                dph.text((chip//2, chip//2), p[:1].upper(), anchor="mm", fill=(200,200,200,255), font=_get_font(int(chip*0.5), True))
                avatar_img = ph

            # Score box dims
            box_w = chip*1.1
            box_h = chip
            # label under avatar
            name_font = _get_font(int(chip*0.28), False)

            # Favorite star backplate
            fav_song = favorites.get(p, None)
            if fav_song and str(fav_song) == str(row["Song"]):
                # draw a translucent star behind the score/ava area
                star_size = int(chip*1.4)
                star_img = Image.new("RGBA", (star_size, star_size), (0,0,0,0))
                d = ImageDraw.Draw(star_img)
                # 5-point star
                cx, cy = star_size//2, star_size//2
                r_outer = star_size//2
                r_inner = int(r_outer*0.5)
                pts = []
                for i in range(10):
                    ang = -math.pi/2 + i*math.pi/5
                    r = r_outer if i%2==0 else r_inner
                    pts.append((cx + r*math.cos(ang), cy + r*math.sin(ang)))
                d.polygon(pts, fill=(255,255,0,int(255*star_opacity)))
                # position star
                if anchor_side == "left":
                    sx = int(x_anchor + chip*0.1)
                else:
                    sx = int(x_anchor - chip*1.5)
                sy = int(y + chip*0.1)
                img.alpha_composite(star_img, (sx, sy))

            # paste avatar
            if anchor_side == "left":
                ax = int(x_anchor)
                img.alpha_composite(avatar_img, (ax, int(y)))
                # score box to the right of avatar
                bx = ax + int(chip*1.2)
            else:
                ax = int(x_anchor - chip)
                img.alpha_composite(avatar_img, (ax, int(y)))
                # score box to the left
                bx = ax - int(chip*1.2)

            # draw score box
            v = None
            try:
                v = float(score_val)
            except:
                v = None
            color = chip_color(v, is_submitter)
            # rounded rectangle behind number/N
            bx0 = bx
            by0 = int(y)
            bx1 = bx + (chip if anchor_side=="left" else chip)
            by1 = by0 + chip
            draw.rounded_rectangle((min(bx0,bx1), by0, max(bx0,bx1), by1), radius=10, fill=(20,20,20,200), outline=(255,255,255,40), width=2)

            center_x = bx + (chip//2 if anchor_side=="left" else -chip//2)
            # draw score or N
            label_font = _get_font(int(chip*0.5), True)
            if is_submitter:
                draw.text((center_x, y + chip/2), "N", font=label_font, anchor="mm", fill=color)
            else:
                if v is None:
                    txt = "-"
                else:
                    # render int if whole number else one decimal
                    txt = str(int(v)) if abs(v - int(v)) < 1e-6 else f"{v:.1f}"
                draw.text((center_x, y + chip/2), txt, font=label_font, anchor="mm", fill=color)

            # name under avatar
            draw.text((ax + chip/2, y + chip + int(chip*0.15)), str(p), font=name_font, anchor="ma", fill=(230,230,230,230))
            y += chip + int(chip*0.6) + gap

    # Gather favorites mapping per person -> song
    favorites = favorites or {}

    # Draw rails
    if left_x is not None:
        draw_rail(left_x, "left", left_people)
    if right_x is not None:
        draw_rail(right_x, "right", right_people)

    return img

# Main content
if not scores_file:
    st.info("Download the sample files below, then upload your own CSV (and optional avatar ZIP) to get started.")
    with open("sample_scores.csv","rb") as f:
        st.download_button("Download sample_scores.csv", f, file_name="sample_scores.csv")
    with open("sample_people.csv","rb") as f:
        st.download_button("Download sample_people.csv", f, file_name="sample_people.csv")
    st.stop()

df = _safe_read_csv(scores_file).fillna("")
if "Song" not in df.columns or "Artist" not in df.columns or "Submitter" not in df.columns:
    st.error("Your CSV must include columns: Submitter, Song, Artist. Optional: Average. Then one column per person with scores.")
    st.stop()

# People are all columns after the required ones (and not Average)
people = [c for c in df.columns if c not in ["Submitter","Song","Artist","Average"]]

# Compute averages if missing
if "Average" not in df.columns:
    def _avg_row(r):
        vals = []
        for p in people:
            try:
                vals.append(float(r[p]))
            except:
                pass
        return sum(vals)/len(vals) if vals else 0.0
    df["Average"] = df.apply(_avg_row, axis=1)

# Sort by Average descending
df = df.copy()
df["_avg"] = df["Average"]
df = df.sort_values("Average", ascending=False).reset_index(drop=True)
df["_rank"] = df.index + 1

# Load avatars
avatar_map = _load_avatars(avatars_zip)

# Favorites selection
st.subheader("Choose favorites (one per person, optional)")
fav_cols = st.columns(min(5, max(1, len(people))))
favorites = {}
for i, p in enumerate(people):
    with fav_cols[i % len(fav_cols)]:
        choices = ["(none)"] + df["Song"].astype(str).tolist()
        pick = st.selectbox(f"{p}'s favorite", choices, index=0)
        favorites[p] = None if pick == "(none)" else pick

# Render and export
cfg = dict(
    card_w=card_w, card_h=card_h, edge_padding=edge_padding, chip_size=chip_size, chip_gap=chip_gap,
    columns_mode=columns_mode, star_alpha=star_opacity/100.0, show_rank=show_rank, show_avg=show_avg
)

st.subheader("Preview & Export")
cols = st.columns(2)

export_images = []
for idx, row in df.iterrows():
    img = render_card(row, people, avatar_map, favorites, cfg)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    export_images.append(("card_%03d_%s.png" % (row["_rank"], str(row["Song"]).strip().replace('/','-')) , bio.getvalue()))
    if idx < 6:
        with cols[idx % 2]:
            st.image(img, caption=f'#{row["_rank"]} — {row["Song"]}', use_column_width=True)

st.success(f"Generated {len(export_images)} cards.")

# Export-all ZIP
zip_bytes = io.BytesIO()
with zipfile.ZipFile(zip_bytes, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for name, data in export_images:
        zf.writestr(name, data)
zip_bytes.seek(0)
st.download_button("⬇️ Download all cards (ZIP)", zip_bytes, file_name="song_cards.zip")

# Also allow single export for first previewed image as example
if export_images:
    st.download_button("⬇️ Download first preview only (PNG)", io.BytesIO(export_images[0][1]), file_name=export_images[0][0])
