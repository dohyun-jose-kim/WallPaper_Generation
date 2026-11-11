"""Static extension renderers. S1/S2 share geometry, not native image operations."""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

W, H = 1920, 1080


def rectangle(photo, canvas=(W, H)):
    W, H = canvas
    return ((W - photo.width) // 2, (H - photo.height) // 2, photo.width, photo.height)


def blurred_backdrop(photo, canvas=(W, H)):
    W, H = canvas
    return ImageOps.fit(photo, (W, H), method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(32 * min(W, H) / 1080))


def glass_maps(photo, preset):
    x, y, w, h = rectangle(photo)
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    qx = np.abs(xx + .5 - (x + w / 2)) - (w / 2 + 32 - 32)
    qy = np.abs(yy + .5 - (y + h / 2)) - (h / 2 + 32 - 32)
    sdf = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - 32
    ny, nx = np.gradient(sdf)
    norm = np.maximum(np.hypot(nx, ny), 1e-6)
    nx, ny = nx / norm, ny / norm
    mask = np.clip(.5 - sdf, 0, 1).astype(np.float32)
    displacement = 12 if preset == 'strong-edge' else 4
    edge = np.exp(-np.maximum(-sdf, 0) / 18) * mask
    coordinates = np.stack([np.clip(xx + nx * edge * displacement, 0, W - 1),
                            np.clip(yy + ny * edge * displacement, 0, H - 1)], axis=2)
    gain = .28 if preset == 'strong-edge' else .12
    highlight = gain * np.exp(-np.abs(sdf) / 1.5) * (.2 + .8 * np.maximum(0, -.65 * nx - .76 * ny)) * mask
    return dict(coordinates=coordinates.astype(np.float32), mask=mask, highlight=highlight.astype(np.float32))


def bilinear(pixels, coordinates):
    x, y = coordinates[..., 0], coordinates[..., 1]
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, pixels.shape[1] - 1), np.minimum(y0 + 1, pixels.shape[0] - 1)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    return ((1 - fy) * ((1 - fx) * pixels[y0, x0] + fx * pixels[y0, x1]) +
            fy * ((1 - fx) * pixels[y1, x0] + fx * pixels[y1, x1]))


def reflect_axis(values, length):
    phase = np.mod(values, 2 * (length - 1))
    return np.minimum(phase, 2 * (length - 1) - phase).astype(np.float32)


