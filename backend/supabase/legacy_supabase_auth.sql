-- LEGACY Supabase Auth schema: preserved for reference; NOT the new Flask authentication schema.
-- Use 0001_identity.sql for the versioned Flask-owned identity backend.
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null default '',
  role text not null default 'patient' check (role in ('patient','doctor','admin','super_admin')),
  created_at timestamptz not null default now()
);

create function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles(id, full_name, role)
  values(new.id, left(coalesce(new.raw_user_meta_data->>'full_name',''),120),
    case when new.raw_user_meta_data->>'role' = 'doctor' then 'doctor' else 'patient' end);
  return new;
end;
$$;
create trigger on_auth_user_created after insert on auth.users
for each row execute function public.handle_new_user();

create function public.current_role() returns text
language sql stable security definer set search_path = '' as $$
  select role from public.profiles where id = (select auth.uid());
$$;

alter table public.profiles enable row level security;
revoke all on public.profiles from anon, authenticated;
grant select on public.profiles to authenticated;
create policy profiles_read on public.profiles for select to authenticated
using (id = (select auth.uid()) or (select public.current_role()) in ('admin','super_admin'));

-- Only this function can change roles through the API. No public admin signup.
create function public.set_user_role(target_id uuid, new_role text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  -- Serialize changes so concurrent requests cannot remove every super admin.
  perform pg_advisory_xact_lock(734922);
  if public.current_role() is distinct from 'super_admin' then
    raise insufficient_privilege using message = 'Super admin required';
  end if;
  if new_role not in ('patient','doctor','admin','super_admin') then
    raise exception 'Invalid role';
  end if;
  if not exists(select 1 from public.profiles where id = target_id) then
    raise exception 'User not found';
  end if;
  if new_role <> 'super_admin'
     and exists(select 1 from public.profiles where id = target_id and role = 'super_admin')
     and (select count(*) from public.profiles where role = 'super_admin') <= 1 then
    raise exception 'Cannot demote the last super admin';
  end if;
  update public.profiles set role = new_role where id = target_id;
end;
$$;
revoke all on function public.handle_new_user() from public, anon, authenticated;
revoke all on function public.current_role() from public, anon;
grant execute on function public.current_role() to authenticated;
revoke all on function public.set_user_role(uuid,text) from public, anon;
grant execute on function public.set_user_role(uuid,text) to authenticated;
