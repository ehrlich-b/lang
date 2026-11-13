# Prepare the Harbor comparison offline

The release draft answers what making Harbor required and where Lang fell short.
It is separate from the existing [Tariff comparison](compare-yacc-antlr.md), which
measures a different workload. Neither establishes a general superiority claim.

Use `scripts/comparison_release.py` with the frozen authoring inputs at commit
`209e4ca1e12a643102e37b58b6e43fe7ce4c5eaf`:

```sh
python3 -B scripts/comparison_release.py prepare --inputs /path/to/frozen-inputs --packet /path/to/offline-packet
python3 -B scripts/comparison_release.py validate --inputs /path/to/frozen-inputs --packet /path/to/offline-packet
```

The output directory must be outside this checkout. Preparation copies the
manifest-bound raw inputs, renders the [story source](comparison-release-story.md.in),
and records claims with source hashes and derivations. Validation independently
binds every quantitative claim to `measurements.json` by SHA-256 and independently
recomputes each metric, checks the exact rendered prose, local links, SDK archive
contents and identity, and the site's complete dry-run file inventory. Unknown
claims and extra prose fail validation. `site-snapshot.tar.gz` contains only the
existing site's files and passes its existing archive validator offline. It does
not include the draft story or assert that this site matches the SDK.
The plan also audits existing site links. Its unresolved legacy SDK download
is a recorded publication blocker; it does not become a valid draft-story link.

`release-plan.json` binds the packet to the product tree, input manifest and
archive. `draft-validated` means only that the draft accurately describes the
frozen records. It must never be relabeled a passed matched comparison.
`validate --final` deliberately fails: final validation needs the existing
matched comparison's committed head, rerunnable results for every arm, every
measured Lang loss and unmeasured dimension, plus a reconciled site/SDK build.
When that comparison passes, extend the derivations from its hashed result,
rerender the story, review the complete loss inventory and run final validation
against that head. This draft cannot promote itself using an arbitrary receipt.

No deploy command, live-site query, automatic fetch, or desk control is part of
this workflow. Publication and served-byte verification need a separate,
explicitly authorized release after final comparison validation.
