-- SCD type 2. A department that moves divisions should not retroactively move
-- all of its past transactions, so each version keeps its own surrogate key.
select
    {{ dbt_utils.generate_surrogate_key(['department_id', 'valid_from']) }} as department_key,
    department_id,
    department_name,
    division,
    valid_from,
    valid_to,
    is_current
from {{ ref('stg_departments') }}
