drop extension if exists "pg_net";


  create table "public"."stripe_customers" (
    "user_id" uuid not null,
    "updated_at" timestamp with time zone,
    "stripe_customer_id" text
      );


alter table "public"."stripe_customers" enable row level security;

CREATE UNIQUE INDEX stripe_customers_pkey ON public.stripe_customers USING btree (user_id);

CREATE UNIQUE INDEX stripe_customers_stripe_customer_id_key ON public.stripe_customers USING btree (stripe_customer_id);

alter table "public"."stripe_customers" add constraint "stripe_customers_pkey" PRIMARY KEY using index "stripe_customers_pkey";

alter table "public"."stripe_customers" add constraint "stripe_customers_stripe_customer_id_key" UNIQUE using index "stripe_customers_stripe_customer_id_key";

alter table "public"."stripe_customers" add constraint "stripe_customers_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."stripe_customers" validate constraint "stripe_customers_user_id_fkey";

grant delete on table "public"."stripe_customers" to "anon";

grant insert on table "public"."stripe_customers" to "anon";

grant references on table "public"."stripe_customers" to "anon";

grant select on table "public"."stripe_customers" to "anon";

grant trigger on table "public"."stripe_customers" to "anon";

grant truncate on table "public"."stripe_customers" to "anon";

grant update on table "public"."stripe_customers" to "anon";

grant delete on table "public"."stripe_customers" to "authenticated";

grant insert on table "public"."stripe_customers" to "authenticated";

grant references on table "public"."stripe_customers" to "authenticated";

grant select on table "public"."stripe_customers" to "authenticated";

grant trigger on table "public"."stripe_customers" to "authenticated";

grant truncate on table "public"."stripe_customers" to "authenticated";

grant update on table "public"."stripe_customers" to "authenticated";

grant delete on table "public"."stripe_customers" to "service_role";

grant insert on table "public"."stripe_customers" to "service_role";

grant references on table "public"."stripe_customers" to "service_role";

grant select on table "public"."stripe_customers" to "service_role";

grant trigger on table "public"."stripe_customers" to "service_role";

grant truncate on table "public"."stripe_customers" to "service_role";

grant update on table "public"."stripe_customers" to "service_role";


