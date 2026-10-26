---
name: vc-weekly-report
description: 실리콘밸리 VC 주간 리포트(Crunchbase Top 10 + 섹터·단계·투자자·엑시트·시사점)를 조사해 data JSON을 채우고 HTML로 빌드해 claude/pages에 push한다. 매주 리포트를 만들 때 사용.
---

# 실리콘밸리 VC 주간 리포트

목표: **매주 같은 구성, 같은 깊이**의 한국어 리포트. 디자인과 HTML은 `tools/build_report.py`가 고정으로 만든다.
너는 **조사하고 `data/START.json`을 채우는 일**만 한다. HTML을 직접 쓰지 말 것.

견본: `data/2026-10-19.json` (이 수준이 최소 기준. 매주 이 파일을 열어 길이·톤·깊이를 맞춘다)

## 0. 기간
`date -u` → 대상 주 = 지난주 월(START)~일(END). 파일명은 START.

## 1. 정보원 (우선순위)
| 정보원 | 무엇을 볼까 | 검색 방법 |
|---|---|---|
| **Crunchbase News** (news.crunchbase.com) | ① 주간 "The Week's 10 Biggest Funding Rounds" (보통 금요일, 금~목 집계. **이 목록은 미국 기업만 집계하므로 출발점일 뿐, 우리 Top 10은 글로벌 기준**) ② 분기·월간 집계(총액, 단계별, AI 비중) ③ 섹터 기사(핀테크·바이오·클린테크) ④ "5 Interesting Startup Deals" (초기 단계) ⑤ Exclusive 시드 기사 | WebFetch 우선. 막히면 WebSearch에 `allowed_domains:["news.crunchbase.com"]` |
| **TechCrunch** (techcrunch.com) | 딜 카드의 1차 출처. 해당 주 펀딩 기사 본문(창업자, 투자자 명단, 직전 라운드, 인용문, 리스크)을 **WebFetch로 실제로 열어 읽는다**. 검색 스니펫만으로 카드를 쓰지 말 것. 펀드 클로즈·인수 기사도 여기서 | WebSearch `allowed_domains:["techcrunch.com"]`로 URL 찾고 WebFetch로 본문 읽기 |
| **Axios Pro Rata** (axios.com/pro/all-deals/YYYY/MM/DD/...) | 매일 Venture Capital Deals, PE, **Fundraising(신규 펀드)**, M&A | WebSearch `allowed_domains:["axios.com"]`, 날짜별로 월~금 5회 |
| **StrictlyVC** (newsletter.strictlyvc.com) | Massive Fundings / New Fundings / **New Funds** / Exits | WebSearch `allowed_domains:["strictlyvc.com"]` |
| 보조 | TechCrunch, Bloomberg, STAT(바이오), 회사 보도자료, Dealroom | 딜별 교차 확인 |

- WebFetch가 막히면(ENOTFOUND/403) 검색 스니펫으로 재구성하고 `limits`에 **어떤 정보원이 막혔는지** 적는다.
- Crunchbase 기사 본문을 못 열면: `"<기사 제목>" + 회사명`으로 여러 번 검색해 순위 스니펫을 모은다. 확인 못 한 순위는 `rank_estimated: true`.
- **다른 주 회차와 혼동 금지**: 기사 발행일이 START~END 안인지, 그 기사의 집계 기간이 무엇인지 확인해 `crunchbase.note`에 적는다.
- **Top 10은 글로벌 기준**: Crunchbase 주간 목록(미국만) 10개에 같은 기간 해외 기업의 확정 발표 딜(TechCrunch·Axios·StrictlyVC·Dealroom·Sifted·Tech.eu·Calcalist·회사 발표)을 합쳐 금액순으로 다시 10개를 뽑는다. 해외 딜 확인 절차: ① 위 정보원에서 해당 주 유럽·이스라엘·아시아 $100M+ 딜 검색 ② 발표일이 대상 주 안인지 확인 ③ 보도만 있고 회사·투자자 확인이 없는 딜("in talks", 익명 소스)은 Top 10에 넣지 않고 `others`에 `[미확인]`으로.
- 해외 딜은 `hq` 앞에 국가를 쓰고, `crunchbase.note`에 "Crunchbase 미국 목록 + 해외 N건 추가, 금액순 재정렬"을 적는다. Crunchbase 목록에서 밀려난 딜은 `others`로 옮긴다. 동액은 공동 순위.
- 해외 딜을 빠짐없이 확인할 수 없으면 `limits`에 어느 지역을 못 봤는지 적는다.

## 2. 딜 카드 10개 (페이지의 주인공) — 필드별 기준
각 딜마다 **회사 발표 + 주요 매체 1~2개**를 더 찾는다. 수치는 2개 출처로 교차 확인. 확인 안 되면 `[미확인]`. 추측 금지.

