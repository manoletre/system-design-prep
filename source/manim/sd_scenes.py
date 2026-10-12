from manim import *
import json, os

config.background_color = "#0e1117"
FG = "#e6e6e6"; MUTED = "#8b93a7"; GRID = "#2a2f3a"
C_OLD = "#9ece6a"   # Supabase / old DB
C_NEW = "#7aa2f7"   # GCP / new DB
C_CDC = "#ff9e64"   # changes / replication
C_APP = "#b392f0"   # app, agent, calls
C_Q = "#e0af68"     # queue, timers
C_LK = "#5fc9b6"    # LiveKit
C_BAD = "#f7768e"; C_GOOD = "#9ece6a"
Text.set_default(color=FG, font="DejaVu Sans")

STEP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steps")
HOLD = 1.8

def T(s, fs=26, c=FG, **kw):
    return Text(s, font_size=fs, color=c, **kw)

def box(label, color, w=2.8, h=1.0, fs=26, sub=None, dashed=False):
    r = RoundedRectangle(width=w, height=h, corner_radius=0.15, stroke_color=color, stroke_width=3,
                         fill_color=color, fill_opacity=0.12)
    if dashed:
        r = DashedVMobject(r, num_dashes=40)
    t = T(label, fs, color)
    if sub:
        s = T(sub, int(fs * 0.7), MUTED)
        g = VGroup(t, s).arrange(DOWN, buff=0.08)
        g.move_to(r)
        return VGroup(r, g)
    t.move_to(r)
    return VGroup(r, t)

def arrow(a, b, color=FG, buff=0.12, sw=4):
    return Arrow(a, b, color=color, buff=buff, stroke_width=sw, max_tip_length_to_length_ratio=0.12)

class StepScene(Scene):
    def setup(self):
        self.steps = []; self._open = None; self.cap = None; self.ttl = None
    def begin(self, key):
        self._open = (key, self.renderer.time)
    def end(self, hold=HOLD):
        self.wait(hold)
        k, t0 = self._open
        self.steps.append({"key": k, "start": round(t0, 3), "end": round(self.renderer.time, 3), "hold": hold})
    def say(self, txt, color=FG, size=28, rt=0.8):
        new = T(txt, size, color).to_edge(DOWN, buff=0.35)
        if new.width > 13.4: new.scale_to_fit_width(13.4)
        anims = [FadeIn(new, shift=UP * 0.1)]
        if self.cap is not None: anims.append(FadeOut(self.cap))
        self.play(*anims, run_time=rt); self.cap = new
    def title(self, txt, rt=0.7):
        new = T(txt, 34).to_edge(UP, buff=0.4)
        anims = [FadeIn(new)]
        if self.ttl is not None: anims.append(FadeOut(self.ttl))
        self.play(*anims, run_time=rt); self.ttl = new
    def tear_down(self):
        os.makedirs(STEP_DIR, exist_ok=True)
        with open(os.path.join(STEP_DIR, type(self).__name__ + ".json"), "w") as f:
            json.dump({"duration": round(self.renderer.time, 3), "steps": self.steps}, f, indent=1)

# ------------------------------------------------------------ Chapter 1
class SupaGCP(StepScene):
    def construct(self):
        def bundle(x, color, head, core, tiles, dashed):
            frame = RoundedRectangle(width=5.4, height=4.6, corner_radius=0.25, stroke_color=color, stroke_width=2,
                                     fill_color=color, fill_opacity=0.04).move_to([x, -0.25, 0])
            h = T(head, 28, color).next_to(frame.get_top(), DOWN, buff=0.22)
            pg = box(core, color, w=4.6, h=0.85, fs=26).next_to(h, DOWN, buff=0.22)
            ts = VGroup(*[box(a, c, w=2.4, h=0.95, fs=20, sub=s, dashed=dashed) for a, s, c in tiles])
            ts.arrange_in_grid(2, 2, buff=0.2).next_to(pg, DOWN, buff=0.25)
            return frame, h, pg, ts
        self.begin("supa")
        self.title("Supabase = Postgres + a bundle of extras")
        f1, h1, p1, t1 = bundle(-3.85, C_OLD, "Supabase (today)", "Postgres database",
            [("Auth", "logins, users", C_OLD), ("Storage", "files", C_OLD), ("Realtime", "live updates", C_OLD), ("RLS", "row-level security", C_OLD)], False)
        self.play(Create(f1), FadeIn(h1), run_time=1.0)
        self.play(FadeIn(p1, shift=UP * 0.2), run_time=1.0); self.wait(0.6)
        for t in t1:
            self.play(FadeIn(t, shift=UP * 0.15), run_time=0.6)
        self.say("Supabase hosts Postgres AND gives you auth, file storage, realtime, row-level security")
        self.end()

        self.begin("gcp")
        f2, h2, p2, t2 = bundle(3.85, C_NEW, "GCP (target)", "Cloud SQL or AlloyDB",
            [("Auth → ?", "Identity Platform / own", MUTED), ("Storage → ?", "Cloud Storage", MUTED), ("Realtime → ?", "Pub/Sub or own", MUTED), ("RLS policies", "come along (Postgres)", MUTED)], True)
        self.play(Create(f2), FadeIn(h2), run_time=1.0)
        self.play(FadeIn(p2, shift=UP * 0.2), run_time=0.9)
        a = arrow(p1.get_right(), p2.get_left(), C_CDC)
        lab = VGroup(T("same", 18, C_CDC), T("engine", 18, C_CDC)).arrange(DOWN, buff=0.04).next_to(a, UP, buff=0.08)
        self.play(GrowArrow(a), FadeIn(lab), run_time=1.0); self.wait(0.6)
        self.play(LaggedStart(*[FadeIn(t) for t in t2], lag_ratio=0.35), run_time=2.0)
        self.say("GCP gives you managed Postgres. The extras you must replace or rebuild yourself.")
        self.end()

        self.begin("gotcha")
        hl = SurroundingRectangle(t1[3], color=C_BAD, buff=0.06, stroke_width=4)
        hl2 = SurroundingRectangle(t2[0], color=C_BAD, buff=0.06, stroke_width=4)
        note = T("policies call auth.uid()", 20, C_BAD).next_to(t1[3], DOWN, buff=0.15)
        self.play(Create(hl), FadeIn(note), run_time=1.0); self.wait(0.6)
        link = CurvedArrow(hl.get_right() + DOWN * 0.1, hl2.get_left() + DOWN * 0.2, color=C_BAD, angle=-TAU / 8)
        self.play(Create(link), Create(hl2), run_time=1.2)
        self.say("Hidden coupling: RLS and app code assume Supabase Auth, so plan auth first", C_BAD)
        self.end()

        self.begin("why")
        self.play(*[FadeOut(m) for m in [f1, h1, p1, t1, f2, h2, p2, t2, a, lab, hl, hl2, note, link]], run_time=0.8)
        self.title("Why companies migrate")
        cards = VGroup(
            box("Compliance", C_NEW, w=5.6, h=1.3, fs=28, sub="HIPAA controls, private VPC, audit logs"),
            box("One cloud", C_NEW, w=5.6, h=1.3, fs=28, sub="data next to the rest of the stack"),
            box("Scale & control", C_NEW, w=5.6, h=1.3, fs=28, sub="replicas, tuning, backups, extensions"),
            box("Cost at scale", C_NEW, w=5.6, h=1.3, fs=28, sub="credits, committed-use pricing"),
        ).arrange_in_grid(2, 2, buff=0.45).shift(DOWN * 0.1)
        for c in cards:
            self.play(FadeIn(c, shift=UP * 0.15), run_time=0.7); self.wait(0.3)
        self.say("Ask Tim which one drives Dodo's move: it changes what 'done' means")
        self.end(2.2)

