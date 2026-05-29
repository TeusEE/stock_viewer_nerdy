# 스타일 가이드 — Bloomberg Terminal Style

> 제품: **주식 관심종목 (Stock Watch)** — 터미널 TUI
> 최종 수정일: 2026-05-30
> 목적: Bloomberg Terminal의 시각 언어를 `rich` 기반 TUI에 이식하기 위한 디자인 표준

---

## 1. 설계 철학

Bloomberg Terminal은 반세기 넘게 금융 전문가들이 신뢰하는 인터페이스다.
그 핵심 원칙은 다음 세 가지다.

| 원칙 | 설명 |
|------|------|
| **정보 밀도** | 화면 낭비 없이 최대한 많은 데이터를 배치 |
| **즉각적 판독** | 색상·위치만으로 데이터 의미를 0.5초 안에 파악 |
| **일관된 신호** | 동일한 색상은 항상 동일한 의미를 가짐 |

이 가이드는 위 원칙을 한국 주식 시장 관례(상승=빨강, 하락=파랑)와 절충하여
`rich` 라이브러리로 구현 가능한 수준으로 정의한다.

---

## 2. 색상 팔레트

### 2-1. 기본 배경

Bloomberg Terminal은 **순수 검정** 배경을 사용한다.
터미널 에뮬레이터의 기본 배경을 검정(#000000)으로 설정하는 것을 권장한다.
`rich`는 배경을 직접 제어하지 않으므로 터미널 설정에 의존한다.

### 2-2. 전경색 팔레트

```
Bloomberg 주황  #FF8C00  rgb(255,140,0)   ← 주 강조색. 타이틀·헤더·구분선
Bloomberg 앰버  #FFA500  rgb(255,165,0)   ← 보조 강조색. 컬럼 레이블
흰색           #FFFFFF  white             ← 일반 데이터
밝은 회색       #AAAAAA  rgb(170,170,170) ← 보조 정보 (코드, URL)
어두운 회색     #555555  dim              ← 비활성 요소
노랑           #FFFF00  yellow            ← 시스템 메시지 (INFO)
빨강           #FF4444  bold red          ← 상승(한국 관례) / 오류
파랑           #4499FF  bold blue         ← 하락(한국 관례)
```

### 2-3. 역할별 색상 매핑

| 역할 | Rich 스타일 문자열 | 비고 |
|------|------------------|------|
| 앱 타이틀 | `bold rgb(255,140,0)` | 패널 제목, 최상위 강조 |
| 패널 테두리 | `rgb(255,140,0)` | Panel border_style |
| 섹션 구분선 | `rgb(255,140,0)` | Rule style |
| 테이블 헤더 | `bold rgb(255,165,0)` | header_style |
| 테이블 제목 | `bold rgb(255,140,0)` | title_style |
| 종목명 | `bold white` | 식별 가능한 핵심 정보 |
| 종목 코드 | `rgb(170,170,170)` | 보조 식별자 |
| 가격 데이터 | `white` | 현재가·고가·저가 |
| 상승 등락률 | `bold red` | 한국 시장 관례 유지 |
| 하락 등락률 | `bold rgb(68,153,255)` | 한국 시장 관례 유지 |
| 보합/데이터 없음 | `dim` | N/A, 0.00% |
| INFO 메시지 | `rgb(255,255,0)` | 시스템 안내 |
| ERROR 메시지 | `bold red` | 오류·경고 |
| 뉴스 제목 | `bold white` | 가독성 우선 |
| 뉴스 출처 | `rgb(255,165,0)` | 주황으로 Bloomberg 느낌 |
| 뉴스 시간 | `dim` | 보조 메타데이터 |
| 뉴스 URL | `rgb(100,100,100)` | 최소 존재감 |
| 메뉴 키 | `bold rgb(255,140,0)` | 키 글자만 강조 |
| 메뉴 설명 | `dim` | 나머지 텍스트 |
| 상태바 | `dim` | 하단 고정 안내 |

---

## 3. 타이포그래피

### 3-1. 텍스트 계층

Bloomberg Terminal은 다음 네 가지 텍스트 계층을 사용한다.

```
Level 1 — HEADER     : 대문자, 주황색, bold     → 화면 제목·섹션 이름
Level 2 — DATA LABEL : 주황/앰버, 일반 굵기     → 컬럼 헤더
Level 3 — DATA       : 흰색                     → 실제 수치·텍스트
Level 4 — METADATA   : 회색/dim                  → 코드, URL, 경과 시간
```

### 3-2. 컬럼 헤더 표기

Bloomberg 스타일은 영문 **ALL CAPS** 약어를 선호한다.
한국어 인터페이스와의 절충안으로 한글 레이블을 유지하되 의미를 압축한다.

| 현재 레이블 | Bloomberg 스타일 제안 |
|------------|----------------------|
| `종목명` | `종 목` |
| `코드` | `CODE` |
| `현재가` | `PRICE` |
| `등락률` | `CHG%` |
| `고가` | `HIGH` |
| `저가` | `LOW` |

> **참고**: 영문 레이블로 전환 시 Bloomberg 느낌이 강해지지만,
> 한국어 사용자 친화성이 낮아진다. 프로젝트 목표에 따라 선택한다.

### 3-3. 숫자 포맷

| 항목 | 포맷 | 예시 |
|------|------|------|
| 원화 가격 | 천 단위 콤마, 소수점 없음 | `317,000` |
| 등락률 | 부호 포함, 소수점 2자리, % 단위 | `+5.84%` / `-1.20%` |
| 고가·저가 | 가격과 동일 | `319,000` |

---

## 4. 레이아웃 구조

### 4-1. 화면 구성

```
┌──────────────────────────────────────────────────────────────────┐
│  TITLE BAR  (주황 텍스트, 전체 너비 Panel)                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  WATCHLIST TABLE  (메인 콘텐츠, 주황 헤더)                       │
│                                                                  │
├── 관련 뉴스 ─────────────────────────────────────────────────────┤  ← 감시 모드만
│  NEWS ITEMS                                                      │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  STATUS BAR  (메뉴 키 / 갱신 주기 안내)                          │
└──────────────────────────────────────────────────────────────────┘
```

### 4-2. 정보 우선순위

1. **Primary** — 현재가, 등락률 (가장 크게, 우측 정렬)
2. **Secondary** — 종목명 (bold white)
3. **Tertiary** — 고가, 저가 (white, 좁은 너비)
4. **Auxiliary** — 코드, 인덱스 번호 (dim, 최소 너비)

### 4-3. 여백 규칙

- 테이블 위아래: `rich` 기본값 사용 (패딩 최소화)
- 뉴스 항목 간: 빈 줄 없이 연속 출력 (밀도 우선)
- 뉴스와 URL 사이: 들여쓰기(4칸)로 시각적 계층 표현
- 메뉴와 프롬프트 사이: 빈 줄 1줄

---

## 5. 컴포넌트 스타일 명세

### 5-1. 타이틀 패널

```python
# 메인 화면
Panel(
    "[bold rgb(255,140,0)]주식 관심종목[/bold rgb(255,140,0)]",
    border_style="rgb(255,140,0)",
    expand=False,
)

# 감시 모드
Panel(
    "[bold rgb(255,140,0)]주식 관심종목[/bold rgb(255,140,0)]"
    "  [dim]WATCH MODE[/dim]",
    border_style="rgb(255,140,0)",
    expand=False,
)
```

시각적 결과:
```
╭─────────────────────────────────╮
│ 주식 관심종목  WATCH MODE       │   ← 주황 테두리, 주황 타이틀
╰─────────────────────────────────╯
```

### 5-2. 관심종목 테이블

```python
Table(
    title="WATCHLIST",
    title_style="bold rgb(255,140,0)",
    header_style="bold rgb(255,165,0)",
    border_style="rgb(80,80,80)",       # 어두운 회색 테두리
    show_edge=True,
    expand=False,
)
```

컬럼 정의:

| 컬럼 | justify | style | 너비 |
|------|---------|-------|------|
| `#` | right | `dim` | auto |
| `종목명` (또는 `NAME`) | left | `bold white` | auto |
| `CODE` | left | `rgb(170,170,170)` | auto |
| `PRICE` | right | `white` | auto |
| `CHG%` | right | (동적) | auto |
| `HIGH` | right | `white` | auto |
| `LOW` | right | `white` | auto |

### 5-3. 등락률 색상 (change_text)

```python
def change_text(value) -> Text:
    if value is None:
        return Text("N/A", style="dim")
    number = float(value)
    label = f"{number:+.2f}%"
    if number > 0:
        return Text(label, style="bold red")           # 상승: 한국 관례
    if number < 0:
        return Text(label, style="bold rgb(68,153,255)")  # 하락: 파랑(Bloomberg blue)
    return Text(label, style="dim")                    # 보합
```

### 5-4. 검색 결과 테이블

```python
Table(
    header_style="bold rgb(255,165,0)",
    border_style="rgb(80,80,80)",
    expand=False,
)
# 종목명 컬럼 style: "bold rgb(255,140,0)"  ← 검색 결과 강조
```

### 5-5. 뉴스 구분선 (Rule)

```python
Rule(
    "[bold rgb(255,140,0)]  NEWS  [/bold rgb(255,140,0)]",
    style="rgb(80,80,80)",      # 선 색상: 어두운 회색
    align="left",
)
```

시각적 결과:
```
──  NEWS  ──────────────────────────────────────────────────
```

### 5-6. 뉴스 아이템

```python
line = Text()
line.append(f"  {i}  ", style="rgb(100,100,100)")
line.append(item.title, style="bold white")
line.append("   ")
line.append(item.source, style="rgb(255,165,0)")     # 출처를 주황으로
line.append("  ")
line.append(item.published_at, style="dim")

# URL 라인
console.print(f"    [rgb(100,100,100)]{item.url}[/rgb(100,100,100)]")
```

### 5-7. 메뉴 바

Bloomberg Terminal의 Function Key Bar에서 영감을 받은 스타일.

```
[A] 추가   [E] 수정   [D] 삭제   [W] 감시   [R] 새로고침   [S] 설정   [Q] 종료
```

구현:
```python
menu = Text()
menu.append("[A]", style="bold rgb(255,140,0)")
menu.append(" 추가   ", style="dim")
menu.append("[E]", style="bold rgb(255,140,0)")
menu.append(" 수정   ", style="dim")
# ... (반복)
console.print(menu)
```

### 5-8. 상태바 (감시 모드 하단)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5s REFRESH  |  NEWS IN 3m  |  Ctrl+C → MENU
```

```python
Rule(style="rgb(60,60,60)")   # 얇은 구분선
status = Text()
status.append(f"{n}s REFRESH", style="rgb(255,165,0)")
status.append("  |  ", style="dim")
status.append(f"NEWS IN {m}m", style="rgb(255,165,0)")
status.append("  |  ", style="dim")
status.append("Ctrl+C → MENU", style="dim")
console.print(status)
```

### 5-9. 시스템 메시지

```python
# INFO
console.print("[rgb(255,255,0)][INFO][/rgb(255,255,0)]  삼성전자 추가 완료.")

# ERROR
console.print("[bold red][ERROR][/bold red]  데이터를 불러올 수 없습니다.")

# 뉴스 로딩 중
console.print("[dim]  ⠿ 뉴스 로딩 중...[/dim]")
```

### 5-10. 설정 화면

```
  [1] REFRESH INTERVAL      5s   (1 – 3600)
  [2] NEWS INTERVAL        300s   (60 – 3600)
  [3] MAX NEWS COUNT         5   (1 – 10)

  [0] CANCEL
```

```python
# 항목 행
label = Text()
label.append(f"  [{n}] ", style="bold rgb(255,140,0)")
label.append(f"{name:<22}", style="dim")
label.append(f"{current_value:>5}", style="bold white")
label.append(f"   {hint}", style="dim")
```

---

## 6. 와이어프레임 (Bloomberg 스타일 적용 후)

### 메인 화면

```
╭───────────────────────────────────────────────╮
│ 주식 관심종목                                  │   ← 주황 테두리·텍스트
╰───────────────────────────────────────────────╯

                     WATCHLIST
 ┌───┬──────────┬────────┬─────────┬───────┬─────────┬─────────┐
 │ # │ NAME     │ CODE   │   PRICE │  CHG% │    HIGH │     LOW │  ← 주황 헤더
 ├───┼──────────┼────────┼─────────┼───────┼─────────┼─────────┤
 │ 1 │ 삼성전자 │ 005930 │ 317,000 │+5.84% │ 319,000 │ 305,500 │  ← CHG%: 빨강
 │ 2 │ 카카오   │ 035720 │  41,950 │-1.20% │  44,000 │  40,450 │  ← CHG%: 파랑
 └───┴──────────┴────────┴─────────┴───────┴─────────┴─────────┘

[A] 추가   [E] 수정   [D] 삭제   [W] 감시   [R] 새로고침   [S] 설정   [Q] 종료
선택: _
```

### 감시 모드

```
╭──────────────────────────────────────────────────────╮
│ 주식 관심종목  WATCH MODE                             │
╰──────────────────────────────────────────────────────╯

                     WATCHLIST
 ┌───┬──────────┬────────┬─────────┬───────┬─────────┬─────────┐
 │ # │ NAME     │ CODE   │   PRICE │  CHG% │    HIGH │     LOW │
 ├───┼──────────┼────────┼─────────┼───────┼─────────┼─────────┤
 │ 1 │ 삼성전자 │ 005930 │ 317,000 │+5.84% │ 319,000 │ 305,500 │
 │ 2 │ 카카오   │ 035720 │  41,950 │-1.20% │  44,000 │  40,450 │
 └───┴──────────┴────────┴─────────┴───────┴─────────┴─────────┘

──  NEWS  ────────────────────────────────────────────────────────────

  1  삼성전자, 2분기 영업이익 10조 전망 상향          Naver Finance  4분 전
     https://finance.naver.com/news/...

  2  Samsung Electronics eyes AI chip expansion        Yahoo Finance  12분 전
     https://finance.yahoo.com/news/...

─────────────────────────────────────────────────────────────────────
5s REFRESH  |  NEWS IN 3m  |  Ctrl+C → MENU
```

---

## 7. Rich 라이브러리 구현 가이드

### 7-1. 색상 표기 방식

`rich`에서 Bloomberg 주황을 사용하는 세 가지 방법:

```python
# 방법 A: RGB (트루컬러 지원 터미널 필요)
Text("WATCHLIST", style="bold rgb(255,140,0)")

# 방법 B: 256색 (color(214) ≈ Bloomberg 주황)
Text("WATCHLIST", style="bold color(214)")

# 방법 C: 마크업 문자열
console.print("[bold rgb(255,140,0)]WATCHLIST[/bold rgb(255,140,0)]")
```

> 터미널 호환성이 우선이면 방법 B 사용.
> 색상 정확도가 우선이면 방법 A 사용.

### 7-2. 터미널 호환성 체크리스트

| 기능 | 필요 조건 |
|------|----------|
| RGB 색상 | 트루컬러(24-bit) 지원 터미널 |
| 256색 | 대부분의 현대 터미널 |
| Bold | 기본 지원 |
| Dim | 기본 지원 |
| 박스 문자 (╭╮╰╯) | UTF-8 폰트 필요 (현재 사용 중) |

### 7-3. 현재 스타일에서 Bloomberg 스타일로 변경 요약

| 요소 | 현재 | Bloomberg 변경 |
|------|------|----------------|
| 패널 테두리 | `cyan` | `rgb(255,140,0)` |
| 테이블 title_style | `bold cyan` | `bold rgb(255,140,0)` |
| 테이블 header_style | `bold` | `bold rgb(255,165,0)` |
| 검색결과 종목명 | `bold cyan` | `bold rgb(255,140,0)` |
| 뉴스 구분선 | `dim` | `rgb(80,80,80)` (선), `bold rgb(255,140,0)` (레이블) |
| 뉴스 출처 | `dim cyan` | `rgb(255,165,0)` |
| 메뉴 (전체) | `dim` | 키: `bold rgb(255,140,0)`, 설명: `dim` |
| INFO 메시지 | `green/yellow` | `rgb(255,255,0)` |
| 하락 등락률 | `bold blue` | `bold rgb(68,153,255)` |

---

## 8. 한국 시장 관례와의 조화

Bloomberg Terminal은 국제 관례에 따라 **상승=초록, 하락=빨강**을 사용한다.
한국 시장은 **상승=빨강, 하락=파랑**을 사용한다.

이 앱은 한국 시장 앱이므로 **한국 관례를 유지**한다.
Bloomberg 스타일은 색상 신호(상승/하락)가 아닌 **전반적인 시각 언어**
(주황 강조색, 검정 배경, 밀도 높은 레이아웃)에서 차용한다.

| 항목 | Bloomberg 국제 표준 | 이 앱 적용 | 이유 |
|------|--------------------|---------|----|
| 상승 색상 | 초록 | **빨강** | 한국 시장 관례 |
| 하락 색상 | 빨강 | **파랑** | 한국 시장 관례 |
| 강조색 | 주황/앰버 | **주황/앰버** | Bloomberg 채택 |
| 배경 | 검정 | **검정** (터미널 설정) | Bloomberg 채택 |
| 정보 밀도 | 높음 | **높음** | Bloomberg 채택 |
| 레이블 스타일 | ALL CAPS | **대문자 권장** | Bloomberg 채택 |

---

## 9. 적용 우선순위

구현 시 다음 순서로 적용한다.

1. **Phase 1 — 색상 교체** (영향 범위 최소)
   - `tui.py`: 패널 border_style `cyan` → `rgb(255,140,0)`
   - `utils.py`: title_style, header_style, 뉴스 출처 색상 변경
   - `utils.py`: 메뉴 텍스트에서 키 부분만 주황으로 분리

2. **Phase 2 — 레이블 변경** (텍스트 변경)
   - 테이블 컬럼 헤더 영문화 (`PRICE`, `CHG%`, `HIGH`, `LOW`)
   - 뉴스 구분선 레이블 영문화 (`NEWS`)
   - 감시 모드 하단 상태바 형식 통일

3. **Phase 3 — 레이아웃 심화** (구조 변경)
   - 설정 화면 Bloomberg 스타일 적용
   - 검색 결과 화면 스타일 통일
   - 메뉴 바 Function Key Bar 스타일 완성
