# Photo-to-Wallpaper

사진의 구도와 분위기를 보존하면서 Brave 배경용 이미지를 만드는 프로젝트입니다. 현재는 환경 설정 단계이며 렌더링 코드는 없습니다.

- [상세 기획 및 시안](Photo-to-Wallpaper-Rendering-Engine/README.md)
- [인수인계](Photo-to-Wallpaper-Rendering-Engine/readme-tmp.md)
- [환경 설정 계획](Photo-to-Wallpaper-Rendering-Engine/plan-docs/environment-setup.md)
- [변경 기록](CHANGELOG.md)

## 폴더

- `Photo-to-Wallpaper-Rendering-Engine/code/`: 향후 구현 코드
- `Photo-to-Wallpaper-Rendering-Engine/plan-docs/`: 계획 문서
- `Photo-to-Wallpaper-Rendering-Engine/results/`: 생성 결과, Git 제외
- `data/`: 원본 사진, Git 제외

## Python 환경

```sh
uv venv .venv
source .venv/bin/activate
python --version
```

초기 환경: uv 0.12.11, CPython 3.9.6. 렌더링 패키지는 설치하지 않았습니다. uv 기본 캐시 경로에 쓰기 권한이 없으면 `UV_CACHE_DIR=/private/tmp/wallpaper-uv-cache uv venv .venv`를 사용할 수 있습니다.

## Git과 버전

기본 브랜치는 `main`, 초기 환경 설정 태그는 `v0.0.1`을 사용합니다. 후속 버전은 `vMAJOR.MINOR.PATCH` 형식이며 기존 태그를 이동하지 않습니다.

GitHub 대상은 `dohyun-jose-kim/WallPaper_Generation` 비공개 저장소입니다. 로컬 origin 연결과 main 추적 설정은 완료되었습니다. 원격의 비공개 상태 및 태그는 사용자 터미널에서 최종 확인해야 합니다. 공개 전환은 별도 작업입니다.

원본 사진, 결과물, ZIP, 가상환경, 비밀 파일은 커밋에서 제외합니다. 기존 A/B/C/D 시안은 추적합니다. `.gitignore`는 이미 커밋된 파일을 제거하지 않으므로 커밋 전 `git diff --cached --name-only`로 확인하세요.

## 브랜치 작업 방식

`main`은 검증된 결과를 유지합니다. 작업마다 짧은 브랜치를 만들고 PR을 통해 squash merge합니다. 별도의 `develop` 브랜치는 사용하지 않습니다.

- `feat/<topic>`: 기능 및 렌더링 실험 구현
- `fix/<topic>`: 오류 수정
- `chore/<topic>`: 환경과 도구 설정
- `docs/<topic>`: 문서만 변경

```sh
git switch main
git pull --ff-only
git switch -c feat/style-comparison
# 작업 및 검증 후
git add <변경한-파일>
git diff --cached
git commit -m "feat: add style comparison"
git push -u origin feat/style-comparison
gh pr create --base main
```

PR에는 변경 목적, 검증 결과와 남은 제한을 기록합니다. 충돌 해결과 검증 후 squash merge하고 작업 브랜치를 삭제합니다. merge 후 로컬 main을 fast-forward로 갱신합니다. main 직접 커밋과 강제 push는 사용하지 않습니다. 이 규칙은 작업 관례이며 GitHub 보호 규칙을 설정한 상태는 아닙니다.

버전 태그는 PR이 합쳐진 main의 검증된 커밋에만 생성합니다. 현재 v0.0.1은 초기 환경 커밋이며 이동하지 않습니다. 문서 수정마다 새 버전을 만들지 않고 CHANGELOG의 Unreleased에 기록합니다. 초기 0.x 단계에서는 기능 추가를 minor, 수정 사항을 patch로 구분합니다.
