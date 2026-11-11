# 렌더링 도구 종합 조사와 최종 후보 5개

> 현재 실행 범위(2026-11-11): [Build and Compare 0.0.1](build-n-compare-0.0.1/README.md). 세로·가로 2장, 도구 5개, 총 54개 케이스이며 실패도 유지한다. 아래는 이전 조사/환경 기록이다. 10개·26개 제안, Miniforge 대안 및 이전 실행 순서는 현재 범위에 적용하지 않는다.

조사일: 2026-11-10 · 상태: 문서·공개 소스 조사 완료, 설치·렌더링·캡처 실험 전.

## 결정과 범위

**동적 후보: medfa12/liquid-glass-react, ybouane/liquidglass, rdev/liquid-glass-react. 정적 후보: Pillow + NumPy, libvips + pyvips.** 비교 실험 대상의 선정이며 최종 엔진 채택이나 품질 검증 완료를 뜻하지 않는다.

현재 산출물은 사진의 contour와 확장 영역을 처리한 1920×1080 PNG/JPEG다. 동적 엔진도 원하는 순간을 저장해 사용하고 향후 동적 활용 가능성을 유지한다. 원본 전체를 비율 보존하여 화면 가로·세로의 90% 이내에 중앙 배치한다. 생성형 아웃페인팅은 이번 비교에서 제외한다.

기존 기획에 따라 첫 실험의 contour는 사진 외곽 경계로 다룬다. 사진 속 피사체의 불규칙 윤곽까지 자동으로 지원한다고 가정하지 않는다. 후자는 별도 마스크·거리장·법선 계산이 필요하며 추가 구현 범위로 평가한다.

동적 구현 6개와 정적 도구 계열 4개를 비교하고 Kube의 광학 설명을 공통 원리 자료로 검토했다. 기존 조사에서 정했던 ‘웹 셰이더 최대 두 개’ 범위는 이번 사용자 요청으로 확대한다. 아래 선택 이유와 구현 적합성은 프로젝트 요구에 대한 판단이다.

## 최종 후보

스타·포크는 **2026-11-10 조회한 GitHub 페이지 표시값**이다. 웹 캐시의 시차가 있을 수 있고 `k`는 반올림 값이다. 관심도와 실제 채택, 성공적인 운영은 서로 다르다. 기반 라이브러리의 인기를 새로 만들 유리 효과 엔진의 실적으로 취급하지 않는다.

