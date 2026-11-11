# Image preparation

The preparation command reads only the two selected source photos. It does not modify files in `data/`.

Run from the repository root:

```sh
Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf/run.sh python Photo-to-Wallpaper-Rendering-Engine/code/image_preparation.py
Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf/run.sh python -m pytest Photo-to-Wallpaper-Rendering-Engine/code/tests -q
```

The command applies EXIF orientation, converts embedded color profiles to sRGB, and fits the complete photo inside 1728 × 972. It uses one scale factor, LANCZOS resampling, and nearest-pixel rounding. Exact half-pixel values round up. Color conversion uses relative colorimetric intent with flags set to zero. Untagged RGB is treated as sRGB. Invalid profiles and unsupported input modes fail without a silent fallback.

The PNG writer rebuilds the image from RGB pixel bytes. A separate structure check permits only IHDR, IDAT and IEND. It checks dimensions, 8-bit RGB, chunk order, CRCs and the end of the file. A decode check verifies the saved pixels. Use this writer for later outputs and thumbnails.

Prepared files are under `results/build-n-compare-0.0.1/prepared/`. Run records are under `results/build-n-compare-0.0.1/runs/`. Both paths are relative to the engine directory and are ignored by Git. Each record contains source and output hashes, the scale, the protected rectangle, and check results. It contains metadata field names only. It does not contain copied metadata values.

Existing output files are kept. An identical rerun succeeds. A different output at the same path causes a failure. The command checks the source hash before and after processing. Run record names include a content hash to preserve earlier records.

## Verified result

Both selected images were prepared on 2026-11-11:

| Input | Prepared size | Protected rectangle on the future canvas |
| --- | --- | --- |
| portrait-01 | 729 × 972 | x=595, y=54, width=729, height=972 |
| landscape-01 | 1296 × 972 | x=312, y=54, width=1296, height=972 |

Nine tests passed. Three runs produced identical PNG bytes and records. Both originals still match their earlier SHA-256 values. Both PNG files have no metadata chunks. Visual inspection confirmed the expected orientation. The prepared files contain the complete photos; the 1920 × 1080 wallpaper canvas will be built in the renderer step.

Verification record: `results/build-n-compare-0.0.1/runs/preparation-135f1179d1e4979c.json`.
