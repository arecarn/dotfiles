# Knowledge routing probes

`agent-knowledge check` verifies a bundle's *structure*: links resolve, entries
match their documents, frontmatter is present. It cannot see the failure that
actually costs a read -- an index entry that is internally consistent but no
longer matches the tasks people bring, so a cold agent opens the wrong document
or none at all.

This measures that directly. Each probe puts a realistic task to a cold agent
that has never seen the repo, and records which entry it opens unprompted.

Run by hand, not in CI: each probe starts a real agent session in a Herdr tab and
spends tokens. Minutes, not seconds.

## Running

Needs a Herdr session and `jq`.

```bash
cd tests/knowledge_routing
while IFS=$'\t' read -r slug cwd expected task; do
	./probe.sh "$slug" "$cwd" "$task" >/dev/null
	echo "=== $slug (expected: $expected)"
	grep -iE 'bundle|\.md|NONE' "results/$slug.txt" | tail -5
done <cases.tsv
```

Close the tabs afterwards -- each `results/<slug>.tab` holds the id:

```bash
for f in results/*.tab; do herdr tab close "$(cat "$f")"; done
```

## Reading the result

A probe passes when the agent consulted **exactly** the expected document. Two
distinct failures:

- **Opened nothing, or the wrong entry.** The description does not match how the
  task is actually worded. Fix the description -- that is the index failing at
  its only job.
- **Opened several.** The entries overlap, or the index does not say clearly
  enough what each one is for.

The `control` case expects `NONE`. Without it a bundle that routes everything
correctly is indistinguishable from one whose agents just open everything.

## cases.tsv

Tab-separated: `slug`, `cwd`, `expected`, `task`. One row per index entry, plus
the control.

Task wording must not leak the answer -- no filename fragments, no "bundle", no
"knowledge". Word it the way someone with the problem would ask, not the way the
document is titled. Add a row when a bundle gains an entry; the harness has no
way to know an entry exists if nothing asks for it.
