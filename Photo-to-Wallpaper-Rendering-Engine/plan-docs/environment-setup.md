# 초기 환경 설정 계획 — v0.0.1

## 범위

현재 작업 폴더를 저장소 루트로 사용합니다. 기존 파일과 폴더를 유지하며 렌더링 구현, 사진 선정, 패키지 설치는 수행하지 않습니다. 보안 범위는 .gitignore 설정입니다.

## 완료한 로컬 설정

- uv venv .venv: CPython 3.9.6, uv 0.12.11.
- README, CHANGELOG, .gitignore와 빈 폴더 유지 파일 추가.
- 원본 data, results 내용, ZIP, 환경과 캐시, 비밀 파일 제외. 기존 시안 4장은 추적 대상.

## 남은 Git 설정

1. main 브랜치로 Git 초기화.
2. 추적 목록과 제외 규칙 확인 후 `chore: initialize project environment` 커밋 생성.
3. annotated tag v0.0.1 생성. 이후 태그는 이동하지 않음.
4. gh 인증 복구 후 dohyun-jose-kim/WallPaper_Generation 존재 여부 확인.
5. 없으면 비공개 생성하고 origin 연결. 기존 저장소가 있으면 이력과 공개 여부 확인 후 연결하며 강제 push 금지.
6. main과 v0.0.1 push 후 원격 일치와 비공개 상태 확인.

## 실행 상태

작업 공간에서 .git 생성이 권한 제한으로 차단되었습니다. GitHub CLI 인증도 유효하지 않아 저장소 생성, 커밋, 태그, push는 미완료입니다. 사용자 터미널에서 나머지 단계를 수행해야 합니다.

## 검증

가상환경 Python 실행과 경로, 제외 규칙, Markdown 상대 링크를 확인합니다. Git 설정 후 작업 트리가 깨끗한지, 태그가 완료 커밋을 가리키는지 확인합니다. 공개 전환은 별도 작업입니다.
