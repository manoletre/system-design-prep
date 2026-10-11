import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE); SITE = os.path.dirname(SRC)
STEPS = f"{SRC}/manim/steps"; VID = f"{SRC}/manim/media/videos/sd_scenes/1080p30"
TPL = open(f"{HERE}/template.html").read()
SYM = {
 "old": ["Supabase · old DB", "Where Dodo's data lives today."],
 "new": ["GCP · new DB", "Cloud SQL for Postgres or AlloyDB."],
 "cdc": ["Change stream (CDC)", "Every insert/update/delete replayed on the other DB."],
 "app": ["App / voice agent", "The code answering calls; it must never stop."],
 "q": ["Queue · timers", "Buffers writes or retries; timeouts and backoff."],
 "lk": ["LiveKit", "Open-source real-time media + Agents framework."],
}
def enc(src, dst, poster_t, poster):
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-c:v","libx264","-pix_fmt","yuv420p","-profile:v","high","-crf","23","-movflags","+faststart","-an",dst],check=True)
    subprocess.run(["ffmpeg","-v","error","-y","-ss",str(poster_t),"-i",dst,"-frames:v","1","-vf","scale=1280:-1","-q:v","4",poster],check=True)
def build(L, outdir):
    os.makedirs(f"{outdir}/media", exist_ok=True); chapters = []
    for c in L["chapters"]:
        j = json.load(open(f"{STEPS}/{c['scene']}.json"))
        assert [s["key"] for s in j["steps"]] == [s[0] for s in c["steps"]], c["scene"]
        name = c["file"]
        enc(f"{VID}/{c['scene']}.mp4", f"{outdir}/media/{name}.mp4", j["steps"][0]["end"] - 0.2, f"{outdir}/media/{name}-poster.jpg")
        steps = []
        for (k, title, html, *rest), t in zip(c["steps"], j["steps"]):
            d = {"key": k, "title": title, "html": html, "start": t["start"], "end": t["end"]}
            if rest: d["resolves"] = rest[0]
            steps.append(d)
        chapters.append({"title": c["title"], "short": c["short"], "video": f"media/{name}.mp4", "poster": f"media/{name}-poster.jpg",
                         "steps": steps, "check": c["check"], "duration": j["duration"]})
    data = {"id": L["id"], "hook": L["hook"], "key": L["key"], "sym": SYM, "macros": {}, "chapters": chapters,
            "drill": L.get("drill", []), "summary": L["summary"]}
    html = TPL.replace("__TITLE__", L["title"]).replace("__H1__", L["h1"]).replace("__SUB__", L["sub"]).replace("__DATA__", json.dumps(data, ensure_ascii=False))
    open(f"{outdir}/index.html", "w").write(html); print("built", outdir, [len(c["steps"]) for c in chapters])
sys.path.insert(0, HERE)
from content import D1
if __name__ == "__main__":
    build(D1, f"{SITE}/lessons/dodo-1")
