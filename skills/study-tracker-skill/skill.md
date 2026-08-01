---
name: study-tracker-skill
description: >-
  Build and maintain Kashika's subject-wise study progress tracker for CBSE Class
  10. Use whenever her parent wants to track, view, update, or set up study
  progress across subjects, sub-subjects and chapters - e.g. "how much of SST is
  left", "mark History chapter 3 notebook done", "show Kashika's Science progress",
  "set up a study tracker", "what has she finished in Maths". Each chapter is
  tracked across five practice areas: reading the NCERT book, doing NCERT
  exercises, learning the notebook, learning the assignment, and revision
  worksheets. Also use it to spin up a focused tracker for a specific assessment -
  "tracker for Friday's weekly test on Science ch 1-2", "mid-term tracker for the
  SST portion", "pre-board revision checklist" - by scoping to that test's
  chapters. Reach for it even when the user doesn't say "tracker" but is clearly
  talking about where Kashika is in her studying or test prep. Output is a live,
  self-contained dashboard the parent reopens anytime and ticks items off in.
---
 
# Kashika's Study Tracker
 
## What this skill produces
 
A single self-contained HTML dashboard that tracks Kashika's study progress for
every CBSE Class 10 subject. Each subject is its own tab (so the page stays short
and focused), and within a tab every chapter is tracked across that subject's
practice-area columns with a per-subject progress bar. The parent ticks items off
directly in the page. Three icons sit top-right: Analytics opens per-subject and
overall progress doughnuts, Download exports a print-to-PDF progress report (full
or a single subject), and Settings holds a Reset that requires typing "RESET" to
confirm. Check-off state is saved in the browser's
`localStorage` (and optionally synced across devices, see below), so it persists
across reopens - the parent does not need to ask you to "save" anything.
 
The point of the tracker is to make a genuinely sprawling task legible: five-plus
subjects, several sub-subjects inside Social Science, dozens of chapters, and five
things to do per chapter. Seeing it as bars that fill up is what makes it usable
day to day, so keep the dashboard the primary artifact and keep it accurate.
 
## How the data works
 
Everything the dashboard shows comes from a syllabus JSON file. The bundled seed
lives at `assets/syllabus.json` and is pre-populated with the CBSE 2025-26
chapter lists. You never hand-edit the HTML - you edit the JSON and rebuild. The
shape is:
 
```json
{
  "student": "Kashika",
  "grade": "CBSE Class 10",
  "note": "shown as an editable-starting-point banner",
  "practice_areas": ["NCERT Read", "NCERT Exercises", "Notebook", "Assignment", "Worksheet"],
  "subjects": [
    { "name": "Social Science (SST)",
      "groups": [
        { "name": "History – India and the Contemporary World-II",
          "chapters": ["The Rise of Nationalism in Europe", "..."] }
      ] }
  ]
}
```
 
`groups` exist so subjects with sub-subjects (Social Science has History,
Geography, Political Science, Economics; Science is split into Chemistry, Biology,
Physics) render as labelled sections. Subjects without sub-subjects use a single
group with an empty `name`.
 
**Practice areas can vary by subject and group.** `practice_areas` is the shared
base every chapter gets. A subject or a group can add its own with `extra_areas`,
and a chapter's columns are base + subject extras + group extras. This is how the
seed reflects Kashika's actual materials: SST adds Sagar's MCQ and Assertion-
Reason (with Map Work on History and Geography), Science adds the Pradeep question
bank across all branches plus Practical for Chemistry, Diagrams for Biology and
Numericals for Physics, English adds BBC Compacta, and Hindi adds All In One.
Maths instead fully replaces the base with its own set (NCERT Examples, NCERT
Exercises, RD Examples, RD Exercises, Worksheets) using an `areas` field - set
`areas` on a subject or group when its columns are completely different rather than
additive. There is also a top-level `common_areas` list appended to every subject's
columns (Revision Assignments, Weekly Test Papers / Model Test Paper).
 
**Progress is stored by meaning, not by position.** Each ticked cell is keyed
`"subject :: chapter :: area"` (the chapter's trailing "(partly)"-style annotation
is stripped, and characters Firebase forbids in keys - `. $ # [ ] /` - are replaced
with `_`). The same logical item therefore produces the same key in every tracker,
which is what lets a weekly test's coverage roll up into the Full Syllabus tracker.
It also means inserting or reordering chapters does NOT invalidate existing progress.
 
Optional top-level fields tailor a tracker: `title` overrides the heading,
`subtitle` overrides the line under it, `tracker_id` is a unique slug that keeps a
tracker's saved progress separate from every other tracker, `home` is a relative
link back to the hub (shown as a "← Dashboard" link), and `rollup_to` names the
tracker_id a test rolls its coverage up into (see the hub section). `sync.db_url`
enables Firebase (below). These are normally injected at build time via flags, not
hand-written.
 
## Building or rebuilding the dashboard
 
Run the bundled script - it injects the JSON into the template so every build is
identical and you are not rewriting HTML by hand:
 
