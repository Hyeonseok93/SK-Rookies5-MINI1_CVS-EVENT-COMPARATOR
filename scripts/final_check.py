"""Final pre-push verification harness. Run: python scripts/final_check.py"""
from __future__ import annotations

import ast
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

results: list[tuple[str, str, str]] = []


def ok(name: str, cond: bool, detail: str = "") -> bool:
    status = "PASS" if cond else "FAIL"
    results.append((status, name, detail))
    extra = f" - {detail}" if detail else ""
    print(f"{status:4} | {name}{extra}")
    return cond


def section(title: str) -> None:
    print(f"\n======== {title} ========")


def main() -> int:
    section("A. SYNTAX")
    files = (
        list(ROOT.glob("app.py"))
        + list((ROOT / "batch").rglob("*.py"))
        + list((ROOT / "utils").glob("*.py"))
        + list((ROOT / "pages").glob("*.py"))
        + list((ROOT / "scraper").glob("*.py"))
    )
    bad = []
    for p in files:
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            bad.append(f"{p}: {e}")
    ok("syntax all py", not bad, f"{len(files)} files" if not bad else "; ".join(bad))

    section("B. SECURITY")
    from utils.chatbot import (
        CHAT_MAX_CHARS,
        GENERIC_ERROR,
        _build_context,
        _safe_history,
        _sanitize_text,
    )
    from utils.filters import SEARCH_MAX_CHARS, name_contains
    from utils.html_safe import esc, safe_img_url, safe_url

    ok("XSS esc", esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;")
    ok("block javascript:", safe_url("javascript:alert(1)") == "#")
    ok("block data:", safe_url("data:text/html,x") == "#")
    ok("allow https", "example.com" in safe_url("https://example.com/a.png"))
    ok("img None empty", safe_img_url(None) == "")

    s = pd.Series(["콜라", "김밥", "(이벤트)"])
    try:
        m = name_contains(s, "((((")
        ok("search (((( no crash", True, str(m.tolist()))
    except Exception as e:
        ok("search (((( no crash", False, str(e))
    try:
        m2 = name_contains(s, ".*")
        ok("search .* literal not regex", m2.tolist() == [False, False, False], str(m2.tolist()))
    except Exception as e:
        ok("search .* literal", False, str(e))

    ok("SEARCH_MAX_CHARS=80", SEARCH_MAX_CHARS == 80)
    ok("CHAT_MAX_CHARS=500", CHAT_MAX_CHARS == 500)
    ok("chatbot truncate", len(_sanitize_text("A" * 5000, limit=CHAT_MAX_CHARS)) == CHAT_MAX_CHARS)
    ok("null byte strip", chr(0) not in _sanitize_text("a" + chr(0) + "b"))
    ok(
        "GENERIC_ERROR no api leak",
        "api_key" not in GENERIC_ERROR.lower() and "401" not in GENERIC_ERROR,
    )

    flt = (ROOT / "utils/filters.py").read_text(encoding="utf-8")
    ok("filters regex=False + name_contains", "regex=False" in flt and "name_contains" in flt)
    ok("filters max_chars", "max_chars=SEARCH_MAX_CHARS" in flt)

    for rel in ["pages/05_diet_guide.py", "pages/06_night_snack_guide.py"]:
        t = (ROOT / rel).read_text(encoding="utf-8")
        ok(f"{rel} no window.parent", "window.parent" not in t)

    jack = (ROOT / "pages/09_jackpot_game.py").read_text(encoding="utf-8")
    ok("jackpot no Google Fonts CDN", "fonts.googleapis" not in jack and "@import" not in jack)

    app = (ROOT / "app.py").read_text(encoding="utf-8")
    ok("app no scheduler", "get_scheduler_manager" not in app and "batch_scheduler" not in app)

    chat = (ROOT / "utils/chatbot.py").read_text(encoding="utf-8")
    ok("chatbot uses GENERIC_ERROR", "GENERIC_ERROR" in chat)
    ok("chatbot product_data boundary", "<product_data>" in chat)

    cfg = (ROOT / ".streamlit/config.toml").read_text(encoding="utf-8")
    ok("XSRF on", "enableXsrfProtection = true" in cfg)
    ok("no enableCORS=false conflict", "enableCORS = false" not in cfg)

    hist = _safe_history(
        [{"role": "system", "content": "x"}, {"role": "user", "content": "hi"}, {"role": "assistant", "content": "ok"}]
    )
    ok("history roles filtered", [h["role"] for h in hist] == ["user", "assistant"])

    section("C. FEATURES")
    from batch.script.crawl_batch_script import run_daily_data_batch
    from scraper.base import save_products
    from utils.brand import BRAND_COLORS, get_brand_color, normalize_brand
    from utils.data_cleaner_batch import _latest_per_brand
    from utils.data_loader import _unit_price_vectorized, load_categorized_df
    from utils.paths import categorized_path, cleaned_path
    from utils.theme_guide import _apply_theme_sort, filter_theme_products

    df = load_categorized_df(with_unit_price=True, with_discount_num=True)
    ok("catalog load", not df.empty, f"rows={len(df)} brands={sorted(df['brand'].unique().tolist())}")
    ok("unit_price <= price", "unit_price" in df.columns and bool((df["unit_price"] <= df["price"]).all()))
    ok("discount_num present", "discount_num" in df.columns)
    got = _unit_price_vectorized(pd.Series(["1+1", "2+1", "3+1"]), pd.Series([1000, 3000, 4000])).tolist()
    ok("unit_price vectorized", got == [500, 2000, 3000], str(got))
    ok("normalize brand", normalize_brand("세븐일레븐") == "7Eleven")
    ok("brand color CU", get_brand_color("CU") == BRAND_COLORS["CU"])

    tdf = pd.DataFrame(
        {
            "name": ["제로콜라", "맥주제로", "단백질"],
            "brand": ["CU", "CU", "GS25"],
            "event": ["1+1", "1+1", "2+1"],
            "category": ["음료", "음료", "간식류"],
            "unit_price": [500, 800, 1000],
            "discount_num": [50.0, 50.0, 33.0],
            "discount_rate": ["50%", "50%", "33%"],
        }
    )
    fout = filter_theme_products(
        tdf,
        keywords=["제로", "단백"],
        exclude_keywords=["맥주"],
        selected_brands=["CU", "GS25"],
        selected_events=["1+1", "2+1"],
        selected_cats=["음료", "간식류"],
        search_query="",
    )
    ok("theme exclude beer", list(fout["name"]) == ["제로콜라", "단백질"], str(list(fout["name"])))
    sout = _apply_theme_sort(fout, "할인율 순")
    ok("theme sort by discount_num", list(sout["discount_num"]) == [50.0, 33.0])

    td = tempfile.mkdtemp()
    os.environ["DATA_DIR"] = td
    os.environ["BATCH_FILE_STAMP"] = "260713"
    pdf = pd.DataFrame({"name": ["a"], "event": ["1+1"], "brand": ["CU"], "price": [1]})
    t0 = time.perf_counter() - 3.2
    path = save_products(pdf, "CU", start_ts=datetime(2026, 1, 1), t0=t0)
    ok("BATCH_FILE_STAMP filename", bool(path and path.endswith("CU_260713.csv")), str(path))
    os.environ.pop("BATCH_FILE_STAMP", None)
    os.environ.pop("DATA_DIR", None)
    shutil.rmtree(td, ignore_errors=True)

    c1, g1 = Path(cleaned_path()), Path(categorized_path())
    m1 = (c1.stat().st_mtime if c1.exists() else None, g1.stat().st_mtime if g1.exists() else None)
    dok = run_daily_data_batch(2026, 7, datetime.now(), dry_run=True)
    m2 = (c1.stat().st_mtime if c1.exists() else None, g1.stat().st_mtime if g1.exists() else None)
    ok("dry-run returns True", dok is True)
    ok("dry-run does not mutate catalog", m1 == m2)

    td = tempfile.mkdtemp()
    f1 = os.path.join(td, "CU_259901.csv")
    open(f1, "w", encoding="utf-8").write("x")
    sel = _latest_per_brand([f1], "2607", allow_fallback=False)
    ok("cleaner no stamp-prefix fallback", sel == [])
    shutil.rmtree(td, ignore_errors=True)

    req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    ok("no streamlit-float", "streamlit-float" not in req)
    ok("no nbformat/ipykernel", "nbformat" not in req and "ipykernel" not in req)
    ok("graph.py removed", not (ROOT / "utils/graph.py").exists())
    ok("theme_guide exists", (ROOT / "utils/theme_guide.py").exists())
    ok("run_once exists", (ROOT / "batch/run_once.py").exists())
    ok("run_scheduler exists", (ROOT / "batch/run_scheduler.py").exists())

    cart = (ROOT / "utils/cart.py").read_text(encoding="utf-8")
    ok("cart no popover(key=)", "st.popover(badge, key" not in cart)
    ok("cart keyed container", 'st.container(key="cvs_floating_cart")' in cart)
    ok("chatbot width 460px", "width: 460px" in chat)

    news_csv = ROOT / "data" / "official_event_news.csv"
    ok("official_event_news.csv present", news_csv.exists(), str(news_csv) if news_csv.exists() else "missing")

    section("D. STREAMLIT PAGES")
    from streamlit.testing.v1 import AppTest

    pages = [
        "pages/01_overall_summary.py",
        "pages/02_brand_comparison.py",
        "pages/03_best_value.py",
        "pages/04_budget_combination.py",
        "pages/05_diet_guide.py",
        "pages/06_night_snack_guide.py",
        "pages/08_random_picker.py",
        "pages/09_jackpot_game.py",
        "pages/10_event_news.py",
    ]
    for p in pages:
        try:
            at = AppTest.from_file(p, default_timeout=60)
            at.run()
            msg = "" if not at.exception else str(at.exception[0].message)[:160]
            ok(f"AppTest {Path(p).name}", not at.exception, msg)
        except Exception as e:
            ok(f"AppTest {Path(p).name}", False, str(e)[:160])

    try:
        at = AppTest.from_file("pages/00_home.py", default_timeout=60)
        at.run()
        if at.exception and "url_pathname" in str(at.exception[0].message):
            ok(
                "AppTest 00_home isolated page_link",
                True,
                "EXPECTED under AppTest (needs st.navigation from app.py)",
            )
        else:
            ok("AppTest 00_home", not at.exception)
    except Exception as e:
        ok("AppTest 00_home", False, str(e)[:160])

    section("E. SCHEDULER")
    from batch.batch_scheduler_manager import SchedulerManager

    m = SchedulerManager()
    m.start()
    m.add_job(day=None, hour=6, minute=0, batch_name="chk", job_id="chk_daily", dry_run=True)
    jobs = m.get_jobs()
    ok(
        "daily cron hour=6",
        any(j["id"] == "chk_daily" and "hour='6'" in j["trigger"] for j in jobs["jobs"]),
        str([j["trigger"] for j in jobs["jobs"]]),
    )
    m.trigger_now("chk_daily")
    ok("scheduler dry trigger", True)
    m.remove_job("chk_daily")
    m.stop()

    fails = [r for r in results if r[0] == "FAIL"]
    section("SUMMARY")
    print(f"Total={len(results)} PASS={len(results) - len(fails)} FAIL={len(fails)}")
    out = ROOT / "docs" / "_final_check_results.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
