# Changelog

## Unreleased

## 0.0.2 — 2026-11-11

- Reviewed the English README guides against the CLI, added the ASCII architecture, and documented source setup, local installation, preset sizes, current UI limitations, and checks available without private comparison assets.
- Aligned the Rust executable, Python engine and local bundle version to 0.0.2. No rendering features were added. Publication tags the final dev-to-main merge commit as v0.0.2; v0.0.1 is preserved.

- Implemented WALL-E for macOS ARM64: Rust CLI, independent four-style engine, variable target geometry, input/privacy safeguards, transactional naming/resume, resource/browser supervision, atomic publication and sanitized logs.
- Added pinned developer tooling, local distribution build, offline selected-prefix installer, validated upgrades, rollback and owned-file uninstall. Verified baseline equality, CLI failure paths and installation lifecycle. No release/tag or main merge.
- Comparison closeout merged through PR #3. Pipeline integration completed through PR #6; Linux/Windows follow-ups are issues #4/#5. See docs/PROJECT_STATUS.md for current status; earlier dated entries below describe their historical checkpoints.


- Completed 54 comparison cases; repaired 11 positive-rating report links without modifying images or run records. Selected S1 Blur, S1 Gallery, D3 Frosted, S2 Gradient. Pipeline work follows on one branch; branch cleanup and releases deferred.

- 2026-11-11: Prepared the two selected photos as clean RGB PNG copies. Added reusable orientation, color conversion, proportional resize, PNG export and validation code. Nine tests passed. Three runs gave identical outputs. Original file hashes are unchanged. The 54 wallpaper cases remain planned.

- 2026-11-11: ARM64 Python 3.12.14 환경과 Python 런타임·빌드 해시 잠금, npm 잠금 및 Chromium 설치 완료. 고정 리비전의 웹 렌더러 필수 소스·라이선스 확인, 소스 해시 검증, 번들링과 Chromium/Brave WebGL 초기화·합성 픽셀 캡처 점검 통과. 실제 사진 처리·54개 비교 렌더링은 아직 시작하지 않음.

- 2026-11-11: Build and Compare 0.0.1의 54개 케이스, 공통 전처리·메타데이터 검증, 다섯 렌더러 절차, 자원 제한과 HTML 비교 보고서 계약을 문서화. 이전 범위를 과거 기록으로 표시하고 향후 로컬 AI 연구를 출처 기반으로 재구성. 구현·설치·렌더링 결과는 아직 없음.

- 2026-11-11: 작업 PR의 병합 정책을 squash merge에서 merge commit으로 변경. 병합 완료 후 작업 브랜치는 로컬·원격에서 삭제하고 개별 커밋과 병합 이력은 보존. main과 dev는 유지.

- 2026-11-10: 동적 3개·정적 2개 렌더링 후보 선정, QuartzCore 역공학 근거와 한계, 공개 사용 신호, 정적 프레임 저장 검증 계획을 조사 문서에 기록.

- 여백 확장 방식 조사와 정적 HTML 보고서 0.0.1, 2단계 비교 초안을 추가합니다.

- 환경 설정 상태 문서를 실제 로컬 Git 상태에 맞게 정정.
- main(안정 버전), dev(개발 통합), 작업 브랜치 전략 추가. 당시 작업 PR은 squash merge, 릴리스 PR은 merge commit으로 정했으며 작업 PR 정책은 위 2026-11-11 기록으로 변경.

## 0.0.1 — 초기 환경 설정

- 기존 폴더 구조를 유지하고 환경 안내와 계획 문서 추가.
- 로컬 사진, 결과물, ZIP, 가상환경 및 비밀 파일의 Git 제외 규칙 추가.
- uv로 Python 가상환경 생성. 렌더링 패키지 설치 없음.
- 초기 커밋 b7d54f6과 annotated tag v0.0.1 생성.
