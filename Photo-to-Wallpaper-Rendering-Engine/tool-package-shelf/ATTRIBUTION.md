# Source and dependency attribution

Inspection date: 2026-11-11. This records local preparation, not independent verification of upstream optical or provenance claims. Source bytes and full revisions are recorded in [source-manifest.json](source-manifest.json).

| ID | Source / revision | License evidence | Local acquisition |
| --- | --- | --- | --- |
| D1 | [medfa12/liquid-glass-react](https://github.com/medfa12/liquid-glass-react/tree/a7d3c5ebd04b7efdf264a901cc521f77878744d1) | MIT, full notice preserved in [D1-LICENSE](licenses/D1-LICENSE) | Renderer, shader, parameters, required generated parameters and supporting notices/config; no React wrapper/demo |
| D2 | [ybouane/liquidglass](https://github.com/ybouane/liquidglass/tree/59af227103795f06421a96e2c7d3dceb081decd2) | `package.json` and README declare MIT; no standalone LICENSE at this revision | GlassRenderer, shaders, defaults, README and package/config; no HtmlCapture/html-to-image/patch-package installation |
| D3 | [rdev/liquid-glass-react](https://github.com/rdev/liquid-glass-react/tree/ac48eab18d1f7f444ae30002d240cae29c863a21) | MIT, full notice preserved in [D3-LICENSE](licenses/D3-LICENSE) | React component, shader utilities, displacement-map constants and supporting notices/config; no example app/media |

D1's shader provenance claims are upstream claims; this project has not reproduced Apple's binary analysis. D3's `shader-utils.ts` credits [shuding/liquid-glass](https://github.com/shuding/liquid-glass) without a source revision. The original comment is preserved. D3's `utils.ts` includes embedded displacement-map data used by the component; it is included unchanged, not a separately downloaded demo image.

D1 has no npm lockfile. D2's manifest version is 1.0.3 while its lock root says 1.0.0. D3's manifest says 1.1.1 and React peers >=18; its npm lock root says 1.0.0 and peers >=16.8.0. Its `bun.lock`, build scripts, and TypeScript configuration were also inspected. The project-owned package/lock files control installation for all three selected entry points.

Direct package license references: [Pillow HPND/PIL notice](https://github.com/python-pillow/Pillow/blob/main/LICENSE), [NumPy BSD-3-Clause](https://github.com/numpy/numpy/blob/main/LICENSE.txt), [pyvips MIT](https://github.com/libvips/pyvips/blob/master/LICENSE.txt), [libvips LGPL-2.1](https://github.com/libvips/libvips), [Playwright Apache-2.0](https://github.com/microsoft/playwright/blob/main/LICENSE), [psutil BSD-3-Clause](https://github.com/giampaolo/psutil/blob/master/LICENSE), [pytest MIT](https://github.com/pytest-dev/pytest/blob/main/LICENSE), [esbuild MIT](https://github.com/evanw/esbuild/blob/main/LICENSE.md), [React/React DOM MIT](https://github.com/facebook/react/blob/main/LICENSE).

Installed wheels/npm packages retain their own license files, including bundled native-library notices. Lockfiles identify exact versions and distribution hashes. Browser bundles retain their supplied notices in ignored local storage. Before distributing binaries or vendored code, carry the applicable notices from those installed artifacts; this local installation does not publish them.
