# Add tests for important no-cov features (apibase-features.csv)

**Date**: 2026-06-24
**Branch**: v2025
**Status**: completed

## Goal

`apibase-features.csv` lists many features with `Test Coverage = None` ("No
tests"). Add tests for the **important** subset — core, high-regression-risk,
or known-buggy behaviors — and fix the broken pytest-django DB harness that
currently blocks any DB-backed test (TLG-003).

Target outcome: green suite (the 7 currently-failing `test_nested_orphan_delete`
tests pass) plus new tests covering the prioritized no-cov features below.

## Constraints and Non-Goals

- Follow TDD philosophy: tests verify **observable behavior via public
  interfaces**, not implementation details (per global testing rules).
- Do not change production behavior to make a test pass, with **one explicit
  approved exception**: the `parse_urn` latent bug (URN-002). User approved
  fixing it — write a regression test that fails against current behavior,
  fix the prefix-shadow so `prefix` is actually validated, confirm green.
- No new runtime dependencies. Test-only infra changes are allowed
  (`tests/settings.py`, `[tool.pytest.ini_options]`).
- Non-goal: 100% coverage. We target the *important* no-cov rows, not all of
  them. GraphQL templates, meta API, consumers, archives, routers are
  deferred unless trivially cheap.
- Non-goal: refactoring production modules.

## Priority rationale (which no-cov rows are "important")

Selected by: core to the library + high regression risk + cheap to test well.

**Tier A — pure functions, no DB, high value (do first):**
- URN-001 `model_urn`, URN-002 `parse_urn` (known latent bug), URN-003
  `rest_endpoint_from_urn` — core identity, currently zero tests.
- FRM-001..004 form fields (`ListCharField`, `ListIntegerField`,
  `CharRangeField`/`CharRangeWidget`, `MonthRangeField.compress`) — pure
  clean/compress logic.
- GQU-006 `to_content_disposition` + GQU-007 `get_filename_from_header`
  (round-trip), GQU-001 `strip_relay` — pure utils.
- GQE-001 `JSONEncode` Decimal handling — pure.
- SET-001..005 `apibase_settings` singleton — defaults, override, caching,
  import-string, AttributeError.

**Tier B — DB-backed, requires harness fix:**
- FIL-003 `WordFilter` Japanese zen/han search (documented, complex, untested).
- FIL-001 `BaseFilter` built-in id filters (pk / id__includes / id__in_csv …).

**Deferred (note in Outcomes, do not silently drop):** SER-007/008/010/014/015,
VWS-002/003 batch, storage STO-001/002, renderers, pagination, GraphQL
mixins. Candidates for a follow-up plan.

## Plan of Work

### Phase 0 — Fix pytest-django DB harness (blocker)
1. Add `tests/settings.py` Django settings module (mirror current
   `conftest.py` configure: in-memory sqlite, contenttypes+auth+tests apps,
   `MIGRATION_MODULES={"tests": None}`, BigAutoField).
2. Add `[tool.pytest.ini_options]` to `pyproject.toml` with
   `DJANGO_SETTINGS_MODULE = "tests.settings"` and register markers.
3. Reduce `conftest.py` to defer to pytest-django (it configures Django early
   in `pytest_load_initial_conftests`, before collection — earlier than the
   root conftest, so the apibase-import-during-collection concern is covered).
   Keep a guarded fallback only if needed.
4. Verify: `uv run pytest -q` → previously-failing 7 nested tests pass, no
   regressions in the 67 passing tests.

### Phase 1 — Tier A pure-function tests (TDD, one behavior at a time)
5. `tests/test_urn.py` — model_urn (default/override nss+nid, no `_meta` →
   ""), parse_urn (valid parse, nid mismatch → None, others tail, **plus a
   characterization test documenting the prefix-shadow no-op bug**),
   rest_endpoint_from_urn (self vs service subdomain, domain resolution
   order, parse-failure → None). Mock `get_current_site` where needed.
6. `tests/test_fields.py` — ListCharField/ListIntegerField (list coercion,
   empty → []), CharRangeWidget value_from_datadict, MonthRangeField.compress
   (YYYYMM → slice start-of-month..end-of-month).
7. `tests/test_utils.py` — to_content_disposition / get_filename_from_header
   round-trip incl. UTF-8 + non-utf8 → None; strip_relay edges/node flatten.
8. `tests/test_encoders.py` — JSONEncode Decimal → float; passthrough.
9. `tests/test_settings.py` — defaults, APIBASE override, caching, import
   string resolution, unknown attr → AttributeError.

### Phase 2 — Tier B DB-backed tests
10. `tests/test_filters.py` — WordFilter zen/han matching, multi-token AND,
    empty value passthrough; BaseFilter id filters. Add fixture models to
    `tests/models.py` only if existing Parent/Child are insufficient.

### Wrap-up
11. Run full suite + coverage; update CSV rows' Test Coverage/Status for the
    features now covered.
12. Update `Outcomes & Retrospective`; move plan to `completed/`.

## Progress

- [x] Phase 0: harness fix — done. Root cause was deeper than config: pytest-django
  AND pyyaml/drf-spectacular were never installed in the devenv venv (only base
  deps synced). Fixed by `uv sync --extra dev --extra schema`, adding
  `tests/settings.py`, wiring `[tool.pytest.ini_options] DJANGO_SETTINGS_MODULE`,
  and slimming root conftest to a fallback. Suite: 74 passed (was 67p/7f).
- [x] Phase 1: Tier A pure tests — done. New: test_urn.py (14, incl. parse_urn
  bug fix red→green), test_fields.py (11), test_utils.py (11), test_encoders.py
  (3), test_settings.py (10). parse_urn fix applied to apibase/urn.py.
- [x] Phase 2: Tier B filter tests — done. test_filters.py (10): WordFilter
  zen/han + multi-token AND + fullwidth-space split + empty passthrough;
  BaseFilter pk/id__includes/id__excludes/id__in_csv/id__not_in_csv.
- [x] Wrap-up: CSV rows updated for all covered features + TLG-003; plan promoted.

## Verification

- `uv run pytest -q` green (0 failed).
- `uv run pytest --cov=apibase` shows coverage increase on urn/fields/utils/
  settings/filters modules.
- `uv run ruff check tests/` clean.

## Decision Log

- 2026-06-24: pytest-django is dormant because `django_settings_module` is set
  only under `[tool.django-stubs]`, not `[tool.pytest.ini_options]`. Fix the
  harness first; it is itself an "important" no-cov gap (TLG-003) and unblocks
  Tier B.
- 2026-06-24: `parse_urn` prefix validation is a confirmed no-op
  (`prefix, *ma = re.findall(...)` then `if prefix == prefix`). **User approved
  fixing it** (regression test → fix → green). Scope confirmed: harness +
  Tier A + Tier B.

## Surprises and Discoveries

- 2026-06-24: The harness wasn't merely mis-wired — the devenv venv
  (`UV_PROJECT_ENVIRONMENT=.devenv/state/venv`) had only base deps; pytest-django,
  pyyaml, drf-spectacular were absent. devenv `uv.sync.enable` does not install
  optional extras. `uv sync --extra dev --extra schema` was required.
- 2026-06-24: Setting `python_files=["tests.py"]` over-collected
  `apibase/tests/tests.py` (the RestTestCase base, TST-001) as a test module.
  Reverted — default `python_files` is correct; that file is a helper, not tests.
- 2026-06-24: **Second latent bug found** (FRM-001/002): the non-sequence
  branch of `ListFieldMixin.to_python_value` raises
  `ValidationError(self.error_messages["invalid_list"])`, but `"invalid_list"`
  is never added to `error_messages` → it raises `KeyError`, not a clean
  ValidationError. Characterized with `pytest.raises(KeyError)` and flagged;
  NOT fixed (outside approved scope — only parse_urn was approved). Candidate
  one-line fix: add the message via `default_error_messages`.

## Outcomes and Retrospective

**Shipped:** suite 67p/7f → **130 passed, 0 failed**. 56 new tests across 6 files.

- Harness: `tests/settings.py` + `[tool.pytest.ini_options]
  DJANGO_SETTINGS_MODULE="tests.settings"` in `pyproject.toml`; root `conftest.py`
  reduced to a fallback. `uv sync --extra dev --extra schema` was required (the
  devenv venv lacked pytest-django/pyyaml/drf-spectacular). The 7 nested-orphan
  tests now pass with real tables.
- New tests: test_urn.py (14), test_fields.py (11), test_utils.py (10),
  test_encoders.py (3), test_settings.py (8), test_filters.py (10).
- Production fix (approved): `parse_urn` prefix shadow bug in `apibase/urn.py`
  — `prefix, *ma = ...; if prefix == prefix` → `actual_prefix, *ma = ...; if
  actual_prefix == prefix`. Red→green regression tests.
- CSV updated: URN-001/002/003, SET-001..005, FRM-001..004, GQU-001/006/007,
  GQE-001, FIL-001/003, TLG-003 → Test Coverage + Pass.

**Verified:** `uv run pytest -q` → 130 passed; `uv run ruff check` clean; CSV
re-parsed (119 rows × 10 cols, intact). pytest-cov is not installed, so no
coverage % was produced.

**Follow-ups (not done — candidate next plan):**
- Second latent bug: `ListFieldMixin.to_python_value` raises `KeyError`
  (missing `error_messages["invalid_list"]`) instead of `ValidationError` on
  non-sequence input. Characterized, not fixed (out of approved scope).
- Deferred no-cov rows: SER-007/008/010/014/015, VWS-002/003 batch, STO-001/002,
  renderers, pagination, GraphQL SummaryMixin/connections.
- Consider adding pytest-cov so coverage floors can be enforced.

**Durable conventions changed:** test harness now standard pytest-django (DB
marker works). Saved to memory.
