# Step keys must match the Manim scene step keys (checked by build.py).
O = lambda t: f'<span class="k-old">{t}</span>'
N = lambda t: f'<span class="k-new">{t}</span>'
C = lambda t: f'<span class="k-cdc">{t}</span>'
A = lambda t: f'<span class="k-app">{t}</span>'
Q = lambda t: f'<span class="k-q">{t}</span>'
K = lambda t: f'<span class="k-lk">{t}</span>'

D1 = {
 "id": "dodo1", "title": "Dodo prep 1 · DB migration, voice agents, LiveKit", "h1": "Dodo prep 1: migrating a live database & how voice agents work",
 "sub": "For the dodo.ai first round · 4 chapters, 20 short steps · about 30 minutes at your own pace",
 "key": ["old", "new", "cdc", "app", "q", "lk"],
 "hook": {"id": "hook", "whereLabel": "chapter 2, step 5",
   "q": "Dodo is on Supabase and wants to move to GCP while calls keep coming in 24/7. What could go wrong, and how would you avoid dropping a single call?",
   "model": "What can go wrong: writes made during the copy get lost, the two databases drift, Supabase-only features (Auth, Storage, RLS that calls auth.uid()) break, and a long maintenance window means unanswered calls. How to avoid it: inventory first, copy a snapshot, stream every change with CDC (logical replication / Database Migration Service), verify with counts, checksums and shadow reads, then cut over by pausing writes for seconds into a queue, waiting for lag 0 and flipping a flag. The agent keeps talking (\"I've noted that, the clinic will confirm\"), and reverse replication keeps a rollback path."},
 "chapters": [
  {"scene": "SupaGCP", "file": "ch1-supabase-vs-gcp", "title": "What Supabase is, and what GCP gives you", "short": "Supabase vs GCP",
   "steps": [
    ("supa", "Supabase is a bundle", f"{O('Supabase')} is hosted <b>Postgres</b> plus extras: <b>Auth</b> (users, logins, tokens), <b>Storage</b> (files), <b>Realtime</b> (push DB changes to clients) and <b>row-level security</b> (RLS: rules inside Postgres that decide which rows each user can see). Startups pick it because one product covers all of that."),
    ("gcp", "GCP gives you the database", f"On GCP the target is {N('Cloud SQL for Postgres')} (managed Postgres) or {N('AlloyDB')} (Google's faster, Postgres-compatible engine). The engine stays Postgres, so tables and SQL move easily. The extras don't come along: auth → Identity Platform or your own, files → Cloud Storage, realtime → Pub/Sub or your own service."),
    ("gotcha", "The hidden coupling", f"RLS policies themselves are plain Postgres, but Supabase's policies usually call <code>auth.uid()</code>, which only works with Supabase Auth. Auth is often the hardest part of leaving Supabase, so plan it first. In the interview: <i>“the database is the easy part; everything around it is the work.”</i>"),
    ("why", "Why migrate at all?", f"Common reasons: <b>compliance</b> (HIPAA controls under one cloud agreement, private networking, audit logs), <b>one cloud</b> (keep data next to the services and credits you already use on GCP), <b>scale and control</b> (replicas, tuning, backups, extensions) and <b>cost</b> at scale. Ask Tim which one drives it, because that defines what “done” means."),
   ],
   "check": {"id": "c1", "q": "In one or two sentences: why is “just copy the Postgres database to Cloud SQL” not the whole migration from Supabase?",
             "model": "Supabase is Postgres plus Auth, Storage, Realtime and RLS policies tied to Supabase Auth (auth.uid()). Cloud SQL / AlloyDB only gives you Postgres, so auth, files, realtime and the policies that depend on auth need their own plan."}},
  {"scene": "Playbook", "file": "ch2-zero-downtime-playbook", "title": "The zero-downtime migration playbook", "short": "Playbook",
   "steps": [
    ("inventory", "1 · Inventory", f"Before moving data, list everything the {O('old DB')} does: tables and indexes, extensions, RLS policies, triggers and cron jobs, auth users, stored files, and every service that connects to it. Surprises found here are cheap; surprises found at cutover are outages."),
    ("snapshot", "2 · Snapshot copy", f"Copy a consistent snapshot (say, at 10:00) of the 1.2M rows into the {N('new DB')}. That takes minutes to hours, and calls keep writing to the {O('old DB')} the whole time, so the copy is already out of date when it finishes."),
    ("cdc", "3 · Stream every change (CDC)", f"<b>Change data capture</b>: read the old DB's change log and replay every insert/update/delete on the new one. Tools: Postgres {C('logical replication')} or GCP's {C('Database Migration Service')}. The new DB now trails by a couple of seconds ({Q('lag ≈ 2 s')})."),
    ("verify", "4 · Verify", "Prove the copies match before trusting the new one: row counts per table, checksums, and <b>shadow reads</b> (send the same read query to both and compare the results). Also load-test the new DB at peak traffic."),
    ("cutover", "5 · Cutover", f"Pause writes for a few seconds and hold them in a {Q('queue')}, wait until lag hits 0, flip a feature flag so the {A('app')} points at the {N('new DB')}, then drain the queue into it. Calls never stop: the {A('agent')} keeps talking and says “I've noted that, the clinic will confirm.” Downtime: seconds, and invisible to callers.", "hook"),
    ("rollback", "6 · Keep a way back", f"Turn on {C('reverse replication')} (new → old) for a few days. If errors spike, flipping back is one flag change with no data lost. <b>Tradeoffs to name:</b> a big-bang copy in a maintenance window is simpler but means downtime, which Dodo can't afford; <b>dual writes</b> (app writes to both DBs) seem easy but drift when one write fails, so CDC is usually safer."),
   ],
   "check": {"id": "c2", "q": "Why not just have the app write to both databases (dual writes) during the migration? And what does Dodo do with writes during the few seconds of cutover?",
             "model": "Dual writes drift: if one write succeeds and the other fails or they land in different orders, the DBs silently disagree. CDC copies from one source of truth (the old DB's change log). During cutover, writes go into a queue for a few seconds, then drain into the new DB once lag is 0 and the flag flips, while the agent keeps the caller in a graceful “noted, the clinic will confirm” mode."}},
  {"scene": "Voice", "file": "ch3-voice-agents-livekit", "title": "How a voice agent works, and where LiveKit fits", "short": "Voice + LiveKit",
   "steps": [
    ("path", "One turn of a call", f"A phone call arrives over the phone network (PSTN) through a telephony provider such as Twilio, using SIP (the protocol that sets up calls). A media server carries the audio streams. Then {N('speech-to-text')} → {A('LLM agent')} (which can call tools like “find a slot” in the PMS) → {O('text-to-speech')} → back to the caller. <i>Dodo's current stack isn't public. A common setup is Twilio plus a hosted voice-agent platform (Vapi, Retell) or a framework like Pipecat. Treat that as a guess and ask.</i>"),
    ("budget", "The latency budget", "People notice a pause longer than about a second. If every stage waits for the previous one to finish (full transcript, then the full LLM answer, then the full audio), you get about 2.5 s of dead air per turn."),
    ("stream", "Fix: stream everything", "Each stage starts on partial output: STT sends words as they're heard, the LLM streams tokens, and TTS starts speaking as soon as the first sentence is ready. Same models, now about 0.9 s. Other levers: run servers close to the telephony region, use faster models, and say a quick filler line (“Let me check that”) before slow tool calls."),
    ("bargein", "Barge-in and turn detection", "Real callers interrupt. <b>Barge-in</b>: voice-activity detection hears the caller and stops TTS instantly. <b>Turn detection</b> decides when the caller has actually finished (a pause vs. the end of a thought). Too eager and the agent cuts people off; too slow and it feels laggy."),
    ("livekit", "What LiveKit is", f"{K('LiveKit')} is an open-source (Apache 2.0) real-time platform: a WebRTC media server, {K('LiveKit SIP')} to bridge phone calls in through a SIP trunk (Twilio, Telnyx, …), and the {K('Agents framework')} (Python/Node) that runs STT → LLM → TTS with plugins for most providers, plus built-in turn detection and interruption handling. Run it yourself or on managed {K('LiveKit Cloud')}."),
    ("tradeoff", "Why a team moves to it", "<b>Pros:</b> you own the pipeline, so you can tune latency, swap STT/LLM/TTS vendors, pay less per minute at high volume than an all-in-one platform, and self-host for tighter control over patient data. <b>Costs:</b> more to operate (scaling, SIP, monitoring), rebuilding what the old platform did, and moving live call traffic safely. It's the same shape as the DB migration: more control, more responsibility. Roll it out gradually, e.g. route 5% of one clinic's calls first."),
   ],
   "check": {"id": "c3", "q": "Name the stages of one voice-agent turn, and two techniques that keep it under about 1 second.",
             "model": "Telephony (PSTN/SIP) → media server → STT → LLM agent (+ tools) → TTS → back to the caller. Keep it fast by streaming every stage (partial transcripts, token streaming, TTS on the first sentence), co-locating servers near the telephony region, faster models, filler phrases before slow tool calls, and good turn detection/barge-in."}},
  {"scene": "PMS", "file": "ch4-pms-safely", "title": "Touching the clinic's PMS safely", "short": "PMS safety",
   "steps": [
    ("retry", "Timeouts and retries", f"The practice management system (PMS) is someone else's software: slow, sometimes down, rate-limited. Every call gets a {Q('timeout')} (for example 3 s), then retries with <b>exponential backoff</b> (0.5 s, 1 s, 2 s) plus random <b>jitter</b> so hundreds of agents don't retry in lockstep. After that, stop and fall back."),
    ("idem", "Idempotency keys", f"The dangerous case: the booking succeeded but the reply got lost, so a retry books Bella twice. Fix: give each write an <b>idempotency key</b> (e.g. {Q('call-8812-book-1')}) and store it with the result. A repeat with the same key returns the existing booking instead of creating a new one. If the PMS doesn't support keys, keep your own bookings table and check it before writing."),
    ("tenant", "Multi-tenant isolation", "Hundreds of clinics share one system. Every row, query, cache key, log line and LLM prompt carries a <code>clinic_id</code>. Each clinic has its own PMS credentials, hours and rules. Enforce isolation in the database (RLS or per-tenant schemas), not just in app code. For HIPAA, add encryption, audit logs and least-privilege access."),
    ("fallback", "Graceful fallbacks", f"If the PMS is down, the {A('agent')} still answers: “I've noted your request; the clinic will text to confirm,” and the task goes into a {Q('queue')} for staff or a later retry. If the LLM provider is down, switch to a backup model or transfer the call to the front desk. The rule: the call is always answered and the work is never lost."),
   ],
   "check": {"id": "c4", "q": "The agent booked an appointment, but the PMS reply timed out and the agent retried. How do you make sure there's only one appointment?",
             "model": "Use an idempotency key per booking attempt (e.g. call ID + action). Store key → result; on retry with the same key, return the stored booking instead of writing again. If the PMS has no idempotency support, keep your own bookings record and check the PMS for an existing appointment (same patient/slot) before writing. Combine with timeouts, backoff with jitter, and a fallback to a staff queue."}},
 ],
 "drill": [
  {"id": "d1", "q": "“We're on Supabase and want to move to GCP. Walk me through how you'd plan it without dropping calls.” Start with the questions you'd ask me.",
   "model": "Ask first: why are we moving (compliance, cost, consolidation)? How big is the DB and what's the write rate? Which Supabase features do we use (Auth, Storage, Realtime, RLS, edge functions)? What downtime is acceptable? Then: inventory → snapshot → CDC (logical replication / DMS) → verify (counts, checksums, shadow reads, load test) → cutover behind a flag with a seconds-long write pause buffered in a queue → reverse replication for rollback. Migrate auth and storage as separate workstreams, and do it at the lowest-traffic hour even though it's near-zero downtime."},
  {"id": "d2", "q": "“Design the system behind our AI phone receptionist.” Give the high-level components and the hardest problem.",
   "model": "Clarify: number of clinics, concurrent calls at peak, languages, which PMSs, SMS too? Components: telephony (SIP trunk) → media server / LiveKit → agent workers (STT → LLM with tools → TTS, streaming) → tools service talking to each PMS → DB (calls, tenants, bookings, transcripts) → queue for follow-ups/recalls → dashboard for staff → evals/monitoring. Hardest parts: sub-second latency (streaming, barge-in, turn detection) and reliable PMS writes (timeouts, retries, idempotency, fallbacks). Also multi-tenancy and HIPAA (encryption, audit logs, BAAs with vendors)."},
  {"id": "d3", "q": "“We're thinking about moving to LiveKit. What would you want to know, and how would you roll it out?”",
   "model": "Want to know: what we use today and its pain (latency, cost per minute, vendor lock-in, HIPAA/data control), call volume, and whether we'd self-host or use LiveKit Cloud. Tradeoff: more control over the pipeline and cost vs more to operate. Rollout: build the agent on LiveKit Agents with the same STT/LLM/TTS, run offline evals on recorded/simulated calls, then route a small % of one clinic's calls, compare latency, task success and transfer rate, and ramp up with a quick switch back to the old path."},
 ],
 "summary": [
  "Supabase = Postgres + Auth + Storage + Realtime + RLS. GCP (Cloud SQL / AlloyDB) gives you Postgres; the extras, especially auth, are the real migration work.",
  "Zero-downtime playbook: inventory → snapshot → CDC → verify → cutover behind a flag (seconds-long write pause in a queue) → reverse replication for rollback.",
  "Prefer CDC over dual writes; big-bang windows are simpler but drop calls.",
  "Voice turn: telephony → media → STT → LLM + tools → TTS. Keep it under 1 s by streaming every stage; handle barge-in and turn detection.",
  "LiveKit = open-source WebRTC media server + SIP bridge + Agents framework, self-hosted or Cloud. More control and lower cost at scale, more to operate.",
  "PMS writes: timeouts, backoff with jitter, idempotency keys, clinic_id everywhere, and the call is always answered.",
 ],
}