| 구분 | 후보·출처 | 스타 / 포크 | 선정 이유 | 필요한 추가 작업 |
| --- | --- | --- | --- | --- |
| 동적 D1 | [medfa12/liquid-glass-react](https://github.com/medfa12/liquid-glass-react) | 0 / 0 | **QuartzCore 역공학 후보 필수 유지**. Apple 경계 모델 비교 | WebGL2 실행, 원본 보호와 확장 배경, 정적 저장 어댑터 |
| 동적 D2 | [ybouane/liquidglass](https://github.com/ybouane/liquidglass) | 611 / 46 | 사진 입력과 굴절·블러·광택 제어, 외부 실행 흔적 | 전체 장면 합성·저장, 초기화와 브라우저 성능 검증 |
| 동적 D3 | [rdev/liquid-glass-react](https://github.com/rdev/liquid-glass-react) | 약 6.7k / 436 | 높은 관심도와 외부 재사용 근거가 있는 비교 기준 | Chromium 캡처, 모드별 동작·호환성 검증 |
| 정적 S1 | [Pillow](https://github.com/python-pillow/Pillow) + NumPy | Pillow 약 14.0k / 2.6k | 원본 보호·패딩·마스크와 광학 수학의 기준 구현 | 굴절 맵·보간·하이라이트 직접 구현 |
| 정적 S2 | [libvips](https://github.com/libvips/libvips) + [pyvips](https://github.com/libvips/pyvips) | libvips 약 11.8k / 802; pyvips 817 / 65 | 좌표 재매핑·합성·배치 처리 비교 | 유리 모델 구현, 네이티브 환경과 실제 비용 측정 |

정적 두 후보는 완성된 Liquid Glass 제품이 아니라 직접 렌더러를 만들 기반 도구다. 동적 후보의 전처리·후처리에도 함께 사용할 수 있다.

## D1 — QuartzCore 역공학 후보

README는 **macOS 26/27 QuartzCore 셰이더 역공학**과 실제 NSGlassEffectView 캡처 비교를 명시하며 오차와 모서리 차이도 인정한다. iOS 바이너리를 직접 분석했다고 확인한 자료는 아니다. 원본 바이너리 → 역어셈블 → 복원 → 측정 과정을 이번 조사에서 독립 재현하지 않았다. 공개 검색에서 이 패키지의 독립적인 운영 채택 사례도 확인하지 못했다. 낮은 스타에도 분석 가치와 사용자 지정 우선순위로 유지한다. [저장소와 Fidelity](https://github.com/medfa12/liquid-glass-react#fidelity)

실제 [shader.ts](https://raw.githubusercontent.com/medfa12/liquid-glass-react/main/src/shader.ts)에 경계 거리 기반 `lensCurve`와 `refractLobe`가 존재한다. 경계에서 강하고 내부에서 줄어드는 변위 모델은 코드로 확인했지만 주석의 Apple 유래 주장까지 입증한 것은 아니다.

[renderer.ts](https://raw.githubusercontent.com/medfa12/liquid-glass-react/main/src/renderer.ts)는 이미지·캔버스·비디오 입력, `resize`, `render(params)`를 제공한다. 적용 제안은 사진 텍스처를 넣고 고정 파라미터로 렌더한 직후 프레임을 복사하는 것이다. 컨텍스트 생성 시 `preserveDrawingBuffer`를 명시하지 않으므로 읽기 시점을 렌더와 연계해야 한다. 전체 wallpaper 합성과 PNG 저장은 별도 작업이다. MIT 표시. [저장소](https://github.com/medfa12/liquid-glass-react)

## D2 — 사진 입력과 광학 제어

ybouane은 사진·캔버스·비디오 배경, 블러·굴절·색수차·Fresnel 반사·광택·테두리·그림자를 제공한다. 사진을 직접 그리는 경로와 향후 동적 배경 지원 때문에 선정했다. README는 MIT를 명시하지만 조회한 루트 목록에 별도 LICENSE 파일이 보이지 않아 도입 시 배포 고지 파일을 확인한다. [README](https://github.com/ybouane/liquidglass)

[GlassRenderer.ts](https://raw.githubusercontent.com/ybouane/liquidglass/main/src/GlassRenderer.ts)에 `preserveDrawingBuffer: true`와 패널 렌더링 캔버스가 있다. 적용 제안은 확장 배경·유리·선명한 원본까지 최종 캔버스에 합성한 뒤 저장하는 것이다. 내부 WebGL 캔버스 하나를 저장하는 것만으로 전체 결과가 완성된다고 가정하지 않는다.

작성자 외 사용자의 [Firefox/LibreWolf 성능 제보 #2](https://github.com/ybouane/liquidglass/issues/2), [Chrome 초기화 미완료 제보 #3](https://github.com/ybouane/liquidglass/issues/3)를 확인했다. 실제 실행 시도의 근거이며 성공적 운영 실적은 아니다. 현재 코드에서 재현되는지는 미검증이다. 사진만 있는 단순 장면에서도 초기화와 저장 완료 조건을 확인해야 한다.

## D3 — 공개 사용 신호가 강한 비교 기준

rdev는 굴절 모드·하이라이트·색수차·frost·탄성 반응을 제공한다. MIT. README는 Safari/Firefox에서는 변위가 보이지 않는다고 명시한다. 따라서 Brave/Chromium에서 사진 배경과 입력 상태를 고정하고 전체 장면을 캡처하는 실험을 제안한다. [README](https://github.com/rdev/liquid-glass-react)

외부 사용자의 [shader 모드 실패 #29](https://github.com/rdev/liquid-glass-react/issues/29)가 있어 모든 모드가 동작한다고 가정하지 않는다. 다른 운영자의 [glass-projects-lab](https://github.com/lekandigital/glass-projects-lab)은 rdev 예제를 포함하고 재배포 주소를 명시한다. 외부 재사용·데모 배포의 근거이며 상용 운영 또는 장기 안정성 검증과 구분한다. 이번에 그 배포를 직접 실행하지 않았다.

## S1 — Pillow + NumPy

[ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html)의 비율 보존 배치·방향 처리, [ImageFilter](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html)의 GaussianBlur, [NumPy pad](https://numpy.org/doc/stable/reference/generated/numpy.pad.html)의 edge/reflect를 조합한다. 마스크·굴절 맵을 명시적으로 조정하기 쉬운 기준 구현으로 선정했다.

경계 거리 → 유리 단면 → 법선 → 샘플링 좌표를 설계하고 보간·색조·하이라이트를 더해야 한다. [Kube의 설명](https://kube.io/blog/liquid-glass-css-svg/)은 굴절·변위 맵·하이라이트를 설명하되 Apple과 픽셀 단위 일치를 목표로 하지 않는 근사 모델임을 밝힌다. 이를 NumPy 정적 연산으로 옮기는 것은 우리의 구현 제안이다.

실제 채택 근거는 [Matplotlib의 의존성 선언](https://raw.githubusercontent.com/matplotlib/matplotlib/main/pyproject.toml)에 Pillow와 NumPy가 포함된다는 점이다. 이미지·수치 처리 기반의 채택 증거이며 유리 효과의 실적은 아니다. 라이선스는 [Pillow의 PIL/HPND 계열 고지](https://github.com/python-pillow/Pillow/blob/main/LICENSE), [NumPy BSD-3-Clause](https://github.com/numpy/numpy/blob/main/LICENSE.txt)를 확인했다.

## S2 — libvips + pyvips

[pyvips API](https://libvips.github.io/pyvips/vimage.html)는 `mapim` 좌표 재매핑·보간·외부 픽셀 정책, 블러·합성·저장을 제공한다. S1과 같은 변위·마스크 모델을 옮겨 결과와 배치 비용을 비교한다. 스트리밍 처리의 일반적 장점을 이 프로젝트의 굴절 재매핑 성능으로 대신하지 않는다. 큰 중간 맵과 임의 좌표 접근 비용은 측정해야 한다.

[Sharp 공식 문서](https://sharp.pixelplumbing.com/)가 libvips 기반임을 명시하므로 실제 채택 근거가 있다. libvips의 채택이며 pyvips 자체나 유리 효과의 실적은 아니다. 라이선스는 [libvips LGPL-2.1](https://github.com/libvips/libvips), [pyvips MIT](https://github.com/libvips/pyvips)다.

현재 [pyvips 설치 안내](https://github.com/libvips/pyvips#binary-installation)는 macOS ARM을 포함하는 `pyvips[binary]` 번들과 별도 libvips 설치를 모두 제공한다. 기존 문서의 별도 설치만 언급한 설명을 보완한다. 실제 패키지 구성·버전·M5 동작은 실행 단계에서 확인한다.

## 나머지 후보를 보류한 이유

| 후보와 출처 | 스타 / 포크 | 평가 |
| --- | --- | --- |
| [DevBehindYou/LiquidLens](https://github.com/DevBehindYou/LiquidLens) | 2 / 0 | 광학·다중 플랫폼 자료로 유지. 외부 사용 근거가 약하고 최종 세 후보에 비해 새 비교 축이 적다고 판단 |
| [Whynotmetoo/liquid-glass-canvas](https://github.com/Whynotmetoo/liquid-glass-canvas) | 5 / 0 | 캔버스 입력은 유용하나 문서상 블러 부재와 적은 사용 근거로 보류. D2의 DOM 합성이 장애가 되면 재검토 |
| [iyinchao/liquid-glass-studio](https://github.com/iyinchao/liquid-glass-studio) | 822 / 82 | SDF·굴절·분산·광택 제어가 유력한 예비 후보. README의 기능 설명과 TODO에 custom background·WebGPU·설정 import/export가 혼재해 완성 범위를 추가 확인해야 함 |
| [ImageMagick](https://github.com/ImageMagick/ImageMagick) | 약 17.8k / 1.7k | CLI에 유용. 이번 두 정적 슬롯은 Python 환경과 수치 모델을 공유하기 쉬운 S1/S2에 배정. 유리 레시피는 이 도구도 별도 설계 필요 |
| [ComfyUI-Majoor-ImageOps](https://github.com/MajoorWaldi/ComfyUI-Majoor-ImageOps) | 14 / 2 | PadOut의 constant/edge/reflect/blurry는 참고 가치가 있음. 독립 CLI 목표에서 전체 ComfyUI 도입의 이점이 작다고 판단 |

Kube는 실행 엔진 슬롯 대신 공통 알고리즘 자료로 유지한다. 앞선 대화의 세 링크를 그대로 고정하지 않고 QuartzCore 후보를 보존하면서 입력 적합성과 사용 신호로 다시 선정했다.

## 다음 비교 실험의 공통 조건

아래는 아직 실행하지 않은 설계다. 후보 선정은 완료했지만 다섯 도구에서 출력 성공을 확인한 것은 아니다.

1. 같은 세로·가로 사진과 같은 확장 배경을 사용한다. 유리 렌즈는 없는 바깥 풍경을 생성하지 않으므로 배경 확장과 광학 처리를 나눈다. 사진의 원본 영역은 마지막에 선명하게 합성한다.
2. 경계 폭·굴절량·블러·색조·광택을 비교한다. 도구별 단위 차이를 기록하고 같은 숫자가 같은 효과라고 가정하지 않는다. 사진 바깥 프레임 형태와 내부 보호 마스크는 별도 구현한다.
3. D1은 렌더 직후 프레임 읽기, D2는 전체 장면 캔버스 합성, D3는 Chromium 장면 캡처를 검증한다. [Canvas toBlob](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob)과 [Playwright screenshots](https://playwright.dev/docs/screenshots)는 저장 수단이며 각 후보의 완성된 export 기능이 아니다.
4. 1920×1080 출력, DPR·줌·이미지 로딩 완료와 시간·포인터·진행률을 고정한다. CSS 애니메이션 정지만으로 JS/WebGL 루프까지 정지한다고 가정하지 않는다. WebGL 버퍼 수명, CORS와 전체 장면 합성도 확인한다.
5. 동일한 정지 상태를 반복 저장해 재현성을 검사한다. 추가로 짧은 동적 시퀀스를 확인해 향후 활용성을 남긴다. 지원하지 않거나 실패한 모드는 별도 기록한다.
6. 원본 보존은 EXIF·색상·리사이즈 처리를 마친 기준 이미지와 PNG 결과를 비교한다. JPEG 압축 오차는 분리한다. 시간·메모리는 동일 조건에서 측정하고 동적 후보의 초기화·프레임 시간은 따로 기록한다.

S1로 배경·배치 기준을 만든 뒤 **D1을 반드시 비교**, D2/D3의 저장 경로를 확인하고 S2로 정적 재매핑과 배치를 비교한다. 이전의 26개 조합은 과거 제안으로 보존하며 실제 조합·개수는 이 다섯 후보의 실행 가능성에 맞춰 정한다.

기존 환경 문서의 Python 3.9.6에 최신 패키지가 그대로 설치된다고 가정할 수 없다. 공식 표에서 Pillow 12/13은 Python 3.9를 지원하지 않는다. 실행 전 Python·패키지를 함께 정하고 버전을 고정한다. [Pillow 지원표](https://pillow.readthedocs.io/en/stable/installation/python-support.html)

이번 조사에서는 설치·렌더링·벤치마크를 수행하지 않았다. M5 성능, 고해상도 색상 정확도, 불규칙 contour, 실제 프레임 저장의 완성도는 후속 실험에서 검증한다.
