-- Generated calendar, not loaded. Fiscal year starts in July, which is where a
-- lot of higher-ed and public-sector reporting quietly breaks.
with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2021-07-01' as date)",
        end_date="cast('2024-07-01' as date)"
    ) }}
)
select
    cast(date_day as date)                              as date_key,
    extract(year  from date_day)                        as calendar_year,
    extract(month from date_day)                        as calendar_month,
    extract(day   from date_day)                        as day_of_month,
    case when extract(month from date_day) >= 7
         then extract(year from date_day) + 1
         else extract(year from date_day)
    end                                                 as fiscal_year,
    case when extract(month from date_day) >= 7
         then extract(month from date_day) - 6
         else extract(month from date_day) + 6
    end                                                 as fiscal_period
from spine
