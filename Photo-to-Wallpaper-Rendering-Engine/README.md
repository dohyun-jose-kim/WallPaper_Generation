> Historical design document. Current implementation and usage are described in the [WALL-E README](../README.md) and [project status](../docs/PROJECT_STATUS.md). This document preserves the original design exploration; it is not the current implementation specification.

# Photo-to-Wallpaper Rendering Engine

The [54-case comparison](plan-docs/build-n-compare-0.0.1/README.md) is complete. Its [selection record](plan-docs/build-n-compare-0.0.1/tool-selection.md) identifies the four implemented styles. The concepts and candidate technologies below describe the earlier exploration.

## 1. Original project objective

The objective was to process portrait, landscape, and square photographs using consistent composition rules to produce full-screen backgrounds for a Brave browser page or hero section. The foreground should retain its proportions and complete composition.

The original principles were:

- **Preserve the source:** protect the subject, composition, and visual character of the photograph.
- **Design the surrounding space:** use blur, translucent glass, gallery mattes, or structural extension to fill the canvas.
- **Keep output consistent:** use standardized output dimensions even when source proportions differ.
- **Compare visual results first:** choose the rendering stack and automation after reviewing the concepts.
- **Run locally:** use an open-source workflow suitable for Apple Silicon.

```text
Content photo: portrait / landscape / square
                    |
                    v
Image analysis and composition
                    |
                    v
Extension style: A / B / C / D
                    |
                    v
Standardized wallpaper output
                    |
                    v
Browser background / hero section
```

## 2. Four original design concepts

These concept images use the same source photograph and a 1920 × 1080 canvas with a 16:9 ratio. They are historical visual references, not the final selected renderer outputs.

### A — Liquid glass extension

![Liquid glass extension concept](./exmpl_a_Expand-liquid-glass.jpg)

[Open the original concept JPG](./exmpl_a_Expand-liquid-glass.jpg)

This concept surrounds the photograph with blur, gloss, glass boundaries, and subtle refraction inspired by translucent interface materials. The original proposal called for adjustable blur layers, refraction, opacity, and edge highlights.

### B — Source-derived blurred background

![Blurred background extension concept](./exmpl_b_Expand-blur.jpg)

[Open the original concept JPG](./exmpl_b_Expand-blur.jpg)

An enlarged copy of the photograph fills the background and is blurred. The complete foreground remains sharp and centered. This preserves visual continuity with a comparatively simple rendering process, although the treatment can resemble a conventional video backdrop.

### C — Gallery-style extension

![Gallery extension concept](./exmpl_c_Expand-galery.jpg)

[Open the original concept JPG](./exmpl_c_Expand-galery.jpg)

A dark matte or a representative color extracted from the photograph creates a gallery presentation. The composition is orderly and preserves the photograph, while the surrounding canvas remains visibly distinct from its content.

### D — Content-aware or generative extension concept

![Structural extension concept](./exmpl_d_Expand-generation.jpg)

[Open the original concept JPG](./exmpl_d_Expand-generation.jpg)

This proposal explored extending architectural structures and textures beyond the photograph. A future generative implementation would require separate quality and fidelity checks because it could introduce visual information absent from the original.

**Scope of these examples:** A is a local compositing concept inspired by liquid glass; it does not implement Apple's system renderer. D simulates structural extension using reflected and transformed image content; it is not AI outpainting. These four concepts were preliminary design references. Generative outpainting is excluded from the current WALL-E pipeline.

## 3. Technologies considered during exploration

The original plan deferred technology selection until after visual review.

| Stage | Candidates considered | Purpose |
| --- | --- | --- |
| Image analysis | Python, Pillow, OpenCV | Dimensions, orientation, composition |
| Glass and blur | Core Image, Metal shaders | Evaluate Apple acceleration and open-source alternatives |
| Compositing and encoding | libvips, ImageMagick | Batch processing and possible WebP/JPEG output |
| Structural extension | PyTorch models with MPS support | Explore model-specific outpainting quality and support |
| Batch orchestration | Python CLI, Bash wrapper | Settings, sequential processing, errors, logs |

The proposal targeted Apple Silicon and called for measuring actual CPU, GPU, and memory behavior before selecting accelerated operations. The implemented architecture now uses a Rust orchestrator and a Python/TypeScript engine; see the [current design](../docs/pipeline-design.md).

## 4. Original development sequence

1. Compare A/B/C/D prototypes using both portrait and landscape photographs.
2. Define photo occupancy, margins, blur and glass strength, placement, and safe areas.
3. Build a reusable CLI with options and presets for the selected styles.
4. Automate input discovery, preparation, rendering, verification, output, and logging.

The proposed Bash wrapper was subsequently replaced by the Rust orchestrator. The original sequence is retained here as historical context.

## 5. Canvas ratio and foreground preservation

Standardizing the output ratio is separate from preserving the photograph's proportions and content. A portrait photograph can appear inside a landscape wallpaper by adding designed surroundings on either side.

The initial experimental targets were:

- 1920 × 1080, 16:9, for the first comparison.
- 2560 × 1440, 16:9, as a higher-resolution candidate.
- Ultrawide and portrait canvases for subsequent composition checks.
- Browser cropping, safe areas, compression quality, and file size as display considerations.

A browser using a `cover` background can crop the wallpaper itself depending on the viewport. Foreground preservation in the exported file does not prevent a consuming application from cropping that file during display.

## 6. Original evaluation criteria

| Criterion | Question |
| --- | --- |
| Source preservation | Are the subject, composition, and contrast preserved? |
| Visual consistency | Do different photographs receive a coherent treatment? |
| Portrait handling | Do the added side regions look intentional? |
| Display compatibility | Do important elements remain visible across target layouts? |
| Automation | Can the treatment be expressed with repeatable parameters? |
| Efficiency | Are runtime, memory use, and output size practical? |

The comparison subsequently selected S1 blurred background, S1 gallery frame, D3 frosted glass, and S2 gradient. These implemented selections supersede the preliminary A/B/C/D set.

## Reference files

```text
Photo-to-Wallpaper-Rendering-Engine/
├── README.md
├── exmpl_a_Expand-liquid-glass.jpg
├── exmpl_b_Expand-blur.jpg
├── exmpl_c_Expand-galery.jpg
└── exmpl_d_Expand-generation.jpg
```

Original concept source dimensions: 2047 × 1365 pixels, approximately 3:2. Concept JPG output dimensions: 1920 × 1080 pixels, 16:9.
