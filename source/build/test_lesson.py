"""Headless checks for the v4 lesson player (see SKILL.md Delivery). usage: python3 test_lesson.py dodo1 ; BASE env overrides URL (default: live GitHub Pages)."""
from playwright.sync_api import sync_playwright
import os, sys, json
BASE = os.environ.get("BASE", "https://manoletre.github.io/system-design-prep/lessons/")
SHOTS = "/tmp/sd-shots"; os.makedirs(SHOTS, exist_ok=True)
LONG = ("My prediction, written out at length to stress the layout: " + "the detector misses some hallucinations and raises false alarms; " * 9).strip()
SLUG = {"dodo1": "dodo-1"}
LEGACY = {"dodo1": {"hook": "legacy hook answer from v3", "c3": "legacy c3 answer from v3"}}  # answers saved by the old player must survive
def run(n, sweep=False, shots=False):
    slug = SLUG[n]; tag = n; errs = []; media = []; fails = []
    def ok(cond, msg):
        print(("  OK   " if cond else "  FAIL ") + msg)
        if not cond: fails.append(msg)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        ctx = b.new_context(viewport={"width": 1440, "height": 900}); pg = ctx.new_page()
        pg.on("console", lambda m: errs.append(f"{m.type}: {m.text}") if m.type == "error" and "ERR_ABORTED" not in m.text else None)
        pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        pg.on("request", lambda r: media.append(r.url.split("/")[-1]) if (".mp4" in r.url or "poster" in r.url) else None)
        # legacy answer from the v3 player must still show up (L1/L2 lesson hook moved into a chapter)
        pg.goto(BASE + slug + "/"); pg.evaluate("localStorage.clear()")
        for q, v in LEGACY.get(n, {}).items(): pg.evaluate(f"localStorage.setItem('lap:{n}:{q}:answer','{v}')")
        pg.goto(BASE + slug + "/"); pg.wait_for_function("window.__ready===true", timeout=20000)
        L = pg.evaluate("LESSON"); NC = len(L["chapters"])
        print(f"[{tag}] chapters={NC} steps={[len(c['steps']) for c in L['chapters']]} katex={pg.eval_on_selector_all('.katex','e=>e.length')} katex-errors={pg.eval_on_selector_all('.katex-error','e=>e.length')}")
        vids = "[...document.querySelectorAll('video')].map(v=>({id:v.id,src:v.getAttribute('src'),paused:v.paused}))"
        pg.wait_for_timeout(2500)
        V = pg.evaluate(vids)
        ok(all(v["src"] is None and v["paused"] for v in V) and not media, f"on load: no video has a source, none playing, no media requests ({media})")
        for q, v in LEGACY.get(n, {}).items():
            ok(pg.input_value(f'textarea[data-ans="{q}"]') == v, f"legacy answer for {q} restored")
        ok(pg.eval_on_selector_all('.katex-error','e=>e.length') == 0 and pg.eval_on_selector_all('.katex','e=>e.length') > 0, "formulas render (KaTeX, no errors)")
        pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(600)
        ok(pg.is_visible('#s1 .phase[data-ph="0"] textarea') and not pg.is_visible("#v0") and not media, "chapter 1 opens on the question; video hidden and not loaded")
        if shots: pg.screenshot(path=f"{SHOTS}/v4-{tag}-question.png")
        hid = L["chapters"][0]["hook"]["id"]; cid = L["chapters"][0]["check"]["id"]
        pg.fill(f'#s1 textarea[data-ans="{hid}"]', LONG)
        pg.click('[data-start="0"]')
        def step_check(ci, si, how):
            s = L["chapters"][ci]["steps"][si]
            pg.wait_for_timeout(450); t0, p0 = pg.evaluate(f"[document.getElementById('v{ci}').currentTime, document.getElementById('v{ci}').paused]")
            pg.wait_for_function(f"document.getElementById('v{ci}').paused && !stopAt", timeout=int((s['end']-s['start'])*1000) + 9000)
            t1 = pg.evaluate(f"document.getElementById('v{ci}').currentTime")
            others = [v for v in pg.evaluate(vids) if v["id"] != f"v{ci}" and (v["src"] or not v["paused"])]
            ok(s["start"] - 0.05 <= t0 <= s["start"] + 0.9 and not p0 and s["end"] - 0.4 <= t1 <= s["end"] + 0.01 and not others,
               f"{how:9s} ch{ci+1} step{si+1}: start {s['start']:.2f} seen {t0:.2f} | end {s['end']:.2f} paused {t1:.2f} | other videos loaded/playing: {len(others)}")
        step_check(0, 0, "start")
        pg.keyboard.press("ArrowRight"); step_check(0, 1, "key →")
        pg.keyboard.press("ArrowLeft"); step_check(0, 0, "key ←")
        pg.keyboard.press("r"); step_check(0, 0, "key R")
        pg.click('li[data-ci="0"][data-si="2"]'); step_check(0, 2, "click")
        if shots: pg.screenshot(path=f"{SHOTS}/v4-{tag}-learn.png")
        last = len(L["chapters"][0]["steps"]) - 1
        pg.click(f'li[data-ci="0"][data-si="{last}"]'); step_check(0, last, "last")
        pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(500)
        ok(pg.is_visible('#s1 .phase[data-ph="2"] .cmp') and pg.evaluate("document.getElementById('v0').getAttribute('src')") is None, "after last step → compare panel; video unloaded")
        mine = pg.inner_text(f'#s1 .phase[data-ph="2"] [data-cmp="{hid}"] .mine p')
        lay = pg.evaluate(f"""(()=>{{const c=document.querySelector('#s1 .phase[data-ph="2"] .cmp'),m=c.querySelector('.mine'),card=c.closest('.card');
           return {{docOverflow:document.documentElement.scrollWidth-innerWidth, cmpOverflow:c.scrollWidth-c.clientWidth, mineW:m.getBoundingClientRect().width, cardW:card.getBoundingClientRect().width,
                   mineOverflow:m.scrollWidth-m.clientWidth}}}})()""")
        ok(mine == LONG and lay["docOverflow"] <= 0 and lay["cmpOverflow"] <= 0 and lay["mineOverflow"] <= 0 and lay["mineW"] > 0.4 * lay["cardW"],
           f"long answer ({len(LONG)} chars) fits the compare panel: {lay}")
        pg.click(f'#s1 [data-cmp="{hid}"] .rate button.p'); pg.fill(f'#s1 textarea[data-note="{hid}"]', "Still unclear: why FN is the second word.")
        if shots: pg.screenshot(path=f"{SHOTS}/v4-{tag}-compare.png", full_page=False)
        pg.click("#fwd"); pg.wait_for_timeout(400)
        pg.fill(f'#s1 textarea[data-ans="{cid}"]', LONG); pg.click(f'#s1 [data-reveal="{cid}"]'); pg.click(f'#s1 [data-cmp="{cid}"] .rate button.g')
        ok(pg.is_visible(f'#s1 [data-revealbox="{cid}"] .cmp'), "practice: reveal shows the roomy comparison")
        if shots: pg.screenshot(path=f"{SHOTS}/v4-{tag}-practice.png")
        # reload: position and answers persist
        pg.reload(); pg.wait_for_function("window.__ready===true")
        st = pg.evaluate(f"""[location.hash, document.querySelector('#s1').classList.contains('on'), document.querySelector('#s1 .phase[data-ph="3"]').classList.contains('on'),
           document.querySelector('textarea[data-ans="{hid}"]').value.length, document.querySelector('textarea[data-note="{hid}"]').value,
           localStorage.getItem('lap:{L["id"]}:{hid}:rating'), !document.querySelector('[data-revealbox="{cid}"]').hidden, document.querySelector('textarea[data-ans="{cid}"]').value.length]""")
        ok(st[1] and st[2] and st[3] == len(LONG) and st[4].startswith("Still") and st[5] == "partly" and st[6] and st[7] == len(LONG), f"after reload: {st}")
        ok(all(v["src"] is None for v in pg.evaluate(vids)), "after reload on practice: no video loaded")
        # revisit
        pg.click(f'.pill[data-go="{len(pg.evaluate("SCR"))-1}"]'); pg.wait_for_timeout(400)
        rv = pg.evaluate(f"""[document.querySelector('[data-cmpro="{hid}"] .mine p').textContent.length, document.querySelector('[data-cmpro="{hid}"] .rv').textContent, document.querySelector('[data-cmpro="{hid}"] .revnote').textContent, document.documentElement.scrollWidth-innerWidth]""")
        ok(rv[0] == len(LONG) and rv[1] == "Partly" and "Still unclear" in rv[2] and rv[3] <= 0, f"revisit shows answer/rating/note: {rv[:3]}")
        if shots: pg.screenshot(path=f"{SHOTS}/v4-{tag}-revisit.png")
        if sweep:
            for ci in range(NC):
                pg.click(f'.pill[data-go="{ci+1}"]'); pg.wait_for_timeout(300)
                ok(all(v["src"] is None for v in pg.evaluate(vids)), f"ch{ci+1} entered on question phase: no video loaded") if pg.evaluate(f"S[{ci}].phase")==0 else None
                if pg.evaluate(f"S[{ci}].phase") == 0: pg.click(f'[data-start="{ci}"]'); step_check(ci, 0, "start")
                else: pg.evaluate(f"setPhase({ci},1)")
                si = len(L["chapters"][ci]["steps"]) - 1; pg.click(f'li[data-ci="{ci}"][data-si="{si}"]'); step_check(ci, si, "sweep")
                if shots: pg.screenshot(path=f"{SHOTS}/v4-{tag}-ch{ci+1}-last.png")
        if "drill" in [s["type"] for s in pg.evaluate("SCR")]:
            pg.click('.pill[data-go="%d"]' % (len(pg.evaluate("SCR")) - 2)); pg.fill('textarea[data-ans="d1"]', "P .75, R .6"); pg.click('[data-reveal="d1"]')
            ok(pg.is_visible('[data-revealbox="d1"] .cmp'), "drill reveal works")
            if shots: pg.screenshot(path=f"{SHOTS}/v4-{tag}-drill.png")
        # narrow
        pg.set_viewport_size({"width": 420, "height": 860}); pg.click('.pill.on') if False else None
        pg.evaluate("go(1)"); pg.evaluate("setPhase(0,2)"); pg.wait_for_timeout(400)
        ok(pg.evaluate("document.documentElement.scrollWidth-innerWidth") <= 0, "narrow 420px: no horizontal overflow on compare")
        if shots: pg.screenshot(path=f"{SHOTS}/v4-{tag}-narrow.png")
        b.close()
    ok(not errs, f"console errors: {errs or 'none'}")
    return fails
if __name__ == "__main__":
    allf = []
    for n in sys.argv[1:] or list(SLUG):
        allf += run(n, sweep=True, shots=True)
    print("TOTAL FAILS:", len(allf))
