from io import BytesIO

from PIL import Image

MAX_DIMENSION = 1600
JPEG_QUALITY = 82
IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp", "gif"}


def compress_image(django_file):
    image = Image.open(django_file)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    if max(image.size) > MAX_DIMENSION:
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    buffer.seek(0)
    return buffer, buffer.getbuffer().nbytes


def image_dimensions(django_file):
    try:
        with Image.open(django_file) as image:
            return image.size
    except Exception:
        return 0, 0
