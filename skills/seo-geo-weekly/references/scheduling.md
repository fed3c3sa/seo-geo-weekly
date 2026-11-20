# Run it every week on its own

Offer this at the end of setup, or whenever the person asks to "schedule it", "run it every week" or "automate it".

## Which scheduler, and why

| Option | Can it read Search Console and Bing? | Verdict |
|---|---|---|
| **The computer's scheduler**, through `scripts/schedule.py` (launchd on macOS, cron on Linux, Task Scheduler on Windows) | Yes: it starts a real Claude Code session with `--chrome` on the person's machine, in their signed-in Chrome | **Use this.** |
| Cloud routines (`/schedule`) | No: they run on Anthropic's servers, with no access to the person's Chrome, local files or signed-in consoles | Only for work that needs no browser. Not this loop. |
| `CronCreate` or `/loop` inside a session | Yes, but only while that one session stays open, and recurring jobs expire after 7 days | A stopgap: "remind me in this session next week". |

## Set it up (do it for them, step by step)

1. **Pick the day and time with the person.**
   - **When:** a weekday morning when the computer is usually on. Pick an odd minute (10:07, not 10:00).
   - **macOS:** if the Mac is asleep at that time, the job runs when it wakes.
   - **Windows:** "StartWhenAvailable" is set, so a missed run starts as soon as possible.
   - **Linux:** cron skips a run missed while the machine was off.
2. **Pick the permissions:**
   - **`safe`** (the default): edits and the commands this skill uses are pre-approved. Anything else waits in the session window for the person to approve. Publishing still follows "Authorization" in `site.md`.
   - **`bypass`**: no prompts at all (`--dangerously-skip-permissions`). Only if the person explicitly wants fully unattended runs and trusts the skill on their machine and accounts. Explain it in one sentence and let them choose.
3. **Install:**
   ```bash
   python3 <skill_dir>/scripts/schedule.py install example.com --day wed --time 10:07 [--permissions safe|bypass] [--model <name>]
   ```
   - **Windows:** use `py` instead of `python3`.
   - **Data folder:** `~/seo/<domain>`, or `--data <dir>`.
   - **To see first what it would do:** `--dry-run` shows the job it would register.
4. **Install tmux** (macOS and Linux), so each run is a background session they can attach to:
   - macOS: `brew install tmux`;
   - Debian/Ubuntu: `sudo apt install tmux`.
   - **Without tmux:** macOS opens a Terminal window instead. Windows always opens a PowerShell window.
5. **Test now, with the person watching** (about a minute):
   ```bash
   python3 <skill_dir>/scripts/schedule.py run example.com --test
   ```
   - **What it does:** it opens a session, checks that Chrome is connected, and sends a desktop notification: "test ok" or "test failed: <reason>".
   - **First run in the folder:** Claude Code asks whether to trust it. With tmux, the script answers yes; in a window, the person clicks it once.
   - **Notifications on macOS:** the first notification may need permission in System Settings, Notifications.
6. **If the test says Chrome isn't connected:**
   - **Why:** Claude in Chrome usually serves one Claude Code session at a time.
   - **Fix:** close other Claude Code sessions that use Chrome (including this one), make sure Chrome is open with the right profile, and run the test again.
   - **At the scheduled time:** the run retries for a few minutes, then reports the blocker and stops.

## What happens each week

- **The scheduler** starts `schedule.py run <domain>`. It skips the run if one was launched or a full report written in the last 5 days, so a hand-made run that week counts.
- **It waits** while another scheduled SEO session is busy (they share Chrome), and closes older idle ones.
- **It opens a visible Claude Code session** named "SEO weekly <domain> <date>", with the weekly prompt:
  - run the skill on this site;
  - read `site.md` first;
  - follow the cadence rules;
  - publish only what `site.md` authorizes;
  - never wait for answers;
  - on a blocker, or at the end, write the report and send a notification.
- **Run logs** are in `<data>/schedule/runner.log`. Each run's prompt is in `<data>/schedule/runs/`.
- **The scheduler runs a copy:** `install` copies `schedule.py` to `~/.seo-geo-weekly/schedule.py`, and the job calls that copy. Updating or moving the skill (a plugin update installs into a new folder) never breaks the schedule. Run `install` again after an update to refresh the copy. The commands below work from either copy.

## Day to day

| Want to | Command |
|---|---|
| See what's scheduled and running | `schedule.py status` |
| Watch a run (tmux) | `tmux -L seo-geo-weekly attach -t <session>` (detach: Ctrl-b, then d) |
| Reopen a finished run | `claude --resume`, then pick "SEO weekly <domain> <date>" |
| Run now | `schedule.py run <domain> --force` |
| Change day, time or permissions | run `install` again with the new values (it replaces the job) |
| Stop it | `schedule.py remove <domain>` (the data folder stays) |

Several sites can be scheduled. Give each its own day or a few hours apart, because they share Chrome.
