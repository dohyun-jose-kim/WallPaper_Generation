# 효과 원리와 예시

> 현재 실행 범위(2026-11-11): [Build and Compare 0.0.1](build-n-compare-0.0.1/README.md). 세로·가로 2장, 도구 5개, 총 54개 케이스이며 실패도 유지한다. 아래는 이전 조사/환경 기록이다. 10개·26개 제안, Miniforge 대안 및 이전 실행 순서는 현재 범위에 적용하지 않는다.

조사일: 2026-10-28. 아래 코드는 직접 작성한 **실행 미검증 코드**이며 출력 품질을 입증하지 않는다. 이미지 사용 예는 [기존 시안과 설명용 도식](research-0.0.1/index.html)에서 확인한다.

## Fuzzy

원본의 별도 복사본을 캔버스를 덮도록 확대·크롭하고 블러 처리한 뒤, 비율을 유지해 90% 이내로 맞춘 선명한 원본을 중앙에 합성한다. 다른 선택지는 가장자리 픽셀 반복 또는 반사 타일을 캔버스 밖까지 확장하고 블러하는 것이다. 경계에서는 페더 마스크로 두 층을 섞을 수 있지만 원본 보호 영역과 분리해야 한다. 반복은 띠, 반사는 대칭 이음새가 생길 수 있다. [ImageMagick의 virtual-pixel 및 blur](https://imagemagick.org/command-line-options/)는 이러한 경계 처리의 참고 자료다.

```python
# 실행 미검증 코드: 배경만 생성; 원본 배치와 색상 관리는 별도
from PIL import Image, ImageFilter, ImageOps
im = Image.open('input.jpg').convert('RGB')
bg = ImageOps.fit(im, (1920, 1080)).filter(ImageFilter.GaussianBlur(24))
bg.save('background.jpg', quality=90)
```

[Pillow 필터](https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html), [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html), [저장](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.save)을 참조한다. `24`는 설명용이며 확정값이 아니다.

## Glassy

배경 복사본에 서로 다른 반경의 블러를 섞고 좌표 변위 맵으로 샘플링해 굴절을 근사한다. 반투명 색조와 경계 하이라이트를 추가하고, 원본 영역의 보호 마스크를 적용한 뒤 선명한 원본을 마지막에 합성한다. 맵의 방향과 세기, 보간 및 이미지 밖 샘플 처리는 직접 설계한다. 이는 물리적 유리나 Apple 시스템 효과의 재현을 보장하지 않는다.

```text
# 실행 미검증 코드: 개념 의사코드
background = mix(blur(source, small), blur(source, large), weight)
glass = sample(background, coordinates + displacement)
margin = composite(tint_and_rim(glass), background, outside_original_mask)
output = composite(sharp_original, margin, original_mask)
```

[pyvips API](https://libvips.github.io/pyvips/vimage.html)의 `gaussblur`, `mapim`, `composite2`와 [NumPy 인덱싱](https://numpy.org/doc/stable/user/basics.indexing.html)을 참고한다. Pillow의 블러·합성은 바로 쓸 수 있지만 변위 맵과 보간은 추가 구현이 필요하다. pyvips는 좌표 이미지 생성·경계 규칙과 합성 파이프라인을 설계해야 한다.

## 외부 구현 예제와 정적 저장

- **외부 구현 예제:** [ybouane/liquidglass](https://github.com/ybouane/liquidglass)는 WebGL 셰이더의 굴절·블러·광택을 보여 준다. 저장소는 MIT로 표시하며 브라우저 DOM 캡처에 의존한다. 코드 복사 시 저작권·라이선스 고지를 보존하고 데모 에셋의 권리는 별도 확인한다. 정적 배경 생성기로 검증하지 않았다.
- [Canvas toBlob](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob)은 캔버스를 PNG 또는 지원되는 JPEG로 인코딩한다. 따라서 효과가 캔버스에 실제 렌더링되면 정적 저장이 가능하다. CSS backdrop-filter가 자동으로 캔버스에 포함되는 것은 아니며 화면 캡처 또는 별도 재렌더링이 필요하다. 교차 출처 이미지의 origin-clean 제약과 브라우저·캡처 환경을 검증해야 한다. [MDN 캡처 예](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Capture_API/Element_Region_Capture)는 사용자 화면 공유 허가를 요구하는 별도 경로다.

## 추가 오픈소스 사례 조사

2026-10-28에 GitHub에서 `blurred background image padding`, `aspect ratio`, `mirror`, `canvas refraction` 등을 검색했다. 아래는 저장소 설명과 공개 소스에 근거한 사례이며 설치하거나 실행하지 않았다. 코드나 이미지 자산을 복제하지 않았다.

| 외부 구현 예제 | 확인한 방식과 참고점 | 한계와 재사용 |
|---|---|---|
| [ComfyUI-Majoor-ImageOps](https://github.com/MajoorWaldi/ComfyUI-Majoor-ImageOps) | PadOut이 16:9 등 목표 비율, constant·edge_extend·reflect·blurry, 블러 반경과 패딩 마스크를 제공한다. 네 가지 여백 처리의 비교 설계에 가장 직접적이다. | ComfyUI 노드이며 독립 CLI는 아니다. 저장소 MIT. 원본을 다시 붙이는 전용 노드는 계획 중이라고 명시한다. |
| [ComfyUI-AusBoss](https://github.com/ausboss/ComfyUI-AusBoss) | Load Image + Pad가 단색·가장자리 평균·확장·블러·반사, 이음새 페더와 마스크를 제공한다. 폴더 일괄 처리도 설명한다. | 생성형 워크플로도 포함하지만 여기서는 비생성 패딩만 참고한다. ComfyUI 의존, MIT. |
| [Gimp change_aspect_ratio](https://github.com/origamifreak2/Gimp-Plugins/blob/main/change_aspect_ratio/change_aspect_ratio.py) | 소스에서 목표 비율에 따른 캔버스 크기, 배경 스케일, 중앙 위치 계산과 블러 배경을 확인할 수 있다. | GIMP `gimpfu` 플러그인으로 CLI 재사용은 별도 작업; 파일 등록부에 Apache 2 표기. 호환성과 전체 라이선스 조건은 사용 전 확인한다. |
| [resize-image-with-padding](https://github.com/aleskl/resize-image-with-padding) | ImageMagick의 resize, center, extent를 이용한 고정 크기 단색 패딩 예제. 갤러리 방식의 기하 계산 참고. | 블러·유리 없음. 확인한 저장소에서 명시 라이선스를 찾지 못해 코드를 복제하지 않는다. |
| [Batchroom](https://github.com/ekinarca/batchroom) | 레시피 기반 배치, contain/pad/cover와 출력 프리셋, 기록 방식의 참고 사례. | 유리 확장 기능을 확인하지 못했다. 저장소는 MIT와 별도 Pro 라이선스가 공존하므로 사용할 구성요소를 확인한다. 서버·AI는 이번 범위 밖이다. |
| [liquid-glass-canvas](https://github.com/Whynotmetoo/liquid-glass-canvas) | 캔버스를 WebGL 텍스처로 사용해 변위·색조·광택을 적용한다. 정적 이미지 캔버스에 적용하는 경로를 검토할 만하다. | MIT 표시. 블러는 제공하지 않으며 DOM 전체에는 적용되지 않는다. 출력 합성과 toBlob, macOS 실행은 미검증. CORS 제약 존재. |

셰이더 저장소는 기존 ybouane 사례와 위 canvas 사례 두 개만 검토했다. MIT/Apache 코드를 실제 복사할 경우 해당 고지·라이선스를 보존하고, 각 프로젝트의 예제 이미지와 의존성은 별도 권리를 확인한다. 위 사례는 기능의 존재를 보여 줄 뿐, 이 프로젝트의 90% 원본 보호나 Brave 출력 요구를 충족한다고 증명하지 않는다.
