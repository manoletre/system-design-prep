"""Build lesson pages with player v4 (ported from manoletre/liquid-ai-prep).
usage: python3 source/build/build.py            (all lessons)   |   python3 source/build/build.py dodo1"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE); SITE = os.path.dirname(SRC)
STEPS = f"{SRC}/manim/steps"
VID = f"{SRC}/manim/media/videos/sd_scenes/1080p30"   # rendered with: manim -r 1920,1080 --fps 30 sd_scenes.py <Scene>
TPL = open(f"{HERE}/template.html").read()

# Symbol chips/tooltips: [label, explanation]. Each symbol keeps one color everywhere (template CSS .k-<key>, Manim C_* constants).
SYM_ALL = {
 "old": ["Supabase · old DB", "Where Dodo's data lives today."],
 "new": ["GCP · new DB", "Cloud SQL for Postgres or AlloyDB."],
 "cdc": ["Change stream (CDC)", "Reads the old DB's WAL and replays every insert/update/delete on the other DB."],
 "app": ["App / voice agent", "The code answering calls; it must never stop."],
 "q": ["Queue · timers", "Buffers writes or retries; timeouts and backoff."],
 "lk": ["LiveKit", "Open-source real-time media server + SIP bridge + Agents framework."],
 "w": ["w · write rate", "Changes per second the app makes on the old DB. Plan with the peak (≈ 3× average)."],
 "ap": ["a · apply rate", "Changes per second the new DB can replay from the change stream."],
 "B": ["B · backlog / lag", "Changes made on the old DB that the new DB hasn't applied yet."],
 "stt": ["STT · speech-to-text", "Turns the caller's audio into words, ideally streaming partial words."],
 "tts": ["TTS · text-to-speech", "Turns the agent's words into audio; streaming starts with the first sentence."],
}
MACROS = {"\\Wr": ["w", "w"], "\\Ap": ["ap", "a"], "\\Bk": ["B", "B"]}

def enc(src, dst, poster_t, poster):
    if os.path.exists(dst) and os.path.exists(poster) and os.path.getmtime(dst) > os.path.getmtime(src):
        return  # already encoded from this render
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-c:v","libx264","-pix_fmt","yuv420p","-profile:v","high","-crf","23","-movflags","+faststart","-an",dst],check=True)
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(poster_t),"-i",dst,"-frames:v","1","-vf","scale=1280:-1","-q:v","4",poster],check=True)

def build(L, outdir):
    os.makedirs(f"{outdir}/media", exist_ok=True); chapters = []
    for c in L["chapters"]:
        j = json.load(open(f"{STEPS}/{c['scene']}.json"))
        keys = [s["key"] for s in j["steps"]]
        assert keys == [s[0] for s in c["steps"]], (c["scene"], keys)
        name = c["file"]
        enc(f"{VID}/{c['scene']}.mp4", f"{outdir}/media/{name}.mp4", j["steps"][0]["end"] - 0.2, f"{outdir}/media/{name}-poster.jpg")
        steps = [{"key": k, "title": title, "html": html, "start": t["start"], "end": t["end"]} for (k, title, html, *_), t in zip(c["steps"], j["steps"])]
        chapters.append({"title": c["title"], "short": c["short"], "video": f"media/{name}.mp4", "poster": f"media/{name}-poster.jpg",
                         "steps": steps, "check": c["check"], "hook": c.get("hook"), "duration": j["duration"]})
    for c in chapters: assert c["hook"] and c["check"], ("every chapter needs a hook (prediction) and a check (practice)", c["title"])
    data = {"id": L["id"], "title": L["title"], "h1": L["h1"], "sub": L["sub"], "drill": L.get("drill", []), "key": L["key"],
            "sym": SYM_ALL, "macros": MACROS, "chapters": chapters, "summary": L["summary"]}
    html = TPL.replace("__TITLE__", L["title"]).replace("__H1__", L["h1"]).replace("__SUB__", L["sub"]).replace("__DATA__", json.dumps(data, ensure_ascii=False))
    open(f"{outdir}/index.html", "w").write(html); print("built", outdir, [len(c["steps"]) for c in chapters])
    used = {f"{c['file']}{ext}" for c in L["chapters"] for ext in (".mp4", "-poster.jpg")}
    for f in os.listdir(f"{outdir}/media"):
        if f not in used: os.remove(f"{outdir}/media/{f}"); print("removed unused", f)

sys.path.insert(0, HERE)
from content import LESSONS
if __name__ == "__main__":
    for n in sys.argv[1:] or list(LESSONS):
        L = LESSONS[n]; build(L, f"{SITE}/lessons/{L['slug']}")
