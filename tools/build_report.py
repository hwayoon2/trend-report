#!/usr/bin/env python3
"""주간 VC 리포트 빌더.

사용법: python3 tools/build_report.py data/YYYY-MM-DD.json      (미국판)
        python3 tools/build_report.py data/kr/YYYY-MM-DD.json   (한국판, JSON에 "region": "kr")

data JSON(스키마는 .claude/skills/vc-weekly-report*/SKILL.md 참고)을 읽어
<리전 폴더>/START.html 을 만들고 <리전 폴더>/index.json, 루트 index.html 을 갱신한다.
본문 텍스트에 '[미확인]' '[추정]' 을 쓰면 회색 배지로 바뀐다.
"""
import html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = open(os.path.join(ROOT, "tools", "report.css"), encoding="utf-8").read()
FONT = '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap" rel="stylesheet">'


def money_us(m):
    return (f"${m/1000:.1f}B".replace(".0B", "B")) if m >= 1000 else f"${m:g}M"


def money_kr(e):
    return (f"{e/10000:.1f}조원".replace(".0조", "조")) if e >= 10000 else f"{e:,.0f}억원"


# 리전별 설정. 미국판 출력은 기존과 동일하게 유지한다.
REGIONS = {
    "us": dict(dir="reports", src="crunchbase", amt="amount_m", money=money_us,
               tile_total=lambda t: f"${t:,.0f}M", tile_avg=lambda a: f"${a:,.0f}M",
               title="Crunchbase Top 10", h1="Crunchbase Top 10 펀딩 라운드", src_label="Crunchbase News",
               back="../index.html", stage_h="2. 단계별 동향 — 시드·시리즈 A vs 메가라운드",
               exit_h="3. M&amp;A · IPO · 엑시트",
               site="실리콘밸리 VC 주간 동향", site_sub="Crunchbase 주간 Top 10 기반 리포트"),
    "kr": dict(dir="kr/reports", src="source", amt="amount_eok", money=money_kr,
               tile_total=money_kr, tile_avg=money_kr,
               title="국내 스타트업 투자 Top 10", h1="국내 스타트업 투자 Top 10", src_label="스타트업레시피",
               back="../../index.html", stage_h="2. 단계별 동향 — 시드·시리즈 A vs 메가딜(100억원+)",
               exit_h="3. 상장 · M&amp;A · 정책",
               site="국내 스타트업 투자 주간 동향", site_sub="스타트업레시피 주간 투자 리포트 기반"),
}

REQ_TOP = ["start", "end", "headline", "lead", "trends", "deals", "sectors", "stages",
           "stage_note", "exits", "implications", "watch", "sources", "limits"]
REQ_DEAL = ["rank", "name", "sector", "round", "valuation", "lead", "hq",
            "what", "funding", "history", "metrics", "why", "sources"]


def badge(s):
    return (s.replace("[미확인]", '<span class="u">미확인</span>')
             .replace("[추정]", '<span class="u">추정</span>'))


