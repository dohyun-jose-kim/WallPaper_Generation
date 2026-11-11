"""Prepare the two comparison photos without modifying their source files."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import zlib

from PIL import Image, ImageCms, ImageOps

CANVAS = (1920, 1080)
FIT_BOX = (1728, 972)
INPUTS = (
    ("portrait-01", "IMG_0622.JPG", (729, 972)),
    ("landscape-01", "IMG_1003.JPG", (1296, 972)),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_clean_png(data: bytes, expected_size: tuple[int, int]) -> dict:
    """Check PNG structure and CRCs without using Pillow's metadata parser."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid PNG signature")
    offset = 8
    chunks = []
    while offset < len(data):
        if len(data) - offset < 12:
            raise ValueError("Truncated PNG chunk")
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("PNG chunk exceeds file bounds")
        if kind not in (b"IHDR", b"IDAT", b"IEND"):
            raise ValueError("PNG contains a forbidden chunk")
        payload = data[offset + 8:offset + 8 + length]
        crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
        if crc != zlib.crc32(kind + payload) & 0xFFFFFFFF:
            raise ValueError("PNG chunk CRC mismatch")
        if not chunks and kind != b"IHDR":
            raise ValueError("PNG must start with IHDR")
        if kind == b"IHDR":
            if chunks or length != 13:
                raise ValueError("Invalid or repeated IHDR")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if (width, height) != expected_size or min(width, height) <= 0:
                raise ValueError("PNG dimensions do not match")
            if (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
                raise ValueError("PNG must be non-interlaced 8-bit RGB")
        if kind == b"IEND":
            if length or b"IDAT" not in chunks or end != len(data):
                raise ValueError("Invalid IEND or trailing payload")
            chunks.append(kind)
            return {"chunk_types": list(dict.fromkeys(k.decode("ascii") for k in chunks)),
                    "chunk_count": len(chunks), "crc_valid": True, "trailing_bytes": 0}
        chunks.append(kind)
        offset = end
    raise ValueError("PNG is missing IEND")


def clean_png_bytes(image: Image.Image) -> bytes:
    """Encode pixels only. Use this writer for future results and thumbnails too."""
    if image.mode != "RGB":
        raise ValueError("Clean PNG export requires RGB pixels")
    clean = Image.frombytes("RGB", image.size, image.tobytes())
    output = io.BytesIO()
    clean.save(output, format="PNG", compress_level=6, optimize=False)
    data = output.getvalue()
    validate_clean_png(data, image.size)
    with Image.open(io.BytesIO(data)) as decoded:
        decoded.load()
        if decoded.mode != "RGB" or decoded.tobytes() != image.tobytes():
            raise ValueError("PNG pixel round trip failed")
    return data


def write_new_or_identical(path: Path, data: bytes) -> None:
    """Publish a complete file without overwriting a different existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".prepare-", delete=False) as file:
            temporary = Path(file.name)
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes() != data:
                raise FileExistsError("Existing output differs; keep it and use a new output location") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def prepare_pixels(source: bytes, fit_box: tuple[int, int] = FIT_BOX, canvas: tuple[int, int] = CANVAS, *, strict: bool = True) -> tuple[Image.Image, dict]:
    """Apply orientation, sRGB conversion, proportional resize, and metadata removal."""
    if min(fit_box) <= 0:
        raise ValueError("Fit dimensions must be positive")
    if len(source) > 200 * 1024 * 1024:
        raise ValueError("Input exceeds 200 MiB")
    with Image.open(io.BytesIO(source)) as decoded:
        if strict and decoded.format not in ('JPEG', 'PNG'):
            raise ValueError("Only JPEG and PNG are supported")
        if decoded.width * decoded.height > 100_000_000:
            raise ValueError("Input exceeds 100 million pixels")
        if strict and getattr(decoded, 'n_frames', 1) != 1:
            raise ValueError("Animated or multi-frame inputs are unsupported")
        decoded.load()
        fields = sorted(decoded.info.keys())
        image = ImageOps.exif_transpose(decoded)
        display_size = image.size
        profile_bytes = image.info.get("icc_profile")
        alpha = image.convert('RGBA').getchannel('A') if image.mode in ('RGBA', 'LA', 'P') or 'transparency' in image.info else None
        if image.mode == 'P':
            image = image.convert('RGB')
        elif image.mode in ('RGBA', 'LA'):
            image = image.convert('RGB' if image.mode == 'RGBA' else 'L')
        if image.mode not in ("RGB", "L", "CMYK"):
            raise ValueError("Unsupported source mode")
        if profile_bytes:
            try:
                profile = ImageCms.ImageCmsProfile(io.BytesIO(profile_bytes))
                image = ImageCms.profileToProfile(
                    image, profile, ImageCms.createProfile("sRGB"),
                    renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                    outputMode="RGB", flags=0,
                )
            except (ImageCms.PyCMSError, OSError, TypeError, ValueError):
                raise ValueError("Embedded color profile cannot be converted to sRGB") from None
            color_policy = "embedded profile converted to sRGB"
        elif image.mode in ("RGB", "L"):
            color_policy = "untagged RGB assumed sRGB" if image.mode == 'RGB' else "untagged grayscale assumed sRGB"
            image = image.convert('RGB')
        else:
            raise ValueError("Untagged non-RGB input has no defined color conversion")
        if alpha is not None:
            image = Image.composite(image, Image.new('RGB', image.size, '#16181D'), alpha)
        scale = min(Fraction(fit_box[0], image.width), Fraction(fit_box[1], image.height))
        # Exact half-up rounding avoids platform-dependent floating-point ties.
        dimensions = tuple((2 * n * scale.numerator + scale.denominator) //
                           (2 * scale.denominator) for n in image.size)
        dimensions = tuple(max(1, n) for n in dimensions)
        resized = image.resize(dimensions, resample=Image.Resampling.LANCZOS)
        prepared = Image.frombytes("RGB", resized.size, resized.tobytes())
    x, y = ((canvas[i] - dimensions[i]) // 2 for i in range(2))
    return prepared, {
        "display_size": list(display_size), "prepared_size": list(dimensions),
        "scale": {"numerator": scale.numerator, "denominator": scale.denominator},
        "rounding": "nearest pixel; ties round up", "resampling": "LANCZOS",
        "color_policy": color_policy, "color_intent": "relative colorimetric; flags=0",
        "metadata_field_names_removed": fields,
        "canvas_size": list(canvas),
        "protected_rectangle_xyxy_exclusive": [x, y, x + dimensions[0], y + dimensions[1]],
        "prepared_pixel_sha256": sha256(prepared.tobytes()),
    }


def main() -> int:
    engine = Path(__file__).resolve().parents[2]
    root = engine.parent
    source_root = root / "data" / "WallPaper_v0.1_2026-10-28"
    result_root = engine / "results" / "build-n-compare-0.0.1"
    # Refuse redirected output directories. Input files are opened read-only.
    for folder in [result_root, result_root / "prepared", result_root / "runs"]:
        if folder.resolve() != folder:
            raise ValueError("Output path contains a symlink")
    report = {"schema_version": 1, "stage": "image preparation", "images": []}
    for image_id, name, expected_size in INPUTS:
        source_path = source_root / name
        source = source_path.read_bytes()
        record = {"input_id": image_id, "source_file": name,
                  "source_sha256_before": sha256(source)}
        try:
            prepared, details = prepare_pixels(source, strict=False)
            if prepared.size != expected_size:
                raise ValueError("Prepared dimensions differ from the comparison plan")
            output = clean_png_bytes(prepared)
            record.update(details)
            record["png_structure"] = validate_clean_png(output, expected_size)
            record["png_sha256"] = sha256(output)
            record["output_file"] = f"prepared/{image_id}.png"
            # Do not publish a prepared image if its source changed while being read.
            if sha256(source_path.read_bytes()) != record["source_sha256_before"]:
                raise ValueError("Source changed during preparation")
            write_new_or_identical(result_root / record["output_file"], output)
            record["status"] = "passed"
        except Exception as error:
            # Do not put metadata values or raw decoder errors into the run log.
            record["status"] = "failed"
            record["error_type"] = type(error).__name__
        finally:
            record["source_sha256_after"] = sha256(source_path.read_bytes())
            record["original_unchanged"] = record["source_sha256_before"] == record["source_sha256_after"]
            if not record["original_unchanged"]:
                record["status"] = "failed"
        report["images"].append(record)
        print(f"{image_id}: {record['status']}; original unchanged: {record['original_unchanged']}")
    payload = (json.dumps(report, indent=2) + "\n").encode()
    # Content-based records preserve previous runs and make identical reruns harmless.
    report_path = result_root / "runs" / f"preparation-{sha256(payload)[:16]}.json"
    write_new_or_identical(report_path, payload)
    print(f"Verification record: {report_path.relative_to(root)}")
    return 0 if all(item["status"] == "passed" for item in report["images"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
