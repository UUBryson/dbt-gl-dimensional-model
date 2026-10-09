-- The accounting falsifier. Every journal entry must balance: total debits must
-- equal total credits. In accounting this is not a guideline, it is an identity.
-- If this test returns any rows, the data is wrong, and the build should fail
-- before anyone sees a report built on it.
--
-- A singular test passes when it returns zero rows.
select
    journal_entry_id,
    sum(debit_amount)  as total_debits,
    sum(credit_amount) as total_credits
from {{ ref('fct_gl_transaction') }}
group by journal_entry_id
having abs(sum(debit_amount) - sum(credit_amount)) > 0.005
