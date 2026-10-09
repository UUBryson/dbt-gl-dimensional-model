# General Ledger: a dimensional model in dbt

A reference implementation of a Kimball-style star schema for general ledger
data, built with dbt and DuckDB on a synthetic dataset. No real institutional
data is used anywhere in this repo.

This is the sanitized, public version of a pattern I built and run in
production: a multi-million-row GL warehouse that serves as the single source
of truth for financial reporting at a private university. This repo keeps the
architecture and the modeling decisions and replaces every byte of real data
with a generator.

## Why this exists

Most "dbt example" repos model an online store. Finance data is harder and more
interesting, because the source system is normalized for transaction integrity,
not for analysis, and because accounting has a built-in correctness check that
most domains lack: every journal entry must balance. That check becomes a test,
which is the part I care about most.

If you only read one section, read [Design decisions](#design-decisions). The
SQL is the easy part. The choices are the job.

## Architecture

```
 source (synthetic GL extract)
        │
        ▼
 staging/         one model per source table, light cleaning only
   stg_gl_transactions
   stg_accounts
   stg_departments
   stg_funds
        │
        ▼
 marts/
   dimensions/    conformed dimensions, SCD where attributes change
     dim_account          (SCD type 2)
     dim_department       (SCD type 2)
     dim_fund             (SCD type 1)
     dim_date             (generated calendar)
   facts/
     fct_gl_transaction   grain: one row per GL transaction line
        │
        ▼
 reporting/       a couple of example aggregate models for BI tools
   rpt_net_by_department_period
```

## The grain (declared first, on purpose)

Kimball's first rule is to declare the grain before modeling anything. The grain
of `fct_gl_transaction` is **one row per general ledger transaction line** (one
debit or credit posting). Everything else follows from that:

- balances are derived, never stored, so they can never drift from the lines
- the fact table is fully additive across account, department, fund, and date
- a running balance is semi-additive (you sum across time, not across a point in
  time), which the reporting models handle explicitly rather than hiding

If I had picked "one row per journal entry" instead, I would have lost the
ability to split a single entry across departments, which is the most common
real question finance asks. Grain choice is not cosmetic.

## Dimensions and why each one is modeled the way it is

| Dimension | SCD | Why |
|---|---|---|
| `dim_account` | Type 2 | The chart of accounts gets recategorized. A type 1 overwrite would silently rewrite history and make last year's report change when you rerun it. Type 2 keeps `valid_from` / `valid_to` / `is_current`. |
| `dim_department` | Type 2 | Reorgs happen. A department that moves under a new division should not retroactively move all of its past transactions. |
| `dim_fund` | Type 1 | Fund attributes here are descriptive and corrected, not historically meaningful. Type 1 is honest about that. Do not reach for Type 2 reflexively. |
| `dim_date` | generated | A real calendar with fiscal period logic, generated in dbt, not loaded. Fiscal year here starts in July, which is where a lot of higher-ed and public-sector reporting quietly breaks. |

## Tests, which are the actual point

This is where the repo connects to how I work. Before a number leaves my hands
it gets a source, a method, and a falsifier. In dbt those become tests:

- **Source integrity:** `unique` and `not_null` on every surrogate and natural
  key; `relationships` tests so no fact row points at a missing dimension row.
- **The accounting falsifier:** a custom singular test that asserts total debits
  equal total credits for every journal entry. In accounting this must be true.
  If the test fails, the data is wrong, full stop. This is the cleanest example
  I know of a domain that hands you a falsifier for free, and most pipelines
  throw it away.
- **Grain protection:** a test that fails if the supposed line-level grain ever
  collapses to entry level (duplicate detection on the line key).

The point is not test coverage for its own sake. The point is that a wrong
number should make the build fail, loudly, before anyone sees it.

## The synthetic data

`seeds/` and `scripts/generate_gl.py` produce a realistic but entirely fake GL:
a chart of accounts, a handful of departments and funds, and balanced journal
entries across a few fiscal years. The generator deliberately injects a small
number of edge cases (a mid-year department reorg, an account recategorization)
so the SCD logic and the tests have something real to catch.

## Run it

```bash
# requires Python 3.11+, no warehouse needed; DuckDB runs in-process
python -m venv .venv && source .venv/Scripts/activate   # or .venv\Scripts\activate on cmd
pip install -r requirements.txt
dbt deps --profiles-dir .            # install dbt_utils
python scripts/generate_gl.py        # writes synthetic seeds
dbt build --profiles-dir .           # seed + run + test in one step
```

`dbt build` runs the seeds, the models, and the tests in dependency order. On a
clean run that is 10 models and 30 tests, all green, in under two seconds.
Everything runs locally against a DuckDB file. There is nothing to provision and
no credentials anywhere.

## Design decisions

- **DuckDB, not Snowflake/BigQuery.** A portfolio model should run on a reviewer's
  laptop in thirty seconds with no signup. The dbt patterns are identical; the
  warehouse is swappable by changing the profile.
- **Surrogate keys via `dbt_utils.generate_surrogate_key`,** not source natural
  keys, so the model survives a source system that reuses or reissues IDs.
- **Staging does cleaning only, never joins.** Joins live in the marts. This keeps
  staging models one-to-one with sources and easy to reason about.
- **Balances are never stored.** See the grain section. Storing a balance is
  storing a number that can disagree with the lines that produced it.
- **SCD type is chosen per dimension, not globally.** Type 2 everywhere is a
  common mistake that bloats the warehouse and slows every query to defend
  against history that nobody actually asks about.

## What I would do differently at real scale

- Incremental materialization on the fact table once it passes a few million
  rows, with a late-arriving-fact strategy, rather than full refresh.
- Snapshotting the source extract so the SCD logic is driven by dbt snapshots
  instead of being inferred, which is more honest about when a change was seen.
- A separate exposures layer documenting which dashboards depend on which models,
  so a column rename cannot silently break a downstream report. (I have been
  burned by exactly that.)

---

*Synthetic data only. This repo demonstrates an architecture, not any
organization's financials.*
