
  create view "pipelineguard"."analytics_analytics"."stg_customers__dbt_tmp"
    
    
  as (
    select
    customer_id,
    first_name,
    last_name,
    email,
    cast(created_at as timestamp) as created_at,
    case
        when email is not null then true
        else false
    end as has_email
from "pipelineguard"."public"."customers"
  );