| 필드 | 써야 할 것 | 분량 |
|---|---|---|
| `what` 어떤 회사인가 | 무엇을 만드는지(쉬운 말로, 비유 OK) · **고객이 누구인지** · **돈 버는 방식** · 창업자 배경(왜 이 팀인지) · 제품/매출 유무 | 3~5문장 |
| `funding` 펀딩 내용 | 리드, 주요 참여사(전략·공모시장 기관 구분), 발표일, 금액 출처 불일치 | 2~3문장 |
| `history` 펀딩 히스토리 | 직전 라운드 시점·금액·밸류 → **밸류 상승 배수**, 누적 조달 | 1~2문장 |
| `metrics` 핵심 지표 | ARR·매출·고객사 이름·고객 수·직원 수·계약. "회사 주장"인지 표시 | 1~2문장 |
| `why` 왜 이 투자가 나왔나 — 시장의 방향 | **첫 문장은 `<b>한 줄 테제</b>`** (이 딜이 보여주는 시장 흐름). 이어서 왜 지금 이 회사에 돈이 들어왔는지(트리거: 계약·출하·시연·정책), 어떤 큰 흐름의 일부인지(경쟁사·유사 딜 언급), 리스크 1개 | 3~4문장 |
| `sources` | `[["매체명","URL"], ...]` 2~4개 | |

메타: `round`, `valuation`(pre/post 구분), `lead`, `hq`("도시 · 설립연도"), `sector`(짧은 태그), `amount_m`(백만 달러 숫자), `site`.

## 3. 페이지 섹션 — 각 섹션에서 볼 것
| JSON 키 | 섹션 | 무엇을 쓸까 |
|---|---|---|
| `headline` | 헤드라인 | "A $X·B $Y가 이끈 주간, 테마1·테마2… Top 10 합계 약 $Z" (마침표 없이) |
| `lead` | 리드 문단 | 상위 집중도(%), AI 건수, 두 번째 축 — 2문장 |
| `top_sector` / `top_sector_note` | 타일 | 예: "AI 6건" / "최다 섹터 (AI 신약 2건 포함)" |
| `trends` | 이번 주 시장의 방향 | 4개. 각 `<b>테제.</b>` + 근거 딜 1~2문장 |
| `others` | Top 10 밖 주목할 딜 | 3~5개 한 줄씩 (해외 대형딜, $100M 근처 딜) |
| `sectors` | 1. 섹터별 동향 | **AI / 바이오·헬스 / 국방·우주·하드테크 / 핀테크·커머스 / 기후·에너지** 5개 고정. `stat`="금액 · 건수", `text`= 이번 주 딜 + Top 10 밖 딜(Axios·StrictlyVC) + Crunchbase 분기/섹터 데이터로 맥락 3~5문장. 딜이 없으면 "이번 주 큰 딜 없음"과 최근 섹터 데이터 |
| `stages` | 2. 단계별 표 | 행 3개 고정: 시드·프리시드 / 시리즈 A / 시리즈 B~E·성장. `deals`는 `<br>`로 구분, `note`= 관찰 1~2문장 |
| `stage_note` | 단계 요약 | 메가라운드($100M+) 비중, 메가 시드·A 존재 여부, Crunchbase 최신 분기 단계별 수치, 굵은 결론 1줄 |
| `investors` | 3. 투자자 | 4~6명. 이번 주 리드/참여 딜을 묶어 "어떤 테마에 베팅 중인지" |
| `funds` | 3. 신규 펀드 | 이번 주 클로즈 우선, 없으면 직전 주 "참고", 모집 중(SEC 신고) |
| `exits` | 4. M&A·IPO | 이번 주 VC 지원 스타트업 인수, IPO 진행(대형 AI IPO 일정), 최신 분기 엑시트 통계. 없으면 "확인하지 못함"을 명시 |
| `implications` | 5. 시사점 | 3개. `<b>결론.</b>` + 근거 |
| `watch` | 5. 다음 주 체크리스트 | 4개. 예정된 IPO/실적/집계 발표, 협상 중인 메가라운드 |
| `sources` | 6. 출처 | 15~25개. Crunchbase·Axios·StrictlyVC 기사 URL 우선 |
| `limits` | 데이터 한계 | 막힌 정보원, 추정 순위, 미확인 값, 회사 주장 수치 |

텍스트 안 HTML은 `<b>`, `<br>`, `<a href>`만. 배지는 `[미확인]`, `[추정]` 문자열.

## 4. 문체
- 한국어 존댓말 평서문("~입니다"), 짧은 문장. 숫자는 `$1.5B`, `$237M`.
- 전문용어는 처음 나올 때 괄호로 풀이 (예: 추론(inference)).
- 과장·투자권유 금지. 회사 주장 수치는 "(회사 주장)".

## 5. 빌드 & 배포
```bash
git fetch origin && git checkout -B claude/pages origin/claude/pages
# data/START.json 작성 (견본 복사 후 채우기)
python3 tools/build_report.py data/START.json   # 검증 실패 시 메시지대로 보완
git add -A && git commit -m "report: START ~ END" && git push origin claude/pages
```
- 빌더가 `reports/START.html`, `reports/index.json`, 루트 `index.html`을 갱신한다. `.nojekyll` 유지.
- PR 생성 금지. push 실패 시 에러를 그대로 보고.

## 6. 마무리
- PushNotification: Top 3 딜(회사·금액) 한 줄씩 + `https://hwayoon2.github.io/trend-report/reports/START.html?v=1` (캐시 우회용 쿼리)
- 최종 응답: 페이지 주소, push 결과, Crunchbase 기사 URL, 데이터 한계.

## 자체 점검 (push 전)
- [ ] 딜 10개 모두 `what` 3문장 이상, `why`가 `<b>테제</b>`로 시작
- [ ] 섹터 5개, 단계 3행, 시사점 3개, 체크리스트 4개
- [ ] 금액·밸류·리드는 2출처 확인 또는 `[미확인]`
- [ ] Crunchbase 기사 발행일이 대상 주 안에 있음
- [ ] 출처 15개 이상
