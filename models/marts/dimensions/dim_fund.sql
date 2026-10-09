-- Type 1. Fund attributes here are descriptive and corrected, not historically
-- meaningful, so one row per fund is the honest choice. Do not reach for type 2
-- reflexively.
select
    {{ dbt_utils.generate_surrogate_key(['fund_id']) }} as fund_key,
    fund_id,
    fund_name,
    fund_type,
    restricted_flag
from {{ ref('stg_funds') }}
