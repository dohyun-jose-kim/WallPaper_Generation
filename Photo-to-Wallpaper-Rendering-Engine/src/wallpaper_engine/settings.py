"""Target policy shared by standalone and orchestrated jobs."""
from pathlib import Path
import io
import math
from PIL import Image, ImageOps

PRESETS = {'FHD': (1920, 1080), 'QHD': (2560, 1440), 'UHD': (3840, 2160),
           'WUXGA': (1920, 1200), 'WQXGA': (2560, 1600), 'Ultrawide': (3440, 1440)}
WARNING = ('This aspect ratio may produce an awkward composition or an incomplete-looking background. '
           'The complete source photo will still be preserved.')
MAX_BYTES = 200 * 1024 * 1024


def read_source(path):
    with Path(path).open('rb') as file:
        data = file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Input exceeds 200 MiB')
    return data


def inspect_source(data):
    with Image.open(io.BytesIO(data)) as image:
        if getattr(image, 'n_frames', 1) != 1:
            raise ValueError('Animated or multi-frame inputs are unsupported')
        if image.format not in ('JPEG', 'PNG'):
            raise ValueError('Only JPEG and PNG are supported')
        if image.width * image.height > 100_000_000:
            raise ValueError('Input exceeds 100 million pixels')
        size = image.size
        if image.getexif().get(274, 1) in (5, 6, 7, 8):
            size = size[::-1]
        return size


def validate_target(width, height, border=.05):
    if type(width) is not int or type(height) is not int:
        raise ValueError('Target dimensions must be integers')
    if not 512 <= min(width, height) or max(width, height) > 8192 or width * height > 16_777_216:
        raise ValueError('Target exceeds dimension or pixel limits')
    if width * 3 < height or width > height * 3:
        raise ValueError('Manual layout customization is required for this aspect ratio')
    if isinstance(border, bool) or not isinstance(border, (float, int)) or not math.isfinite(border) or not .03 <= border <= .20:
        raise ValueError('Border must be 3%–20% per edge')
    return WARNING if width * 2 < height or width > height * 2 else None


def fit_box(width, height, border):
    validate_target(width, height, border)
    return tuple(math.floor(n * (1 - 2 * border) + .5) for n in (width, height))
