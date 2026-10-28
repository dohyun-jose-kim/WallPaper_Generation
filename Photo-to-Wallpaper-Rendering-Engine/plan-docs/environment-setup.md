# 초기 환경 설정 — v0.0.1

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
git switch -c chore/environment-and-branching
git add README.md CHANGELOG.md Photo-to-Wallpaper-Rendering-Engine/plan-docs/environment-setup.md
git diff --cached
git commit -m "chore: document environment and branching workflow"
git push -u origin chore/environment-and-branching
gh pr create --base main --title "Document environment and branching workflow" --body "Update verified local environment status and define short-lived branches with squash merges. Remote visibility and tag verification remain a manual check."
```

GitHub visibility는 PRIVATE여야 하며 원격 main 및 v0.0.1의 peeled commit은 b7d54f6과 일치해야 합니다. 원격 태그가 없으면 `git push origin v0.0.1`로 업로드합니다. 원격 상태가 예상과 다르면 덮어쓰지 않고 먼저 이력을 확인합니다.

## 브랜치 정책

루트 README의 브랜치 작업 방식을 따릅니다. main은 검증된 결과를 유지하고 feat/fix/chore/docs 작업 브랜치에서 PR을 생성해 squash merge합니다. develop 브랜치는 두지 않습니다. GitHub 보호 규칙은 아직 설정하지 않았습니다. 기존 v0.0.1 태그는 이동하지 않습니다. 공개 전환은 별도 작업입니다.
