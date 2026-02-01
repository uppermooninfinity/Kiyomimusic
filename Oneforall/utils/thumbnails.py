import os
import re
import aiohttp
import aiofiles

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageFilter,
    ImageEnhance
)
from youtubesearchpython.__future__ import VideosSearch

CACHE_DIR = "cache"
BRAND_NAME = "Kiyomi Music"


def resize(img, size):
    return img.resize(size, Image.LANCZOS)


def clean_title(text, limit=58):
    text = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text))
    out = ""
    for w in text.split():
        if len(out) + len(w) <= limit:
            out += " " + w
    return out.strip()


async def get_thumb(videoid: str):
    final = f"{CACHE_DIR}/{videoid}.png"
    temp = f"{CACHE_DIR}/raw_{videoid}.jpg"

    if os.path.exists(final):
        return final

    os.makedirs(CACHE_DIR, exist_ok=True)

    try:
        search = VideosSearch(
            f"https://www.youtube.com/watch?v={videoid}", limit=1
        )
        data = (await search.next())["result"][0]

        title = clean_title(data.get("title", "Unknown Title"))
        channel = data.get("channel", {}).get("name", "Unknown Channel")
        duration = data.get("duration", "LIVE")
        thumb_url = data["thumbnails"][-1]["url"].split("?")[0]

        # download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(temp, "wb") as f:
                        await f.write(await resp.read())

        base = Image.open(temp).convert("RGB")

        # ================= BACKGROUND =================
        bg = resize(base, (1280, 720))
        bg = bg.filter(ImageFilter.GaussianBlur(30))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)
        bg = ImageEnhance.Contrast(bg).enhance(1.1)

        overlay = Image.new("RGBA", bg.size, (0, 0, 0, 160))
        bg = Image.alpha_composite(bg.convert("RGBA"), overlay)

        # ================= FOREGROUND CARD =================
        card_img = resize(base, (760, 430))
        card_img = ImageEnhance.Sharpness(card_img).enhance(1.6)

        radius = 34
        mask = Image.new("L", card_img.size, 0)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle(
            [(0, 0), card_img.size], radius=radius, fill=255
        )

        card = Image.new("RGBA", card_img.size)
        card.paste(card_img, (0, 0), mask)

        shadow = Image.new("RGBA", card_img.size, (0, 0, 0, 200))
        shadow = shadow.filter(ImageFilter.GaussianBlur(28))

        cx = (1280 - card_img.width) // 2
        cy = 95

        bg.paste(shadow, (cx + 16, cy + 20), shadow)
        bg.paste(card, (cx, cy), card)

        draw = ImageDraw.Draw(bg)

        # ================= PROGRESS BAR =================
        bar_y = cy + card_img.height - 16
        draw.line(
            [(cx + 60, bar_y), (cx + 300, bar_y)],
            fill=(255, 255, 255),
            width=5
        )

        # ================= FONTS =================
        try:
            title_font = ImageFont.truetype("Oneforall/assets/font.ttf", 44)
            meta_font = ImageFont.truetype("Oneforall/assets/font2.ttf", 26)
        except:
            title_font = meta_font = ImageFont.load_default()

        # ================= TEXT =================
        draw.text(
            (cx, cy + card_img.height + 38),
            title,
            font=title_font,
            fill="white"
        )

        draw.text(
            (cx, cy + card_img.height + 92),
            f"{channel}  •  {duration}",
            font=meta_font,
            fill=(200, 200, 200)
        )

        # ================= BRAND =================
        brand_font = meta_font
        bw = draw.textlength(BRAND_NAME, brand_font)
        draw.text(
            (1280 - bw - 40, 650),
            BRAND_NAME,
            font=brand_font,
            fill=(255, 210, 235)
        )

        bg.convert("RGB").save(final, "PNG", quality=95)

        try:
            os.remove(temp)
        except:
            pass

        return final

    except Exception as e:
        print("THUMB ERROR:", e)
        return None
