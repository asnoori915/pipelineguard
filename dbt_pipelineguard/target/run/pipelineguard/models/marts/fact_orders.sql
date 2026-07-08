
  
    

  create  table "pipelineguard"."analytics_analytics"."fact_orders__dbt_tmp"
  
  
    as
  
  (
    with order_totals as (
    select
        order_id,
        sum(line_total) as total_order_amount
    from "pipelineguard"."analytics_analytics"."stg_order_items"
    group by order_id
),

order_payments as (
    select
        order_id,
        sum(amount) as payment_amount,
        max(payment_status) as payment_status
    from "pipelineguard"."analytics_analytics"."stg_payments"
    group by order_id
)

select
    orders.order_id,
    orders.customer_id,
    orders.order_date,
    orders.status,
    coalesce(order_totals.total_order_amount, 0) as total_order_amount,
    order_payments.payment_amount,
    order_payments.payment_status
from "pipelineguard"."analytics_analytics"."stg_orders" as orders
left join order_totals
    on orders.order_id = order_totals.order_id
left join order_payments
    on orders.order_id = order_payments.order_id
  );
  