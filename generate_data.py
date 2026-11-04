import numpy as np
import pandas as pd
from pathlib import Path

OUT=Path(__file__).parent/'data'; OUT.mkdir(exist_ok=True)
rng=np.random.default_rng(20261031)
END=pd.Timestamp('2026-10-31')
projects={
 'A':dict(genre='MMORPG',start='2021-10-27',mg=500_000_000,rs=.20,staff=35_000_000,server=22_000_000,ua=.05,base=380_000_000,peak=1_800_000_000,dau=18000,mau=65000,mpu=5200),
 'B':dict(genre='SLG',start='2024-07-24',mg=300_000_000,rs=.18,staff=30_000_000,server=18_000_000,ua=.08,base=290_000_000,peak=900_000_000,dau=12000,mau=38000,mpu=3800),
 'C':dict(genre='Puzzle',start='2026-01-28',mg=50_000_000,rs=.25,staff=12_000_000,server=12_000_000,ua=.25,base=65_000_000,peak=80_000_000,dau=55000,mau=180000,mpu=2700),
}
monthly=[]; daily=[]; events=[]; cs=[]; reviews=[]; cohorts=[]
for code,p in projects.items():
 start=pd.Timestamp(p['start']); months=pd.period_range(start,END,freq='M')
 for ix,period in enumerate(months):
  month_start=period.start_time; month_end=min(period.end_time.normalize(),END)
  valid=pd.date_range(max(start,month_start),month_end); n=len(valid)
  if code!='C':
   shape=p['base']+(p['peak']-p['base'])*np.exp(-ix/(8 if code=='A' else 5))
   factor=1+rng.normal(0,.065)
   if ix>3 and ix%12 in (0,1): factor+=.19
   if ix>4 and ix%7==0: factor+=.13
  else:
   shape=p['base']*(.75+.48*rng.random())
   factor=1+(.25 if ix in (3,7) else 0)
  gross=max(1_000_000,round(shape*factor))
  # C gross includes both IAP and net IAA; ads are intentionally light (~2.9 impressions/DAU/day in Oct)
  if code=='C':
   ads_share=.18+.08*rng.random()
   iaa=round(gross*ads_share); iap=gross-iaa
  else: iaa=0; iap=gross
  refund=round(iap*.02); fee=round((iap-refund)*.20)
  net=iap-refund-fee+iaa
  avg_dau=max(100,round(p['dau']*(gross/p['base'])**.43*rng.uniform(.94,1.06)))
  mau=max(avg_dau,round(p['mau']*(avg_dau/p['dau'])**.75))
  mpu=min(mau,round(p['mpu']*(iap/(p['base'] if code!='C' else 50_000_000))**.52))
  month_event=('주년 이벤트' if period.month==start.month and ix>=12 else '시즌/콘텐츠 업데이트' if ix>2 and ix%7==0 else '명절 프로모션' if period.month in (1,2,9,10) and ix>2 else '')
  if month_event: events.append(dict(project=code,date=str(valid[min(len(valid)-1,12)].date()),category='이벤트/업데이트',title=month_event))
  weights=rng.lognormal(0,.17,n); weights=weights/weights.sum()
  d_revenue=np.floor(iap*weights).astype('int64'); d_revenue[-1]+=iap-int(d_revenue.sum())
  d_ads=np.floor(iaa*weights).astype('int64'); d_ads[-1]+=iaa-int(d_ads.sum())
  d_ref=np.floor(refund*weights).astype('int64'); d_ref[-1]+=refund-int(d_ref.sum())
  d_fee=np.floor(fee*weights).astype('int64'); d_fee[-1]+=fee-int(d_fee.sum())
  dau_vals=np.maximum(1,np.round(avg_dau*rng.uniform(.89,1.11,n))).astype(int)
  for j,day in enumerate(valid):
   d=day.date(); dau=int(dau_vals[j]); inquiries=int(rng.poisson(max(1,dau*.004)))
   if j==min(12,n-1) and month_event: inquiries=int(inquiries*1.7)
   daily.append(dict(date=str(d),project=code,genre=p['genre'],iap=int(d_revenue[j]),iaa=int(d_ads[j]),refund=int(d_ref[j]),market_fee=int(d_fee[j]),dau=dau,cs_count=inquiries))
   categories=['결제/환불','접속/서버','버그','계정','이벤트','기타']
   counts=rng.multinomial(inquiries,[.19,.20,.23,.14,.14,.10])
   for category,count in zip(categories,counts):
    cs.append(dict(date=str(d),project=code,category=category,count=int(count)))
   if j%3==0:
    for k in range(max(1,int(inquiries*.18))):
     rating=int(rng.choice([1,2,3,4,5],p=[.13,.10,.15,.27,.35]))
     reviews.append(dict(date=str(d),project=code,store='Google Play' if k%2==0 else 'App Store',rating=rating,topic=categories[int(rng.integers(0,6))],review_id=f'{code}-{period}-{j}-{k}'))
  monthly.append(dict(month=str(period),project=code,genre=p['genre'],iap=iap,iaa=iaa,refund=refund,market_fee=fee,net_revenue=net,mau=mau,mpu=mpu,staff_cost=p['staff'],server_cost=p['server'],event=month_event))
  # Cohort records are illustrative aggregate estimates; no user-level identity is asserted.
  new_users=max(100,round(mau*(.07 if code=='A' else .09 if code=='B' else .25)))
  paid_share=.35 if code=='A' else .45 if code=='B' else .70
  for channel,share in [('Organic',1-paid_share),('Google Ads',paid_share*.60),('Meta Ads',paid_share*.40)]:
   cohort_size=round(new_users*share)
   for day_n,rate in [(1,.43 if code=='A' else .37 if code=='B' else .49),(3,.33 if code=='A' else .27 if code=='B' else .35),(7,.25 if code=='A' else .19 if code=='B' else .24),(14,.18 if code=='A' else .13 if code=='B' else .15),(30,.12 if code=='A' else .08 if code=='B' else .09)]:
    if (month_end-month_start).days<day_n and period==months[-1]: continue
    cohorts.append(dict(project=code,cohort_month=str(period),channel=channel,day=day_n,cohort_users=cohort_size,retained_users=round(cohort_size*rate*(1.10 if channel=='Organic' else .95))))

