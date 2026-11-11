# WALL-E — wallpaper engine made by DH-thejose

This project makes Brave background images while preserving the complete source photo. The 54-case comparison is complete. Selected outputs: S1 blurred background, S1 gallery frame, D3 frosted glass, and S2 gradient. The user pipeline is now being implemented; see [project status](docs/PROJECT_STATUS.md), [decisions](docs/DECISIONS.md), and [pipeline design](docs/pipeline-design.md).

- [현재 비교 실행 계획](Photo-to-Wallpaper-Rendering-Engine/plan-docs/build-n-compare-0.0.1/README.md)
- [설치 결과와 구현 준비 상태](Photo-to-Wallpaper-Rendering-Engine/plan-docs/build-n-compare-0.0.1/environment-readiness.md)
- [환경 재설치·점검 방법](Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf/README.md)
- [Image preparation and results](Photo-to-Wallpaper-Rendering-Engine/code/README.md)
- [향후 로컬 AI 아웃페인팅 조사](Photo-to-Wallpaper-Rendering-Engine/plan-docs/reseatch-0.0.1/local-ai-outpainting-research.md)
- [상세 기획 및 시안](Photo-to-Wallpaper-Rendering-Engine/README.md)
- [인수인계](Photo-to-Wallpaper-Rendering-Engine/readme-tmp.md)
- [환경 설정 계획](Photo-to-Wallpaper-Rendering-Engine/plan-docs/environment-setup.md)
- [변경 기록](CHANGELOG.md)

## 폴더

- `Photo-to-Wallpaper-Rendering-Engine/code/`: 비교 실행 코드
- `Photo-to-Wallpaper-Rendering-Engine/plan-docs/`: 계획 문서
- `Photo-to-Wallpaper-Rendering-Engine/results/`: 생성 결과, Git 제외
- `data/`: 원본 사진, Git 제외

## Python 환경

uv 관리 ARM64 Python **3.12.14**와 루트 `.venv`를 사용합니다. Python 런타임·빌드 의존성은 해시 잠금 파일로, Node 의존성은 프로젝트 전용 npm 잠금 파일로 설치했습니다. Miniforge는 사용하지 않습니다. 브라우저 바이너리와 캐시는 프로젝트의 Git 제외 경로에 보관합니다.

```sh
Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf/run.sh python --version
Photo-to-Wallpaper-Rendering-Engine/tool-package-shelf/run.sh uv pip check --python .venv/bin/python
```

기존 CPython 3.9.6 가상환경은 `tool-package-shelf/.cache/venv-before-python312/`에 보관했습니다. 새 환경의 재설치·검증 명령은 위 환경 안내를 따릅니다. 설치 점검 통과는 실제 54개 렌더링 결과나 품질 검증을 뜻하지 않습니다.

## Git과 버전

기본 브랜치는 `main`, 초기 환경 설정 태그는 `v0.0.1`을 사용합니다. 후속 버전은 `vMAJOR.MINOR.PATCH` 형식이며 기존 태그를 이동하지 않습니다.

GitHub 대상은 `dohyun-jose-kim/WallPaper_Generation` 비공개 저장소입니다. 로컬 origin 연결과 main 추적 설정은 완료되었습니다. 원격의 비공개 상태 및 태그는 사용자 터미널에서 최종 확인해야 합니다. 공개 전환은 별도 작업입니다.

원본 사진, 결과물, ZIP, 가상환경, 비밀 파일은 커밋에서 제외합니다. 기존 A/B/C/D 시안은 추적합니다. `.gitignore`는 이미 커밋된 파일을 제거하지 않으므로 커밋 전 `git diff --cached --name-only`로 확인하세요.

## 브랜치 작업 방식

- `main`: 검증된 안정 버전과 릴리스 태그.
- `dev`: 개발 통합 브랜치. 삭제하지 않습니다.
- `feat/*`, `fix/*`, `chore/*`, `docs/*`: 최신 dev에서 분기하는 짧은 작업 브랜치.

```sh
git switch dev
git pull --ff-only
git switch -c feat/style-comparison
# 작업 및 검증 후 커밋
git push -u origin feat/style-comparison
gh pr create --base dev
```

작업 PR은 dev에 merge commit으로 합칩니다. 개별 커밋과 분기·병합 이력을 보존하며 squash/rebase merge는 사용하지 않습니다. PR에는 변경 목적, 검증 결과와 제한을 기록합니다.

현재 작업에서는 브랜치 삭제와 문서 보관을 연기합니다. 브랜치 삭제는 merge commit과 기존 커밋 이력을 삭제하지 않습니다. main과 dev는 유지합니다.

릴리스는 dev → main PR을 검증한 뒤 merge commit으로 합칩니다. 장기 브랜치 간 공통 이력을 보존하기 위해 릴리스 PR에는 squash/rebase merge를 사용하지 않습니다. 릴리스 후 main → dev 동기화 PR도 merge commit으로 합칩니다.

main과 dev에는 직접 커밋하거나 강제 push하지 않습니다. 이 규칙은 작업 관례이며 GitHub 보호 규칙은 아직 설정하지 않았습니다.

태그는 검증된 main 커밋에 생성하고 기존 v0.0.1은 이동하지 않습니다. 문서 변경은 CHANGELOG의 Unreleased에 기록하며 매번 태그를 만들지 않습니다. 초기 0.x에서는 기능 추가를 minor, 수정을 patch로 구분합니다.
