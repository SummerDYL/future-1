insert into margin_daily
select capital_account_new,vari_code,tradedate,sum(margin),sum(market_margin)
from chicang group by capital_account_new,vari_code,tradedate;

insert into margin_daily
select capital_account_new,"all",tradedate,sum(margin),sum(market_margin)
from chicang group by capital_account_new,tradedate;