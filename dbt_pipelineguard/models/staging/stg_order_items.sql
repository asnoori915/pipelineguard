select
    order_item_id,
    order_id,
    product_id,
    quantity,
    cast(unit_price as numeric(10, 2)) as unit_price,
    quantity * cast(unit_price as numeric(10, 2)) as line_total
from {{ source('raw', 'order_items') }}