# ------------------------------------------------------------ Chapter 2
class Playbook(StepScene):
    def construct(self):
        app = box("App + voice agents", C_APP, w=3.8, h=0.95, fs=26).move_to([0, 1.75, 0])
        old = box("Supabase Postgres", C_OLD, w=3.4, h=1.1, fs=24, sub="old").move_to([-4.9, -0.9, 0])
        new = box("Cloud SQL Postgres", C_NEW, w=3.4, h=1.1, fs=24, sub="new").move_to([4.9, -0.9, 0])
        live = arrow(app.get_bottom() + LEFT * 0.8, old.get_top() + RIGHT * 0.6, C_APP)
        livelab = T("reads + writes", 20, C_APP).next_to(live, LEFT, buff=0.05).shift(UP * 0.2)

        self.begin("inventory")
        self.title("1 · Inventory")
        self.play(FadeIn(app), FadeIn(old), run_time=0.9)
        self.play(GrowArrow(live), FadeIn(livelab), run_time=0.8)
        self.play(FadeIn(new), run_time=0.7)
        items = ["tables & indexes", "extensions", "RLS policies", "triggers & cron", "auth users", "storage files"]
        chk = VGroup(*[T("☐ " + s, 21, FG) for s in items]).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([0, -1.05, 0])
        self.play(LaggedStart(*[FadeIn(c) for c in chk], lag_ratio=0.3), run_time=2.0)
        self.say("List everything Supabase does for you before moving a single row")
        self.end()

        self.begin("snapshot")
        self.play(FadeOut(chk), run_time=0.5)
        self.title("2 · Snapshot copy")
        bulk = arrow(old.get_right(), new.get_left(), C_CDC, sw=8)
        bl = T("snapshot at 10:00", 20, C_CDC).next_to(bulk, UP, buff=0.1)
        track = Rectangle(width=4.6, height=0.18, stroke_width=0, fill_color=GRID, fill_opacity=1).next_to(bulk, DOWN, buff=0.25)
        bar = Rectangle(width=0.01, height=0.18, stroke_width=0, fill_color=C_CDC, fill_opacity=1).align_to(track, LEFT).align_to(track, UP)
        self.play(GrowArrow(bulk), FadeIn(bl), FadeIn(track), run_time=1.0)
        full = bar.copy().stretch_to_fit_width(4.6).align_to(track, LEFT)
        self.play(Transform(bar, full), run_time=2.2, rate_func=linear)
        rows = T("1.2M rows copied", 20, C_NEW).next_to(new, DOWN, buff=0.15)
        self.play(FadeIn(rows), run_time=0.6)
        self.say("Bulk-copy a consistent snapshot. Calls keep writing to the old DB meanwhile.")
        self.end()

        self.begin("cdc")
        self.title("3 · Stream every change (CDC)")
        self.play(FadeOut(bulk), FadeOut(bl), FadeOut(track), FadeOut(bar), run_time=0.5)
        line = DashedLine(old.get_right(), new.get_left(), color=C_CDC, stroke_width=3)
        cl = VGroup(T("change stream", 20, C_CDC), T("(logical replication / GCP DMS)", 17, C_CDC)).arrange(DOWN, buff=0.04).next_to(line, UP, buff=0.12)
        lag = T("lag ≈ 2 s", 22, C_Q).next_to(line, DOWN, buff=0.2)
        self.play(Create(line), FadeIn(cl), run_time=1.0)
        for i in range(3):
            w = Dot(color=C_APP, radius=0.09).move_to(live.get_start())
            self.play(MoveAlongPath(w, live), run_time=0.4)
            d = Dot(color=C_CDC, radius=0.1).move_to(old.get_right())
            self.remove(w)
            self.play(d.animate.move_to(new.get_left()), run_time=0.7)
            self.remove(d)
            if i == 0: self.play(FadeIn(lag), run_time=0.4)
        self.say("Each insert/update on the old DB is replayed on the new one, seconds behind")
        self.end()

        self.begin("verify")
        self.title("4 · Verify")
        ver = VGroup(T("rows   1,204,331 = 1,204,331  ✓", 22, C_GOOD), T("checksums per table match  ✓", 22, C_GOOD),
                     T("shadow reads: 0 differences  ✓", 22, C_GOOD)).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to([0, -2.35, 0])
        self.play(LaggedStart(*[FadeIn(v) for v in ver], lag_ratio=0.5), run_time=2.0)
        self.say("Prove they match: counts, checksums, and the same queries run against both", size=26)
        self.end()

        self.begin("cutover")
        self.play(FadeOut(ver), run_time=0.5)
        self.title("5 · Cutover (seconds, not hours)")
        q = box("write queue", C_Q, w=2.4, h=0.8, fs=22).move_to([0, 0.15, 0])
        self.play(live.animate.set_opacity(0.25), livelab.animate.set_opacity(0.25), FadeIn(q), run_time=0.8)
        qa = arrow(app.get_bottom(), q.get_top(), C_Q, buff=0.05)
        self.play(GrowArrow(qa), run_time=0.5)
        pend = VGroup()
        for i in range(3):
            d = Dot(color=C_APP, radius=0.09).move_to(app.get_bottom())
            self.play(d.animate.move_to(q.get_bottom() + UP * 0.12 + RIGHT * (i - 1) * 0.35 + DOWN * 0.0), run_time=0.45)
            pend.add(d)
        lag0 = T("lag = 0 s", 22, C_GOOD).move_to(lag)
        self.play(Transform(lag, lag0), run_time=0.8)
        flag = T("flag: db = gcp", 22, C_NEW).next_to(app, RIGHT, buff=0.3)
        newlive = arrow(app.get_bottom() + RIGHT * 0.8, new.get_top() + LEFT * 0.6, C_APP)
        self.play(FadeIn(flag), GrowArrow(newlive), FadeOut(live), FadeOut(livelab), run_time=1.0)
        self.play(*[d.animate.move_to(new.get_top() + LEFT * 0.3 * (i - 1)) for i, d in enumerate(pend)], run_time=0.9)
        self.play(FadeOut(pend), FadeOut(qa), FadeOut(q), run_time=0.5)
        bub = VGroup(T("Agent keeps talking:", 19, C_APP), T("\"Got it, I've noted that.\"", 19, C_APP)).arrange(DOWN, buff=0.05).move_to([-3.6, 0.65, 0])
        self.play(FadeIn(bub), run_time=0.6)
        self.say("Pause writes ~10 s into a queue, wait for lag 0, flip the flag, drain the queue")
        self.end(2.2)

        self.begin("rollback")
        self.play(FadeOut(bub), run_time=0.4)
        self.title("6 · Keep a way back")
        rev = DashedLine(new.get_left(), old.get_right(), color=C_CDC, stroke_width=3)
        self.play(FadeOut(line), FadeOut(cl), run_time=0.4)
        rl = T("reverse replication  new → old", 20, C_CDC).next_to(rev, UP, buff=0.12)
        self.play(Create(rev), FadeIn(rl), run_time=1.0)
        for _ in range(2):
            d = Dot(color=C_CDC, radius=0.1).move_to(new.get_left())
            self.play(d.animate.move_to(old.get_right()), run_time=0.7); self.remove(d)
        self.say("Old DB stays in sync for a few days, so flipping back is one flag change")
        self.end(2.2)

