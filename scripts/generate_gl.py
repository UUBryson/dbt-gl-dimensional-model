"""
Generate a synthetic, balanced general ledger for the dbt model.

Everything here is fake. The point is to produce data that exercises the
modeling decisions: balanced journal entries (debits == credits), a couple of
slowly-changing dimension events (an account recategorization and a department
reorg), and a date range that spans three fiscal years.

Run from anywhere:  python scripts/generate_gl.py
Writes CSV seeds into ../seeds/.
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)  # deterministic output so the repo is reproducible

HERE = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.normpath(os.path.join(HERE, "..", "seeds"))
os.makedirs(SEED_DIR, exist_ok=True)

FY_START = date(2021, 7, 1)
FY_END = date(2024, 6, 30)
REORG = date(2023, 7, 1)        # the SCD type 2 change point
CURRENT_END = date(2999, 12, 31)
N_JOURNAL_ENTRIES = 3000


def iso(d: date) -> str:
    return d.isoformat()


# ---------------------------------------------------------------------------
# dim_account source: chart of accounts, effective-dated (SCD type 2 expressed
# as rows). One account (6100) is recategorized at the reorg date.
# ---------------------------------------------------------------------------
ACCOUNTS = [
    # id,   name,                      type,         category
    ("1000", "Operating Cash",         "asset",      "Current Assets"),
    ("1200", "Accounts Receivable",    "asset",      "Current Assets"),
    ("1500", "Property and Equipment", "asset",      "Fixed Assets"),
    ("2000", "Accounts Payable",       "liability",  "Current Liabilities"),
    ("2500", "Deferred Revenue",       "liability",  "Current Liabilities"),
    ("3000", "Net Assets",             "net_assets", "Net Assets"),
    ("4000", "Tuition Revenue",        "revenue",    "Operating Revenue"),
    ("4100", "Gifts and Grants",       "revenue",    "Operating Revenue"),
    ("4200", "Auxiliary Revenue",      "revenue",    "Operating Revenue"),
    ("5000", "Salaries and Wages",     "expense",    "Compensation"),
    ("5100", "Benefits",               "expense",    "Compensation"),
    ("6000", "Supplies",               "expense",    "Operating"),
    ("6200", "Travel",                 "expense",    "Operating"),
    ("6300", "Utilities",              "expense",    "Operating"),
    ("7000", "Depreciation",           "expense",    "Non-Operating"),
]

RECATEGORIZED = ("6100", "Professional Services", "expense")


def write_accounts():
    rows = []
    for acct_id, name, acct_type, category in ACCOUNTS:
        rows.append([acct_id, name, acct_type, category,
                     iso(FY_START), iso(CURRENT_END), "true"])
    # 6100 changes category from Operating to Instruction at the reorg date.
    rid, rname, rtype = RECATEGORIZED
    rows.append([rid, rname, rtype, "Operating",
                 iso(FY_START), iso(REORG), "false"])
    rows.append([rid, rname, rtype, "Instruction",
                 iso(REORG), iso(CURRENT_END), "true"])
    _write("raw_accounts.csv",
           ["account_id", "account_name", "account_type", "category",
            "valid_from", "valid_to", "is_current"],
           rows)
    return [a[0] for a in ACCOUNTS] + [RECATEGORIZED[0]]


# ---------------------------------------------------------------------------
# dim_department source: one department (Library) moves divisions at the reorg.
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    # id,  name,                  division
    ("10", "College of Arts",     "Academic Affairs"),
    ("11", "College of Business", "Academic Affairs"),
    ("12", "College of Nursing",  "Academic Affairs"),
    ("20", "Admissions",          "Enrollment"),
    ("21", "Financial Aid",       "Enrollment"),
    ("30", "Facilities",          "Operations"),
    ("31", "Information Tech",    "Operations"),
]
REORG_DEPT = ("40", "Library")  # moves Academic Affairs -> Student Success


def write_departments():
    rows = []
    for dep_id, name, division in DEPARTMENTS:
        rows.append([dep_id, name, division,
                     iso(FY_START), iso(CURRENT_END), "true"])
    did, dname = REORG_DEPT
    rows.append([did, dname, "Academic Affairs",
                 iso(FY_START), iso(REORG), "false"])
    rows.append([did, dname, "Student Success",
                 iso(REORG), iso(CURRENT_END), "true"])
    _write("raw_departments.csv",
           ["department_id", "department_name", "division",
            "valid_from", "valid_to", "is_current"],
           rows)
    return [d[0] for d in DEPARTMENTS] + [REORG_DEPT[0]]


# ---------------------------------------------------------------------------
# dim_fund source: type 1, no history.
# ---------------------------------------------------------------------------
FUNDS = [
    ("F100", "Unrestricted Operating",  "unrestricted",          "false"),
    ("F200", "Restricted Scholarships", "temporarily_restricted", "true"),
    ("F300", "Endowment",               "permanently_restricted", "true"),
    ("F400", "Auxiliary Enterprises",   "unrestricted",          "false"),
    ("F500", "Plant Fund",              "temporarily_restricted", "true"),
]


def write_funds():
    rows = [[fid, name, ftype, restricted] for fid, name, ftype, restricted in FUNDS]
    _write("raw_funds.csv",
           ["fund_id", "fund_name", "fund_type", "restricted_flag"],
           rows)
    return [f[0] for f in FUNDS]


# ---------------------------------------------------------------------------
# fact source: balanced journal entries, one row per line.
# ---------------------------------------------------------------------------
def random_date() -> date:
    span = (FY_END - FY_START).days
    return FY_START + timedelta(days=random.randint(0, span))


def write_transactions(account_ids, department_ids, fund_ids):
    rows = []
    txn_id = 1
    for je in range(1, N_JOURNAL_ENTRIES + 1):
        je_id = f"JE{je:06d}"
        d = random_date()
        total = random.randint(100, 50000)  # whole dollars, exact balancing

        # debit side: 1 or 2 lines summing to total
        debit_splits = _split(total, random.randint(1, 2))
        # credit side: 1 or 2 lines summing to total
        credit_splits = _split(total, random.randint(1, 2))

        for amt in debit_splits:
            rows.append([txn_id, je_id, iso(d),
                         random.choice(account_ids),
                         random.choice(department_ids),
                         random.choice(fund_ids),
                         amt, 0, "debit posting"])
            txn_id += 1
        for amt in credit_splits:
            rows.append([txn_id, je_id, iso(d),
                         random.choice(account_ids),
                         random.choice(department_ids),
                         random.choice(fund_ids),
                         0, amt, "credit posting"])
            txn_id += 1

    _write("raw_gl_transactions.csv",
           ["transaction_id", "journal_entry_id", "transaction_date",
            "account_id", "department_id", "fund_id",
            "debit_amount", "credit_amount", "description"],
           rows)


def _split(total: int, parts: int):
    if parts == 1:
        return [total]
    cut = random.randint(1, total - 1)
    return [cut, total - cut]


def _write(filename, header, rows):
    path = os.path.join(SEED_DIR, filename)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {len(rows):>6} rows -> {path}")


if __name__ == "__main__":
    accts = write_accounts()
    deps = write_departments()
    funds = write_funds()
    write_transactions(accts, deps, funds)
    print("done. next: dbt deps && dbt seed && dbt run && dbt test")
