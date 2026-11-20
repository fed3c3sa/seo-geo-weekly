"""Tests for the seo-geo-weekly scripts. Standard library only: python -m unittest discover -s tests -v"""
import functools
import http.server
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "skills", "seo-geo-weekly", "scripts")
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, SCRIPTS)
import seo_checks  # noqa: E402


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def site_copy(name, origin):
    """Copy a fixture site to a temp folder, filling in {{ORIGIN}}; add the binary og.png the pages reference."""
    dst = tempfile.mkdtemp()
    for root, _, files in os.walk(os.path.join(FIXTURES, name)):
        rel = os.path.relpath(root, os.path.join(FIXTURES, name))
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            with open(os.path.join(root, f), encoding="utf-8") as src:
                text = src.read().replace("{{ORIGIN}}", origin)
            with open(os.path.join(dst, rel, f), "w", encoding="utf-8", newline="\n") as out:
                out.write(text)
    if name == "good-site":
        with open(os.path.join(dst, "og.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
    return dst


def run(script, *args, env=None):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env, timeout=600)


class SeoChecks(unittest.TestCase):
    def test_meta_any_quoting_and_order(self):
        t = '<meta name=description content=hello><meta content=\'img\' property="og:image">'
        self.assertEqual(seo_checks.meta(t, "name", "description"), "hello")
        self.assertEqual(seo_checks.meta(t, "property", "og:image"), "img")

    def test_canonical_unquoted(self):
        self.assertEqual(seo_checks.canonical("<link rel=canonical href=https://a.com/x/>"), "https://a.com/x/")
        self.assertIsNone(seo_checks.canonical("<link rel=stylesheet href=a.css>"))

    def test_robots_groups(self):
        g = seo_checks.robots_groups("User-agent: *\nDisallow: /\n\nUser-agent: Googlebot\nAllow: /\n")
        self.assertTrue(seo_checks.blocks_all(g))
        self.assertFalse(seo_checks.blocks_all(g, "Googlebot"))  # its own group allows it
        self.assertTrue(seo_checks.blocks_all(g, "GPTBot"))  # no group of its own: follows *
        g = seo_checks.robots_groups("User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n")
        self.assertFalse(seo_checks.blocks_all(g))
        self.assertTrue(seo_checks.blocks_all(g, "gptbot"))
        self.assertTrue(seo_checks.blocks_all(seo_checks.robots_groups("User-agent: *\nDisallow: /*\n")))

    def test_nested_id_is_a_definition(self):
        t = ('<title>x</title><script type="application/ld+json">{"@graph":[{"@type":"Organization","@id":"https://a.com/#o",'
             '"logo":{"@type":"ImageObject","@id":"https://a.com/#logo"},"image":{"@id":"https://a.com/#logo"}}]}</script>')
        issues, _, _ = seo_checks.check_page(t, site="https://a.com", indexable=False)
        self.assertFalse([i for i in issues if "dangling" in i], issues)

    def test_dangling_id_and_faq_mismatch(self):
        t = ('<title>x</title><script type="application/ld+json">{"@graph":[{"@type":"WebSite","publisher":{"@id":"https://a.com/#org"}},'
             '{"@type":"FAQPage","mainEntity":[{"name":"Q?","acceptedAnswer":{"text":"Yes."}}]}]}</script>'
             '<details><summary>Q?</summary><p>No.</p></details>')
        issues, _, _ = seo_checks.check_page(t, site="https://a.com", indexable=False)
        self.assertTrue(any("dangling @id /#org" in i for i in issues), issues)
        self.assertTrue(any("FAQ JSON-LD differs" in i for i in issues), issues)


class VerifySite(unittest.TestCase):
    origin = "https://www.example.com"

    def test_good_site_passes(self):
        d = site_copy("good-site", self.origin)
        r = run("verify_site.py", d, "--site", self.origin, "--no-dashes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("FAQ 1/1", r.stdout)

    def test_bad_site_fails_with_reasons(self):
        d = site_copy("bad-site", self.origin)
        r = run("verify_site.py", d, "--site", self.origin, "--no-dashes")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        for expected in ("title 86 chars > 65", "2 h1 tags", "img without alt", "dangling @id /#org",
                         "FAQ JSON-LD differs", "broken link /gone/", "dashes: em 1",
                         "sitemap lists a non-canonical URL: /old/", "disallows the whole site"):
            self.assertIn(expected, r.stdout, expected)


class AuditLive(unittest.TestCase):
    @unittest.skipIf(shutil.which("curl") is None, "curl not installed")
    def test_good_site_live(self):
        port = free_port()
        origin = f"http://127.0.0.1:{port}"
        d = site_copy("good-site", origin)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=d)
        handler.log_message = lambda *a, **k: None
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            r = run("audit_live.py", origin, "--no-dashes")
        finally:
            srv.shutdown()
        self.assertIn("missing page answers 404", r.stdout, r.stdout)
        self.assertIn("2 URLs", r.stdout, r.stdout)
        self.assertRegex(r.stdout, r"OK\s+/about/")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class Compare(unittest.TestCase):
    def test_numbers_and_bom(self):
        d = tempfile.mkdtemp()
        for day, row, bom in (("2026-11-01", '28d,"1,234",1.64K,"6,7%",8.2', ""), ("2026-11-08", '28d,"1,300",2.1K,7.1%,7.9', "﻿")):
            os.makedirs(os.path.join(d, day, "28d"))
            with open(os.path.join(d, day, "28d", "totals.csv"), "w", encoding="utf-8") as f:
                f.write(bom + "window,clicks,impressions,ctr,position\n" + row + "\n")
        r = run("compare.py", d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("+66.0 better", r.stdout)
        self.assertIn("+460.0 better", r.stdout)
        self.assertIn("-0.3 better", r.stdout)


class IndexNow(unittest.TestCase):
    def test_usage_without_args(self):
        r = run("indexnow.py")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Usage", r.stdout + r.stderr)


class Schedule(unittest.TestCase):
    def env(self):
        home = tempfile.mkdtemp()
        e = dict(os.environ, HOME=home, USERPROFILE=home)
        return e, home

    def test_install_dry_run_per_os(self):
        e, home = self.env()
        r = run("schedule.py", "install", "example.com", "--day", "wed", "--time", "10:07", "--dry-run", env=e)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        expected = {"Darwin": "StartCalendarInterval", "Linux": "7 10 * * 3", "Windows": "Register-ScheduledTask"}[platform.system()]
        self.assertIn(expected, r.stdout)
        self.assertIn(os.path.join(home, ".seo-geo-weekly", "schedule.py"), r.stdout.replace("\\\\", "\\"))
        self.assertFalse(os.path.exists(os.path.join(home, ".seo-geo-weekly")), "dry run must not write anything")

    def test_status_and_notify(self):
        e, _ = self.env()
        r = run("schedule.py", "status", env=e)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("No sites scheduled", r.stdout)
        r = run("schedule.py", "notify", "test", "hello", env=e)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_bad_day(self):
        e, _ = self.env()
        r = run("schedule.py", "install", "example.com", "--day", "someday", "--dry-run", env=e)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
