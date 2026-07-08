
    
    

select
    customer_id as unique_field,
    count(*) as n_records

from "pipelineguard"."analytics_analytics"."customer_order_summary"
where customer_id is not null
group by customer_id
having count(*) > 1


