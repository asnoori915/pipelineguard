
  create view "pipelineguard"."analytics_analytics"."stg_orders__dbt_tmp"
    
    
  as (
    select
    order_id,
    customer_id,
    cast(order_date as date) as order_date,
    status,
    case
        when order_date > current_date then true
        else false
    end as is_future_order
from "pipelineguard"."public"."orders"
  );