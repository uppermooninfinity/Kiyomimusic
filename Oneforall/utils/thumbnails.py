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
BRAND = "Kiyomi Music"


def resize(img, size):
    return img.resize(size, Image.LANCZOS)


def clean_title(text, limit=60):
    text = re.sub(r"[^\w\s]", "", text)
    out = ""
    for w in text.split():
        if len(out) + len(w) <= limit:
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
            f"https://www.youtube.com/watch?v={videoid}", limit=1
        )
        result = (await search.next())["result"][0]

        title = clean_title(result.get("title", "Unknown Title"))
        channel = result.get("channel", {}).get("name", "Unknown Channel")
        duration = result.get("duration", "LIVE")
        thumb_url = result["thumbnails"][-1]["url"].split("?")[0]

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as r:
                async with aiofiles.open(temp, "wb") as f:
                    await f.write(await r.read())

        base = Image.open(temp).convert("RGB")

        # ===== BACKGROUND =====
        bg = resize(base, (1280, 720))
        bg = ImageOps.grayscale(bg)
        bg = bg.filter(ImageFilter.GaussianBlur(26))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)
        bg = ImageEnhance.Contrast(bg).enhance(1.2)

        overlay = Image.new("RGBA", bg.size, (0, 0, 0, 150))
        bg = Image.alpha_composite(bg.convert("RGBA"), overlay)

        # ===== FOREGROUND CARD =====
        card_img = resize(base, (760, 430))
        card_img = ImageOps.grayscale(card_img)
        card_img = ImageEnhance.Contrast(card_img).enhance(1.25)
        card_img = ImageEnhance.Sharpness(card_img).enhance(1.4)

        radius = 32
        mask = Image.new("L", card_img.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle(
            [(0, 0), card_img.size],
            radius=radius,
            fill=255
        )

        card = Image.new("RGBA", card_img.size)
        card.paste(card_img, (0, 0), mask)

        shadow = Image.new("RGBA", card_img.size, (0, 0, 0, 220))
        shadow = shadow.filter(ImageFilter.GaussianBlur(30))

        cx = (1280 - card_img.width) // 2
        cy = 90

        bg.paste(shadow, (cx + 14, cy + 18), shadow)
        bg.paste(card, (cx, cy), card)

        draw = ImageDraw.Draw(bg)

        # ===== PROGRESS LINE =====
        bar_y = cy + card_img.height - 14
        draw.line(
            [(cx + 60, bar_y), (cx + 280, bar_y)],
            fill=(230, 230, 230),
            width=4
        )

        # ===== FONTS =====
        try:
            title_font = ImageFont.truetype("Oneforall/assets/font.ttf", 44)
            meta_font = ImageFont.truetype("Oneforall/assets/font2.ttf", 26)
        except:
            title_font = meta_font = ImageFont.load_default()

        # ===== TEXT =====
        draw.text(
            (cx, cy + card_img.height + 36),
            title,
            font=title_font,
            fill=(245, 245, 245)
        )

        draw.text(
            (cx, cy + card_img.height + 90),
            f"{channel} • {duration}",
            font=meta_font,
            fill=(190, 190, 190)
        )

        # ===== BRAND =====
        bw = draw.textlength(BRAND, meta_font)
        draw.text(
            (1280 - bw - 36, 652),
            BRAND,
            font=meta_font,
            fill=(210, 210, 210)
        )

        bg.convert("RGB").save(final, "PNG", quality=95)

        os.remove(temp)
        return final

    except Exception as e:
        print("THUMB ERROR:", e)
        return None
