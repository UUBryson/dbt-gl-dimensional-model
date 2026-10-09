-- SCD type 2. Surrogate key includes valid_from so each version is distinct.
-- A type 1 overwrite here would silently rewrite history when accounts are
-- recategorized, which is exactly what we do not want for financial reporting.
select
    {{ dbt_utils.generate_surrogate_key(['account_id', 'valid_from']) }} as account_key,
    account_id,
    account_name,
    account_type,
    category,
    valid_from,
    valid_to,
    is_current
from {{ ref('stg_accounts') }}
