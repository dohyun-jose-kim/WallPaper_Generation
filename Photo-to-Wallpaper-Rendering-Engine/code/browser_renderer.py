import base64
import io
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from static_renderers import rectangle


class BrowserRenderer:
    def __init__(self, spec, photo):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(channel='chromium', headless=True, timeout=120_000)
        self.page = self.browser.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=1)
        self.page.set_default_timeout(60_000)
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('console', lambda msg: self.errors.append(msg.text) if msg.type == 'error' else None)
        self.page.set_content('<!doctype html><html><head></head><body></body></html>')
        shelf = Path(__file__).resolve().parents[1] / 'tool-package-shelf'
        self.page.add_script_tag(path=str(shelf / 'dist/comparison.js'))
        args = {**spec, 'rectangle': rectangle(photo), 'backdropData': 'data:image/png;base64,' +
                base64.b64encode(Path(spec['backdrop']).read_bytes()).decode()}
        info = self.page.evaluate('s => WallpaperAdapter.setup(s)', args)
        if info['viewport'] != {'width': 1920, 'height': 1080, 'dpr': 1, 'zoom': 1}:
            raise ValueError('Browser viewport or scale is incorrect')
        self.backend = info['backend']
        self.settings = info['settings']
        self.settings.update(browser_version=self.browser.version, viewport=info['viewport'], pane=info['pane'],
                             backdrop_sha256=spec['backdrop_sha256'],
                             software_fallback=any(w in self.backend.lower() for w in ('swiftshader', 'llvmpipe', 'software')))
        self.tool = spec['tool']

    def render(self, diagnostic=None):
        data = self.page.evaluate('kind => window.renderCase(kind)', diagnostic or 'on')
        if self.errors:
            raise RuntimeError('Browser error: ' + '; '.join(self.errors)[:1200])
        raw = self.page.screenshot(timeout=60_000) if self.tool == 'D3' else base64.b64decode(data.split(',', 1)[1])
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            if image.size != (1920, 1080):
                raise ValueError('Incomplete browser capture')
            return image.convert('RGB')

    def close(self):
        self.browser.close()
        self.playwright.stop()
