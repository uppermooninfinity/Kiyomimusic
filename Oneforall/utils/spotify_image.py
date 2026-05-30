"""
Modern Spotify-style autoplay thumbnail generator
"""

import io
import textwrap
import requests

from PIL import (
    Image,
    ImageDraw,
    ImageFilter,
    ImageFont
)


SPOTIFY_GREEN = (29, 185, 84)


def format_time(seconds):
    try:
        seconds = int(seconds)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    except:
        return "0:00"


def load_fonts():

    try:
        return {
            "title": ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                42
            ),
            "artist": ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                28
            ),
            "small": ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                22
            ),
            "time": ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                24
            ),
        }

    except:

        return {
            "title": ImageFont.load_default(),
            "artist": ImageFont.load_default(),
            "small": ImageFont.load_default(),
            "time": ImageFont.load_default(),
        }


def create_spotify_thumbnail_with_yt_image(
    thumbnail_url,
    title,
    duration_str,
    current_sec=0,
    total_sec=0,
    mood="autoplay",
    artist=""
):

    try:

        WIDTH = 1280
        HEIGHT = 720

        # DOWNLOAD THUMBNAIL

        try:

            response = requests.get(
                thumbnail_url,
                timeout=10
            )

            album = Image.open(
                io.BytesIO(response.content)
            ).convert("RGB")

        except:

            album = Image.new(
                "RGB",
                (640, 640),
                (40, 40, 40)
            )

        # BACKGROUND

        bg = album.resize(
            (WIDTH, HEIGHT),
            Image.Resampling.LANCZOS
        )

        bg = bg.filter(
            ImageFilter.GaussianBlur(40)
        )

        overlay = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
            (0, 0, 0, 170)
        )

        bg = bg.convert("RGBA")
        bg = Image.alpha_composite(bg, overlay)

        draw = ImageDraw.Draw(bg)

        fonts = load_fonts()

        # ALBUM ART

        album_size = 420

        album_art = album.resize(
            (album_size, album_size),
            Image.Resampling.LANCZOS
        )

        mask = Image.new(
            "L",
            (album_size, album_size),
            0
        )

        mask_draw = ImageDraw.Draw(mask)

        mask_draw.rounded_rectangle(
            (0, 0, album_size, album_size),
            radius=35,
            fill=255
        )

        album_art.putalpha(mask)

        art_x = 80
        art_y = (HEIGHT - album_size) // 2

        bg.paste(
            album_art,
            (art_x, art_y),
            album_art
        )

        # SHADOW BORDER

        draw.rounded_rectangle(
            (
                art_x - 5,
                art_y - 5,
                art_x + album_size + 5,
                art_y + album_size + 5
            ),
            radius=35,
            outline=(255, 255, 255),
            width=2
        )

        # TEXT AREA

        text_x = art_x + album_size + 70
        text_y = 120

        draw.text(
            (text_x, text_y),
            "NOW PLAYING",
            fill=SPOTIFY_GREEN,
            font=fonts["artist"]
        )

        # TITLE

        wrapped_title = textwrap.fill(
            title,
            width=22
        )

        title_y = text_y + 60

        draw.multiline_text(
            (text_x, title_y),
            wrapped_title,
            fill="white",
            font=fonts["title"],
            spacing=10
        )

        bbox = draw.multiline_textbbox(
            (text_x, title_y),
            wrapped_title,
            font=fonts["title"],
            spacing=10
        )

        title_height = bbox[3] - bbox[1]

        info_y = title_y + title_height + 35

        # ARTIST / MOOD

        info_text = artist if artist else mood.upper()

        draw.text(
            (text_x, info_y),
            info_text,
            fill=(190, 190, 190),
            font=fonts["artist"]
        )

        # PROGRESS BAR

        bar_y = info_y + 70

        bar_width = 500
        bar_height = 8

        draw.rounded_rectangle(
            (
                text_x,
                bar_y,
                text_x + bar_width,
                bar_y + bar_height
            ),
            radius=4,
            fill=(80, 80, 80)
        )

        progress = 0

        if total_sec > 0:
            progress = current_sec / total_sec

        filled = int(bar_width * progress)

        draw.rounded_rectangle(
            (
                text_x,
                bar_y,
                text_x + filled,
                bar_y + bar_height
            ),
            radius=4,
            fill="white"
        )

        dot_x = text_x + filled

        draw.ellipse(
            (
                dot_x - 7,
                bar_y - 6,
                dot_x + 7,
                bar_y + 14
            ),
            fill="white"
        )

        # TIME

        draw.text(
            (text_x, bar_y + 30),
            format_time(current_sec),
            fill=(200, 200, 200),
            font=fonts["time"]
        )

        draw.text(
            (text_x + bar_width - 80, bar_y + 30),
            duration_str,
            fill=(200, 200, 200),
            font=fonts["time"]
        )

        # SPOTIFY LOGO AREA

        draw.text(
            (WIDTH - 210, HEIGHT - 70),
            "SNOWY DEVELOPERS",
            fill=SPOTIFY_GREEN,
            font=fonts["small"]
        )

        return bg.convert("RGB")

    except Exception as e:

        print(
            f"Thumbnail Error: {e}"
        )

        return None


def save_image_to_bytes(image):

    try:

        if image is None:
            return None

        output = io.BytesIO()

        image.save(
            output,
            format="PNG",
            quality=95
        )

        output.seek(0)

        output.name = "spotify_thumbnail.png"

        return output

    except Exception as e:

        print(
            f"Save Error: {e}"
        )

        return None