# Colors for the worked-example symbols (same colors as the lesson page chips)
C_W = C_APP      # w  write rate (changes the app makes per second)
C_A = C_NEW      # a  apply rate (changes the new DB replays per second)
C_B = C_Q        # B  backlog / lag (changes not yet on the new DB)
C_STT = "#7dcfff"; C_TTS = "#e08fd0"; C_TOOL = C_BAD

def lines(rows, y0, buff=0.16, x=None):
    """rows: list of (text, color, size). Left-aligned block whose top sits at y0."""
    g = VGroup(*[T(t, fs, c) for t, c, fs in rows]).arrange(DOWN, aligned_edge=LEFT, buff=buff)
    if g.width > 13.2: g.scale_to_fit_width(13.2)
    g.move_to([0 if x is None else x, y0 - g.height / 2, 0])
    return g

# ------------------------------------------------------------ Chapter 3: catch-up and cutover math
class CatchUp(StepScene):
    def construct(self):
        old = box("Supabase (old)", C_OLD, w=3.2, h=1.0, fs=22).move_to([-4.7, 1.5, 0])
        new = box("GCP (new)", C_NEW, w=3.2, h=1.0, fs=22).move_to([4.7, 1.5, 0])
        app = box("Calls (app)", C_APP, w=2.6, h=0.8, fs=22).move_to([-4.7, -0.6, 0])
        wal = box("WAL", C_CDC, w=1.6, h=0.7, fs=20, sub="change log").move_to([-1.9, 1.5, 0])

        self.begin("terms")
        self.title("Two rates decide whether the copy catches up")
        self.play(FadeIn(old), FadeIn(new), FadeIn(app), run_time=1.0)
        wa = arrow(app.get_top(), old.get_bottom(), C_W)
        wl = T("w = write rate (changes/s)", 21, C_W).next_to(wa, RIGHT, buff=0.15)
        self.play(GrowArrow(wa), FadeIn(wl), run_time=0.9); self.wait(0.5)
        self.play(FadeIn(wal), run_time=0.7)
        aa = arrow(wal.get_right(), new.get_left(), C_A)
        al = T("a = apply rate (changes/s)", 21, C_A).next_to(aa, UP, buff=0.12)
        self.play(GrowArrow(aa), FadeIn(al), run_time=0.9); self.wait(0.5)
        bk = Rectangle(width=2.4, height=0.42, stroke_width=0, fill_color=C_B, fill_opacity=0.85).move_to([2.6, 0.75, 0])
        bl = VGroup(T("B = backlog:", 21, C_B), T("changes not yet on the new DB", 19, C_B)).arrange(DOWN, buff=0.06).next_to(bk, DOWN, buff=0.15)
        self.play(GrowFromEdge(bk, LEFT), FadeIn(bl), run_time=1.0); self.wait(0.4)
        rule = lines([("Backlog grows by w and shrinks by a every second", FG, 24),
                      ("net change per second = w − a", C_B, 24)], -1.6)
        self.play(FadeIn(rule[0]), run_time=0.8); self.wait(0.6)
        self.play(FadeIn(rule[1]), run_time=0.8)
        self.say("Every change hits the WAL first; logical replication replays it on the new DB")
        self.end()

        # chart helper: backlog over time
        def chart(segs, tmax_h, bmax, color_rows=None):
            ox, oy, W, H = -5.4, -0.15, 10.8, 2.5
            ax = VGroup(Line([ox, oy, 0], [ox + W, oy, 0], color=MUTED, stroke_width=2),
                        Line([ox, oy, 0], [ox, oy + H, 0], color=MUTED, stroke_width=2))
            yl = T("backlog B", 17, C_B).next_to(ax[1], UP, buff=0.08)
            xl = T("time (hours)", 17, MUTED).next_to(ax[0], DOWN, buff=0.08).align_to(ax[0], RIGHT).shift(DOWN * 0.22)
            P = lambda t, b: [ox + W * t / tmax_h, oy + H * min(b, bmax) / bmax, 0]
            ticks = VGroup(*[T(f"{h}", 15, MUTED).move_to([ox + W * h / tmax_h, oy - 0.2, 0]) for h in range(0, int(tmax_h) + 1)])
            parts = VGroup(*[Line(P(*a), P(*b), color=c, stroke_width=5) if not dash else DashedLine(P(*a), P(*b), color=c, stroke_width=5)
                             for a, b, c, dash in segs])
            return VGroup(ax, yl, xl, ticks), parts, P

        self.begin("ex1")
        self.play(*[FadeOut(m) for m in [old, new, app, wal, wa, wl, aa, al, bk, bl, rule]], run_time=0.7)
        self.title("Worked example 1 · w = 50/s, snapshot 2 h, a = 250/s")
        frame, parts, P = chart([((0, 0), (2, 360000), C_B, False), ((2, 360000), (2.5, 0), C_A, False)], 3, 400000)
        self.play(FadeIn(frame), run_time=0.7)
        e = lines([("1. Snapshot time T = 2 h = 2 × 3,600 = 7,200 s", FG, 23),
                   ("2. Backlog B = w × T = 50 × 7,200 = 360,000 changes", C_B, 23),
                   ("3. Net shrink = a − w = 250 − 50 = 200 changes/s", C_A, 23),
                   ("4. Catch-up = B ÷ (a − w) = 360,000 ÷ 200 = 1,800 s = 30 min", C_GOOD, 23)], -0.75)
        self.play(FadeIn(e[0]), run_time=0.7); self.wait(0.6)
        self.play(Create(parts[0]), FadeIn(e[1]), run_time=1.6); self.wait(0.8)
        pk = T("360,000", 17, C_B).next_to(P(2, 360000), UP, buff=0.08)
        self.play(FadeIn(pk), FadeIn(e[2]), run_time=0.9); self.wait(0.8)
        self.play(Create(parts[1]), FadeIn(e[3]), run_time=1.4)
        self.say("Snapshot builds the backlog; the net rate a − w drains it")
        self.end(2.0)

        self.begin("ex2")
        self.play(FadeOut(e), FadeOut(parts[1]), FadeOut(pk), run_time=0.6)
        self.title("Worked example 2 (edge case) · a is not above w")
        flat = DashedLine(P(2, 360000), P(3, 360000), color=C_BAD, stroke_width=5)
        up = Line(P(2, 360000), P(3, 396000), color=C_BAD, stroke_width=5)
        e2 = lines([("a = 50/s:  net = 50 − 50 = 0/s  →  360,000 ÷ 0  →  never catches up", C_BAD, 23),
                    ("a = 40/s:  net = 40 − 50 = −10/s  →  backlog GROWS 10 × 3,600 = 36,000 per hour", C_BAD, 23),
                    ("Plan with PEAK w (≈ 3 × average): 3 × 50 = 150/s, so you need a > 150/s", C_W, 23),
                    ("Fixes: parallel apply, bigger target, build indexes after the copy, run off-peak", FG, 21)], -0.75)
        self.play(Create(flat), FadeIn(e2[0]), run_time=1.2); self.wait(0.8)
        self.play(Create(up), FadeIn(e2[1]), run_time=1.2); self.wait(0.8)
        self.play(FadeIn(e2[2]), run_time=0.8); self.wait(0.6)
        self.play(FadeIn(e2[3]), run_time=0.8)
        self.say("If a ≤ w the division has no positive answer: the copy never catches up", C_BAD)
        self.end(2.0)

        self.begin("cutover")
        self.play(*[FadeOut(m) for m in [frame, parts[0], flat, up, e2]], run_time=0.6)
        self.title("Cutover math · lag 2 s, w = 50/s, a = 250/s")
        e3 = lines([("1. In flight = w × lag = 50 × 2 = 100 changes", C_B, 24),
                    ("2. Pause writes into a queue for 5 s: 5 × 50 = 250 queued writes", C_Q, 24),
                    ("3. Drain in-flight changes: 100 ÷ 250 = 0.4 s  →  lag = 0", C_A, 24),
                    ("4. Flip the flag, replay the queue on GCP: 250 ÷ 250 = 1 s", C_NEW, 24),
                    ("Callers wait seconds, not hours, because B is tiny by now", C_GOOD, 24)], 2.2, buff=0.3)
        for i, l in enumerate(e3):
            self.play(FadeIn(l, shift=UP * 0.1), run_time=0.7); self.wait(0.7)
        self.say("Same two rates, tiny backlog: the write pause lasts seconds")
        self.end(2.0)

        self.begin("faded")
        self.play(FadeOut(e3), run_time=0.6)
        self.title("Your turn · w = 30/s, snapshot 4 h, a = 150/s")
        e4 = lines([("1. T = 4 × 3,600 = 14,400 s", FG, 24),
                    ("2. B = w × T = 30 × 14,400 = 432,000 changes", C_B, 24),
                    ("3. Net shrink = a − w = 150 − 30 = 120 changes/s", C_A, 24),
                    ("4. Catch-up = 432,000 ÷ 120 = ?", C_GOOD, 26)], 2.0, buff=0.32)
        for l in e4[:3]:
            self.play(FadeIn(l, shift=UP * 0.1), run_time=0.7); self.wait(0.6)
        self.play(FadeIn(e4[3], shift=UP * 0.1), run_time=0.8)
        box4 = SurroundingRectangle(e4[3], color=C_GOOD, buff=0.15)
        self.play(Create(box4), run_time=0.7)
        self.say("Pause here: do step 4 on paper, then check it beside the video")
        self.end(2.0)

