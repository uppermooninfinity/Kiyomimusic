import os
import re
import aiohttp
import aiofiles

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageFilter,
    ImageEnhance,
    ImageOps
)

from youtubesearchpython.__future__ import VideosSearch


CACHE_DIR = "cache"
BRAND = "Snowy Music"


def resize(img, size):
    return img.resize(size, Image.LANCZOS)


def clean_title(text, limit=32):
    text = re.sub(r"[^\w\s]", "", text)
    words = text.split()

    out = ""
    for w in words:
        if len(out + " " + w) <= limit:
            out += " " + w

    return out.strip()


async def get_thumb(videoid: str):
    final = f"{CACHE_DIR}/{videoid}.png"
    temp = f"{CACHE_DIR}/{videoid}_raw.jpg"

    if os.path.isfile(final):
        return final

    os.makedirs(CACHE_DIR, exist_ok=True)

    try:
        search = VideosSearch(
            f"https://www.youtube.com/watch?v={videoid}",
            limit=1
        )

        result = (await search.next())["result"][0]

        title = clean_title(result.get("title", "Unknown"))
        channel = result.get("channel", {}).get("name", "Unknown")
        duration = result.get("duration", "LIVE")

        thumb_url = result["thumbnails"][-1]["url"].split("?")[0]

        # DOWNLOAD THUMB
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                async with aiofiles.open(temp, "wb") as f:
                    await f.write(await r.read())

        cover = Image.open(temp).convert("RGB")

        # =========================
        # BACKGROUND
        # =========================

        bg = resize(cover, (1280, 720))
        bg = bg.filter(ImageFilter.GaussianBlur(40))
        bg = ImageEnhance.Brightness(bg).enhance(0.30)

        dark = Image.new("RGBA", bg.size, (0, 0, 0, 120))
        bg = Image.alpha_composite(bg.convert("RGBA"), dark)

        draw = ImageDraw.Draw(bg)

        # =========================
        # MAIN PLAYER CARD
        # =========================

        card_x = 95
        card_y = 185
        card_w = 1090
        card_h = 320

        # shadow
        shadow = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)

        sd.rounded_rectangle(
            (0, 0, card_w, card_h),
            radius=42,
            fill=(0, 0, 0, 210)
        )

        shadow = shadow.filter(ImageFilter.GaussianBlur(18))

        bg.paste(shadow, (card_x + 8, card_y + 10), shadow)

        # card
        card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 245))
        cd = ImageDraw.Draw(card)

        cd.rounded_rectangle(
            (0, 0, card_w, card_h),
            radius=42,
            fill=(0, 0, 0, 240)
        )

        bg.paste(card, (card_x, card_y), card)

        # =========================
        # COVER IMAGE
        # =========================

        album = resize(cover, (138, 138))

        mask = Image.new("L", album.size, 0)
        mdraw = ImageDraw.Draw(mask)

        mdraw.rounded_rectangle(
            (0, 0, 138, 138),
            radius=18,
            fill=255
        )

        album_x = card_x + 42
        album_y = card_y + 58

        bg.paste(album, (album_x, album_y), mask)

        # =========================
        # FONTS
        # =========================

        try:
            title_font = ImageFont.truetype(
                "Oneforall/assets/font.ttf",
                52
            )

            artist_font = ImageFont.truetype(
                "Oneforall/assets/font2.ttf",
                30
            )

            small_font = ImageFont.truetype(
                "Oneforall/assets/font2.ttf",
                22
            )

        except:
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # =========================
        # TOP TEXT
        # =========================

        draw.text(
            (album_x + 180, album_y - 5),
            "This phone",
            font=small_font,
            fill=(210, 210, 210)
        )

        # TITLE
        draw.text(
            (album_x + 180, album_y + 42),
            title,
            font=title_font,
            fill="white"
        )

        # CHANNEL
        draw.text(
            (album_x + 180, album_y + 118),
            channel,
            font=artist_font,
            fill=(180, 180, 180)
        )

        # =========================
        # BUTTONS
        # =========================

        controls_y = card_y + 210

        draw.text(
            (540, controls_y),
            "⏮",
            font=title_font,
            fill="white"
        )

        draw.text(
            (660, controls_y - 4),
            "⏸",
            font=title_font,
            fill="white"
        )

        draw.text(
            (790, controls_y),
            "⏭",
            font=title_font,
            fill="white"
        )

        # =========================
        # PROGRESS BAR
        # =========================

        bar_x1 = card_x + 55
        bar_x2 = card_x + card_w - 55
        bar_y = card_y + 286

        # inactive
        draw.line(
            (bar_x1, bar_y, bar_x2, bar_y),
            fill=(90, 90, 90),
            width=6
        )

        # active
        progress = int((bar_x2 - bar_x1) * 0.22)

        draw.line(
            (bar_x1, bar_y, bar_x1 + progress, bar_y),
            fill=(255, 255, 255),
            width=6
        )

        # circle
        draw.ellipse(
            (
                bar_x1 + progress - 10,
                bar_y - 10,
                bar_x1 + progress + 10,
                bar_y + 10
            ),
            fill="white"
        )

        # =========================
        # TIME
        # =========================

        draw.text(
            (bar_x1, bar_y + 18),
            "0:00",
            font=small_font,
            fill=(220, 220, 220)
        )

        draw.text(
            (bar_x2 - 40, bar_y + 18),
            duration,
            font=small_font,
            fill=(220, 220, 220)
        )

        # =========================
        # BRAND
        # =========================

        bw = draw.textlength(BRAND, font=small_font)

        draw.text(
            (1240 - bw, 28),
            BRAND,
            font=small_font,
            fill=(240, 240, 240)
        )

        # SAVE
        bg.convert("RGB").save(
            final,
            "PNG",
            quality=95
        )

        os.remove(temp)

        return final

    except Exception as e:
        print(f"THUMB ERROR: {e}")
        return None
