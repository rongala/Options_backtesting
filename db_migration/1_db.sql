create database simapi;

--use schema public;
SET search_path TO public;


--#######################################
-- create  sim_strikes table ###
--#######################################
drop table if exists public.sim_strikes;

create table public.sim_strikes
(
    conid int4,
    option_month text,
    option_type varchar,
    strike numeric(10,2)
);

-- Create sample data
insert into sim_strikes
values(756733, 'DEC15', 'P', 198.00);
insert into sim_strikes
values(756733, 'DEC15', 'C', 252.50);
insert into sim_strikes
values(756733, 'DEC15', 'P', 140.50);
insert into sim_strikes
values(756733, 'DEC15', 'C', 150.00);
insert into sim_strikes
values(756733, 'FEB15', 'C', 219.00);
insert into sim_strikes
values(756733, 'FEB15', 'P', 40.00);
insert into sim_strikes
values(756733, 'FEB15', 'P', 150.00);
insert into sim_strikes
values(756733, 'FEB15', 'C', 141.50);

select *
from sim_strikes
where conid = 756733
    and option_month = 'DEC15';

--#######################################
-- create  sim_contracts table ###
--#######################################
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
values
    (2015120420019250, 112.00 , 'P', '20151204', 756733, 'DEC15');

select *
from sim_contracts
where conid = 756733
    and option_month = 'DEC15'
    and strike = 189
    and option_type='C';



--#######################################
-- create  sim_stock_history table ###
--#######################################

drop table if exists public.sim_stock_history;

CREATE TABLE if not exists public.sim_stock_history (
	quote_datetime timestamp NULL,
	conid int4 NULL,
	last_price numeric NULL
);


insert into public.sim_stock_history values (to_timestamp('2012-09-07 12:15:00','yyyy-mm-dd hh24:mi:ss'),756733,144.16);
insert into public.sim_stock_history values (to_timestamp('2011-10-27 14:30:00','yyyy-mm-dd hh24:mi:ss'),756733,128.70);
insert into public.sim_stock_history values (to_timestamp('2014-08-04 12:15:00','yyyy-mm-dd hh24:mi:ss'),756733,192.64);
insert into public.sim_stock_history values (to_timestamp('2011-09-26 13:15:00','yyyy-mm-dd hh24:mi:ss'),756733,113.81);
insert into public.sim_stock_history values (to_timestamp('2012-10-18 10:15:00','yyyy-mm-dd hh24:mi:ss'),756733,145.95);
insert into public.sim_stock_history values (to_timestamp('2013-10-07 14:30:00','yyyy-mm-dd hh24:mi:ss'),756733,168.22);
insert into public.sim_stock_history values (to_timestamp('2011-12-27 11:15:00','yyyy-mm-dd hh24:mi:ss'),756733,126.54);
insert into public.sim_stock_history values (to_timestamp('2013-06-21 11:45:00','yyyy-mm-dd hh24:mi:ss'),756733,157.71);
insert into public.sim_stock_history values (to_timestamp('2015-06-09 13:15:00','yyyy-mm-dd hh24:mi:ss'),756733,208.90);
insert into public.sim_stock_history values (to_timestamp('2014-01-06 10:00:00','yyyy-mm-dd hh24:mi:ss'),756733,182.98);



--#######################################
-- create  sim_option_history table ###
--#######################################

drop table if exists public.sim_option_history;

CREATE TABLE public.sim_option_history (
	quote_datetime timestamp NULL,
	contractid int8 NULL,
	strike numeric(10,2) NULL,
	option_type varchar(5) NULL,
	option_month text NULL,
	conid int4 NULL,
	option_expiry_date int4 NULL,
	bid_price numeric(10,4) NULL,
	ask_price numeric(10,4) NULL,
	last_price numeric NULL
)


INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 11:45:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.5900, 52.0000, 47.5900);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 12:00:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.7300, 52.0000, 47.7300);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 12:15:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.5900, 52.0000, 47.5900);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 12:30:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.2500, 52.0000, 47.2500);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 12:45:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.5300, 52.0000, 47.5300);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 13:00:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.6800, 52.0000, 47.6800);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 13:15:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.6800, 52.0000, 47.6800);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 13:30:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.8500, 52.0000, 47.8500);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 13:45:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.8500, 52.0000, 47.8500);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) VALUES(to_timestamp('2013-06-28 14:00:00','yyyy-mm-dd hh24:mi:ss'), 2013062810011100, 111.00, 'C', 'JUN13', 756733, 20130628, 47.8500, 52.5800, 47.8500);

INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 09:45:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.2300, 1.2900, 1.2900);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 10:00:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.1800, 1.2900, 1.2900);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 10:15:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.1800, 1.2400, 1.2400);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 10:30:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.1900, 1.2400, 1.2400);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 10:45:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.1500, 1.2200, 1.2200);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 11:00:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.1000, 1.1500, 1.1500);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 11:15:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.0900, 1.1400, 1.1400);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 11:30:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.1400, 1.1800, 1.1800);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 11:45:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.1100, 1.1600, 1.1600);
INSERT INTO public.sim_option_history (quote_datetime, contractid, strike, option_type, option_month, conid, option_expiry_date, bid_price, ask_price, last_price) values ('2015-10-22 12:00:00', '2015120420019250', 173, 'P', 'DEC15', 756733, 20151204, 1.0700, 1.1200, 1.1200);


--#######################################
-- create sim_order_history table ###
--#######################################

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

--insert INTO public.sim_order_history
--(acctid, conid, coid, parentid, ordertype, price, side, ticker, quantity, quote_timestamp)
--VALUES('DU2554692', 435098432, 'DU25546921234', 'DU25546921234', 'LIMIT', 1.41, 'SELL', 'SPY', 29, '2019-01-04 14:23:34')
--returning order_id
--;


--#######################################
-- create  sim_ledger_history table ###
--#######################################

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

-- Seed the ledger table.
insert into public.sim_ledger_history
 (account_id, cashbalance, order_id, order_amount, quote_timestamp,rec_created_by)
 values
 ('DU2387565', 250000, null, null, '2019-01-04 14:23:34', 'Manual Account Seed' )
 returning ledger_id;


--#######################################
-- create  sim_positions table        ###
--#######################################

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