# ------------------------------------------------------------ Chapter 4: voice pipeline and its latency budget
class Voice(StepScene):
    def construct(self):
        P = {"caller": [-5.4, 1.3], "tel": [-1.9, 1.3], "media": [1.6, 1.3], "stt": [5.0, 1.3], "llm": [5.0, -1.2], "tts": [1.6, -1.2]}
        caller = box("Caller", C_APP, w=2.4, h=1.0, fs=24, sub="phone").move_to(P["caller"] + [0])
        tel = box("Telephony", FG, w=2.8, h=1.0, fs=24, sub="PSTN / SIP").move_to(P["tel"] + [0])
        media = box("Media server", FG, w=2.8, h=1.0, fs=24, sub="audio streams").move_to(P["media"] + [0])
        stt = box("STT", C_STT, w=2.4, h=1.0, fs=24, sub="speech → text").move_to(P["stt"] + [0])
        llm = box("LLM agent", C_APP, w=2.6, h=1.0, fs=24, sub="+ tools (PMS)").move_to(P["llm"] + [0])
        tts = box("TTS", C_TTS, w=2.4, h=1.0, fs=24, sub="text → speech").move_to(P["tts"] + [0])
        arrs = VGroup(arrow(caller.get_right(), tel.get_left()), arrow(tel.get_right(), media.get_left()),
                      arrow(media.get_right(), stt.get_left()), arrow(stt.get_bottom(), llm.get_top()),
                      arrow(llm.get_left(), tts.get_right()), arrow(tts.get_top(), media.get_bottom()))
        diag = VGroup(caller, tel, media, stt, llm, tts, arrs)

        self.begin("path")
        self.title("One turn of a phone call")
        for m, a in zip([caller, tel, media, stt, llm, tts], list(arrs) + [None]):
            self.play(FadeIn(m), run_time=0.5)
            if a is not None: self.play(GrowArrow(a), run_time=0.35)
        self.play(GrowArrow(arrs[5]), run_time=0.4)
        d = Dot(color=C_Q, radius=0.12).move_to(caller)
        for m in [tel, media, stt, llm, tts, media, tel, caller]:
            self.play(d.animate.move_to(m), run_time=0.45)
        self.play(FadeOut(d), run_time=0.3)
        self.say("Caller audio → STT → LLM (may call tools) → TTS → back to the caller")
        self.end()

        S = 4.2 / 1000  # 1000 ms = 4.2 units
        def bars(parts, y, x0=-6.0):
            g = VGroup(); x = x0
            for name, ms, c in parts:
                r = Rectangle(width=ms * S, height=0.5, stroke_width=1, stroke_color="#0e1117", fill_color=c, fill_opacity=0.85)
                r.move_to([x + ms * S / 2, y, 0]); x += ms * S
                l = T(f"{name} {ms}", 15, "#0e1117").move_to(r)
                if l.width > r.width - 0.05: l.scale_to_fit_width(r.width - 0.08)
                g.add(VGroup(r, l))
            return g, x

        self.begin("seq")
        self.title("Worked example 1 · no streaming (each stage waits)")
        self.play(diag.animate.scale(0.55).move_to([0, 1.6, 0]), run_time=1.0)
        limit = DashedLine([-6.0 + 4.2, 0.0, 0], [-6.0 + 4.2, -0.9, 0], color=C_Q)
        ll = T("1 s", 20, C_Q).next_to(limit, UP, buff=0.05)
        slow, xe = bars([("net", 100, MUTED), ("STT final", 300, C_STT), ("LLM full answer", 1400, C_APP), ("TTS full", 600, C_TTS), ("net", 100, MUTED)], -0.45)
        self.play(Create(limit), FadeIn(ll), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.2) for b in slow], lag_ratio=0.5), run_time=2.4)
        eq1 = T("100 + 300 + 1,400 + 600 + 100 = 2,500 ms of silence", 22, C_BAD).move_to([0, -1.15, 0])
        self.play(FadeIn(eq1), run_time=0.8)
        self.say("Wait for each stage to finish: the silences add up to 2.5 s", C_BAD)
        self.end(2.0)

        self.begin("stream")
        self.title("Worked example 2 · streaming (only the first piece counts)")
        fast, xe2 = bars([("net", 100, MUTED), ("STT", 200, C_STT), ("LLM 1st sentence", 350, C_APP), ("TTS 1st audio", 150, C_TTS), ("net", 100, MUTED)], -1.85)
        limit2 = DashedLine([-6.0 + 4.2, -1.4, 0], [-6.0 + 4.2, -2.3, 0], color=C_Q)
        self.play(Create(limit2), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.2) for b in fast], lag_ratio=0.5), run_time=2.2)
        eq2 = T("100 + 200 + 350 + 150 + 100 = 900 ms  ✓ under 1 s", 22, C_GOOD).move_to([0, -2.55, 0])
        self.play(FadeIn(eq2), run_time=0.8)
        self.say("Same models; the rest of the answer is generated while the first sentence plays")
        self.end(2.0)

        self.begin("tool")
        self.play(*[FadeOut(m) for m in [slow, fast, eq1, eq2, limit, limit2, ll]], run_time=0.6)
        self.title("Worked example 3 (edge case) · a 1.2 s PMS lookup")
        x0 = -6.0; S2 = 4.6 / 1000
        def seg(t0, t1, y, c, lab):
            r = Rectangle(width=(t1 - t0) * S2, height=0.48, stroke_width=1, stroke_color="#0e1117", fill_color=c, fill_opacity=0.85)
            r.move_to([x0 + (t0 + t1) / 2 * S2, y, 0])
            l = T(lab, 14, "#0e1117").move_to(r)
            if l.width > r.width - 0.05: l.scale_to_fit_width(r.width - 0.08)
            return VGroup(r, l)
        rowA = T("agent", 17, MUTED).move_to([x0 - 0.5, 0.0, 0]); rowC = T("caller", 17, MUTED).move_to([x0 - 0.5, -0.75, 0])
        agent = VGroup(seg(0, 100, 0, MUTED, "net"), seg(100, 300, 0, C_STT, "STT"), seg(300, 600, 0, C_APP, "LLM →tool"),
                       seg(600, 1800, 0, C_TOOL, "PMS lookup 1,200"), seg(1800, 2150, 0, C_APP, "LLM"), seg(2150, 2300, 0, C_TTS, "TTS"), seg(2300, 2400, 0, MUTED, "net"))
        tick = VGroup(*[T(f"{t/1000:g} s", 14, MUTED).move_to([x0 + t * S2, -1.2, 0]) for t in (0, 1000, 2000)])
        self.play(FadeIn(rowA), FadeIn(rowC), FadeIn(tick), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(s) for s in agent], lag_ratio=0.4), run_time=2.4)
        e = lines([("Tool call starts at 100 + 200 + 300 = 600 ms", FG, 21),
                   ("Answer audio at 600 + 1,200 + 350 + 150 + 100 = 2,400 ms  →  2.4 s of silence", C_BAD, 21),
                   ("Filler (pre-recorded “Let me check that”, 1.5 s) at 600 + 100 = 700 ms", C_TTS, 21),
                   ("Silence left: 700 ms before it + (2,400 − 2,200) = 200 ms after it", C_GOOD, 21)], -1.55)
        self.play(FadeIn(e[0]), run_time=0.7); self.wait(0.6)
        silent = seg(0, 2400, -0.75, "#3a2030", "silence 2,400 ms")
        self.play(FadeIn(silent), FadeIn(e[1]), run_time=0.9); self.wait(0.9)
        filler = seg(700, 2200, -0.75, C_TTS, "filler 1.5 s"); ans = seg(2400, 2700, -0.75, C_GOOD, "answer")
        self.play(FadeIn(filler), FadeIn(ans), FadeIn(e[2]), run_time=0.9); self.wait(0.8)
        self.play(FadeIn(e[3]), run_time=0.8)
        self.say("Tool calls blow the budget; speak a filler line while the PMS answers")
        self.end(2.0)

        self.begin("faded")
        self.play(*[FadeOut(m) for m in [rowA, rowC, tick, agent, silent, filler, ans, e]], run_time=0.6)
        self.title("Your turn · streaming, different vendors")
        e4 = lines([("net 80  +  STT 250  +  LLM 1st sentence 400  +  TTS 1st audio 200  +  net 80", FG, 23),
                    ("1. 80 + 250 + 400 = 730 ms", C_STT, 24),
                    ("2. 730 + 200 + 80 = ?   Under 1 s or not?", C_GOOD, 26)], -0.2, buff=0.35)
        for l in e4:
            self.play(FadeIn(l, shift=UP * 0.1), run_time=0.8); self.wait(0.6)
        self.play(Create(SurroundingRectangle(e4[2], color=C_GOOD, buff=0.14)), run_time=0.7)
        self.say("Pause here: finish the sum on paper, then check it beside the video")
        self.end(2.0)

        self.begin("bargein")
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (diag, self.ttl, self.cap)], run_time=0.6)
        self.play(diag.animate.scale(1 / 0.55).move_to([0, 0.05, 0]), run_time=0.9)
        self.title("Barge-in and turn detection")
        sp = T("TTS: \"Your next opening is Monday at 9…\"", 20, C_TTS).next_to(tts, LEFT, buff=0.35)
        self.play(FadeIn(sp), run_time=0.7)
        cut = T("Caller: \"Wait, Tuesday!\"", 22, C_APP).next_to(caller, DOWN, buff=0.35)
        self.play(FadeIn(cut, shift=UP * 0.1), run_time=0.6)
        x = T("✕ TTS stopped mid-sentence", 21, C_BAD).next_to(sp, DOWN, buff=0.2)
        self.play(FadeIn(x), sp.animate.set_opacity(0.35), run_time=0.6)
        self.say("Detect the caller speaking → stop TTS instantly; a turn detector decides when they're done")
        self.end()

        self.begin("livekit")
        self.play(FadeOut(sp), FadeOut(x), FadeOut(cut), run_time=0.5)
        self.title("Where LiveKit fits")
        l1 = T("LiveKit SIP", 20, C_LK).next_to(tel, UP, buff=0.45)
        l2 = T("LiveKit server (WebRTC)", 20, C_LK).next_to(media, UP, buff=0.45)
        grp = DashedVMobject(SurroundingRectangle(VGroup(stt, llm, tts), color=C_LK, buff=0.22, corner_radius=0.2), num_dashes=70)
        l3 = T("LiveKit Agents: your Python/Node code, any STT/LLM/TTS plugin", 20, C_LK).next_to(grp, DOWN, buff=0.12).shift(LEFT * 1.2)
        self.play(FadeIn(l1), tel[0].animate.set_stroke(C_LK), run_time=0.8)
        self.play(FadeIn(l2), media[0].animate.set_stroke(C_LK), run_time=0.8)
        self.play(Create(grp), FadeIn(l3), run_time=1.2)
        self.say("Open source (Apache 2.0): self-host it or use LiveKit Cloud", C_LK)
        self.end()

        self.begin("tradeoff")
        self.play(*[FadeOut(m) for m in [diag, l1, l2, grp, l3]], run_time=0.7)
        self.title("Moving to LiveKit: the tradeoff")
        pro = VGroup(T("Why move", 26, C_GOOD), *[T("• " + s, 21) for s in ["own the pipeline → tune latency", "swap STT / LLM / TTS vendors freely", "cheaper per minute at high volume", "self-host option: control over data"]]).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([-3.4, 0, 0])
        con = VGroup(T("What it costs", 26, C_BAD), *[T("• " + s, 21) for s in ["you operate more (scaling, SIP, monitoring)", "rebuild what the old platform did", "migrating live call traffic safely", "need voice / real-time expertise"]]).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([3.4, 0, 0])
        self.play(FadeIn(pro[0]), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(p) for p in pro[1:]], lag_ratio=0.4), run_time=1.6)
        self.play(FadeIn(con[0]), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(p) for p in con[1:]], lag_ratio=0.4), run_time=1.6)
        self.say("Control and cost vs operating burden: same shape as the DB migration")
        self.end(2.2)

