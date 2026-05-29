# Project Plan

> 프로젝트: **주식 관심종목 (Stock Watch)**
> 최종 수정일: 2026-05-29

---

## 1. 프로젝트 개요

한국 주식시장(KRX) 전용 인터랙티브 터미널 앱. 종목명 검색 기반 관심종목 관리와
실시간 감시(자동 갱신) 기능을 제공한다.

- **기술 스택**: Python 3.11+, FinanceDataReader, rich
- **실행**: `run.bat` / `python app\main.py`
- **배포**: PyInstaller 단일 EXE 가능

---

## 2. 마일스톤 (Milestones)

| 단계 | 내용 | 상태 |
| ---- | ---- | ---- |
| M1 | 기본 CLI(검색/추가/삭제/수정/조회) + JSON 저장 | ✅ 완료 |
| M2 | 인터랙티브 TUI 전환 (메뉴, 검색→선택, 감시) — rich 도입 | ✅ 완료 |
| M3 | 한국시장 전환: 데이터 소스 FinanceDataReader, 종목명 표시, 원화/색상 관례 | ✅ 완료 |
| M4 | 감시 갱신 주기 설정 기능 (`settings.json` + 설정 메뉴) | ✅ 완료 |
| M5 | 문서화 (도메인 정의서/PRD/사용자 시나리오/와이어프레임/플랜) | ✅ 완료 |
| M6 | 검색 보완(영문명 별칭/코드 검색), 가격 알림, CSV export | ⏳ 예정 |
| M7 | PyInstaller EXE 빌드 및 배포 패키징 | ⏳ 예정 |

> M1~M2는 초기 yfinance 기반으로 구현 후, M3에서 한국시장 요구에 맞춰
> FinanceDataReader로 전면 교체했다.

---

## 3. 작업 분해 (WBS)

### 3.1 데이터 계층 (`app/stock_service.py`)
- [x] KRX 종목 목록 로드 + 세션/디스크(당일) 캐시
- [x] 종목명 부분일치 검색 + 정렬(완전>접두>부분), 최대 20건
- [x] 코드별 시세 조회(현재가/등락률/고가/저가), 오류 정규화
- [ ] 영문 등록 종목 한글 별칭 매핑 (M6)

### 3.2 저장 계층 (`app/storage.py`, `app/settings.py`)
- [x] 관심종목 (코드+종목명) JSON 저장/로드, 중복 방지, 레거시 호환
- [x] 설정(감시 주기) JSON 저장/로드, 범위 클램핑, 기본값 복구

### 3.3 표현 계층 (`app/tui.py`, `app/utils.py`)
- [x] 메인 메뉴 루프 / 화면 렌더링
- [x] 추가/수정/삭제/감시/새로고침/설정/종료 액션
- [x] rich 테이블(종목명 우선), 원화 콤마, 상승=빨강/하락=파랑
- [x] 감시 모드 자동 갱신 + Ctrl+C 복귀

### 3.4 진입점/실행 (`app/main.py`, `run.bat`)
- [x] UTF-8 출력 강제(cp949 대응), 의존성 누락 안내
- [x] Windows 런처 배치

### 3.5 문서/배포
- [x] README (한글)
- [x] docs/ (도메인 정의서, PRD, 시나리오, 와이어프레임, 플랜)
- [ ] EXE 빌드/배포 가이드 검증 (M7)

---

## 4. 일정 (Timeline, 개략)

| 기간 | 작업 |
| ---- | ---- |
| Day 1 | M1 기본 CLI + 저장 |
| Day 1 | M2 TUI 전환 (rich) |
| Day 1 | M3 한국시장 전환 (FinanceDataReader) |
| Day 1 | M4 설정 기능 + GitHub push |
| Day 1 | M5 문서화 |
| 추후 | M6 기능 확장 / M7 배포 |

> 본 프로젝트는 단기 집중 개발로 M1~M5를 완료했다.

---

## 5. 산출물 (Deliverables)

```
stock_viewer_nerdy/
├── run.bat
├── requirements.txt          # finance-datareader, rich
├── README.md
├── app/                      # main, tui, stock_service, storage, settings, utils
├── data/                     # watchlist.json, settings.json, krx_listing.csv(캐시)
└── docs/                     # 본 문서 5종
```

---

## 6. 리스크 및 대응 (Risks)

| 리스크 | 영향 | 대응 |
| ------ | ---- | ---- |
| 시세가 일봉(EOD) 지연 데이터 | 감시 모드가 초 단위로 안 바뀜 | 한계 명시, 필요 시 실시간 소스 보강(M6) |
| 영문 등록 종목 한글 검색 불가 | 일부 검색 실패 | 별칭 매핑 / 코드 검색 지원(M6) |
| KRX 목록 다운로드 실패/지연 | 검색 불가 | 당일 로컬 CSV 캐시 활용, 오류 메시지 |
| Windows 콘솔 인코딩(cp949) | 한글/박스 깨짐 | stdout UTF-8 강제 설정 |
| 외부 라이브러리 API 변경 | 파싱 실패 | 컬럼 존재 여부 방어 처리, 오류 정규화 |

---

## 7. 완료 정의 (Definition of Done)

- 종목명 검색→추가→감시까지 한 화면에서 동작한다.
- 관심종목/설정이 재실행 후에도 유지된다.
- 네트워크/입력 오류 시 크래시 없이 안내 메시지를 출력한다.
- 핵심 흐름(추가/수정/삭제/감시/설정)이 실제 데이터로 검증되었다.
- 문서(docs/) 5종이 구현 사항과 일치한다.

---

## 8. 다음 단계 (Next Steps)

1. M6: 영문명 별칭/코드 검색, 가격 알림, CSV export
2. M7: PyInstaller EXE 빌드 검증 및 배포 패키지 작성
3. (선택) 등락 추세 미니 차트, 관심종목 그룹 분리
