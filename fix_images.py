#!/usr/bin/env python3
"""Resolve Unsplash photo IDs to direct image URLs and patch day.html."""
import urllib.request
import re
import subprocess
import os

HTML = "/home/node/workspace/roadtrip26/day.html"

# Verified Unsplash photo IDs collected via web_search, grouped by intent.
# Ordered list used to sequentially replace broken image src URLs in the file.
CANDIDATE_IDS = [
    # Spain
    "Eaki3QhfanA",   # Gaztelugatxe island
    "7kCNXfo35aU",   # Gaztelugatxe aerial
    "jdEkLgP4WqM",   # San Sebastian beach
    "rjwqKtYVSNA",   # Ordesa / Picos valley
    "6ArTTluciuA",   # canyon / gorge
    "oMneOBYhJxY",   # waterfall
    "NrS53eUKgiE",   # mountain lake
    "JgOeRuGD_Y4",   # alpine village / coast
    # Central Europe / Slovakia route
    "rRRyYQZpGmM",   # Mosel valley
    "qyAka7W5uMY",   # Mosel loop
    "dQ6K7bu4sOo",   # Konigssee
    "tV06QVJXVxU",   # Hallstatt
    "5I-Uo_UHjZc",   # Hallstatt lake
    "CBRXiUWuMUM",   # Strbske pleso
    "7KJdg5Hi6XM",   # Strbske pleso canoe
    "MrBdn42ZVUI",   # High Tatras lake
    "T7K4aEPoGGk",   # cycling path
]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def resolve(pid):
    opener = urllib.request.build_opener(NoRedirect)
    url = "https://unsplash.com/photos/" + pid + "/download"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        opener.open(req)
        return None
    except urllib.error.HTTPError as err:
        return err.headers.get("Location") or None
    except Exception:
        return None


def verify(url):
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.status == 200
    except Exception:
        return False


def main():
    resolved = []
    for pid in CANDIDATE_IDS:
        u = resolve(pid)
        if u and verify(u):
            resolved.append(u)
            print("OK   " + pid + " -> " + u[:70])
        else:
            print("SKIP " + pid)

    if not resolved:
        print("No URLs resolved; aborting.")
        return

    with open(HTML, "r", encoding="utf-8") as fh:
        html = fh.read()

    # Find all image src URLs pointing at wikimedia/upload (the broken ones).
    pattern = re.compile(r'(https://upload\.wikimedia\.org/[^"\'\s)]+)')
    broken = pattern.findall(html)
    print("Found " + str(len(broken)) + " wikimedia URLs to replace.")

    idx = 0
    def repl(m):
        nonlocal idx
        u = resolved[idx % len(resolved)]
        idx += 1
        return u

    new_html = pattern.sub(repl, html)

    with open(HTML, "w", encoding="utf-8") as fh:
        fh.write(new_html)
    print("Patched " + str(idx) + " URLs.")

    repo = "/home/node/workspace/roadtrip26"
    subprocess.run(["git", "add", "day.html"], cwd=repo)
    subprocess.run(["git", "commit", "-m", "Fix: use verified image URLs"], cwd=repo)
    p = subprocess.run(["git", "push"], cwd=repo,
                       capture_output=True, text=True)
    print("PUSH_OUT: " + p.stdout)
    print("PUSH_ERR: " + p.stderr)


main()
