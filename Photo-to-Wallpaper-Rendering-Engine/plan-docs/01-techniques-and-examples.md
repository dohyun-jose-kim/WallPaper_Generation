# 효과 원리와 예시

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
