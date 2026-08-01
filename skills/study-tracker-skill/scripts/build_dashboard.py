#!/usr/bin/env python3
"""Build a self-contained study-tracker dashboard from a syllabus JSON file.
 
Usage:
    python build_dashboard.py <syllabus.json> <output.html> [--template <template.html>]
 
The syllabus JSON drives everything (subjects, groups, chapters, practice areas),
so to change what the dashboard tracks you edit the JSON and rebuild - you never
hand-edit the HTML. Check-off state lives in the browser's localStorage, keyed by
student + grade, so rebuilding to add/rename chapters keeps existing progress.
"""
import json, sys, os, argparse
 
def main():
    p = argparse.ArgumentParser()
    p.add_argument("syllabus")
    p.add_argument("output")
    p.add_argument("--template", default=None)
    p.add_argument("--sync-url", default=None,
                   help="Firebase Realtime Database URL to enable cross-device sync "
                        "(e.g. https://kashika-tracker-default-rtdb.firebaseio.com)")
    p.add_argument("--home-url", default=None,
                   help="Relative link back to the hub, shown as a 'Dashboard' link "
                        "(e.g. 'index.html' for the master, '../index.html' for test-tracker/ files)")
    p.add_argument("--rollup-to", default=None,
                   help="tracker_id of the tracker this one rolls coverage up into "
                        "(e.g. 'full-syllabus'). Set on test trackers so ticking a chapter "
                        "there durably marks it covered in the Full Syllabus tracker.")
    args = p.parse_args()
 
    here = os.path.dirname(os.path.abspath(__file__))
    template_path = args.template or os.path.join(here, "..", "assets", "dashboard_template.html")
 
    with open(args.syllabus, encoding="utf-8") as f:
        syllabus = json.load(f)
    # Enabling sync is just a data change - the template already knows what to do
    # with syllabus.sync, so we inject it here rather than editing the JSON by hand.
    if args.sync_url:
        syllabus["sync"] = {"db_url": args.sync_url}
    if args.home_url:
        syllabus["home"] = args.home_url
    if args.rollup_to:
        syllabus["rollup_to"] = args.rollup_to
    # Validate minimally so mistakes surface early rather than as a blank page.
    assert syllabus.get("practice_areas"), "syllabus needs a non-empty 'practice_areas' list"
    assert syllabus.get("subjects"), "syllabus needs a non-empty 'subjects' list"
    for s in syllabus["subjects"]:
        assert s.get("groups"), f"subject '{s.get('name')}' needs at least one group"
 
    with open(template_path, encoding="utf-8") as f:
        template = f.read()
 
    injected = json.dumps(syllabus, ensure_ascii=False)
    html = template.replace("__SYLLABUS_JSON__", injected)
 
    # Catch broken JavaScript before the file ships. A dashboard that fails to
    # parse renders as a blank page, and that failure is invisible until someone
    # opens it - so verify the embedded <script> parses if node is available.
    import re, shutil, subprocess, tempfile
    if shutil.which("node"):
        m = re.search(r"<script>(.*)</script>", html, re.S)
        if m:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as t:
                t.write(m.group(1)); tmp = t.name
            r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
            os.unlink(tmp)
            if r.returncode != 0:
                sys.exit("Dashboard JS failed to parse - not writing output:\n" + r.stderr)
 
    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
 
    n_ch = sum(len(g["chapters"]) for s in syllabus["subjects"] for g in s["groups"])
    print(f"Built {args.output}: {len(syllabus['subjects'])} subjects, "
          f"{n_ch} chapters, {len(syllabus['practice_areas'])} practice areas each.")
 
if __name__ == "__main__":
    main()