m=pd.DataFrame(monthly).sort_values(['project','month']); m['ua_budget']=0
for code,p in projects.items():
 mask=m.project==code; prev=m.loc[mask,'iap'].add(m.loc[mask,'iaa']).shift(1)
 m.loc[mask,'ua_budget']=(prev.fillna(0)*p['ua']).round().astype('int64').values
m['rs_accrued']=(m.net_revenue*m.project.map({k:v['rs'] for k,v in projects.items()})).round().astype('int64')
m['mg_offset']=0;m['rs_paid']=0;m['mg_remaining']=0
for code,p in projects.items():
 remaining=p['mg']
 for idx in m.index[m.project==code]:
  amount=int(m.at[idx,'rs_accrued']); offset=min(remaining,amount);remaining-=offset
  m.at[idx,'mg_offset']=offset;m.at[idx,'rs_paid']=amount-offset;m.at[idx,'mg_remaining']=remaining
m['lf_cost']=m.apply(lambda r:100_000_000 if r.project=='A' and r.month=='2021-10' else 0,axis=1)
m['business_profit']=m.net_revenue-m.rs_accrued-m.staff_cost-m.server_cost-m.ua_budget-m.lf_cost
for name,df in [('daily',pd.DataFrame(daily)),('monthly',m),('events',pd.DataFrame(events)),('cs',pd.DataFrame(cs)),('reviews',pd.DataFrame(reviews)),('cohorts',pd.DataFrame(cohorts))]:
 df.to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig')
print('Generated',len(daily),'daily rows; latest',max(d['date'] for d in daily))

# 별도 난수 생성기를 사용하므로 기존 v4 데이터는 그대로 재현됩니다.
cohort_rng=np.random.default_rng(20261104)
daily_cohorts=[]
for row in daily:
 day=pd.Timestamp(row['date']);code=row['project'];dau=row['dau']
 newcomers=max(15,int(dau*(.055 if code=='A' else .065 if code=='B' else .085)*cohort_rng.uniform(.85,1.15)))
 weights={'Organic':.62 if code=='A' else .55 if code=='B' else .30,'Google Ads':.23 if code=='A' else .27 if code=='B' else .42,'Meta Ads':.15 if code=='A' else .18 if code=='B' else .28}
 for channel,share in weights.items():
  cohort_n=max(1,round(newcomers*share))
  for day_n,rate in {1:.45,3:.34,7:.25,14:.17,30:.10}.items():
   if day+pd.Timedelta(days=day_n)>END:continue
   event_drop=.73 if (day.month in (9,10) and day.day in (13,14) and code in ('A','B')) else 1.0
   quality=1.08 if channel=='Organic' else .95 if channel=='Google Ads' else .90
   prob=min(.95,max(.01,rate*quality*event_drop*cohort_rng.uniform(.91,1.09)))
   daily_cohorts.append(dict(project=code,cohort_date=str(day.date()),channel=channel,day=day_n,cohort_users=cohort_n,retained_users=int(cohort_rng.binomial(cohort_n,prob))))
pd.DataFrame(daily_cohorts).to_csv(OUT/'daily_cohorts.csv',index=False,encoding='utf-8-sig')
