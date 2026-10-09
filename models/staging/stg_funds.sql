-- Light cleaning only. One row per fund. No joins here.
select
    cast(fund_id as varchar)           as fund_id,
    trim(fund_name)                    as fund_name,
    lower(trim(fund_type))             as fund_type,
    cast(restricted_flag as boolean)   as restricted_flag
from {{ ref('raw_funds') }}
