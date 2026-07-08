
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select product_id
from "pipelineguard"."analytics_analytics"."stg_order_items"
where product_id is null



  
  
      
    ) dbt_internal_test