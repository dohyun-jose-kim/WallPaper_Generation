# 작업 인수인계 — Photo-to-Wallpaper

작성일: 2026-10-28

## 이 문서의 목적

사용자가 프로젝트 전체를 다른 위치로 옮긴 뒤 새 작업 공간에서 작업을 이어가기 위한 임시 인수인계 문서다. 이 파일과 같은 위치의 `README.md`에 상세 기획이 있다. 다음 작업자는 먼저 두 문서를 읽는다.

## 사용자 요구사항

- 세로·가로·정방형 사진의 주요 피사체, 구도, 분위기를 최대한 보존하면서 Brave 웹페이지/Hero 배경용 이미지를 만든다.
- 남는 공간을 의도적으로 디자인하고, 사진마다 일관된 규칙을 적용한다.
- A: Liquid Glass, B: 원본 기반 블러, C: 갤러리 여백, D: 생성형 확장을 비교하되 A안을 우선 실험한다.
- 시각적 결과를 먼저 비교한 뒤 규칙과 기술 스택을 확정한다.
- 최종적으로 Apple Silicon M5에서 실행 가능한 로컬 CLI와 Bash 일괄 처리를 지향한다.
- 초기 출력은 1920×1080이다. 사진 점유율과 안전 영역, 실제 배경 표시에서의 크롭을 검증한다.
- 사용자는 data의 JPG 전체를 읽을 필요가 없다고 명시했다. 실험 시 필요한 대표 사진만 확인한다.

## 현재까지 확인한 상태

- 프로젝트는 기획 및 시안 단계이며 구현 코드는 없다.
- 기존 문서는 `README.md` 하나였고, 전체 내용을 읽었다.
- 기존 시안 JPG 4장은 아직 시각적으로 검토하지 않았다. data의 사진도 아직 열어보지 않았다.
- A 시안은 Liquid Glass 지향의 합성이며 실제 Apple 시스템 렌더러 구현이 아니다.
- D 시안은 반사·변형을 이용한 개념 시안이며 실제 생성형 아웃페인팅 결과가 아니다.
- 이동 전 프로젝트 전체 크기는 약 173MB였다.
- 이동 전 프로젝트는 Git 저장소가 아니었으며 GitHub 연결도 수행하지 않았다.
- 이 인수인계 문서 외에 파일 이동, 구조 변경, 구현, 의존성 설치는 하지 않았다.

## 사용자와 합의된 이동 방식

사용자가 **data 폴더를 포함한 현재 작업 폴더 전체를 직접 이동**한다. 에이전트는 이동하지 않는다.

이동 전 작업 공간:

```text
/Users/dhk/01_Projects/03_experiments/2026_WallPaper_Generation
```

이동 대상 상위 경로:

```text
/Users/dhk/01_Projects/02_personal/github_projects/01_Active
```

권장 새 폴더 이름은 `photo-to-wallpaper`이다. 실제 이름과 이동 완료 여부는 새 세션에서 확인한다. 대상에는 확인 당시 `WebSite/`만 있어 이름 충돌이 없었다.

전체 폴더를 그대로 옮긴 경우 예상 구조:

```text
01_Active/
├── WebSite/
└── photo-to-wallpaper/
    ├── Photo-to-Wallpaper-Rendering-Engine/
    │   ├── README.md
    │   ├── readme-tmp.md
    │   └── 시안 JPG 4장
    ├── Photo-to-Wallpaper-Rendering-Engine.zip
    └── data/
```

전체 이동만으로 README의 상대경로 이미지 링크는 유지된다. 이동 전 세션은 대상 위치에 쓰기 권한이 없으므로 사용자가 새 경로를 작업 공간으로 다시 열어야 한다.

## 제안한 저장소 구조 — 아직 적용하지 않음

새 프로젝트 폴더 자체를 Git 저장소 루트로 사용한다. 다음 구조는 제안이며, 빈 코드 파일을 미리 만들 필요는 없다.

