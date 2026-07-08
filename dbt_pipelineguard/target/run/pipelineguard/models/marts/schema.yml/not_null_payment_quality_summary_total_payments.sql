
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_payments
from "pipelineguard"."analytics_analytics"."payment_quality_summary"
where total_payments is null



  
  
      
    ) dbt_internal_test