```bash
python scripts/build_dashboard.py <syllabus.json> <output.html>
```
 
Then publish it (see "Delivering the dashboard" below).
 
## Updating progress
 
There are two ways progress changes, and they should stay in sync.
 
**The parent ticks boxes in the dashboard.** This is the normal path. The page
saves to `localStorage` automatically. You do not need to do anything.
 
**The parent tells you in chat** ("mark History chapter 2 notebook done"). If sync
is configured, the Firebase node `<db_url>/trackers/<tracker_id>.json` holds a flat
map of `"subject :: chapter :: area": true` for completed cells. Read it with a GET,
and apply a change with a PATCH (merge) of just the affected key(s) - `{key: true}`
to set, `{key: null}` to clear - rather than a whole-object PUT, so you never clobber
a concurrent write. Without sync the state lives only in each browser, so the
practical path is to have the parent tick in the page, or rebuild if the change is
structural.
 
## Answering "what's left" / progress questions
 
Read the current `state` (ask the parent to export it if you do not have a recent
copy) against the syllabus and answer concretely: which chapters are fully done,
which practice areas are outstanding, and a subject-level percentage. Lead with the
subject or sub-subject they asked about, name the specific gaps (e.g. "Geography
is 4 of 7 chapters fully done; Agriculture still needs Assignment and Worksheet"),
and keep it scannable. Offer to regenerate the dashboard if the structure changed.
 
## Changing what is tracked
 
The syllabus is a starting point, not gospel - schools differ, and Hindi/English
chapter lists in particular vary by course and edition. When the parent wants
changes, edit `assets/syllabus.json` (or a copy) and rebuild:
 
- **Add/remove/rename a chapter**: edit the relevant `chapters` array and rebuild.
  Progress is keyed by name, so inserting or reordering is safe; only *renaming* a
  chapter orphans its saved ticks (they'd need re-ticking under the new name).
- **Add a subject or sub-subject**: add a subject object, or add a group to an
  existing subject.
- **Change the practice areas**: edit the top-level `practice_areas` for the base
  columns every chapter shares, or add `extra_areas` on a subject or a group for
  ones only that subject/branch needs (e.g. a new question bank, or "Map Work" for
  just History and Geography). Table columns follow automatically.
- **Different student or grade**: change `student` and `grade`. The `localStorage`
  key is derived from them, so a new student starts with a clean slate.
The current CBSE Class 10 seed and its sourcing notes are documented in
`references/syllabus.md` - read it if the parent asks what the tracker is
pre-loaded with or whether a chapter list is current.
 
## Focused trackers for a specific test or exam
 
Weekly tests, mid-terms and pre-boards each cover their own slice of the syllabus,
and the parent will often want a small tracker for just that test rather than
scanning the whole-year one. This is the same machinery with a scoped syllabus, so
lean into it whenever the parent describes a test ("she has a weekly test on
Friday covering Science chapters 1 and 2 and Maths Real Numbers", "make a
mid-term tracker for the SST portion").
 
Build a focused tracker like this:
 
1. Copy the seed to a new file (e.g. `weekly-test-2026-07-31.json`) and keep only
   the subjects/groups/chapters that are on that test. It is fine to list loose
   chapters the parent names even if they cross subjects.
2. **Keep every practice-area header intact.** The parent always wants the same
   detailed column set as the master tracker, so preserve each subject's and
   group's full areas exactly as they appear in the seed - `practice_areas`,
   `common_areas`, and every `areas`/`extra_areas` on the subjects and groups you
   carried over. Do NOT swap in a lighter revision-only set of columns and do not
   drop columns; a test tracker is the master tracker narrowed to fewer chapters,
   with all the applicable headers still there. The only per-column trimming that
   is ever appropriate is dropping a column that literally cannot apply to the
   chapters on the test (e.g. no Map Work if the test has no map-based chapters) -
   and even then, only if the parent asks.
3. Set these top-level fields so it stands on its own and does not collide with
   the master tracker's saved progress:
   - `title`: what shows as the heading, e.g. `"Weekly Test - 31 Jul"`.
   - `subtitle`: optional context, e.g. `"Science Ch 1-2 · Maths: Real Numbers"`.
   - `tracker_id`: a unique slug, e.g. `"weekly-test-2026-07-31"`. This is what
     keeps its check-off state separate - always set it for test trackers.
4. Build and deliver exactly as below.
Because `tracker_id` scopes storage, the parent can keep the master tracker plus
several live test trackers open over time without them interfering.
 
## The exam hub, file layout, and roll-up
 
The whole thing is hosted as a small static site (GitHub Pages) with a landing hub:
 
```
repo root/
  index.html            hub: Full Syllabus box + a daily To-Do + every exam,
                        upcoming sorted by date (next highlighted), past dimmed
  full-syllabus.html    the whole-year master tracker (tracker_id: full-syllabus)
  test-tracker/
    weekly-cycle2-sst.html   one file per assessment
    ...
```
 
The hub is a hand-maintained page, bundled at `assets/hub.html` as the current
working version (Kashika's exams, Firebase URL, the Cycle Test Papers + Assignments
boxes, the daily To-Do, and a Settings gear with Backup/Restore all). To update the
hub, edit that file's `EXAMS` list (flip `ready:true`, adjust dates) and re-host it
as `index.html`. It is not produced by the build script.
 
**Slug/nomenclature.** Test tracker files and their `tracker_id` share one stable
slug of the form `{type}-{term}-{subject}` (lowercase, hyphenated): e.g.
`weekly-cycle2-sst`, `weekly-cycle3-science`, `mid-sem-term1-all`, `pre-board-1-all`.
Dates live in the hub's `EXAMS` list, never in filenames, so a teacher moving a date
never renames a file. The hub links `./test-tracker/<slug>.html`; flip an exam's
`ready:true` once its file exists.
 
**One-way roll-up (tests → Full Syllabus).** Test trackers are built with
`--rollup-to full-syllabus`. When a cell is ticked in a test, it is written once
(PATCH-merged) into the Full Syllabus tracker's cloud record, so that coverage is
durable: later un-ticking or resetting the test does NOT remove it from Full
Syllabus. It never flows the other way. The Full Syllabus tracker is built WITHOUT
`--rollup-to`, so it only receives. Because matching is by the semantic key, this
works automatically for chapter-based subjects; topic/section-based tests (a Hindi
grammar test, an English paper-sections test) simply have no full-syllabus chapter
to map onto.
 
**Build flags** (all optional, injected into the syllabus JSON at build time):
 
```bash
python scripts/build_dashboard.py <syllabus.json> <output.html> \
  --sync-url  https://<project>-default-rtdb.firebaseio.com \
  --home-url  ../index.html        # "← Dashboard" link target (index.html for the master)
  --rollup-to full-syllabus        # set on TEST trackers only
```
 
**Daily to-do / prep targets.** The hub carries a daily To-Do and each tracker
carries its own "Prep targets & notes" list (homework / tuition / self-goal / target
chips, optional due dates). These live in a separate Firebase area (`/todos/<listId>`)
and never touch the chapter-tracking data.
 
**Assignments & cycle-test papers.** The hub lists files from the repo's
`assignments/` and `cycle-tests/` folders via the GitHub contents API (user/repo
auto-detected from the Pages URL), so the parent just drops files in and they appear
as links. Cycle-test papers are named `cycle_test{N}_{subject}.pdf`, which maps onto
each exam, so a matching exam card also shows a direct "Test paper" link. Only works
when served from GitHub Pages.
 
**Backup / restore.** Each tracker's Settings has Export/Import for its own state.
The hub has a Backup all / Restore all that reads the entire `/trackers` and `/todos`
into one JSON and can PUT it back - the safety net if the database is ever cleared
(e.g. Firebase test-mode expiring). Restore only works once write rules are enabled.
 
## Cross-device sync (optional)
 
By default progress is saved per device in `localStorage`. To sync across devices,
the tracker can also read/write to a Firebase Realtime Database. It is off unless a
`sync.db_url` is present, and it degrades gracefully: the page always paints from
the on-device cache first, then pulls the latest from the cloud, and if the network
is unreachable (including inside the sandboxed Cowork preview) it just shows "saved
on this device" and keeps working. Ticks push to the cloud debounced; on open, the
cloud copy is treated as the source of truth for that tracker_id.
 
To enable it, build with the database URL rather than hand-editing JSON:
 
```bash
python scripts/build_dashboard.py <syllabus.json> <output.html> \
  --sync-url https://<project>-default-rtdb.firebaseio.com
```
 
The parent's one-time setup: create a free Firebase project, add a Realtime
Database, set its rules to allow read/write, and copy the database URL. Because
open rules mean anyone with the URL can read/write, this is fine for a low-stakes
personal tracker but is not private - say so when setting it up. Sync is device-
wide by origin, so host the synced build (see below) rather than opening it as a
local file, and reuse the same URL when you rebuild so progress carries over.
 
## Delivering the dashboard
 
**In Cowork**, publish the built HTML as an artifact so it persists and the parent
can reopen it anytime, then share it. This is the "live dashboard" experience they
want. If artifacts are unavailable, save the `.html` to the outputs folder and
present it as a file - it is fully self-contained and works by double-clicking.
 
For the real multi-tracker setup the parent hosts the files on GitHub Pages (hub +
full-syllabus + `test-tracker/`), which is what makes the cross-device sync and the
hub links work. Whichever way you deliver, remind them their ticks save
automatically, and that when you rebuild you reuse the same `--sync-url` so progress
carries over.
 
## Tone
 
You are helping a parent stay on top of their child's board-exam prep, which can be
stressful. Be encouraging and matter-of-fact, celebrate real progress (a subject
hitting 100%), and never turn "what's left" into pressure. Keep answers short and
practical.
