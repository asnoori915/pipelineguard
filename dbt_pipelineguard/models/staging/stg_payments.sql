select
    payment_id,
    order_id,
    cast(amount as numeric(10, 2)) as amount,
    payment_status,
    cast(paid_at as timestamp) as paid_at,
    case
        when payment_status = 'paid' then true
        else false
    end as is_paid,
    case
        when amount < 0 then true
        else false
    end as is_negative_payment
from {{ source('raw', 'payments') }}
