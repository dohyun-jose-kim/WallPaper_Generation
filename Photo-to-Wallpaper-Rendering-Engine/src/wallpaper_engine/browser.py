"""Production D3 browser renderer; no comparison or Node dependency at runtime."""
import base64
import io
from importlib.resources import files
from PIL import Image
from playwright.sync_api import sync_playwright
from .image_preparation import clean_png_bytes
from .static_renderers import rectangle


class BrowserStartupError(RuntimeError):
    pass


def render_frosted(photo, backdrop, canvas):
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(channel='chromium', headless=True, timeout=120_000)
        except Exception:
            raise BrowserStartupError('browser_startup') from None
        try:
            page = browser.new_page(viewport=dict(zip(('width', 'height'), canvas)), device_scale_factor=1)
            page.set_default_timeout(60_000)
            errors = []
            page.on('pageerror', lambda error: errors.append('page_error'))
            page.on('console', lambda msg: errors.append('console_error') if msg.type == 'error' else None)
            page.set_content('<!doctype html><html><head></head><body></body></html>')
            page.add_script_tag(path=str(files('wallpaper_engine') / 'resources/production.js'))
            info = page.evaluate('s => WallpaperAdapter.setup(s)', {
                'canvas': canvas, 'rectangle': rectangle(photo, canvas),
                'backdropData': 'data:image/png;base64,' + base64.b64encode(clean_png_bytes(backdrop)).decode()})
            if info['viewport'] != {'width': canvas[0], 'height': canvas[1], 'dpr': 1, 'zoom': 1}:
                raise RuntimeError('browser_geometry')
            page.evaluate('() => window.renderCase("on")')
            raw = page.screenshot(timeout=60_000)
            if errors:
                raise RuntimeError('browser_render')
            with Image.open(io.BytesIO(raw)) as frame:
                if frame.size != canvas:
                    raise RuntimeError('browser_capture')
                return frame.convert('RGB'), info
        finally:
            browser.close()
