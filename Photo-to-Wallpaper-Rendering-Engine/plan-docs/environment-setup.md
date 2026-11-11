# 초기 환경 설정 — v0.0.1

> 현재 실행 범위(2026-11-11): [Build and Compare 0.0.1](build-n-compare-0.0.1/README.md). 세로·가로 2장, 도구 5개, 총 54개 케이스이며 실패도 유지한다. 아래는 이전 조사/환경 기록이다. 10개·26개 제안, Miniforge 대안 및 이전 실행 순서는 현재 범위에 적용하지 않는다.

## 범위

현재 작업 폴더를 저장소 루트로 사용합니다. 기존 구조를 유지하며 렌더링 구현, 사진 선정, 패키지 설치는 후속 작업입니다. 보안 범위는 .gitignore 설정입니다.

## 확인 완료

- uv 0.12.11과 .venv의 CPython 3.9.6 실행 확인. pip은 설치하지 않았으며 uv 기반 최소 환경을 유지합니다.
- 원본 data, results 내용, ZIP, 가상환경, 비밀 파일의 Git 제외 확인. 기존 시안 4장은 추적합니다.
- main, 캐시된 origin/main, annotated tag v0.0.1은 모두 b7d54f6을 가리킵니다.
- origin은 https://github.com/dohyun-jose-kim/WallPaper_Generation.git 입니다.
- 이번 문서 수정 전 작업 트리는 깨끗했습니다.

## 남은 확인 및 적용

에이전트 환경에서는 GitHub DNS 접근과 .git 쓰기가 제한됩니다. 실시간 원격 확인과 작업 브랜치 생성은 사용자 터미널에서 수행합니다.

```sh
gh repo view --json visibility,url
git ls-remote origin refs/heads/main 'refs/tags/v0.0.1*'
git add README.md CHANGELOG.md Photo-to-Wallpaper-Rendering-Engine/plan-docs/environment-setup.md
git commit -m "docs: adopt dev integration branch"
git push
git push -u origin dev
gh pr create --base dev --head chore/environment-and-branching --fill
```

GitHub visibility는 PRIVATE여야 하며 원격 main 및 v0.0.1의 peeled commit은 b7d54f6과 일치해야 합니다. 원격 태그가 없으면 `git push origin v0.0.1`로 업로드합니다. 원격 상태가 예상과 다르면 덮어쓰지 않고 먼저 이력을 확인합니다.

## 브랜치 정책

루트 README를 따릅니다. 작업 브랜치는 dev에서 분기하고 dev로 PR을 보내 merge commit으로 합칩니다. 작업 PR, dev → main 릴리스 PR, main → dev 동기화 PR 모두 squash/rebase merge를 사용하지 않습니다. 병합 완료를 확인한 작업 브랜치는 로컬과 원격에서 삭제하되, 개별 커밋과 병합 이력은 보존합니다. main과 dev는 유지합니다. 기존 v0.0.1은 이동하지 않습니다. GitHub 보호 규칙과 공개 전환은 이번에 설정하지 않았습니다.

## 진행 상태

사용자 터미널에서 dev와 chore/environment-and-branching 생성, 9c6a29f 커밋과 작업 브랜치 push를 완료했습니다. 현재 문서 수정은 아직 미커밋이며 dev 원격 게시와 dev 대상 PR 생성이 남았습니다.
