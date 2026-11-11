"""One-photo worker, using version 1 JSON Lines and sanitized events."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

STYLES = ['blur', 'gallery', 'frosted', 'gradient']


class VerificationError(RuntimeError):
    pass


def emit(kind, **fields):
    print(json.dumps({'version': 1, 'type': kind, **fields}, allow_nan=False), flush=True)


def request(line):
    value = json.loads(line)
    if not isinstance(value, dict) or type(value.get('version')) is not int or value.get('version') != 1 or value.get('type') != 'job':
        raise ValueError('protocol')
    if set(value) - {'version','type','source','source_sha256','width','height','border','styles','threads','work_dir'}:
        raise ValueError('protocol')
    if value.get('styles') != STYLES or type(value.get('threads')) is not int or not 1 <= value['threads'] <= 256:
        raise ValueError('settings')
    from .settings import validate_target
    validate_target(value['width'], value['height'], value['border'])
    if not Path(value['source']).is_absolute() or not Path(value['work_dir']).is_absolute():
        raise ValueError('paths')
    return value


def run(job, managed=False):
    for name in ('VIPS_CONCURRENCY', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[name] = str(job['threads'])
    from PIL import Image
    from .settings import read_source, inspect_source, fit_box
    from .image_preparation import prepare_pixels, clean_png_bytes, validate_clean_png, write_new_or_identical
    from .static_renderers import StaticRenderer, blurred_backdrop, rectangle
    from .browser import render_frosted
    canvas = job['width'], job['height']
    work = Path(job['work_dir'])
    work.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    emit('stage', stage='prepare')
    try:
        source = read_source(job['source'])
        inspect_source(source)
        digest = hashlib.sha256(source).hexdigest()
        if job.get('source_sha256', digest) != digest:
            raise ValueError('input_changed')
        photo, details = prepare_pixels(source, fit_box(*canvas, job['border']), canvas)
    except (OSError, Image.DecompressionBombError):
        raise ValueError('invalid_input') from None
    x, y, w, h = rectangle(photo, canvas)
    artifacts = []
    for index, style in enumerate(STYLES, 1):
        if style == 'frosted' and managed:
            emit('browser_slot_request')
            grant = json.loads(sys.stdin.readline(65537))
            if grant != {'version': 1, 'type': 'browser_slot_grant'}:
                raise ValueError('protocol')
        emit('stage', stage='browser_initialization' if style == 'frosted' else 'render', style=style)
        begin = time.monotonic()
        if style == 'frosted':
            frame, info = render_frosted(photo, blurred_backdrop(photo, canvas), canvas, lambda: emit('stage', stage='render', style=style))
            backend = info['backend']
            if managed:
                emit('browser_slot_release')
        else:
            renderer = StaticRenderer({'tool': 'S2' if style == 'gradient' else 'S1',
                'method': {'blur': 'blurred-background', 'gallery': 'gallery-frame', 'gradient': 'gradient'}[style]}, photo, canvas)
            frame, backend = renderer.render(), renderer.backend
        emit('stage', stage='export', style=style)
        if frame.size != canvas:
            raise VerificationError('verification')
        frame.paste(photo, (x, y))
        try:
            data = clean_png_bytes(frame)
            checks = validate_clean_png(data, canvas)
        except ValueError:
            raise VerificationError('verification') from None
        import io
        with Image.open(io.BytesIO(data)) as decoded:
            if decoded.crop((x, y, x+w, y+h)).tobytes() != photo.tobytes():
                raise VerificationError('verification')
        path = work / f'{index}.png'
        write_new_or_identical(path, data)
        artifacts.append({'path': str(path), 'style': style, 'sha256': hashlib.sha256(data).hexdigest(),
                          'checks': {**checks, 'foreground_exact': True}, 'backend': backend,
                          'seconds': time.monotonic()-begin})
        emit('progress', completed=index, total=4)
    if hashlib.sha256(read_source(job['source'])).hexdigest() != digest:
        raise ValueError('input_changed')
    emit('complete', artifacts=artifacts, seconds=time.monotonic()-started,
         source_sha256=digest, dimensions=canvas, foreground_sha256=details['prepared_pixel_sha256'],
         rectangle=[x, y, w, h])


def main():
    parser = argparse.ArgumentParser(description='Independent WALL-E four-style engine')
    parser.add_argument('--request', type=Path, help='Standalone JSON job file; otherwise JSONL on stdin')
    parser.add_argument('--inspect', type=Path, help='Inspect displayed dimensions and content hash')
    parser.add_argument('--doctor', action='store_true')
    args = parser.parse_args()
    try:
        if args.doctor:
            import pyvips
            from importlib.resources import files
            from playwright.sync_api import sync_playwright
            if not (files('wallpaper_engine') / 'resources/production.js').is_file():
                raise RuntimeError('assets_missing')
            with sync_playwright() as p:
                with p.chromium.launch(channel='chromium', headless=True, timeout=120_000) as browser:
                    page = browser.new_page()
                    if not page.evaluate("!!document.createElement('canvas').getContext('webgl2')"):
                        raise RuntimeError('webgl_unavailable')
            emit('ready', engine='0.1.0', vips='.'.join(str(pyvips.version(i)) for i in range(3)))
        elif args.inspect:
            from .settings import read_source, inspect_source
            try:
                data = read_source(args.inspect)
            except OSError:
                raise ValueError('invalid_input') from None
            emit('inspected', dimensions=inspect_source(data), sha256=hashlib.sha256(data).hexdigest())
        else:
            line = args.request.read_text() if args.request else sys.stdin.readline(65537)
            if len(line) > 65536:
                raise ValueError('protocol')
            run(request(line), managed=args.request is None)
        return 0
    except (ValueError, KeyError, TypeError) as error:
        emit('error', code='invalid_input', retryable=False)
        return 2
    except Exception as error:
        from .browser import BrowserStartupError
        retryable = isinstance(error, BrowserStartupError)
        code = 'browser_startup' if retryable else 'verification_failed' if isinstance(error, VerificationError) else 'processing_failed'
        emit('error', code=code, retryable=retryable)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
