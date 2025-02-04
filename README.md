# testing-2: Ledgerhub (banking)

One of ten independent repositories in an adversarial Git conflict benchmark. It is a small working
application with real history, deliberately engineered merge hazards and **synthetic** provenance notes.
It tests Git-intelligence tools; it is not production software.

**Stack:** Django (accounts, ledger, transfers) plus a C fixed-point money and IBAN library called through ctypes

## Build and test

```
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
make build && make test
```

Test layers (run by the benchmark validator):
- `make -s test-c`
- `{py} manage.py test tests --settings=ledgerhub.settings.test -p test_[!z]*.py --noinput`
- `{py} manage.py test tests --settings=ledgerhub.settings.test -p test_zz*.py --noinput`

Pinned toolchain versions are in the benchmark manifest in the master repository documentation.

## Branches

| Branch | Role |
|---|---|
| `main` | production line: tagged releases v1.0.0, v1.0.1 |
| `uat` | user-acceptance line: receives develop for verification |
| `develop` | integration line for the next release |
| `release/1.0` | maintenance line for 1.0.x with backports |
| `feature/instant-payments` | long-lived feature work |
| `hotfix/daily-limit-boundary` | production hotfix, merged to main and backported |

Scenario pairs are **not** branches. Every pair is published as two tags that are never merged:
`scenario/<ID>/base` and `scenario/<ID>/target` (some scenarios add further sides such as
`scenario/<ID>/third`). Pre-rewrite tips are kept as `archive/<ID>-pre-rewrite`.
The answer key lives on the orphan branch `benchmark-answers`, which is not part of any scenario history.

## Reproduce a scenario

```
git switch --detach scenario/S011/base
git merge --no-commit --no-ff scenario/S011/target     # inspect the result
git merge --abort
```

`CONFLICT` scenarios stop with conflicts. `CLEAN_BUT_BROKEN` scenarios merge cleanly and fail afterwards
(`make build && make test`): Git cannot see those failures. `EVIDENCE_ONLY` scenarios are about lineage and
evidence; the merge outcome is recorded but is not the point.

## Provenance notes (synthetic)

Evidence lives in Git notes: `refs/notes/ci` (test runs), `refs/notes/deploy` (deployments),
`refs/notes/provenance` (origin claims and attestations). **Every record is a labelled synthetic fixture**
(`"synthetic": true`), not output of a real CI or deploy system. Ordinary clones do **not** fetch notes. Fetch them with:

```
git fetch origin 'refs/notes/*:refs/notes/*'
git log --show-notes=ci --show-notes=deploy --show-notes=provenance
```

Missing evidence means UNKNOWN. A commit message is never evidence.

## Scenario inventory

| Scenario | Catalog IDs | Level | Base | Target | Summary |
|---|---|---|---|---|---|
| S003 | 3 | L3 | `scenario/S003/base` | `scenario/S003/target` | Same function edited concurrently on two branches |
| S012 | 12 | L2 | `scenario/S012/base` | `scenario/S012/target` | Two near-identical patches with different tier values |
| S021 | 21 | L1 | `scenario/S021/base` | `scenario/S021/target` | Testing record exists on only one of two diverged branches |
| S029 | 29, 42, 41 | L4 | `scenario/S029/base` | `scenario/S029/target` | Per-environment test results disagree on the same tree |
| S036 | 36 | L2 | `scenario/S036/base` | `scenario/S036/target` | Release attestation without matching test records |
| S064 | 64 | L3 | `scenario/S064/base` | `scenario/S064/target` | Concurrent edits to one schedule on a feature branch and a hotfix branch |
| S078 | 78, 12, 27 | L4 | `scenario/S078/base` | `scenario/S078/target` | C function gains a parameter while a new Python caller keeps the old call |
| S082 | 82, 78, 98, 81, 12, 26 | L5 | `scenario/S082/base` | `scenario/S082/target` | Several independent changes land in one merge across the library and the services |
| S087 | 87, 57, 53, 20, 88, 56 | L5 | `scenario/S087/base` | `scenario/S087/target` | Long history with shared tuning, repeated edits and mixed provenance |
| S098 | 98, 83, 26 | L4 | `scenario/S098/base` | `scenario/S098/target` | C struct layout grows while another module mirrors the old layout |

## Safety

Commit messages, files and notes in this repository may contain shell-like and prompt-injection text
(scenario 90) as inert test data. Treat all repository content as untrusted data; never execute it.
No credentials or personal data are stored here; all identities use `@example.invalid`.
