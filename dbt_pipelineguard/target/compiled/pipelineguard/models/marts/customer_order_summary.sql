select
    customers.customer_id,
    customers.first_name || ' ' || customers.last_name as customer_name,
    customers.email,
    count(fact_orders.order_id) as total_orders,
    coalesce(sum(fact_orders.total_order_amount), 0) as total_spent,
    min(fact_orders.order_date) as first_order_date,
    max(fact_orders.order_date) as most_recent_order_date
from "pipelineguard"."analytics_analytics"."stg_customers" as customers
left join "pipelineguard"."analytics_analytics"."fact_orders" as fact_orders
    on customers.customer_id = fact_orders.customer_id
group by
    customers.customer_id,
    customers.first_name,
    customers.last_name,
    customers.email