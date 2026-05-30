"""
Spotify-styled image generation for autoplay thumbnails
Creates beautiful, professional Spotify-like player cards with blurry backgrounds
"""
import io
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import textwrap


def create_spotify_thumbnail_simple(title, duration, mood="chill"):
    """
    Create a simple Spotify-styled thumbnail with blurry gradient background
    Perfect for generating thumbnails without needing album art
    
    Args:
        title (str): Song title
        duration (str): Song duration in MM:SS format
        mood (str): Autoplay mood (chill, energetic, etc.)
    
    Returns:
        PIL.Image: Generated thumbnail image
    """
    try:
        width, height = 1080, 1080
        
        # Create dark background with gradient
        background = Image.new('RGB', (width, height), color=(20, 20, 20))
        draw = ImageDraw.Draw(background)
        
        # Create gradient overlay effect (Spotify colors - dark purple to dark blue)
        for y in range(height):
            ratio = y / height
            r = int(20 + (40 * ratio))
            g = int(20 + (30 * ratio))
            b = int(20 + (50 * ratio))
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add decorative circles with Spotify green
        accent_color = (29, 185, 84)  # Spotify green #1DB954
        
        # Top right circle
        draw.ellipse(
            [(width - 250, -80), (width + 100, 200)],
            fill=accent_color,
            outline=None
        )
        
        # Bottom left circle
        draw.ellipse(
            [(-100, height - 250), (200, height + 100)],
            fill=accent_color,
            outline=None
        )
        
        # Apply Gaussian blur for blurry background effect
        background = background.filter(ImageFilter.GaussianBlur(radius=25))
        
        # Redraw text on blurred background
        draw = ImageDraw.Draw(background)
        
        # Load fonts with fallback
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        except:
            try:
                # Fallback for macOS
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 65)
                info_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
                small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 35)
            except:
                # Fallback to default font
                title_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
        
        # Calculate center position
        center_y = height // 2
        
        # Wrap title text for multiple lines
        wrapped_title = textwrap.fill(title, width=28)
        title_lines = wrapped_title.split('\n')
        
        # Draw title with text stroke for better visibility
        title_start_y = center_y - 120
        for idx, line in enumerate(title_lines):
            y_pos = title_start_y + (idx * 80)
            draw.text(
                (width // 2, y_pos),
                line,
                font=title_font,
                fill=(255, 255, 255),
                anchor="mm",
                stroke_width=2,
                stroke_fill=(0, 0, 0)
            )
        
        # Draw duration and mood info
        info_text = f"🕐 {duration}  •  🎵 {mood.upper()}"
        draw.text(
            (width // 2, center_y + 120),
            info_text,
            font=info_font,
            fill=(177, 177, 177),
            anchor="mm"
        )
        
        # Add Spotify green accent bar at bottom
        draw.rectangle(
            [(0, height - 50), (width, height)],
            fill=accent_color
        )
        
        # Add play button and text on accent bar
        draw.text(
            (width // 2, height - 25),
            "▶  NOW PLAYING",
            font=small_font,
            fill=(255, 255, 255),
            anchor="mm"
        )
        
        # Add subtle border
        draw.rectangle(
            [(0, 0), (width - 1, height - 1)],
            outline=(50, 50, 50),
            width=3
        )
        
        return background
    
    except Exception as e:
        print(f"Spotify Thumbnail Creation Error: {e}")
        return None


def create_spotify_thumbnail_with_image(thumbnail_bytes, title, duration, mood="chill"):
    """
    Create a Spotify-styled thumbnail with actual album art and blurry background
    Uses the provided thumbnail image as the base with blur effect
    
    Args:
        thumbnail_bytes (bytes): Raw bytes of the thumbnail image
        title (str): Song title
        duration (str): Song duration in MM:SS format
        mood (str): Autoplay mood
    
    Returns:
        PIL.Image: Generated thumbnail image with album art
    """
    try:
        width, height = 1080, 1080
        
        # Load the thumbnail image
        thumb_img = Image.open(io.BytesIO(thumbnail_bytes))
        thumb_img = thumb_img.convert('RGB')
        
        # Resize for background (slightly larger for crop effect)
        thumb_resized = thumb_img.resize((width + 200, height + 200), Image.Resampling.LANCZOS)
        
        # Create blurry background
        background = thumb_resized.filter(ImageFilter.GaussianBlur(radius=40))
        
        # Add dark overlay to make text readable
        overlay = Image.new('RGBA', (width, height), color=(0, 0, 0, 200))
        background = background.crop((100, 100, 100 + width, 100 + height))
        background = background.convert('RGBA')
        background = Image.alpha_composite(background, overlay)
        background = background.convert('RGB')
        
        # Add centered album art with rounded corners
        thumb_size = 480
        thumb_display = thumb_img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        
        # Create rounded corners mask
        mask = Image.new('L', (thumb_size, thumb_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, thumb_size - 1, thumb_size - 1], radius=60, fill=255)
        
        thumb_display = thumb_display.convert('RGBA')
        thumb_display.putalpha(mask)
        
        # Center album art vertically
        x_offset = (width - thumb_size) // 2
        y_offset = (height - thumb_size) // 2 - 120
        
        background.paste(thumb_display, (x_offset, y_offset), thumb_display)
        
        # Add text
        draw = ImageDraw.Draw(background)
        
        # Load fonts with fallback
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 55)
                info_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 38)
                small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
            except:
                title_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
        
        # Draw title
        wrapped_title = textwrap.fill(title, width=32)
        title_y = y_offset + thumb_size + 80
        draw.text(
            (width // 2, title_y),
            wrapped_title,
            font=title_font,
            fill=(255, 255, 255),
            anchor="mm",
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )
        
        # Draw duration and mood
        info_text = f"🕐 {duration}  •  {mood.upper()}"
        draw.text(
            (width // 2, title_y + 100),
            info_text,
            font=info_font,
            fill=(177, 177, 177),
            anchor="mm"
        )
        
        # Spotify green bar at bottom
        accent_color = (29, 185, 84)
        draw.rectangle([(0, height - 50), (width, height)], fill=accent_color)
        draw.text(
            (width // 2, height - 25),
            "▶  NOW PLAYING",
            font=small_font,
            fill=(255, 255, 255),
            anchor="mm"
        )
        
        return background
    
    except Exception as e:
        print(f"Spotify Thumbnail with Image Error: {e}")
        return None


def save_image_to_bytes(image):
    """
    Convert PIL Image to bytes for sending to Telegram
    
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
        return img_bytes
    except Exception as e:
        print(f"Image Save Error: {e}")
        return None
