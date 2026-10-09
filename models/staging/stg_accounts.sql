-- Light cleaning only. One row per (account_id, version). No joins here.
select
    cast(account_id as varchar)        as account_id,
    trim(account_name)                 as account_name,
    lower(trim(account_type))          as account_type,
    trim(category)                     as category,
    cast(valid_from as date)           as valid_from,
    cast(valid_to as date)             as valid_to,
    cast(is_current as boolean)        as is_current
from {{ ref('raw_accounts') }}