```text
photo-to-wallpaper/
├── README.md                       # 소개 및 실행 방법
├── .gitignore
├── pyproject.toml                  # Python 채택 시 생성
├── docs/
│   ├── design-brief.md             # 기존 상세 README 이동
│   ├── research.md                 # 조사 근거와 구현 후보
│   └── decisions.md                # 시각 규칙과 결정 이유
├── references/
│   └── concepts/                  # 기존 A/B/C/D 시안
├── data/                          # Git 제외
│   ├── originals/
│   └── samples/
├── presets/                       # 효과별 재현 가능한 설정
├── src/
│   └── photo_to_wallpaper/
│       ├── cli.py
│       ├── pipeline.py
│       ├── layout.py
│       └── styles/
├── scripts/                       # 일괄 처리 및 비교판 생성
├── experiments/
│   └── 001-style-comparison/
│       ├── README.md
│       └── manifest.yaml
├── outputs/                       # Git 제외: 결과, 비교판, 로그
└── tests/                         # 구현에 필요한 검증
```

정리 시 유의사항:

- 기존 README를 `docs/design-brief.md`로, 시안을 `references/concepts/`로 옮기면 이미지 링크도 수정한다.
- data 내부 실제 구조를 확인한 뒤 정리하며 원본을 보존한다.
- 코드, 프리셋, 실험 기록은 Git에 포함하고 원본 사진과 대량 결과물은 제외하는 방안을 제안했다.
- 기존 시안 4장은 설명 자료로 Git에 포함하는 방안을 제안했다.
- ZIP은 저장소 밖에 보관하거나 Git에서 제외하는 방안을 제안했다. 삭제하지 않았다.
- GitHub 저장소명, 공개 여부, 계정/조직은 아직 정하지 않았다. 원격 저장소 생성이나 업로드도 하지 않았다.

## 제안한 다음 실행 순서

1. 새 위치와 실제 파일 구성을 확인하고 프로젝트 문서 및 시안 4장을 검토한다.
2. data에서 세로·가로·정방형, 밝고 어두운 장면을 섞어 대표 사진 약 6장을 선정한다.
3. 유리 효과를 블러, 굴절, 경계 하이라이트, 색조·투명도, 원본과 배경의 연결 방식으로 나누어 조사한다.
4. 사진마다 A안 3종(은은한 유리, 경계 강조, 굴절 강조), B 블러, C 갤러리를 렌더링하는 작은 프로토타입을 만든다.
5. 6장×5종의 1920×1080 결과와 비교판을 생성한다. 실제 생성형 D안은 별도 실험으로 제안했다.
6. 사용자 선호를 반영해 사진 점유율, 배경 밝기, 블러 반경, 굴절 강도, 경계 폭을 수치화한다.
7. 다른 사진으로 일반화 여부를 확인한 뒤 CLI, 폴더 처리, 검증, 로그를 구현한다.
8. 실제 처리 시간과 메모리를 측정한 후 GPU 가속 필요성을 판단한다.

첫 실험의 제안 완료 기준은 **대표 사진 비교판과 재현 가능한 실험 스크립트**다. 이 계획은 아직 실행하지 않았으며 기술 스택도 확정하지 않았다.

## 초기 검색에서 확인한 공식 자료

2026-10-28에 웹 검색으로 아래 자료를 확인했다. 실제 API와 로컬 설치 가능 여부를 검증한 단계는 아니다.

- ImageMagick 이미지 합성 및 변위 기반 유리·렌즈 효과: https://usage.imagemagick.org/compose/
- ImageMagick 이미지 맵 효과: https://usage.imagemagick.org/mapping/
- Apple Core Image 왜곡 필터: https://developer.apple.com/documentation/coreimage/distortion-filters
- libvips 리사이즈 API: https://www.libvips.org/API/8.17/method.Image.resize.html

ImageMagick과 Core Image는 초기 구현 후보로 언급했다. Core Image는 Apple 전용 프레임워크이므로 오픈소스 중심의 선호와 구분해서 검토한다. 특정 모델, GPU 성능, 생성형 품질은 아직 검증하지 않았다.
