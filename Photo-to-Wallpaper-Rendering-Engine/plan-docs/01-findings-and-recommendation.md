# 후보 비교와 추천

> 현재 실행 범위(2026-11-11): [Build and Compare 0.0.1](build-n-compare-0.0.1/README.md). 세로·가로 2장, 도구 5개, 총 54개 케이스이며 실패도 유지한다. 아래는 이전 조사/환경 기록이다. 10개·26개 제안, Miniforge 대안 및 이전 실행 순서는 현재 범위에 적용하지 않는다.

> 2026-11-10 후속 조사: [종합 조사와 최종 후보 5개](03-renderer-shortlist-research.md)에서 동적 3개·정적 2개를 선정했다. 아래는 2026-10-28의 초기 조사 기록이며, 현재 후보 선정과 동적 프레임 저장 범위는 후속 문서를 따른다.

조사일: 2026-10-28. 기능과 라이선스는 연결된 공식 자료에 근거하며 복잡도와 추천은 조사자의 추론이다. 설치·실행·품질·성능은 미검증이다. 상세 효과와 코드, 셰이더 및 캡처 근거는 [구현 원리](01-techniques-and-examples.md)에 있다.

| 후보 | 제공 / 직접 구현 | 저장·배치 / macOS 조건 | 라이선스·유지보수·복잡도 |
|---|---|---|---|
| Pillow + NumPy | 블러·크기·마스크 합성 / 변위 맵·보간·유리 레이어 | JPEG/PNG 저장, Python CLI를 직접 작성. Pillow [설치](https://pillow.readthedocs.io/en/stable/installation/basic-installation.html), [ARM64 배포 파일](https://pypi.org/project/pillow/); [NumPy 설치](https://numpy.org/install/)에서 환경별 조건 확인 | Pillow [PIL 라이선스](https://github.com/python-pillow/Pillow/blob/main/LICENSE), NumPy [BSD-3-Clause](https://github.com/numpy/numpy/blob/main/LICENSE.txt). 두 프로젝트 공식 저장소에서 릴리스 확인 가능. 중간: 수학을 직접 조정하기 쉬우나 변위 보간 구현 필요 |
| libvips / pyvips | 블러·좌표 재매핑·합성 / 변위 맵과 레이어 설계 | JPEG/PNG, `vips` CLI 및 Python 배치. [macOS 설치](https://www.libvips.org/install.html); [pyvips binary](https://libvips.github.io/pyvips/README.html)는 macOS ARM을 명시, 별도 libvips도 가능 | [libvips LGPL-2.1-or-later](https://www.libvips.org/), [pyvips MIT](https://github.com/libvips/pyvips/blob/master/LICENSE). 공식 저장소 릴리스 활동 확인 가능. 중상: 지연 연산과 좌표 이미지 학습 필요 |
| ImageMagick | 블러·virtual pixel·변위 합성 / 유리 맵과 프리셋 설계 | `magick` CLI 및 스크립트 배치, JPEG/PNG. [macOS Homebrew](https://imagemagick.org/download/); Apple Silicon 설치는 환경별 확인 | [ImageMagick 라이선스](https://imagemagick.org/license/), 배포 시 고지 확인. 공식 다운로드에 안정 릴리스 제공. 중상: 긴 명령과 합성 순서 관리 |
| OpenCV | GaussianBlur·remap·마스크 / 유리 맵·색상 및 합성 설계 | `imwrite`, Python CLI 직접 작성. [macOS 설치](https://opencv.org/get-started/); ARM wheel 환경별 확인 | [4.5 이상 Apache-2.0](https://opencv.org/license/). 공식 프로젝트 릴리스 제공. 중상: BGR·자료형·알파 처리에 주의 |
| 웹 셰이더 | WebGL 굴절·광택 / 배경 캡처·정적 출력·배치 | 캔버스 인코딩 또는 캡처 필요. macOS 브라우저/WebGL 조건에 의존, ARM 환경 미검증 | [예제 저장소 MIT](https://github.com/ybouane/liquidglass). 프로젝트별 유지보수와 에셋 권리 확인. 높음: 브라우저 렌더와 캡처 경로 필요 |
| Core Image / Metal | Apple 플랫폼의 필터·커스텀 GPU 처리 / 효과·CLI·인코딩 구현 | [Core Image](https://developer.apple.com/documentation/coreimage), [Metal](https://developer.apple.com/metal/) 기반 macOS 개발 환경 필요. Apple 전용 비교 자료; 실제 ARM 및 배치 미검증 | Apple SDK 사용 조건 별도 확인; 오픈소스 후보로 취급하지 않음. 높음: Swift/Metal 및 플랫폼 종속성 |

라이브러리 라이선스는 이미지나 데모 에셋에 자동으로 적용되지 않는다. 외부 이미지는 복제하지 않았다. 배포 시 의존성·코덱의 별도 라이선스와 고지, LGPL 연결·재배포 조건을 확인한다. 유지보수 평가는 공개 문서와 릴리스 존재에 근거한 정성적 판단이며 장기 지원 보장은 아니다.

## 결정

**우선 실험: Pillow + NumPy.** 원본 보호와 레이어를 Python에서 명시적으로 제어하고 수치를 비교하기 쉬울 것으로 추론한다. 다만 변위 보간은 추가 작업이며 성능상 우위는 주장하지 않는다. **대안: libvips + pyvips.** 재매핑과 배치에 필요한 연산이 있어 첫 방식이 느리거나 구현이 복잡할 때 비교한다. 공식 자료의 효율성 설명은 이 프로젝트의 M5 측정 결과가 아니다.

2단계에서는 세로·가로 각 1장에 5개 스타일을 적용해 10개를 비교하고 원본 영역의 비율·픽셀 변화, EXIF 방향·색상 프로파일, 경계 이음새, 블러 반경·변위·색조, JPEG/PNG와 Brave 표시, 재현성, 시간·최대 메모리를 측정한다. 원본을 90% 이내로 맞출 때 정수 반올림과 업스케일 허용 여부도 정한다. 평가 후 대표 6장으로 확장한다. Python 버전·라이브러리·수치·CLI는 이 실험 이후 확정한다.

## 환경과 추가 사례 반영

[Miniforge](https://github.com/conda-forge/miniforge)는 macOS 11 이상 Apple Silicon용 arm64 설치본을 제공하고, conda-forge는 [Pillow](https://anaconda.org/conda-forge/Pillow)와 [pyvips](https://anaconda.org/channels/conda-forge/packages/pyvips/overview)의 macOS-arm64 패키지를 표시한다. 현재 프로젝트의 uv 환경을 우선 유지하되 네이티브 의존성 관리가 필요하면 별도 Miniforge 환경을 비교한다. 어느 쪽도 이 작업에서 설치·검증하지 않았으며 Python과 패키지 버전은 고정하지 않았다.

추가 GitHub 조사에서 [ImageOps PadOut](https://github.com/MajoorWaldi/ComfyUI-Majoor-ImageOps)과 [AusBoss Load Image + Pad](https://github.com/ausboss/ComfyUI-AusBoss)는 가장자리·반사·블러와 마스크 설계의 직접적인 참고 사례다. [canvas 기반 유리](https://github.com/Whynotmetoo/liquid-glass-canvas)는 정적 출력 경로를 확인할 두 번째 셰이더 사례다. 이들은 실행·적합성 미검증이며 도구 선택을 확정하지 않는다. 각 사례의 제한과 라이선스는 [추가 사례 조사](01-techniques-and-examples.md#추가-오픈소스-사례-조사)에 기록했다.
