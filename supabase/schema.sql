create table if not exists public.readings (
 id bigint generated always as identity primary key,
 device_id text not null check (device_id ~ '^[a-zA-Z0-9_-]{1,50}$'),
 message_id text not null check (length(message_id) between 3 and 80),
 measurement text not null check (measurement='temperature'),
 value numeric(6,2) not null check (value between -55 and 125),
 raw_value numeric(6,2) not null check (raw_value between -55 and 125),
 unit text not null check (unit='C'),
 alert text not null check (alert in ('normal','warning','critical')),
 sample_count smallint not null check (sample_count between 1 and 3),
 received_at timestamptz not null default now(),
 constraint readings_device_message_unique unique(device_id,message_id)
);
create index if not exists readings_device_received_idx on public.readings(device_id,received_at desc,id desc);
alter table public.readings enable row level security;
revoke all on public.readings from anon,authenticated;
grant select on public.readings to anon;
drop policy if exists demo_readings_public_read on public.readings;
create policy demo_readings_public_read on public.readings for select to anon using(true);
grant usage on schema public to service_role;
grant select,insert on public.readings to service_role;
grant usage,select on sequence public.readings_id_seq to service_role;
