
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select pending_payment_count
from "pipelineguard"."analytics_analytics"."payment_quality_summary"
where pending_payment_count is null



  
  
      
    ) dbt_internal_test