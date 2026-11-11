# Local AI outpainting — future candidates

Research date: 2026-11-11. **Outside Build and Compare 0.0.1; no models downloaded or run.** The supplied plan says an earlier sub-agent completed a report, but its text was absent from this workspace and handoff. This is a reconstruction from primary documentation, not a verbatim recovery or a claim to reproduce that agent's conclusions. The folder spelling `reseatch-0.0.1` is intentional.

## Diffusers and Apple Silicon MPS

Diffusers documents Apple Silicon execution through PyTorch's `mps` device and an ARM64 Python environment. Its MPS guide discusses memory pressure and attention slicing. These establish an implementation path, not measured compatibility or performance on this project's M5 machine. A future experiment should pin PyTorch, Diffusers and model revisions separately from the renderer environment, check MPS availability, and record any CPU fallback. [Diffusers MPS guide](https://huggingface.co/docs/diffusers/optimization/mps).

Project proposal: place the prepared source on a larger canvas, mask only the added region for generation, and restore the prepared source as the final layer. A model's keep-mask alone is not evidence of pixel-perfect foreground preservation. Test seams, plausible architecture, color continuity and generated objects separately from speed. Keep prompts, seed, scheduler, steps, precision, mask geometry, model revision and memory measurements with each run; compare repeated decoded outputs rather than promising determinism.

## SD 1.5 Inpainting

The maintained `stable-diffusion-v1-5/stable-diffusion-inpainting` repository identifies itself as an unaffiliated mirror of the deprecated Runway repository. Its model card describes mask-conditioned inpainting, 512 × 512 training, and the CreativeML OpenRAIL-M license. This is the specific inpainting checkpoint candidate, not a claim that any SD 1.5 base checkpoint is equivalent. Pin and verify checkpoint provenance and license before a future download. [Model repository and preserved card](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-inpainting).

Project inference: this is a useful first baseline for a smaller working canvas. The final 1920 × 1080 extension would require a deliberate working-resolution/upscale strategy. Quality, memory savings relative to SDXL, and M5 throughput have not been measured here.

## SDXL Inpainting

The Diffusers team's `diffusers/stable-diffusion-xl-1.0-inpainting-0.1` card describes mask-conditioned generation initialized from SDXL base, trained at 1024 × 1024, under CreativeML Open RAIL++-M. The card's example uses CUDA; it is not an M5 benchmark or an assurance that changing a device string is sufficient. [SDXL inpainting model card](https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1).

Project inference: evaluate it after the smaller baseline, with a separately tested MPS configuration and a measured memory budget. Compare scene continuation and seams at a common final size. Do not infer better output merely from the larger model or training resolution. Model-license obligations remain separate from the Python library license.

## Draw Things

Draw Things advertises local/offline generation on Apple devices and an Infinite Canvas. Its site also offers cloud compute, so the application name alone does not establish that a particular run is local. [Official product site](https://drawthings.ai/).

Project proposal: use an explicitly local model/backend for an interactive outpainting baseline, then check whether the installed version exposes suitable scripting or automation for repeatable export. Record application version, model revision, sampler, seed, canvas transform and output properties. GUI convenience does not establish batch reproducibility, pixel preservation, metadata cleanliness or speed. Do not describe the entire app as open source without a separate license/source audit.

## Siri, Shortcuts and Apple Intelligence

Apple's App Intents material describes exposing app actions through Shortcuts and Spotlight, and the Shortcuts `Use Model` action offers on-device and Private Cloud Compute choices. These are workflow integration surfaces; the cited material does not establish a general local mask-conditioned outpainting API. Siri is a potential future invocation surface for an exposed action, not the renderer selected by this project. [Apple developer session](https://developer.apple.com/videos/play/wwdc2025/260/).

Apple's current Photos guide lists Clean Up, Reframe and Extend. Therefore a blanket claim that Apple offers no image extension would be inaccurate. This review has not established an offline programmable export path, seed control, model pinning, or pixel-preserving mask support for those features. [Photos User Guide](https://support.apple.com/guide/photos/welcome/mac). Apple describes a mixture of on-device and Private Cloud Compute processing, including server-side image generation, so Apple Intelligence should not be assumed to be wholly local. [Apple Intelligence privacy description](https://www.apple.com/legal/privacy/data/en/intelligence-engine/).

Project proposal: evaluate Shortcuts/Siri only after a dependable local renderer exists. Check actual installed OS, language/region availability, action inputs/outputs, file access and compute destination. Keep cloud-backed features separate from local-only comparisons.

## Future experiment and present decision

Prefer Diffusers as the first candidate for a scripted, inspectable experiment; use Draw Things as an interactive comparison. This is an engineering recommendation from the documented interfaces, not an image-quality ranking. SD 1.5 and SDXL both remain untested. Apple automation and image tools remain separate candidates requiring capability verification.

A future run should record model/source licenses and hashes before acquisition, use sanitized input copies, retain the protected rectangle, clean-export every image, compare at least three repeated results, and measure initialization, rendering time, process memory and actual backend. Respect the resource stop rules, inspect seams at 100%, and ask the user to select preferred appearance from real images. No AI candidate is added to the current 54-case matrix.
