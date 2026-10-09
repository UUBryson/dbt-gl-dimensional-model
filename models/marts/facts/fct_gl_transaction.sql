-- Grain: one row per GL transaction line.
-- Balances are intentionally NOT stored. They are derived downstream so they can
-- never drift from the lines that produced them.
-- journal_entry_id is carried as a degenerate dimension (no dim table; it lives
-- on the fact) so the debits-equal-credits test can group by it.
with txn as (
    select * from {{ ref('stg_gl_transactions') }}
)
select
    {{ dbt_utils.generate_surrogate_key(['txn.transaction_id']) }} as gl_transaction_key,
    txn.transaction_id,
    txn.journal_entry_id,                              -- degenerate dimension
    a.account_key,
    d.department_key,
    f.fund_key,
    txn.transaction_date                               as date_key,
    txn.debit_amount,
    txn.credit_amount,
    txn.debit_amount - txn.credit_amount               as net_amount
from txn
-- effective-dated joins resolve each line to the dimension version that was
-- live on the transaction date (this is what makes SCD type 2 actually useful)
left join {{ ref('dim_account') }} a
    on  txn.account_id = a.account_id
    and txn.transaction_date >= a.valid_from
    and txn.transaction_date <  a.valid_to
left join {{ ref('dim_department') }} d
    on  txn.department_id = d.department_id
    and txn.transaction_date >= d.valid_from
    and txn.transaction_date <  d.valid_to
left join {{ ref('dim_fund') }} f
    on  txn.fund_id = f.fund_id
