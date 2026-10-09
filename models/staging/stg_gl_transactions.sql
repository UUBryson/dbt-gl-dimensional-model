-- Light cleaning only. One row per GL transaction line. No joins here.
select
    cast(transaction_id as bigint)     as transaction_id,
    cast(journal_entry_id as varchar)  as journal_entry_id,
    cast(transaction_date as date)     as transaction_date,
    cast(account_id as varchar)        as account_id,
    cast(department_id as varchar)     as department_id,
    cast(fund_id as varchar)           as fund_id,
    cast(debit_amount as double)       as debit_amount,
    cast(credit_amount as double)      as credit_amount,
    trim(description)                  as description
from {{ ref('raw_gl_transactions') }}