# ------------------------------------------------------------ Chapter 5: PMS writes, counted
X_ = "✗"; W_ = "⚠"; OK_ = "✓"
OUT = {X_: ("failed before writing", MUTED), W_: ("wrote, reply lost", C_Q), OK_: ("wrote, reply OK", C_GOOD)}
class PMS(StepScene):
    def construct(self):
        agent = box("Voice agent", C_APP, w=2.8, h=1.0, fs=24).move_to([-4.6, 1.0, 0])
        pms = box("Clinic PMS", FG, w=2.8, h=1.0, fs=24, sub="slow, flaky, rate-limited").move_to([4.6, 1.0, 0])
        self.begin("retry")
        self.title("Calling someone else's system")
        self.play(FadeIn(agent), FadeIn(pms), run_time=0.8)
        a = arrow(agent.get_right(), pms.get_left(), C_APP)
        al = T("book(10:30, Bella)", 20, C_APP).next_to(a, UP, buff=0.1)
        self.play(GrowArrow(a), FadeIn(al), run_time=0.8)
        clock = T("timeout 3 s", 22, C_Q).next_to(a, DOWN, buff=0.15)
        self.play(FadeIn(clock), run_time=0.5); self.wait(0.6)
        xx = Cross(clock, stroke_color=C_BAD, stroke_width=4)
        self.play(Create(xx), run_time=0.5)
        tries = VGroup(*[T(s, 21, C_Q) for s in ["retry after 0.5 s", "retry after 1 s", "retry after 2 s (+ jitter)"]]).arrange(DOWN, buff=0.1).move_to([0, -1.2, 0])
        self.play(LaggedStart(*[FadeIn(t) for t in tries], lag_ratio=0.6), run_time=2.0)
        self.say("Never wait forever: time out, retry with growing backoff, then give up gracefully")
        self.end()

        self.begin("idem")
        self.play(FadeOut(tries), FadeOut(clock), FadeOut(xx), run_time=0.5)
        self.title("Idempotency: retries must not double-book")
        cal = VGroup(T("PMS calendar", 20, MUTED), T("10:30 Bella (dog)", 22), T("10:30 Bella (dog)", 22, C_BAD)).arrange(DOWN, buff=0.12).next_to(pms, DOWN, buff=0.4)
        lost = T("booked… but reply lost", 20, C_BAD).move_to([0, 0.0, 0])
        self.play(FadeIn(cal[0]), FadeIn(cal[1]), FadeIn(lost), run_time=0.9); self.wait(0.6)
        self.play(FadeIn(cal[2]), Indicate(cal[2], color=C_BAD), run_time=1.0)
        self.wait(0.6)
        key = T("Idempotency-Key: call-8812-book-1", 21, C_GOOD).move_to([-1.0, -1.6, 0])
        same = T("same key → return the existing booking", 21, C_GOOD).next_to(key, DOWN, buff=0.15)
        self.play(FadeIn(key), run_time=0.7)
        self.play(FadeOut(cal[2]), FadeIn(same), FadeOut(lost), run_time=1.0)
        self.say("Attach a unique key to every write; a repeat with the same key changes nothing")
        self.end()

        def legend():
            g = VGroup(*[VGroup(T(k, 26, OUT[k][1]), T(OUT[k][0], 20, OUT[k][1])).arrange(RIGHT, buff=0.15) for k in (X_, W_, OK_)]).arrange(RIGHT, buff=0.7)
            return g.move_to([0, 2.45, 0])
        def attempts(seq, y=1.3):
            g = VGroup(*[box(f"try {i+1}  {s}", OUT[s][1], w=2.3, h=0.75, fs=22) for i, s in enumerate(seq)]).arrange(RIGHT, buff=0.35)
            return g.move_to([0, y, 0])

        self.begin("count")
        self.play(*[FadeOut(m) for m in [agent, pms, a, al, cal[0], cal[1], key, same]], run_time=0.6)
        self.title("Counting appointments, attempt by attempt")
        lg = legend()
        self.play(LaggedStart(*[FadeIn(x) for x in lg], lag_ratio=0.5), run_time=1.8); self.wait(0.6)
        r = lines([("No key:   appointments = number of tries that WROTE (⚠ or ✓)", C_BAD, 24),
                   ("With key: appointments = 1 if any try wrote (PMS returns the first one)", C_GOOD, 24),
                   ("The agent keeps retrying until ✓ or it runs out of tries", MUTED, 21)], 1.2, buff=0.35)
        for l in r:
            self.play(FadeIn(l, shift=UP * 0.1), run_time=0.8); self.wait(0.6)
        self.say("Only tries that reached the PMS write can create an appointment")
        self.end(2.0)

        self.begin("ex1")
        self.play(FadeOut(r), run_time=0.5)
        self.title("Worked example 1 · ⚠ then ✓")
        at = attempts([W_, OK_])
        self.play(LaggedStart(*[FadeIn(x) for x in at], lag_ratio=0.5), run_time=1.4); self.wait(0.5)
        e = lines([("No key:   try 1 wrote (1) + try 2 wrote (1) = 2 appointments  ✗ double-booked", C_BAD, 23),
                   ("With key: try 2 sends call-8812-book-1 again → PMS returns try 1's booking", C_GOOD, 23),
                   ("               = 1 appointment  ✓", C_GOOD, 23)], 0.2, buff=0.3)
        for l in e:
            self.play(FadeIn(l, shift=UP * 0.1), run_time=0.8); self.wait(0.7)
        self.say("A lost reply is the whole danger: the write happened, the agent doesn't know")
        self.end(2.0)

        self.begin("ex2")
        self.play(FadeOut(at), FadeOut(e), run_time=0.5)
        self.title("Worked example 2 (edge cases) · ⚠ ⚠ ⚠ and ✗ ✗ ✓")
        at2 = attempts([W_, W_, W_])
        self.play(LaggedStart(*[FadeIn(x) for x in at2], lag_ratio=0.5), run_time=1.5); self.wait(0.5)
        e2 = lines([("No key:   1 + 1 + 1 = 3 appointments, and the agent tells the caller it FAILED", C_BAD, 22),
                    ("With key: 1 appointment. Before saying “failed”, look up the key → it's booked", C_GOOD, 22),
                    ("✗ ✗ ✓:   0 + 0 + 1 = 1 either way: retries are harmless if nothing was written", MUTED, 22)], 0.2, buff=0.32)
        for l in e2:
            self.play(FadeIn(l, shift=UP * 0.1), run_time=0.8); self.wait(0.7)
        self.say("Out of tries ≠ not booked. Check the key before telling the caller", C_Q)
        self.end(2.0)

        self.begin("faded")
        self.play(FadeOut(at2), FadeOut(e2), run_time=0.5)
        self.title("Your turn · ✗ then ⚠ then ✓")
        at3 = attempts([X_, W_, OK_])
        self.play(LaggedStart(*[FadeIn(x) for x in at3], lag_ratio=0.5), run_time=1.5); self.wait(0.5)
        e3 = lines([("No key:   0 + 1 + 1 = 2 appointments", C_BAD, 24),
                    ("With key: ?", C_GOOD, 26)], 0.2, buff=0.35)
        self.play(FadeIn(e3[0]), run_time=0.8); self.wait(0.7)
        self.play(FadeIn(e3[1]), run_time=0.8)
        self.play(Create(SurroundingRectangle(e3[1], color=C_GOOD, buff=0.14)), run_time=0.7)
        self.say("Pause here: count the with-key case, then check it beside the video")
        self.end(2.0)

        self.begin("tenant")
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (self.ttl, self.cap)], run_time=0.6)
        self.title("Multi-tenant isolation")
        ca = box("Paws Vet", C_OLD, w=4.2, h=2.4, fs=26, sub="PMS creds · hours · rules").move_to([-3.3, 0.1, 0])
        cb = box("Smile Dental", C_NEW, w=4.2, h=2.4, fs=26, sub="PMS creds · hours · rules").move_to([3.3, 0.1, 0])
        wall = Line([0, 1.5, 0], [0, -1.3, 0], color=C_BAD, stroke_width=6)
        self.play(FadeIn(ca), FadeIn(cb), run_time=0.8)
        self.play(Create(wall), run_time=0.6)
        rule = T("every query, cache key, log and prompt is scoped by clinic_id", 22, C_Q).move_to([0, -1.9, 0])
        self.play(FadeIn(rule), run_time=0.8)
        self.say("One clinic must never see another's patients, even through a cache or an LLM prompt")
        self.end()

        self.begin("fallback")
        self.play(FadeOut(ca), FadeOut(cb), FadeOut(wall), FadeOut(rule), run_time=0.6)
        self.title("When the PMS or the LLM is down")
        agent.move_to([-4.6, 1.0, 0]); pms2 = box("Clinic PMS", C_BAD, w=2.8, h=1.0, fs=24, sub="DOWN").move_to([4.6, 1.0, 0])
        self.play(FadeIn(agent), FadeIn(pms2), run_time=0.7)
        sayit = T("\"I've noted your request; the clinic will text to confirm.\"", 21, C_APP).move_to([0, -0.1, 0])
        self.play(FadeIn(sayit), run_time=0.8)
        q = box("task queue → staff / retry later", C_Q, w=5.2, h=0.9, fs=22).move_to([0, -1.3, 0])
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.8)
        llm = T("LLM down → backup model, or transfer to the front desk", 21, MUTED).move_to([0, -2.4, 0])
        self.play(FadeIn(llm), run_time=0.7)
        self.say("The call is always answered; the work is never lost")
        self.end(2.2)