class StaticRenderer:
    def __init__(self, spec, photo, canvas=(W, H)):
        self.canvas = canvas
        self.scale = min(canvas) / 1080
        self.spec, self.photo = spec, photo
        self.x, self.y, self.w, self.h = rectangle(photo, canvas)
        self.pixels = np.asarray(photo)
        strip = max(1, math.floor(self.h * .1 + .5))
        self.colors = [np.median(a.reshape(-1, 3), axis=0) for a in
                       (self.pixels, self.pixels[:strip], self.pixels[-strip:])]
        self.backend = 'CPU: Pillow + NumPy'
        self.settings = {'background_sigma_px': 32, 'resampling': 'LANCZOS / vips lanczos3',
                         'gradient_strip_rows': strip, 'statistics': 'per-channel medians from prepared RGB',
                         'rounding': 'floor(value+0.5)', 'mirror': 'reflect; no repeated boundary pixel',
                         'foreground_and_export': 'shared pixel restoration and clean Pillow PNG writer'}
        if spec['tool'] == 'S2':
            import pyvips
            self.vips = pyvips
            pyvips.cache_set_max(0)  # Evaluate each warm run; do not reuse an operation cache.
            self.native = pyvips.Image.new_from_array(self.pixels)
            self.backend = 'CPU: libvips ' + '.'.join(str(pyvips.version(i)) for i in range(3))
        if spec['method'] == 'glass':
            self.backdrop = Image.open(spec['backdrop']).convert('RGB')
            with np.load(spec['maps']) as maps:
                self.maps = {key: maps[key] for key in maps.files}
            self.settings.update(model='project approximation; rounded-rectangle SDF', pane_extension_px=32,
                                 corner_radius_px=32, edge_decay_px=18, light_direction=[-.65, -.76],
                                 blur_sigma_px=12 if spec['preset'] == 'frosted' else 4,
                                 displacement_px=12 if spec['preset'] == 'strong-edge' else 4,
                                 highlight_gain=.28 if spec['preset'] == 'strong-edge' else .12,
                                 backdrop_sha256=spec['backdrop_sha256'], maps_sha256=spec['maps_sha256'])
        if spec['method'] == 'gallery-frame':
            self.settings.update(background='#16181D', matte='#E9E5DC', matte_width_px=24,
                                 shadow_sigma_px=18, shadow_offset_px=[0, 12], shadow_opacity=.45)

    def render(self, diagnostic=None):
        if self.spec['method'] == 'glass' and diagnostic == 'off':
            return self.backdrop.copy()
        return self._vips(diagnostic) if self.spec['tool'] == 'S2' else self._pillow(diagnostic)

    def _pillow(self, diagnostic):
        W, H = self.canvas
        method = self.spec['method']
        if method == 'solid':
            return Image.new('RGB', (W, H), tuple(np.floor(self.colors[0] + .5).astype(int)))
        if method == 'gradient':
            row = np.linspace(self.colors[1], self.colors[2], H, dtype=np.float32)
            return Image.fromarray(np.floor(np.repeat(row[:, None, :], W, axis=1) + .5).astype(np.uint8))
        if method == 'blurred-background':
            return blurred_backdrop(self.photo, self.canvas)
        if method in ('edge-extension', 'mirror-extension'):
            padded = np.pad(self.pixels, ((self.y, H - self.y - self.h),
                            (self.x, W - self.x - self.w), (0, 0)),
                            mode='edge' if method == 'edge-extension' else 'reflect')
            return Image.fromarray(padded).filter(ImageFilter.GaussianBlur(32 * min(W, H) / 1080))
        if method == 'gallery-frame':
            mask = Image.new('L', (W, H))
            matte = max(1, math.floor(24 * self.scale + .5))
            offset = math.floor(12 * self.scale + .5)
            box = (self.x - matte, self.y - matte, self.x + self.w + matte - 1, self.y + self.h + matte - 1)
            ImageDraw.Draw(mask).rectangle((box[0], box[1] + offset, box[2], box[3] + offset), fill=115)
            mask = mask.filter(ImageFilter.GaussianBlur(18 * self.scale))
            result = Image.composite(Image.new('RGB', (W, H)), Image.new('RGB', (W, H), '#16181D'), mask)
            ImageDraw.Draw(result).rectangle(box, fill='#E9E5DC')
            return result
        base = np.asarray(self.backdrop).astype(np.float32)
        blurred = np.asarray(self.backdrop.filter(ImageFilter.GaussianBlur(self.settings['blur_sigma_px']))).astype(np.float32)
        sampled = blurred if diagnostic == 'refraction-off' else bilinear(blurred, self.maps['coordinates'])
        mask, light = self.maps['mask'][..., None], self.maps['highlight'][..., None]
        result = (base * (1 - mask) + sampled * mask) * (1 - light) + 255 * light
        return Image.fromarray(np.clip(np.floor(result + .5), 0, 255).astype(np.uint8))

    def _vips(self, diagnostic):
        W, H = self.canvas
        v = self.vips
        method = self.spec['method']
        grid = v.Image.xyz(W, H)
        if method == 'solid':
            result = v.Image.black(W, H, bands=3) + np.floor(self.colors[0] + .5).tolist()
        elif method == 'gradient':
            result = grid[1] / (H - 1) * (self.colors[2] - self.colors[1]).tolist() + self.colors[1].tolist()
        elif method == 'blurred-background':
            scale = max(W / self.w, H / self.h)
            large = self.native.resize(scale, kernel='lanczos3')
            result = large.crop((large.width - W) // 2, (large.height - H) // 2, W, H).gaussblur(32)
        elif method == 'edge-extension':
            result = self.native.embed(self.x, self.y, W, H, extend='copy').gaussblur(32)
        elif method == 'mirror-extension':
            yy, xx = np.mgrid[:H, :W]
            coordinates = np.stack([reflect_axis(xx - self.x, self.w), reflect_axis(yy - self.y, self.h)], axis=2)
            result = self.native.mapim(v.Image.new_from_array(coordinates),
                                      interpolate=v.Interpolate.new('bilinear'), extend='copy').gaussblur(32)
        elif method == 'gallery-frame':
            x, y = grid[0], grid[1]
            matte = (x >= self.x - 24) & (x < self.x + self.w + 24) & (y >= self.y - 24) & (y < self.y + self.h + 24)
            shadow = (x >= self.x - 24) & (x < self.x + self.w + 24) & (y >= self.y - 12) & (y < self.y + self.h + 36)
            base = v.Image.black(W, H, bands=3) + [22, 24, 29]
            result = matte.ifthenelse([233, 229, 220], base * (1 - shadow.cast('float').gaussblur(18) / 255 * .45))
        else:
            base = v.Image.new_from_array(np.asarray(self.backdrop))
            blurred = base.cast('float').gaussblur(self.settings['blur_sigma_px'])
            sampled = blurred if diagnostic == 'refraction-off' else blurred.mapim(
                v.Image.new_from_array(self.maps['coordinates']), interpolate=v.Interpolate.new('bilinear'), extend='copy')
            mask = v.Image.new_from_array(self.maps['mask'])
            light = v.Image.new_from_array(self.maps['highlight'])
            result = (base * (1 - mask) + sampled * mask) * (1 - light) + 255 * light
        result = (result + .5).floor().cast('uchar')
        return Image.frombytes('RGB', (W, H), bytes(result.write_to_memory()))
