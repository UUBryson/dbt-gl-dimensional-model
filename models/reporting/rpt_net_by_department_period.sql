-- Example aggregate for a BI tool. Net activity by division, department, and
-- fiscal period. net_amount is additive, so this is a plain sum.
select
    dt.fiscal_year,
    dt.fiscal_period,
    dep.division,
    dep.department_name,
    sum(f.net_amount) as net_amount,
    sum(f.debit_amount) as total_debits,
    sum(f.credit_amount) as total_credits
from {{ ref('fct_gl_transaction') }} f
join {{ ref('dim_date') }} dt
    on f.date_key = dt.date_key
join {{ ref('dim_department') }} dep
    on f.department_key = dep.department_key
group by 1, 2, 3, 4
