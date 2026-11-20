#!/usr/bin/env python3
"""Run the SEO/GEO loop every week on its own, as a VISIBLE Claude Code session with Claude in Chrome.

Why not Claude Code's other schedulers:
- cloud routines (/schedule) run on Anthropic's servers: they can't reach your Chrome, so no Search Console or Bing;
- CronCreate and /loop live only inside one open session and expire after 7 days.
So this script asks the computer's own scheduler (launchd on macOS, cron on Linux, Task Scheduler on Windows)
to start `claude --chrome` with the weekly prompt, in tmux (or a Terminal window), where you can watch it.

  schedule.py install <domain> --day wed --time 10:07 [--data DIR] [--permissions safe|bypass] [--model NAME] [--dry-run]
  schedule.py run <domain> [--force] [--test]   what the scheduler calls; --force ignores the 5-day guard,
                                                --test starts a 1-minute check instead of the real run
  schedule.py status                            scheduled sites, last launches, live sessions
  schedule.py remove <domain>                   unschedule (keeps the data folder)
  schedule.py notify <title> <text>             desktop notification (used by the session itself)

Permissions:
  safe   (default) edits and the commands this skill needs are pre-approved; anything else waits for you
         in the visible window. Publishing still follows "Authorization" in site.md.
  bypass every tool runs without asking (--dangerously-skip-permissions). Only on a machine and accounts you
         trust the skill with; the session can push to your site if site.md allows it.
"""
import argparse
import datetime as dt
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(HOME, ".seo-geo-weekly", "sites.json")
# The scheduler runs a stable copy of this script, so updating or moving the skill (e.g. a plugin update, which
# installs into a new versioned folder) never breaks a scheduled job. `install` refreshes the copy.
RUNNER = os.path.join(HOME, ".seo-geo-weekly", "schedule.py")
SYSTEM = platform.system()  # Darwin, Linux, Windows
DAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
SKIP_DAYS = 5
SOCK = "seo-geo-weekly"  # its own tmux server, so it never touches other tmux sessions
EXTRA_PATH = [os.path.join(HOME, ".local", "bin"), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin",
              "/usr/sbin", "/sbin", os.path.join(HOME, ".npm-global", "bin")]
SAFE_TOOLS = [
    "Read", "Edit", "Write", "Glob", "Grep", "ToolSearch", "Skill", "Agent", "TodoWrite", "WebFetch", "WebSearch",
    "mcp__claude-in-chrome",
    "Bash(python3:*)", "Bash(python:*)", "Bash(py:*)", "Bash(git:*)", "Bash(gh:*)", "Bash(curl:*)", "Bash(npx:*)",
    "Bash(dig:*)", "Bash(nslookup:*)", "Bash(ls:*)", "Bash(mkdir:*)", "Bash(cat:*)", "Bash(head:*)", "Bash(tail:*)",
    "Bash(grep:*)", "Bash(diff:*)", "Bash(date:*)", "Bash(cp:*)", "Bash(mv:*)", "Bash(wc:*)", "Bash(sed:*)",
]


# ---------- small helpers ----------

def which(name):
    return shutil.which(name, path=os.pathsep.join([os.environ.get("PATH", "")] + EXTRA_PATH))


