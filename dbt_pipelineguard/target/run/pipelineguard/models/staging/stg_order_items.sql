
  create view "pipelineguard"."analytics_analytics"."stg_order_items__dbt_tmp"
    
    
  as (
    select
    order_item_id,
    order_id,
    product_id,
    quantity,
    cast(unit_price as numeric(10, 2)) as unit_price,
    quantity * cast(unit_price as numeric(10, 2)) as line_total
from "pipelineguard"."public"."order_items"
  );