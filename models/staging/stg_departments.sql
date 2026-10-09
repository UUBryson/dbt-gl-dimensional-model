-- Light cleaning only. One row per (department_id, version). No joins here.
select
    cast(department_id as varchar)     as department_id,
    trim(department_name)              as department_name,
    trim(division)                     as division,
    cast(valid_from as date)           as valid_from,
    cast(valid_to as date)             as valid_to,
    cast(is_current as boolean)        as is_current
from {{ ref('raw_departments') }}
