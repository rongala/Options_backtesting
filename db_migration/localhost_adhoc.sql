create database simapi;

--use schema public;
SET search_path TO public;

drop table if exists public.sim_contracts;

CREATE TABLE public.sim_contracts
(
    contractid int8 NULL,
    strike numeric(10,2) NULL,
    option_type varchar(5) NULL,
    option_expiry_date int4 NULL,
    conid int4 NULL,
    option_month text NULL
);

-- Create sample data
insert into sim_contracts
values
    (2015120410017500, 175.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018000, 180.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018100, 181.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018200, 182.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018300, 183.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018400, 184.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018500, 185.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018600, 186.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018700, 187.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018800, 188.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018900, 189.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018900, 189.00, 'C', '20151211', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018900, 189.00, 'C', '20151218', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018900, 189.00, 'C', '20151219', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018900, 189.00, 'C', '20151224', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018900, 189.00, 'C', '20151231', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410018950, 189.50, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410019000, 190.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410019050, 190.50, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410019100, 191.00, 'C', '20151204', 756733, 'DEC15');
insert into sim_contracts
values
    (2015120410019150, 191.50, 'C', '20151204', 756733, 'DEC15');
   
insert into sim_contracts
values(2015120420019250, 112.00 , 'P', '20151204', 756733, 'DEC15')



select option_expiry_date
from public.sim_contracts 
where contractid = 2011010710011300
;


drop table if exists public.sim_order_history;
create table public.sim_order_history
(
	order_id serial primary key,
	account_id text,
	conid int8,
	option_type text null,
	option_expiry_date int4 NULL,
	option_strike numeric(10,2),
	coid text,
	parentid text,
	ordertype text,
	price numeric(10,2),
	side text,
	ticker text,
	sectype text,
	quantity numeric(10,2),
	amount numeric(20,2),
	quote_timestamp timestamp,
	rec_created_datetime timestamp
		not null default current_timestamp,
	rec_created_by text not null
);

drop table if exists public.sim_ledger_history;
create table public.sim_ledger_history
(ledger_id serial primary key,
 account_id text,
 cashbalance numeric(20,2),
 order_id bigint,
 order_amount numeric(20,2),
 quote_timestamp timestamp,
 rec_created_datetime timestamp 
	not null default current_timestamp,	
 rec_created_by text not null 
 );
 
 insert into public.sim_ledger_history
 (account_id, cashbalance, order_id, order_amount, quote_timestamp,rec_created_by)
 values
 ('DU2387565', 250000, null, null, '2019-01-04 14:23:34', 'Manual Account Seed' )
 returning ledger_id;
 
 commit;

select a.cashbalance 
  from public.sim_ledger_history a
where a.acctid = 'DU2387565'
  and a.sim_create_datetime = (select max(sim_create_datetime) 
                                from public.sim_ledger_history b
                                where b.acctid = a.acctid);
                               
--acctId, conid, ticker, assetClass, position, putOrCall, mktPrice, mktValue, avgCost, avgPrice, right, expiry

select * from public.sim_contracts where contractid = 2015120410019100;

drop table public.sim_positions;
create table public.sim_positions
	(account_id text null,
	 conid int8,
	 sectype text null,
	 quantity int4,
	 avg_price float null,
	 mkt_price float null,
	 side text null,
	 ordertype text null,
	 option_type text null,
	 option_expiry_date int4 null,
	 ticker text null,
	 option_strike float null,
	 expired boolean default false,
	 rec_created_datetime timestamp not null default current_timestamp,
	 rec_updated_datetime timestamp not null default current_timestamp,
     rec_created_by text not null,
     PRIMARY KEY (account_id, conid)
	 );
	 
select current_timestamp;


select contractid, last_price from public.sim_option_history
where contractid=1998010520011000
and quote_datetime  = (select max(quote_datetime) 
						 from public.sim_option_history
						where contractid=1998010520011000
						  and quote_datetime <= '1998-01-05 09:00:00')
;

 select * from public.sim_order_history
 where account_id = 'DU2387565'
 ;
 
 select * from public.sim_ledger_history
 where account_id = 'DU2387565';

 select * 
 from public.sim_positions
 where account_id = 'DU2387565';
 
 select b.last_price, a.*
 from public.sim_positions a
 left join (select contractid, last_price 
 			  from public.sim_option_history z
			 where quote_datetime = (select max(quote_datetime) 
								 	   from public.sim_option_history
									  where contractid = z.contractid
								  	    and quote_datetime <= '1998-01-05 09:00:00')
		) b
 on a.conid = b.contractid
 where account_id = 'DU2387565';
 

select
	account_id as acctId,
	conid::varchar(25),
	ticker,
	sectype as assetClass,
	quantity as position,
	option_type as putOrCall,
	side as right,
	option_expiry_date::varchar(25) as expiry,
	option_strike as strike,
	expired,
	rec_created_datetime::varchar(25),
	rec_updated_datetime::varchar(25),
	rec_created_by,
	mkt_price as mktPrice,
	avg_price as avgPrice
from
	public.sim_positions a
left join(
		select
			contractid,
			last_price as mkt_price
		from
			public.sim_option_history z
		where
			quote_datetime =(
				select
					max( quote_datetime )
				from
					public.sim_option_history
				where
					contractid = z.contractid
					and quote_datetime <= '1998-01-05 09:00:00'
			)
	) b on
	a.conid = b.contractid
where
	account_id = '{account_id}';
	

 
-- delete from public.sim_order_history
-- where account_id = 'DU2387565'
-- --and order_id in (14)
-- ;
-- 
-- delete from public.sim_ledger_history
-- where account_id = 'DU2387565'
-- --and ledger_id in (10)
-- ;
-- 
-- delete from public.sim_positions
-- where account_id = 'DU2387565'
-- ;
 
 
 truncate table public.sim_order_history;
 truncate table public.sim_ledger_history;
 truncate table public.sim_positions;

  insert into public.sim_ledger_history
 (account_id, cashbalance, order_id, order_amount, quote_timestamp,rec_created_by)
 values
 ('DU2387565', 250000, null, null, '2019-01-04 14:23:34', 'Manual Account Seed' )
 returning ledger_id;
 
 
 
  select
        account_id as acctId,
        conid::varchar(25),
        ticker,
        sectype as assetClass,
        quantity as position,
        option_type as putOrCall,
        side as right,
        option_expiry_date::varchar(25) as expiry,
        option_strike as strike,
        expired,
        rec_created_datetime::varchar(25),
        rec_updated_datetime::varchar(25),
        rec_created_by,
        b.mkt_price::float as mktPrice,
        avg_price::float as avgPrice
    from
        public.sim_positions a
    left join(
            select
                contractid,
                last_price as mkt_price
            from
                public.sim_option_history z
            where
                quote_datetime =(
                    select
                        max( quote_datetime )
                    from
                        public.sim_option_history
                    where
                        contractid = z.contractid
                        and quote_datetime <= '1998-01-05 09:00:00'
                )
        ) b on
        a.conid = b.contractid
    where
        account_id = 'DU2387565'; 
 