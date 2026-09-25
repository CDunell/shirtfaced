---
name: design-batch
description: Run a batch of Shirtfaced design generations — pick evidence-informed concepts, generate each through the owner's real ChatGPT/Gemini login (never a billed API), and push the results into Studio's Gallery as pending for review. Use when the owner asks to "run a batch", "generate some designs", or Gallery's review queue is empty and needs new work.
---

# Design batch

Generates new Shirtfaced designs and drops them into Gallery's review queue
(`status: pending`). The owner reviews and decides kept/dropped themselves,
in the app — this skill's job stops at getting real, evidence-informed
designs in front of them, not deciding anything about them.

**Never runs unattended.** This is a session the owner explicitly asks for,
each time. Do not schedule it, loop it, or treat a mention of design work
as an invitation to run it — only a direct ask ("run a batch", "generate N
designs") counts. Automating the trigger itself was explicitly ruled out:
it both breaks the owner's "I run the session, I review the output" rule
and risks the ChatGPT/Gemini account being flagged for automated use at
real volume.

**No metered API calls.** Generation happens through the owner's real,
logged-in browser session (`claude-in-chrome` tools) against chatgpt.com —
ChatGPT is the default; use Gemini only if the owner asks for it or ChatGPT
is unavailable — using their paid subscription — never `GoogleImageClient` or any other
API-billed path. This is a hard rule, not a preference: the owner pays for
ChatGPT/Gemini already and does not want to pay again per image.

## Running it in the background

For 1–2 designs, run them yourself in this session. For 3 or more, dispatch the `design-batch-runner`
subagent (`.claude/agents/design-batch-runner.md`) with the count and any
traditions or concepts the owner named. It follows this same procedure in
its own Chrome tab and reports back, so the owner isn't watching every
click. It never edits code or deploys, so a template regression it reports
comes back to the main session to fix, with the owner's sign-off.

## Prerequisites

- `claude-in-chrome` connected and logged into ChatGPT (verify with
  `list_connected_browsers` before starting if unsure).
- SSH access to the production box via the repo's gitignored `.secrets/`:
  `.secrets/box_host` (the `ubuntu@<ip>` target) and `.secrets/oracle.key`
  (see `.secrets/README.md`). `push_generation.sh` reads both on its own;
  for the step-2 SSH call below, use
  `ssh -i .secrets/oracle.key "$(cat .secrets/box_host)"`. Never copy the
  host into a committed file — `deploy.yml` keeps it as a GitHub secret for
  the same reason. If `.secrets/` is missing, ask the owner.

## Steps, per design

1. **Pick a tradition and a concept.** Traditions are the values already in
   `design_generation_samples.tradition` (au-surf, skate, streetwear,
   band-merch, moto, …) — pick one that's thin in the current pending queue
   if no direction is given, otherwise use what the owner asked for. Write
   one or two sentences describing the actual graphic (motif, texture,
   mood) — this is the one genuinely creative step, still done by a person
   or by you, not automated.

2. **Get the real prompt** (evidence-informed, not hand-written):
   ```
   ssh -i .secrets/oracle.key "$(cat .secrets/box_host)" \
     "cd /home/ubuntu/shirtfaced-studio && .venv/bin/python scripts/render_prompt_for.py '<tradition>' '<concept text>'"
   ```
   If this refuses ("nothing evidence-backed to build a prompt from"), the
   corpus isn't measured for that tradition — try a different one rather
   than fabricating a prompt yourself.

3. **Generate it.** Navigate `claude-in-chrome` to chatgpt.com, submit
   "Generate an image. " + the prompt from step 2, wait for the render
   (usually 30-50s, poll with short waits and screenshots), and confirm
   visually before moving on:
   - Isolated graphic on a plain background — no garment, no mockup, no
     model. If it drew a t-shirt photo instead, the prompt's own
     instruction already covers this; look again before assuming the model
     ignored it.
   - Proportions plausible for a chest print (roughly square to ~2:1 wide),
     not a stretched banner.
   - If lettering appears, it reads "Shirtfaced" (never an invented brand),
     lettered to match the illustration's own style — not a default-font
     caption dropped underneath.
   Any of these wrong is a prompt-template bug, not a one-off bad render —
   fix `app/services/design_advisor.py`'s `render_generation_prompt()`,
   commit, then **ask the owner before pushing** (a push to `main` deploys
   to production — see CLAUDE.md), and regenerate once it's live. Don't
   accept a flawed image or patch around it per-image.

4. **Download it** (extension download UI is unreliable for blob URLs; do
   this instead):
   ```js
   const imgs = Array.from(document.querySelectorAll('img'))
     .map(i => i.src).filter(s => s.startsWith('blob:'));
   const a = document.createElement('a');
   a.href = imgs[imgs.length - 1];
   a.download = 'design.png';
   document.body.appendChild(a); a.click(); a.remove();
   ```
   via `javascript_tool`, then confirm the file landed (`ls -lt ~/Downloads`
   — it lands on whatever machine's Chrome is connected, i.e. wherever this
   session's Bash tool also runs).

5. **Push it into the queue** — one command, replaces the old hand-typed
   SSH/scp/python-heredoc sequence:
   ```
   studio/scripts/push_generation.sh <downloaded_image_path> <tradition> <batch_label> "<concept text>" "<the exact prompt from step 2>"
   ```
   Use one `batch_label` per run (e.g. `session-YYYY-MM-DD-<short-label>`)
   so the owner can see which designs came from which batch in Gallery.

## When something looks wrong

Don't quietly retry or patch around it — say what broke and fix the actual
cause:
- **Mockup photo instead of isolated artwork**, **impossible proportions**,
  **generic-font or invented brand name** → the prompt template regressed;
  read `render_generation_prompt()` in `app/services/design_advisor.py`,
  fix it, redeploy, and only then regenerate. These have all happened
  before and were each a real bug in that function, not a fluke render.
- **`push_generation.sh` fails on the SSH step** → the deployed box doesn't
  have `scripts/ingest_local_image.py` yet; it ships with the normal
  `studio/` sync on every deploy, so this means the latest push hasn't
  deployed (check `gh run list --workflow=deploy.yml`), not that the
  script is broken.
- **Corpus refuses a tradition** → don't fabricate advice; either pick a
  measured tradition or tell the owner that one needs `design-data
  --refresh` run against fresher evidence.
