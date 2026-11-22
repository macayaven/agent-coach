# Playbook refresh procedure

This is for the agent that refreshes `playbook.md`, normally the monthly GitHub Action. The goal is to keep the playbook matched to what top AI labs and coding-agent makers currently recommend, without letting unsourced opinion creep in.

1. Read `playbook.md` and `sources.md` in this directory. Note the playbook's `reviewed:` date.
2. Fetch every source in `sources.md`. Look for guidance that is new, changed or withdrawn since the `reviewed:` date: new recommended workflows, features that replace older techniques, practices a lab now advises against.
3. Edit `playbook.md`:
   - **Revise** a technique when its guidance changed. Update its `Sources` line and set its `verified:` date to today.
   - **Add** a technique only when at least one official lab or tool-maker source recommends it. Practitioner sources can support a technique but not justify one alone.
   - **Retire** a technique that sources now advise against or that a newer feature has replaced. Move it to "Retired" with a one-line reason and a link. Don't delete it, because people learning need to know why it changed.
   - Keep the existing format for each entry. Keep the whole file under about 4,500 words, since agents load it into context. Merge overlapping techniques rather than growing the list.
   - Every claim needs a source URL you actually fetched in this run. If you can't source something, leave it out.
4. If you found an official source that should be checked every month, add it to `sources.md`. Remove sources that no longer exist.
5. Set the playbook's `reviewed:` date to today, even if nothing changed. A refresh that found nothing new is still a refresh.
6. Write `.refresh-summary.md` in the repository root. It becomes the pull request description. Include:
   - what changed, as one bullet per technique (added, revised or retired), each with its source link
   - anything you were unsure about, for the human reviewer
   - sources that failed to load
7. Run `python3 -m unittest discover -s tests` and fix anything you broke.

Don't change any files outside `skills/agent-coach/references/`, apart from `.refresh-summary.md`.
