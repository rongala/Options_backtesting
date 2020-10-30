select * from public.sim_stock_history limit 20;

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
	 
 truncate table public.sim_order_history;
 truncate table public.sim_ledger_history;
 truncate table public.sim_positions;

insert into public.sim_ledger_history
(account_id, cashbalance, order_id, order_amount, quote_timestamp,rec_created_by)
values
('rongar-test', 100000, null, null, current_timestamp, 'Manual Account Seed' )
returning ledger_id;
 
 
 select * from public.ibkr_premium_trade_history
 order by trade_id desc;
 
 select * from public.sim_order_history
 where account_id = 'rongar1H3';
 
 select * from public.sim_ledger_history
 where account_id = 'rongar1H3';

 select * 
 from public.sim_positions
 where account_id = 'rongar1H3';
 
select * from public.sim_option_history
where contractid=1998010920010500;
and quote_datetime = '1998-01-02 09:00:00';

select * from public.sim_option_history
where contractid=1998010920010500
and quote_datetime = '1998-01-02 09:00:00';

insert into public.sim_option_history
select quote_datetime,
'1998010920011100' as contractid,
111.00 as strike,
option_type,
option_month,
conid,
option_expiry_date,
bid_price,
ask_price,
last_price
from public.sim_option_history
where contractid=1998010920010500; 


insert into public.sim_contracts
select 
'1998010920011100' as contractid,
111.00 as strike,
'C' as option_type,
option_expiry_date,
conid,
option_month
from public.sim_contracts
where contractid=1998010920010500; 


select * from public.sim_stock_history
where conid = 756733
--conid = 13455763
and date(quote_datetime) = '2013-10-02'
order by quote_datetime 
;

insert into public.sim_ledger_history
 (account_id, cashbalance, order_id, order_amount, quote_timestamp,rec_created_by)
 values
 ('rongar1M', 1000000, null, null, current_timestamp, 'Manual Account Seed' )
 returning ledger_id;
 
 
-- delete from public.sim_order_history
-- where account_id = 'rongar1M'
-- ;
-- 
-- delete from public.sim_ledger_history
-- where account_id = 'rongar1M';
--
-- delete from public.sim_positions
-- where account_id = 'rongar1M';
--
-- update  public.ibkr_premium_trade_history
-- set active_trade_flag = 0
-- where account_id = 'rongar1M';
--
-- update  public.ibkr_insurance_trade_history
-- set active_trade_flag = 0
-- where account_id = 'rongar1M';
 
 
 select contractid as option_contractid, 'SPY' as option_symbol, strike as strike_price, cast(option_expiry_date as varchar) as option_contract_exp_date 
 from public.sim_contracts 
 where option_expiry_date>=cast(to_char(cast('1998-01-07 15:00:00' as timestamp),'YYYYMMDD') as integer) and strike = '111.0' and option_type = 'C' order by option_expiry_date, strike;

 
 
 
 select
	account_id as acctId,
	a.conid::varchar(25),
	ticker,
	sectype as assetClass,
	quantity as position,
	a.option_type as putOrCall,
	side as right,
	a.option_expiry_date::varchar(25) as expiry,
	option_strike as strike,
	expired,
	rec_created_datetime::varchar(25),
	rec_updated_datetime::varchar(25),
	rec_created_by,
	z.last_price::float as mktPrice,
	avg_price::float as avgPrice
from
	public.sim_positions a
left join public.sim_option_history z on
	z.contractid = a.conid
	and z.quote_datetime = '{quotetime}'
where
	account_id = '{account_id}';


	
select contractid as option_contractid, 'SPY' as option_symbol, strike as strike_price, cast(option_expiry_date as varchar) as option_contract_exp_date 
from public.sim_contracts 
where option_expiry_date='20131016' 
--and strike <= '169' 
and option_type = 'P' 
order by option_expiry_date, strike;


select *  
from public.sim_option_history
where option_expiry_date='20131016' 
--and strike <= '169' 
and option_type = 'P' 
order by option_expiry_date, strike;
