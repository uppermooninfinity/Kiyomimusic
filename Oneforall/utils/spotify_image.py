"""
Spotify-styled image generation for autoplay thumbnails
Creates beautiful, professional Spotify-like player cards with YouTube thumbnail
"""
import io
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import textwrap


def create_spotify_thumbnail_with_yt_image(thumbnail_url, title, duration_str, current_sec=0, total_sec=0, mood="chill"):
    """
    Create a Spotify-styled thumbnail with YouTube album art and animated progress bar
    
    Args:
        thumbnail_url (str): URL of YouTube thumbnail
        title (str): Song title
        duration_str (str): Song duration in MM:SS format
        current_sec (int): Current playback position in seconds
        total_sec (int): Total duration in seconds
        mood (str): Autoplay mood (chill, energetic, etc.)
    
    Returns:
        PIL.Image: Generated thumbnail image with album art
    """
    try:
        # Dimensions
        width, height = 1080, 1080
        
        # Download and load YouTube thumbnail
        try:
            response = requests.get(thumbnail_url, timeout=5)
            thumb_img = Image.open(io.BytesIO(response.content))
        except:
            # Create fallback gradient if thumbnail fails
            thumb_img = Image.new('RGB', (640, 480), color=(30, 30, 30))
        
        thumb_img = thumb_img.convert('RGB')
        
        # Create blurry background from thumbnail
        thumb_resized = thumb_img.resize((width + 200, height + 200), Image.Resampling.LANCZOS)
        background = thumb_resized.filter(ImageFilter.GaussianBlur(radius=50))
        background = background.crop((100, 100, 100 + width, 100 + height))
        
        # Add strong dark overlay for readability
        overlay = Image.new('RGBA', (width, height), color=(10, 10, 10, 220))
        background = background.convert('RGBA')
        background = Image.alpha_composite(background, overlay)
        background = background.convert('RGB')
        
        # Add Spotify green gradient overlay on left side
        gradient_overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        grad_draw = ImageDraw.Draw(gradient_overlay)
        
        # Gradient from green to transparent
        for y in range(height):
            ratio = y / height
            alpha = int(30 * (1 - abs(ratio - 0.5) * 2))  # More green in middle
            color = (29, 185, 84, alpha)  # Spotify green
            grad_draw.line([(0, y), (width // 3, y)], fill=color)
        
        background = Image.alpha_composite(background.convert('RGBA'), gradient_overlay).convert('RGB')
        
        draw = ImageDraw.Draw(background)
        
        # Position thumbnail on left side
        thumb_display_size = 420
        thumb_display = thumb_img.resize((thumb_display_size, thumb_display_size), Image.Resampling.LANCZOS)
        
        # Create rounded corners mask
        mask = Image.new('L', (thumb_display_size, thumb_display_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [0, 0, thumb_display_size - 1, thumb_display_size - 1],
            radius=40,
            fill=255
        )
        
        thumb_display = thumb_display.convert('RGBA')
        thumb_display.putalpha(mask)
        
        # Position on left with padding
        x_offset = 80
        y_offset = (height - thumb_display_size) // 2
        background.paste(thumb_display, (x_offset, y_offset), thumb_display)
        
        # Add white border around thumbnail
        border_draw = ImageDraw.Draw(background)
        border_draw.rounded_rectangle(
            [x_offset - 3, y_offset - 3, x_offset + thumb_display_size + 3, y_offset + thumb_display_size + 3],
            radius=40,
            outline=(255, 255, 255),
            width=2
        )
        
        # Right side text area starts here
        text_x_start = x_offset + thumb_display_size + 60
        text_y_start = 100
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            artist_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
                artist_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
                time_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
                small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            except:
                title_font = ImageFont.load_default()
                artist_font = ImageFont.load_default()
                time_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
        
        # Title
        wrapped_title = textwrap.fill(title, width=25)
        draw.text(
            (text_x_start, text_y_start),
            wrapped_title,
            font=title_font,
            fill=(255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )
        
        # Artist/Mood label
        mood_label = f"🎵 {mood.upper()}"
        draw.text(
            (text_x_start, text_y_start + 180),
            mood_label,
            font=artist_font,
            fill=(29, 185, 84),
            stroke_width=1,
            stroke_fill=(0, 0, 0)
        )
        
        # Progress bar (Spotify style - white line with dot)
        progress_bar_y = text_y_start + 280
        progress_bar_width = 350
        progress_bar_height = 6
        
        # Background bar (dark gray)
        draw.rounded_rectangle(
            [text_x_start, progress_bar_y, text_x_start + progress_bar_width, progress_bar_y + progress_bar_height],
            radius=3,
            fill=(60, 60, 60)
        )
        
        # Filled portion (white)
        if total_sec > 0:
            fill_width = (current_sec / total_sec) * progress_bar_width
        else:
            fill_width = 0
        
        if fill_width > 0:
            draw.rounded_rectangle(
                [text_x_start, progress_bar_y, text_x_start + fill_width, progress_bar_y + progress_bar_height],
                radius=3,
                fill=(255, 255, 255)
            )
        
        # Progress dot
        dot_x = text_x_start + fill_width
        dot_radius = 8
        draw.ellipse(
            [dot_x - dot_radius, progress_bar_y - dot_radius, dot_x + dot_radius, progress_bar_y + progress_bar_height + dot_radius],
            fill=(255, 255, 255)
        )
        
        # Time display (current / total)
        time_text = f"{format_time(current_sec)} / {duration_str}"
        draw.text(
            (text_x_start, progress_bar_y + 40),
            time_text,
            font=time_font,
            fill=(177, 177, 177),
            stroke_width=1,
            stroke_fill=(0, 0, 0)
        )
        
        # Bottom green bar with "Now Playing"
        accent_color = (29, 185, 84)
        draw.rectangle(
            [(0, height - 70), (width, height)],
            fill=accent_color
        )
        
        draw.text(
            (width // 2, height - 35),
            "▶  NOW PLAYING",
            font=small_font,
            fill=(255, 255, 255),
            anchor="mm",
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )
        
        return background
    
    except Exception as e:
        print(f"Spotify Thumbnail Creation Error: {e}")
        return None


def format_time(seconds):
    """Convert seconds to MM:SS format"""
    if isinstance(seconds, str):
        return seconds
    try:
        seconds = int(seconds)
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
    except:
        return "00:00"


def save_image_to_bytes(image):
    """
    Convert PIL Image to bytes for sending to Telegram
    Uses PNG format with proper filename for Pyrogram
    
    Args:
        image (PIL.Image): The image to convert
    
    Returns:
        io.BytesIO: Image bytes ready to send, or None if failed
    """
    try:
        if image is None:
            return None
        
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG', quality=95)
        img_bytes.seek(0)
        img_bytes.name = "autoplay_thumbnail.png"
        return img_bytes
    except Exception as e:
        print(f"Image Save Error: {e}")
        return None
