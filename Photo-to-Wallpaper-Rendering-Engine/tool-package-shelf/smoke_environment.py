"""Synthetic installation checks, not renderer implementations or benchmarks."""
import argparse
import importlib.metadata as metadata
import io
import json
from pathlib import Path
import platform
import plistlib
import sys

import numpy as np
from PIL import Image, ImageCms, ImageOps, features
from playwright.sync_api import sync_playwright
import psutil
import pyvips
import _libvips


def python_checks():
    assert sys.version_info[:2] == (3, 12)
    assert platform.machine() == "arm64"
    expected = {"Pillow": "13.0.0", "numpy": "2.5.4", "pyvips": "3.2.0",
                "pyvips-binary": "8.18.7", "playwright": "1.65.0",
                "psutil": "7.2.2", "pytest": "9.2.0"}
    versions = {name: metadata.version(name) for name in expected}
    assert versions == expected
    pixels = np.arange(12 * 16 * 3, dtype=np.uint8).reshape(12, 16, 3)
    original = Image.fromarray(pixels)
    original.getexif()[274] = 6
    assert ImageOps.exif_transpose(original).size == (12, 16)
    profile = ImageCms.createProfile("sRGB")
    converted = ImageCms.profileToProfile(Image.fromarray(pixels), profile, profile,
                                        outputMode="RGB")
    assert np.array_equal(np.asarray(converted), pixels)
    output = io.BytesIO()
    converted.save(output, format="PNG")
    with Image.open(io.BytesIO(output.getvalue())) as decoded:
        assert np.array_equal(np.asarray(decoded), pixels)
    vips_image = pyvips.Image.new_from_memory(pixels.tobytes(), 16, 12, 3, "uchar")
    remapped = vips_image.mapim(pyvips.Image.xyz(16, 12),
                              interpolate=pyvips.Interpolate.new("bilinear"))
    actual = np.frombuffer(remapped.write_to_memory(), dtype=np.uint8).reshape(pixels.shape)
    assert np.array_equal(actual, pixels)
    assert len(vips_image.gaussblur(1).write_to_memory()) == pixels.size
    assert pyvips.API_mode
    native_file = Path(_libvips.__file__).resolve()
    binary_dist = metadata.distribution("pyvips-binary")
    assert native_file in {Path(binary_dist.locate_file(f)).resolve() for f in binary_dist.files}
    assert tuple(pyvips.version(i) for i in range(3)) == (8, 18, 7)
    vm = psutil.virtual_memory()
    assert psutil.Process().memory_info().rss > 0
    return {"status": "passed", "python": platform.python_version(),
            "architecture": platform.machine(), "packages": versions,
            "libvips": "8.18.7", "bundled_native_module_verified": True,
            "littlecms": features.version("littlecms2"),
            "logical_cpus": psutil.cpu_count(), "memory_gib": vm.total / 2**30,
            "available_memory_percent_at_check": 100 * vm.available / vm.total,
            "checks": ["EXIF transpose", "sRGB conversion", "PNG pixel round trip",
                       "libvips array and identity mapim", "libvips blur", "psutil memory"]}


def browser_checks(playwright, shelf, executable=None):
    options = {"headless": True, "timeout": 120_000}
    if executable:
        options["executable_path"] = str(executable)
    else:
        # Real Chromium in new headless mode; no forced software fallback.
        options["channel"] = "chromium"
    with playwright.chromium.launch(**options) as browser:
        context = browser.new_context(viewport={"width": 1920, "height": 1080},
                                      device_scale_factor=1)
        page = context.new_page()
        page.set_default_timeout(60_000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content('<!doctype html><html><body style="margin:0;background:#123456"></body></html>')
        dimensions = page.evaluate("({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,zoom:visualViewport.scale})")
        assert dimensions == {"width": 1920, "height": 1080, "dpr": 1, "zoom": 1}
        gl = page.evaluate("""() => {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl2');
            if (!gl) return {supported:false};
            const ext = gl.getExtension('WEBGL_debug_renderer_info');
            const result = {supported:true, version:gl.getParameter(gl.VERSION),
                vendor:ext ? gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR),
                renderer:ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)};
            gl.getExtension('WEBGL_lose_context')?.loseContext();
            return result;
        }""")
        assert gl["supported"], "WebGL2 unavailable"
        gl["software_fallback_detected"] = any(s in gl["renderer"].lower()
                                               for s in ("swiftshader", "llvmpipe", "software"))
        smoke_dir = shelf / "dist" / "smoke"
        for name in ["D1", "D2", "D3", "react-dom"]:
            page.add_script_tag(path=str(smoke_dir / f"{name}.js"))
        constructors = page.evaluate("""() => {
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = 16;
            const d1 = new PreparationD1.LiquidGlassRenderer(canvas, {pixelRatio:1});
            d1.dispose();
            const d2 = new PreparationD2.GlassRenderer();
            d2.destroy();
            return {D1:'constructor and shaders passed', D2:'constructor and shaders passed',
                D3:typeof PreparationD3.default, ReactDOM:typeof PreparationReactDOM.createRoot};
        }""")
        assert constructors["D3"] == "function" and constructors["ReactDOM"] == "function"
        screenshot = page.screenshot(timeout=60_000)
        with Image.open(io.BytesIO(screenshot)) as decoded:
            assert decoded.size == (1920, 1080)
            assert decoded.convert("RGB").getpixel((960, 540)) == (18, 52, 86)
        assert not errors, errors
        return {"status": "passed", "version": browser.version, "viewport": dimensions,
                "webgl2": gl, "source_checks": constructors, "page_errors": errors,
                "synthetic_screenshot": "1920x1080; center RGB matches CSS",
                "limitations": "No source photos, D3 component mount, glass rendering or visual comparison performed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brave", action="store_true", help="Also check an installed Brave with an isolated temporary profile")
    args = parser.parse_args()
    shelf = Path(__file__).resolve().parent
    report = {"purpose": "Installation readiness only", "python": python_checks()}
    with sync_playwright() as playwright:
        report["chromium"] = browser_checks(playwright, shelf)
        brave_app = Path("/Applications/Brave Browser.app/Contents")
        if (brave_app / "Info.plist").exists():
            with (brave_app / "Info.plist").open("rb") as f:
                report["brave_installed_version"] = plistlib.load(f).get("CFBundleShortVersionString")
        if args.brave:
            report["brave_synthetic_check"] = browser_checks(
                playwright, shelf, brave_app / "MacOS" / "Brave Browser")
    destination = shelf / ".cache" / "installation-smoke.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