def ul(items, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<ul{c}>" + "".join(f"<li>{badge(i)}</li>" for i in items) + "</ul>"


def links(pairs):
    return " · ".join(f'<a href="{u}">{html.escape(t)}</a>' for t, u in pairs)


def validate(d, R):
    errs = [f"필드 누락: {k}" for k in REQ_TOP + [R["src"]] if not d.get(k)]
    deals = d.get("deals", [])
    if len(deals) != 10:
        errs.append(f"딜이 10개가 아님: {len(deals)}개")
    for x in deals:
        for k in REQ_DEAL + [R["amt"]]:
            if x.get(k) in (None, "", []):
                errs.append(f"{x.get('name','?')}: {k} 비어 있음")
    if errs:
        sys.exit("검증 실패\n- " + "\n- ".join(errs))


def page(d, R):
    S, E, cb = d["start"], d["end"], d[R["src"]]
    A, money = R["amt"], R["money"]
    deals = sorted(d["deals"], key=lambda x: (x["rank"], -x[A]))
    tot = sum(x[A] for x in deals)
    top = max(deals, key=lambda x: x[A])
    mx = top[A]
    bars = "".join(
        f'<a class="bar" href="#d{i}"><span class="bn">{x["rank"]}. {html.escape(x["name"])}</span>'
        f'<span class="bt"><i style="width:{x[A]/mx*100:.1f}%"></i></span><span class="ba">{money(x[A])}</span></a>'
        for i, x in enumerate(deals, 1))
    cards = ""
    for i, x in enumerate(deals, 1):
        src = links(x["sources"]) + (f' · <a href="{x["site"]}">공식 사이트</a>' if x.get("site") else "")
        est = ' <span class="u">추정</span>' if x.get("rank_estimated") else ""
        cards += f'''<article class="card" id="d{i}"><div class="ch"><span class="rk">{x["rank"]}</span><h3>{html.escape(x["name"])}{est}</h3><span class="tag">{html.escape(x["sector"])}</span></div>
<div class="amt">{money(x[A])}</div>
<dl class="meta"><div><dt>라운드</dt><dd>{badge(x["round"])}</dd></div><div><dt>밸류에이션</dt><dd>{badge(x["valuation"])}</dd></div><div><dt>리드</dt><dd>{badge(x["lead"])}</dd></div><div><dt>본사 · 설립</dt><dd>{badge(x["hq"])}</dd></div></dl>
<h4>어떤 회사인가</h4><p>{badge(x["what"])}</p><h4>펀딩 내용</h4><p>{badge(x["funding"])}</p><h4>펀딩 히스토리</h4><p>{badge(x["history"])}</p><h4>핵심 지표</h4><p>{badge(x["metrics"])}</p><h4>왜 이 투자가 나왔나 — 시장의 방향</h4><p class="why">{badge(x["why"])}</p>
<div class="src">출처: {src}</div></article>'''
    sectors = "".join(f'<div class="sec"><div class="sh"><b>{s["name"]}</b><span>{badge(s["stat"])}</span></div><p>{badge(s["text"])}</p></div>' for s in d["sectors"])
    stages = ('<div class="tw"><table><thead><tr><th>단계</th><th>이번 주 주요 딜</th><th>관찰</th></tr></thead><tbody>'
              + "".join(f'<tr><td><b>{s["stage"]}</b></td><td>{badge(s["deals"])}</td><td>{badge(s["note"])}</td></tr>' for s in d["stages"])
              + "</tbody></table></div>")
    toc = [("trend", "시장의 방향"), ("chart", "Top 10"), ("cards", "딜 카드"), ("s1", "1. 섹터"), ("s2", "2. 단계"),
           ("s3", "3. 엑시트"), ("s4", "4. 시사점"), ("s5", "5. 출처")]
    others = f'<h2>Top 10 밖 주목할 딜</h2>{ul(d["others"], "small")}' if d.get("others") else ""
    policy = f'<h4>정책 · 모태펀드</h4>{ul(d["policy"])}' if d.get("policy") else ""
    exits = (f'<h4>상장 · M&amp;A</h4>{ul(d["exits"])}{policy}' if policy else ul(d["exits"]))
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{R["title"]} | {S}~{E}</title>
{FONT}<style>{CSS}</style></head><body><div class="w">
<a href="{R["back"]}">← 전체 리포트</a><h1>{R["h1"]}</h1><div class="sub">{S} ~ {E} · 원문: {R["src_label"]} “{html.escape(cb["title"])}” ({cb.get("note","")}) · <a href="{cb["url"]}">원문 링크</a></div>
<nav class="toc">{"".join(f'<a href="#{a}">{b}</a>' for a, b in toc)}</nav>
<p class="lead"><b>{badge(d["headline"])}.</b> {badge(d["lead"])}</p>
<div class="tiles"><div class="tile"><b>{R["tile_total"](tot)}</b><span>Top 10 합계</span></div><div class="tile"><b>{money(top[A])}</b><span>최대 딜 · {html.escape(top["name"])}</span></div><div class="tile"><b>{d.get("top_sector","")}</b><span>{d.get("top_sector_note","최다 섹터")}</span></div><div class="tile"><b>{R["tile_avg"](tot/len(deals))}</b><span>평균 라운드 규모</span></div></div>
<h2 id="trend">이번 주 시장의 방향</h2>{ul(d["trends"], "trend")}
<h2 id="chart">Top 10 한눈에</h2>{bars}
<h2 id="cards">딜 카드</h2>{cards}
{others}
<h2 id="s1">1. 섹터별 동향</h2>{sectors}
<h2 id="s2">{R["stage_h"]}</h2>{stages}<p>{badge(d["stage_note"])}</p>
<h2 id="s3">{R["exit_h"]}</h2>{exits}
<h2 id="s4">4. 시사점 · 다음 주에 지켜볼 것</h2><h4>시사점</h4>{ul(d["implications"])}<h4>다음 주 체크리스트</h4>{ul(d["watch"])}
<h2 id="s5">5. 출처</h2><ul class="srcs">{"".join(f'<li><a href="{u}">{html.escape(t)}</a></li>' for t, u in d["sources"])}</ul>
<h2>데이터 한계</h2><p class="small">{badge(d["limits"])} 투자 조언이 아닙니다.</p>
</div></body></html>''', tot, top


def load_index(R):
    ip = os.path.join(ROOT, R["dir"], "index.json")
    return json.load(open(ip, encoding="utf-8")) if os.path.exists(ip) else []


def region_block(key):
    R, idx = REGIONS[key], load_index(REGIONS[key])
    if not idx:
        return f'<h2>{R["site"]}</h2><p class="small">아직 리포트가 없습니다.</p>'
    l = idx[0]
    rows = "".join(f'<li><a href="{R["dir"]}/{r["file"]}">{r["start"]} ~ {r["end"]}</a> — {html.escape(r["headline"])}</li>' for r in idx[1:])
    return f'''<h2>{R["site"]}</h2><div class="sub">{R["site_sub"]}</div><article class="card"><div class="sub">최신 · {l["start"]} ~ {l["end"]}</div><h3><a href="{R["dir"]}/{l["file"]}">{html.escape(l["headline"])}</a></h3><dl class="meta"><div><dt>Top 10 합계</dt><dd>{l.get("top10_total","")}</dd></div><div><dt>최대 딜</dt><dd>{html.escape(l.get("top_deal",""))}</dd></div></dl></article>
<h4>지난 주차</h4><ul class="small">{rows or "<li>아직 없음</li>"}</ul>'''


def main(path):
    d = json.load(open(path, encoding="utf-8"))
    key = d.get("region", "us")
    R = REGIONS[key]
    validate(d, R)
    S = d["start"]
    out, tot, top = page(d, R)
    os.makedirs(os.path.join(ROOT, R["dir"]), exist_ok=True)
    open(os.path.join(ROOT, R["dir"], f"{S}.html"), "w", encoding="utf-8").write(out)

    entry = {"start": S, "end": d["end"], "file": f"{S}.html", "headline": d["headline"],
             "top10_total": R["money"](tot), "top_deal": f'{top["name"]} {R["money"](top[R["amt"]])} ({top["round"]})'.replace("[미확인]", "").strip()}
    idx = sorted([entry] + [o for o in load_index(R) if o["start"] != S], key=lambda o: o["start"], reverse=True)
    json.dump(idx, open(os.path.join(ROOT, R["dir"], "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    root = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VC 주간 동향</title>
{FONT}<style>{CSS}</style></head><body><div class="w"><h1>VC 주간 동향</h1><div class="sub">실리콘밸리 · 국내 스타트업 투자 주간 리포트</div>
<nav class="toc"><a href="#us">실리콘밸리</a><a href="#kr">국내</a></nav>
<section id="us">{region_block("us")}</section><section id="kr">{region_block("kr")}</section></div></body></html>'''
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(root)
    print(f"OK {R['dir']}/{S}.html · 합계 {R['money'](tot)} · 최대 {top['name']}")


if __name__ == "__main__":
    main(sys.argv[1])
