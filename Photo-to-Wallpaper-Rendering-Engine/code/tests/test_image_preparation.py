import io
from pathlib import Path
import struct
import sys
import zlib

import pytest
from PIL import Image, ImageCms

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from image_preparation import clean_png_bytes, prepare_pixels, validate_clean_png, write_new_or_identical


def source_bytes(image, **options):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", **options)
    return buffer.getvalue()


def chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def test_orientation_moves_pixels_and_drops_tags():
    image = Image.new("RGB", (3, 2))
    image.putdata([(n, n + 1, n + 2) for n in range(6)])
    exif = Image.Exif()
    exif[274] = 6
    exif[270] = "private test metadata"
    prepared, details = prepare_pixels(source_bytes(image, exif=exif), (2, 3))
    assert prepared.tobytes() == image.transpose(Image.Transpose.ROTATE_270).tobytes()
    assert prepared.size == (2, 3)
    assert prepared.info == {} and not prepared.getexif()
    assert details["color_policy"] == "untagged RGB assumed sRGB"
    assert "private test metadata" not in str(details)


def test_valid_profile_conversion_and_clean_export():
    image = Image.new("RGB", (8, 6), (30, 100, 210))
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    prepared, details = prepare_pixels(source_bytes(image, icc_profile=profile), (8, 6))
    assert prepared.tobytes() == image.tobytes()
    assert details["color_policy"] == "embedded profile converted to sRGB"
    # Even a caller that reattaches metadata cannot cause it to be copied by the writer.
    prepared.info.update(icc_profile=profile, comment=b"private comment")
    prepared.getexif()[270] = "private test metadata"
    encoded = clean_png_bytes(prepared)
    assert validate_clean_png(encoded, image.size)["chunk_types"] == ["IHDR", "IDAT", "IEND"]
    assert b"private" not in encoded
    with Image.open(io.BytesIO(encoded)) as decoded:
        assert decoded.tobytes() == image.tobytes()
        assert decoded.info == {} and not decoded.getexif()


@pytest.mark.parametrize("size,box,expected", [((3024, 4032), (1728, 972), (729, 972)),
    ((4032, 3024), (1728, 972), (1296, 972)), ((3, 2), (8, 5), (8, 5)),
    ((2, 3), (20, 20), (13, 20))])
def test_proportional_fit_and_enlargement(size, box, expected):
    prepared, details = prepare_pixels(source_bytes(Image.new("RGB", size)), box)
    assert prepared.size == expected
    assert prepared.width <= box[0] and prepared.height <= box[1]
    scale = details["scale"]["numerator"] / details["scale"]["denominator"]
    assert all(abs(expected[i] - size[i] * scale) <= 0.5 for i in range(2))


def test_invalid_profile_and_untagged_cmyk_fail():
    with pytest.raises(ValueError, match="profile"):
        prepare_pixels(source_bytes(Image.new("RGB", (4, 3)), icc_profile=b"not a profile"))
    buffer = io.BytesIO()
    Image.new("CMYK", (4, 3)).save(buffer, format="JPEG")
    with pytest.raises(ValueError, match="non-RGB"):
        prepare_pixels(buffer.getvalue())


def test_png_validator_rejects_metadata_trailing_bytes_and_corruption():
    encoded = clean_png_bytes(Image.new("RGB", (4, 3)))
    bad_crc = bytearray(encoded)
    bad_crc[-1] ^= 1
    samples = [encoded + b"hidden data", encoded[:33] + chunk(b"tEXt", b"comment\0hidden") + encoded[33:],
               bytes(bad_crc), encoded[:-1], encoded[:33] + encoded[8:33] + encoded[33:]]
    for sample in samples:
        with pytest.raises(ValueError):
            validate_clean_png(sample, (4, 3))
    with pytest.raises(ValueError, match="dimensions"):
        validate_clean_png(encoded, (3, 4))


def test_existing_output_is_preserved(tmp_path):
    target = tmp_path / "prepared.png"
    write_new_or_identical(target, b"first")
    write_new_or_identical(target, b"first")
    with pytest.raises(FileExistsError):
        write_new_or_identical(target, b"second")
    assert target.read_bytes() == b"first"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["prepared.png"]
