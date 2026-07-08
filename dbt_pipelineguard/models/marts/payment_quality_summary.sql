select
    count(*) as total_payments,
    sum(
        case
            when is_negative_payment then 1
            else 0
        end
    ) as negative_payment_count,
    sum(amount) as total_payment_amount,
    sum(
        case
            when payment_status = 'failed' then 1
            else 0
        end
    ) as failed_payment_count,
    sum(
        case
            when payment_status = 'pending' then 1
            else 0
        end
    ) as pending_payment_count
from {{ ref('stg_payments') }}
