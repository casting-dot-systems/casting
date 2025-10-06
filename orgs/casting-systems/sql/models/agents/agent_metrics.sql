{{ config(unique_key="agent_id", on_schema_change="sync_all_columns") }}

with agent_events as (
    select
        agent_id,
        count(*) as event_count,
        max(created_at) as last_activity_at
    from {{ source('agent_ops', 'agent_events') }}
    group by agent_id
)

select
    agents.id as agent_id,
    agents.org_id,
    agents.name,
    coalesce(events.event_count, 0) as total_events,
    events.last_activity_at
from {{ ref('agent_activity') }} as agents
left join agent_events as events on events.agent_id = agents.id
