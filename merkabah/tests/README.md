# Merkabah validation — candidate v0.1

Run from the repository root:

```bash
python merkabah/tests/validate_graph.py merkabah/schema/merkabah_candidate_v0.1.json
python -m unittest discover -s merkabah/tests -v
```

Requires Python 3.10+; no third-party dependencies.

**Scope:** structural consistency only, on the existing graph seed (45 nodes, 50 edges). A PASS is **not** an exegetical, visual or scientific endorsement.

Open questions: textual face attribution differs in Ezekiel 1:10 / 10:14; historical canal and wheel geometry are not yet independently checked; source verse-range references are too broad for a final claim-level provenance standard. Keep proposed changes in pull requests until reviewed.

Contributions: [issue #36](https://github.com/talkus/harmonie-libre/issues/36); [graph #39](https://github.com/talkus/harmonie-libre/issues/39); [tests #40](https://github.com/talkus/harmonie-libre/issues/40).
