{{ config(materialized="view") }}

select
    a.id,
    a.org_id,
    a.name,
    a.status,
    a.created_at
from {{ source('agent_ops', 'agents') }} as a
