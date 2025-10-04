create table catalog.members (
    member_id      uuid primary key default gen_random_uuid(),
    name           text not null,
    status         text not null default 'active'
    ,created_at    timestamptz not null default now()
    ,updated_at    timestamptz not null default now()
);