def load():
    try:
        return json.load(open(REGISTRY, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save(reg):
    os.makedirs(os.path.dirname(REGISTRY), exist_ok=True)
    json.dump(reg, open(REGISTRY, "w", encoding="utf-8"), indent=2)


def slug(domain):
    return re.sub(r"[^a-z0-9]+", "-", domain.lower()).strip("-")


def log(cfg, msg):
    d = os.path.join(cfg["data"], "schedule")
    os.makedirs(d, exist_ok=True)
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with open(os.path.join(d, "runner.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def notify(title, text):
    try:
        if SYSTEM == "Darwin":
            q = lambda s: '"' + s.replace('\\', '').replace('"', "'") + '"'  # noqa: E731
            subprocess.run(["osascript", "-e", f"display notification {q(text)} with title {q(title)}"],
                           capture_output=True)
        elif SYSTEM == "Linux" and which("notify-send"):
            subprocess.run(["notify-send", title, text], capture_output=True)
        elif SYSTEM == "Windows":
            subprocess.run(["msg", os.environ.get("USERNAME", "*"), f"{title}: {text}"], capture_output=True)
    except OSError:
        pass
    print(f"[notify] {title}: {text}")


def env():
    e = dict(os.environ)
    e["PATH"] = os.pathsep.join(EXTRA_PATH + [e.get("PATH", "")])
    e.setdefault("LANG", "en_US.UTF-8")
    e.setdefault("TERM", "xterm-256color")
    return e


# ---------- the prompt each run starts with ----------

def build_prompt(domain, cfg, test=False):
    now = dt.datetime.now()
    me = shlex.quote(os.path.abspath(__file__)) if SYSTEM != "Windows" else f'"{os.path.abspath(__file__)}"'
    py = cfg["python"]
    notify_cmd = f'{py} {me} notify "SEO weekly {domain}" "<one line>"'
    if test:
        return (f"This is a scheduler test for the seo-geo-weekly skill. Do only this: call tabs_context_mcp "
                f"(load the Claude in Chrome tools with ToolSearch if needed), then run `{notify_cmd}` with "
                f"\"test ok, Chrome connected\" or \"test failed: <reason>\" as the line, then say done.")
    return f"""Use the seo-geo-weekly skill to run this week's SEO / GEO pass on {domain}. (When this schedule was set up the skill was in {cfg.get('skill_dir', SKILL_DIR)}; if that folder is gone, for example after a plugin update, load the skill by name.)

The data folder is {cfg['data']}. Read site.md there first: it holds the mode, the authorization, the owner's rules and the queries that matter. Follow the skill's cadence rules (a check-in instead of changes if the last run was less than 7 days ago or a Google core update is running).

## How this session runs

The computer's scheduler started this session on its own; nobody is watching it live. Work end to end without asking anything:
- Do not use AskUserQuestion and do not wait for answers.
- Chrome: use the connected browser whose Search Console shows the account recorded in site.md. Check the account shown on the page, not the browser's name. Open your own tabs and close them at the end.
- Publish only what "Authorization" in site.md allows without asking. Anything else: prepare it (branch, diff, exact steps) and list it under "Needs the owner" in the report.
- If the Chrome tools say the extension is not connected, another Claude Code session probably holds it: wait 2 minutes and retry, up to 3 times.
- Truly blocked (Chrome still not connected, a sign-in needed, the site's repo or admin unreachable): write what blocks you into weekly/{now:%Y-%m-%d}.md, run `{notify_cmd}` with the blocker as the line, and stop.
- At the end: write the report and data files the skill asks for, run `{notify_cmd}` with a one-line result, and stop.

Today is {now:%A %Y-%m-%d %H:%M} (local time).
"""


# ---------- launching the visible session ----------

def claude_flags(cfg, name):
    f = [cfg["claude"], "--chrome", "-n", name]
    if cfg.get("model"):
        f += ["--model", cfg["model"]]
    if cfg["permissions"] == "bypass":
        f += ["--dangerously-skip-permissions"]
    else:
        f += ["--permission-mode", "acceptEdits", "--allowedTools", *SAFE_TOOLS, f"Bash({cfg['python']}:*)"]
    return f


def tmux(cfg, *args):
    return subprocess.run([cfg["tmux"], "-L", SOCK, *args], capture_output=True, text=True, env=env())


def tmux_sessions(cfg):
    if not cfg.get("tmux"):
        return []
    r = tmux(cfg, "list-sessions", "-F", "#{session_name}")
    return r.stdout.split() if r.returncode == 0 else []


def pane(cfg, name, lines=60):
    r = tmux(cfg, "capture-pane", "-p", "-J", "-t", f"={name}:", "-S", f"-{lines}")
    return r.stdout if r.returncode == 0 else ""


def busy(cfg, name):
    return "esc to interrupt" in pane(cfg, name, 15)


def answer_trust_dialog(cfg, name, limit=90):
    """First run in a new folder: Claude asks whether to trust it. Accept, since the folder is the person's data."""
    t0 = time.time()
    while time.time() - t0 < limit:
        time.sleep(2)
        if name not in tmux_sessions(cfg):
            return "exited"
        p = pane(cfg, name)
        m = re.search(r"(\d)\.\s*Yes, I trust this folder", p)
        if m:
            tmux(cfg, "send-keys", "-t", f"={name}:", m.group(1))
            time.sleep(1.5)
            if "Yes, I trust this folder" in pane(cfg, name):
                tmux(cfg, "send-keys", "-t", f"={name}:", "Enter")
            continue
        if "esc to interrupt" in p or re.search(r"(?m)^\s*⏺", p):
            return "working"
    return "unknown (look at the window)"


def launch(domain, cfg, test=False):
    now = dt.datetime.now()
    name = f"seo-{slug(domain)}-{now:%Y%m%d-%H%M}" + ("-test" if test else "")
    run_dir = os.path.join(cfg["data"], "schedule", "runs")
    os.makedirs(run_dir, exist_ok=True)
    pf = os.path.join(run_dir, name + ".prompt.md")
    open(pf, "w", encoding="utf-8").write(build_prompt(domain, cfg, test))
    flags = claude_flags(cfg, f"SEO weekly {domain} {now:%Y-%m-%d}" + (" test" if test else ""))

    if SYSTEM == "Windows":
        q = lambda s: "'" + str(s).replace("'", "''") + "'"  # noqa: E731  PowerShell single-quoted literal
        ps1 = os.path.join(run_dir, name + ".ps1")
        open(ps1, "w", encoding="utf-8-sig").write(
            f"Set-Location -LiteralPath {q(cfg['data'])}\r\n"
            f"$p = Get-Content -Raw -LiteralPath {q(pf)}\r\n"
            f"& {' '.join(q(x) for x in flags)} -- $p\r\n")
        subprocess.Popen(["cmd", "/c", "start", f"SEO weekly {domain}", "powershell", "-NoExit", "-NoProfile",
                          "-ExecutionPolicy", "Bypass", "-File", ps1], cwd=cfg["data"])
        return name, "started in a new PowerShell window"

    sh = os.path.join(run_dir, name + ".sh")
    open(sh, "w", encoding="utf-8").write(
        "#!/bin/sh\n"
        f"export PATH={shlex.quote(env()['PATH'])}\n"
        f"cd {shlex.quote(cfg['data'])} || exit 1\n"
        f"{' '.join(shlex.quote(x) for x in flags)} -- \"$(cat {shlex.quote(pf)})\"\n"
        f"echo \"exit=$? $(date '+%Y-%m-%d %H:%M:%S')\" >> {shlex.quote(os.path.join(run_dir, name + '.exit'))}\n")
    os.chmod(sh, 0o700)

    if cfg.get("tmux"):
        r = tmux(cfg, "new-session", "-d", "-s", name, "-x", "200", "-y", "50", sh)
        if r.returncode != 0:
            return name, "tmux failed: " + r.stderr.strip()
        return name, "tmux: " + answer_trust_dialog(cfg, name) + f" (watch: tmux -L {SOCK} attach -t {name})"
    if SYSTEM == "Darwin":
        subprocess.run(["osascript", "-e", f'tell application "Terminal" to do script {json.dumps(sh)}',
                        "-e", 'tell application "Terminal" to activate'], capture_output=True)
        return name, "started in a Terminal window"
    return name, "no tmux found: install it (e.g. sudo apt install tmux) and run again"


# ---------- commands ----------

def last_report(cfg):
    d = os.path.join(cfg["data"], "weekly")
    days = [dt.date.fromisoformat(f[:10]) for f in (os.listdir(d) if os.path.isdir(d) else [])
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", f)]
    return max(days) if days else None


def cmd_run(a):
    reg = load()
    cfg = reg.get(a.domain)
    if not cfg:
        sys.exit(f"{a.domain} is not scheduled; run: schedule.py install {a.domain} ...")
    today = dt.date.today()
    if not (a.force or a.test):
        last = dt.date.fromisoformat(cfg["last_launch"]) if cfg.get("last_launch") else None
        rep = last_report(cfg)
        for when, what in ((last, "launched"), (rep, "a full report written")):
            if when and (today - when).days < SKIP_DAYS:
                log(cfg, f"skipped: already {what} on {when}")
                return 0
    # one SEO session at a time: they share Chrome
    t0 = time.time()
    while cfg.get("tmux") and any(busy(cfg, s) for s in tmux_sessions(cfg)):
        if time.time() - t0 > 8 * 3600:
            break
        time.sleep(120)
    for s in tmux_sessions(cfg):  # close older idle runs: Claude in Chrome serves one session at a time
        if not busy(cfg, s):
            tmux(cfg, "kill-session", "-t", f"={s}")
    name, state = launch(a.domain, cfg, a.test)
    log(cfg, f"{'test ' if a.test else ''}started {name}: {state}")
    if not a.test:
        cfg["last_launch"] = today.isoformat()
        reg[a.domain] = cfg
        save(reg)
    notify(f"SEO weekly {a.domain}", ("Test started. " if a.test else "Started. ") + state[:120])
    return 0


def cmd_install(a):
    day = a.day.lower()[:3]
    if day not in DAYS:
        sys.exit("--day must be one of " + ", ".join(DAYS))
    hh, mm = (int(x) for x in a.time.split(":"))
    data = os.path.abspath(os.path.expanduser(a.data or os.path.join("~", "seo", a.domain)))
    claude = which("claude") or which("claude.exe") or which("claude.cmd")
    if not claude:
        if not a.dry_run:
            sys.exit("claude not found on PATH: install Claude Code first")
        claude = "claude (not found on PATH)"
    this = os.path.abspath(__file__)
    # remember where the skill lives; when re-run from the stable copy, keep what the first install recorded
    skill_dir = load().get(a.domain, {}).get("skill_dir", SKILL_DIR) if this == RUNNER else SKILL_DIR
    cfg = {"data": data, "day": day, "time": f"{hh:02d}:{mm:02d}", "permissions": a.permissions,
           "model": a.model, "claude": claude, "python": sys.executable, "skill_dir": skill_dir,
           "tmux": which("tmux") if SYSTEM != "Windows" else None}
    me = RUNNER
    label = f"com.seo-geo-weekly.{slug(a.domain)}"
    if SYSTEM == "Darwin":
        plist = os.path.join(HOME, "Library", "LaunchAgents", label + ".plist")
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{label}</string>
  <key>ProgramArguments</key><array><string>{sys.executable}</string><string>{me}</string><string>run</string><string>{a.domain}</string></array>
  <key>StartCalendarInterval</key><dict><key>Weekday</key><integer>{DAYS.index(day)}</integer><key>Hour</key><integer>{hh}</integer><key>Minute</key><integer>{mm}</integer></dict>
  <key>StandardOutPath</key><string>{os.path.join(data, 'schedule', 'launchd.log')}</string>
  <key>StandardErrorPath</key><string>{os.path.join(data, 'schedule', 'launchd.log')}</string>
</dict></plist>
"""
        steps = [("write", plist, body), ["launchctl", "bootout", f"gui/{os.getuid()}/{label}"],
                 ["launchctl", "bootstrap", f"gui/{os.getuid()}", plist]]
        cfg["job"] = {"kind": "launchd", "label": label, "plist": plist}
    elif SYSTEM == "Linux":
        line = (f"{mm} {hh} * * {DAYS.index(day)} PATH={os.pathsep.join(EXTRA_PATH)} {shlex.quote(sys.executable)} "
                f"{shlex.quote(me)} run {shlex.quote(a.domain)} >> {shlex.quote(os.path.join(data, 'schedule', 'cron.log'))} 2>&1 # {label}")
        steps = [("crontab", label, line)]
        cfg["job"] = {"kind": "cron", "label": label}
    elif SYSTEM == "Windows":
        task = f"SEO GEO weekly {a.domain}"
        day_full = {"sun": "Sunday", "mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday",
                    "fri": "Friday", "sat": "Saturday"}[day]
        ps = (f"$a = New-ScheduledTaskAction -Execute '{sys.executable}' -Argument '\"{me}\" run {a.domain}'; "
              f"$t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek {day_full} -At {hh:02d}:{mm:02d}; "
              f"$s = New-ScheduledTaskSettingsSet -StartWhenAvailable; "
              f"Register-ScheduledTask -TaskName '{task}' -Action $a -Trigger $t -Settings $s -Force | Out-Null")
        steps = [["powershell", "-NoProfile", "-Command", ps]]
        cfg["job"] = {"kind": "windows", "task": task}
    else:
        sys.exit(f"unsupported system {SYSTEM}")

    if a.dry_run:
        print(json.dumps(cfg, indent=2))
        for s in steps:
            print("\n--- would", s[0] if isinstance(s, tuple) else "run", ":\n", s[2] if isinstance(s, tuple) else " ".join(s))
        return 0
    os.makedirs(os.path.join(data, "schedule"), exist_ok=True)
    os.makedirs(os.path.dirname(RUNNER), exist_ok=True)
    if this != RUNNER:
        shutil.copy2(this, RUNNER)
    for s in steps:
        if isinstance(s, tuple) and s[0] == "write":
            os.makedirs(os.path.dirname(s[1]), exist_ok=True)
            open(s[1], "w", encoding="utf-8").write(s[2])
        elif isinstance(s, tuple) and s[0] == "crontab":
            cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
            keep = [ln for ln in cur.splitlines() if not ln.endswith("# " + s[1])]
            subprocess.run(["crontab", "-"], input="\n".join(keep + [s[2]]) + "\n", text=True, check=True)
        else:
            r = subprocess.run(s, capture_output=True, text=True)
            if r.returncode and "bootout" not in s[1]:
                sys.exit(f"failed: {' '.join(s)}\n{r.stderr}")
    reg = load()
    cfg["last_launch"] = reg.get(a.domain, {}).get("last_launch")
    reg[a.domain] = cfg
    save(reg)
    print(f"Scheduled {a.domain}: every {day} at {hh:02d}:{mm:02d} local time, data in {data}, permissions {a.permissions}.")
    if SYSTEM != "Windows" and not cfg["tmux"]:
        print("Note: tmux not found. macOS will open a Terminal window instead; on Linux install tmux.")
    print(f"Test it now (about a minute): {sys.executable} {me} run {a.domain} --test")
    return 0


def cmd_remove(a):
    reg = load()
    cfg = reg.pop(a.domain, None)
    if not cfg:
        sys.exit(f"{a.domain} is not scheduled")
    job = cfg.get("job", {})
    if job.get("kind") == "launchd":
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{job['label']}"], capture_output=True)
        if os.path.exists(job["plist"]):
            os.remove(job["plist"])
    elif job.get("kind") == "cron":
        cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        keep = [ln for ln in cur.splitlines() if not ln.endswith("# " + job["label"])]
        subprocess.run(["crontab", "-"], input="\n".join(keep) + "\n", text=True)
    elif job.get("kind") == "windows":
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"Unregister-ScheduledTask -TaskName '{job['task']}' -Confirm:$false"], capture_output=True)
    save(reg)
    print(f"Unscheduled {a.domain}. The data folder {cfg['data']} is untouched.")
    return 0


def cmd_status(_a):
    reg = load()
    if not reg:
        print("No sites scheduled.")
    for d, c in reg.items():
        print(f"{d}: every {c['day']} {c['time']}, permissions {c['permissions']}, last launch {c.get('last_launch') or 'never'}, "
              f"last report {last_report(c) or 'none'}, data {c['data']}")
        sess = [s for s in tmux_sessions(c) if s.startswith(f"seo-{slug(d)}-")]
        for s in sess:
            print(f"   session {s} ({'busy' if busy(c, s) else 'idle'}): tmux -L {SOCK} attach -t {s}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("install")
    p.add_argument("domain")
    p.add_argument("--day", default="wed")
    p.add_argument("--time", default="10:07")
    p.add_argument("--data")
    p.add_argument("--permissions", choices=["safe", "bypass"], default="safe")
    p.add_argument("--model")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("run")
    p.add_argument("domain")
    p.add_argument("--force", action="store_true")
    p.add_argument("--test", action="store_true")
    p = sub.add_parser("remove")
    p.add_argument("domain")
    sub.add_parser("status")
    p = sub.add_parser("notify")
    p.add_argument("title")
    p.add_argument("text")
    a = ap.parse_args()
    if a.cmd == "notify":
        notify(a.title, a.text)
        return 0
    return {"install": cmd_install, "run": cmd_run, "remove": cmd_remove, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
