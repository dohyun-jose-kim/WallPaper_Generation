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

GitHub 대상은 `dohyun-jose-kim/WallPaper_Generation` 비공개 저장소입니다. 현재 원격 생성 및 연결은 미완료입니다. 공개 전환은 별도 작업입니다.

원본 사진, 결과물, ZIP, 가상환경, 비밀 파일은 커밋에서 제외합니다. 기존 A/B/C/D 시안은 추적합니다. `.gitignore`는 이미 커밋된 파일을 제거하지 않으므로 커밋 전 `git diff --cached --name-only`로 확인하세요.
