from pathlib import Path
import calendar
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Game Publishing BI | DEMO',page_icon='📊',layout='wide')
BASE=Path(__file__).parent/'data'; CUTOFF=pd.Timestamp('2026-10-31')
LAUNCH={'A':pd.Timestamp('2021-10-27'),'B':pd.Timestamp('2024-07-24'),'C':pd.Timestamp('2026-01-28')}
PROJECTS=list(LAUNCH); LABELS={'A':'A · MMORPG','B':'B · SLG','C':'C · Puzzle'}
RS={'A':.20,'B':.18,'C':.25}; MG={'A':500_000_000,'B':300_000_000,'C':50_000_000}; LF={'A':100_000_000,'B':0,'C':0}
NAMES={'project':'프로젝트','month':'정산월','date':'일자','genre':'장르','iap':'IAP 매출','iaa':'IAA 매출','revenue':'총매출','refund':'환불액','market_fee':'마켓 수수료','net_revenue':'순매출','rs_accrued':'개발사 RS 발생액','mg_offset':'MG 상계액','rs_paid':'개발사 RS 지급액','mg_remaining':'MG 미회수 잔액','staff_cost':'운영비(인건비)','server_cost':'서버비','ua_budget':'UA 집행비','business_profit':'사업이익','dau':'DAU','mau':'MAU','mpu':'월 결제자(MPU)','cs_count':'CS 문의 건수','category':'문의 유형','count':'문의 건수','rating':'별점','store':'마켓','topic':'리뷰 유형','review_id':'리뷰 ID','cohort_month':'코호트월','channel':'유입 채널','day':'경과일','cohort_users':'코호트 이용자','retained_users':'잔존 이용자','title':'이벤트명','data_type':'데이터 구분','revenue_target':'목표 매출','profit_target':'목표 사업이익','lf_cost':'LF 비용','cohort_date':'유입일'}
@st.cache_data
def load(name): return pd.read_csv(BASE/f'{name}.csv',encoding='utf-8-sig')
daily,monthly,events,cs,reviews,cohorts=[load(n) for n in ('daily','monthly','events','cs','reviews','cohorts')]
daily_cohorts=load('daily_cohorts')
for df in (daily,events,cs,reviews): df['date']=pd.to_datetime(df.date)
monthly['month_date']=pd.to_datetime(monthly.month+'-01'); monthly=monthly.sort_values(['project','month_date']).reset_index(drop=True)
daily['month']=daily.date.dt.strftime('%Y-%m'); daily['revenue']=daily.iap+daily.iaa
monthly['revenue']=monthly.iap+monthly.iaa
if 'lf_cost' not in monthly.columns:
    monthly['lf_cost']=monthly.apply(lambda r: LF[r.project] if r.month==LAUNCH[r.project].strftime('%Y-%m') else 0,axis=1)
    monthly['business_profit']=monthly.business_profit-monthly.lf_cost

# 계획은 월 시작 시점에 알 수 있는 이전 3개월 실적과 사전 정의된 가상 운영 일정만 사용합니다.
# 실적을 반영해 과거 목표를 다시 계산하지 않도록 월별 계획을 별도 고정 테이블로 만듭니다.
plan=[]
for p in PROJECTS:
    g=monthly[monthly.project==p].sort_values('month_date')
    prior=[]
    for _,r in g.iterrows():
        if prior:
            baseline=float(np.mean(prior[-3:]))
        else:
            baseline={'A':1_500_000_000,'B':750_000_000,'C':65_000_000}[p]
        # 이벤트 계획에 따른 사전 목표 가중치 (실제 성과를 사용하지 않음)
        event_factor=(1.08 if p=='A' and r.month_date.month in (5,10) else
                      1.10 if p=='B' and r.month_date.month in (1,7,10) else
                      1.05 if p=='C' and r.month_date.month in (5,9) else 1.0)
        factor={'A':.98,'B':1.00,'C':1.04}[p]
        target=int(round(baseline*factor*event_factor/1_000_000)*1_000_000)
        if not prior:
            active_days=(r.month_date+pd.offsets.MonthEnd(0)-max(r.month_date,LAUNCH[p])).days+1
            target=int(round(target*active_days/r.month_date.days_in_month/1_000_000)*1_000_000)
        plan.append({'project':p,'month':r.month,'revenue_target':target,'profit_target':int(round(target*.15/1_000_000)*1_000_000)})
        prior.append(int(r.revenue))
plan=pd.DataFrame(plan)
monthly=monthly.merge(plan,on=['project','month'],how='left')

st.markdown('''<style>
[data-testid="stMetric"]{background:var(--secondary-background-color);border:1px solid var(--border-color,rgba(128,128,128,.23));padding:13px;border-radius:12px}
[data-testid="stSidebar"]{border-right:1px solid var(--border-color,rgba(128,128,128,.22))}
.demo-banner{padding:13px 17px;border:2px solid #bb923b;border-radius:12px;background:rgba(187,146,59,.12);color:var(--text-color)}
.demo-title{font-size:17px;font-weight:800;line-height:1.5}.demo-sub{font-size:12px;line-height:1.5;margin-top:5px}
</style>''',unsafe_allow_html=True)
h1,h2=st.columns([3,2],vertical_alignment='center')
h1.title('Game Publishing | Business Intelligence')
h2.markdown('<div class="demo-banner"><div class="demo-title">DEMO DASHBOARD · 가상 데이터</div><div class="demo-sub">실제 기업 및 게임의 운영 실적과 무관한 시뮬레이션 환경입니다.</div></div>',unsafe_allow_html=True)
st.caption('가상 데이터 기준일 2026-10-31 · 실시간 연동 및 실제 API 수집 없음')
with st.sidebar:
    st.header('조회 설정')
    page=st.radio('메뉴',['프로젝트 소개 · AI 활용','통합 대시보드','사업 성과','이용자·리텐션','운영·CS·리뷰','운영 이력 · 영향 분석','데이터 추출·외부 링크'])
    project=st.selectbox('프로젝트',['전체']+PROJECTS,format_func=lambda p:'전체 프로젝트' if p=='전체' else LABELS[p])
    period=st.selectbox('조회 기간',['직접 선택 (달력)','2026년 10월','최근 90일','최근 1년','전체 기간'])
    if period=='직접 선택 (달력)':
        dates=st.date_input('시작일 ~ 종료일',value=(pd.Timestamp('2026-10-01').date(),CUTOFF.date()),min_value=min(LAUNCH.values()).date(),max_value=CUTOFF.date(),format='YYYY-MM-DD')
        if not isinstance(dates,(tuple,list)) or len(dates)!=2:
            st.info('시작일과 종료일을 모두 선택해 주세요.');st.stop()
        begin,end=map(pd.Timestamp,dates)
    else:
        end=CUTOFF
        begin={'2026년 10월':pd.Timestamp('2026-10-01'),'최근 90일':end-pd.Timedelta(days=89),'최근 1년':end-pd.Timedelta(days=364),'전체 기간':min(LAUNCH.values())}[period]
    span=(end-begin).days+1
    unit=st.selectbox('그래프 집계 단위',['자동','일별','월별'],help='자동: 30일 이하 일별, 31일 이상 월별. 수동 선택은 조회 기간을 바꿔도 유지됩니다.')
    freq=('일별' if span<=30 else '월별') if unit=='자동' else unit
    st.caption(f'적용 기간: {begin:%Y-%m-%d} ~ {end:%Y-%m-%d} ({span:,}일)')
    st.caption(f'그래프 집계: {freq}')
    st.divider();st.caption('모든 지표는 시뮬레이션용 가상 데이터입니다.')
selected=PROJECTS if project=='전체' else [project]
def pf(df): return df[df.project.isin(selected)].copy()
d=pf(daily);d=d[d.date.between(begin,end)].copy()
cc=pf(cs);cc=cc[cc.date.between(begin,end)].copy()
rr=pf(reviews);rr=rr[rr.date.between(begin,end)].copy()
ev=pf(events);ev=ev[ev.date.between(begin,end)].copy()
mm=pf(monthly);mm=mm[(mm.month_date<=end)&(mm.month_date+pd.offsets.MonthEnd(0)>=begin)].copy()

def money(v): return f'{v/100_000_000:,.2f}억 원'
def pct(a,b): return f'{a/b:.1%}' if b else '—'
def display_table(df,cols=None):
    if df.empty: st.info('표시할 데이터가 없습니다.');return
    shown=df[cols].copy() if cols else df.copy()
    shown=shown.rename(columns=NAMES)
    for c in shown.columns:
        if pd.api.types.is_datetime64_any_dtype(shown[c]): shown[c]=shown[c].dt.strftime('%Y-%m-%d')
    for c in shown.columns:
        if pd.api.types.is_integer_dtype(shown[c]): shown[c]=shown[c].map(lambda v:f'{v:,}')
        elif pd.api.types.is_float_dtype(shown[c]): shown[c]=shown[c].map(lambda v:f'{v:,.1f}')
    st.dataframe(shown,hide_index=True,use_container_width=True)

def export(label,df,filename):
    if df.empty: st.info(f'{label}: 데이터가 없습니다.');return
    x=df.rename(columns=NAMES).copy();x.insert(0,'데이터 구분','SYNTHETIC_DEMO')
    st.download_button(label,x.to_csv(index=False).encode('utf-8-sig'),filename,mime='text/csv',use_container_width=True)

def daily_cost_rows(frame):
    # 일별 실제 매출과 월별 정산 금액의 합계는 완전히 일치하도록, 고정 비용을 해당 서비스 월의 일수에 배분.
    if frame.empty: return frame.copy()
    x=frame.merge(monthly[['project','month','staff_cost','server_cost','ua_budget']],on=['project','month'],how='left')
    service_days=[]
    for _,r in x.iterrows():
        ms=pd.Timestamp(r.month+'-01');me=ms+pd.offsets.MonthEnd(0)
        service_days.append((me-max(ms,LAUNCH[r.project])).days+1)
    x['service_days']=service_days
    for c in ('staff_cost','server_cost','ua_budget'): x[c]=x[c]/x.service_days
    x['net_revenue']=x.iap+x.iaa-x.refund-x.market_fee
    x['rs_accrued']=x.net_revenue*x.project.map(RS)
    x['lf_cost']=x.apply(lambda r: LF[r.project] if r.date==LAUNCH[r.project] else 0,axis=1)
    x['business_profit']=x.net_revenue-x.rs_accrued-x.staff_cost-x.server_cost-x.ua_budget-x.lf_cost
    return x
# 금액의 일별 배분에서 생기는 소수점 오차는 월말 원본 정산 테이블을 정본으로 유지합니다.
dcost=daily_cost_rows(d)

def target_days():
    rows=[]
    for _,r in mm.iterrows():
        ms=r.month_date;me=ms+pd.offsets.MonthEnd(0)
        active_start=max(ms,LAUNCH[r.project]);s=max(begin,active_start);e=min(end,me)
        if s>e:continue
        active_days=(me-active_start).days+1
        days=(e-s).days+1
        rows.append({'project':r.project,'month':r.month,'days':days,'target':r.revenue_target*days/active_days,'profit_target':r.profit_target*days/active_days})
    return pd.DataFrame(rows)
tr=target_days()

def trend(frame,value,title,kind='sum',suffix='원',include_total=True):
    if frame.empty:st.info('해당 기간에 데이터가 없습니다.');return
    x=frame.copy();x['bucket']=x.date if freq=='일별' else x.date.dt.to_period('M').dt.to_timestamp()
    if kind=='mean':
        grouped=x.groupby(['bucket','project'],as_index=False)[value].mean()
        total=x.groupby(['bucket','date'],as_index=False)[value].sum().groupby('bucket',as_index=False)[value].mean()
    else:
        grouped=x.groupby(['bucket','project'],as_index=False)[value].sum()
        total=x.groupby('bucket',as_index=False)[value].sum()
    fig=go.Figure()
    if include_total and project=='전체':
        fig.add_trace(go.Scatter(x=total.bucket,y=total[value]/(1e8 if suffix=='원' else 1),name='TOTAL · 전체',mode='lines+markers',line=dict(width=4,color='#e6a34b'),marker=dict(size=7),hovertemplate='%{x|%Y-%m-%d}<br>TOTAL: %{y:,.2f}'+('억 원' if suffix=='원' else suffix)+'<extra></extra>'))
    palette={'A':'#65b8f5','B':'#277bdf','C':'#ec8b9b'}
    for p,g in grouped.groupby('project'):
        fig.add_trace(go.Scatter(x=g.bucket,y=g[value]/(1e8 if suffix=='원' else 1),name=LABELS[p],mode='lines+markers',line=dict(width=2,color=palette[p]),hovertemplate='%{x|%Y-%m-%d}<br>'+p+': %{y:,.2f}'+('억 원' if suffix=='원' else suffix)+'<extra></extra>'))
    fig.update_layout(title=title,hovermode='x unified',legend_title_text='',margin=dict(l=5,r=5,t=50,b=10),xaxis_title='날짜' if freq=='일별' else '월',yaxis_title='억 원' if suffix=='원' else suffix)
    fig.update_yaxes(tickformat=',.2f' if suffix=='원' else ',.0f',separatethousands=True)
    fig.update_xaxes(tickformat='%m/%d' if freq=='일별' else '%Y-%m',dtick='M1' if freq=='월별' and len(total if include_total and project=='전체' else grouped)<=24 else None)
    st.plotly_chart(fig,use_container_width=True)
    if freq=='월별' and (begin.day!=1 or end.day!=end.days_in_month): st.caption('첫 달과 마지막 달은 선택한 날짜만 집계한 부분 월입니다.')

def period_kpi():
    st.markdown(f'#### 기간별 목표 KPI · {begin:%Y.%m.%d} ~ {end:%Y.%m.%d}')
    target=float(tr.target.sum()) if len(tr) else 0
    profit_target=float(tr.profit_target.sum()) if len(tr) else 0
    actual=float(d.revenue.sum());profit=float(dcost.business_profit.sum()) if len(dcost) else 0
    cols=st.columns(4)
    cols[0].metric('기간 목표 매출',money(target))
    cols[1].metric('기간 실적 매출',money(actual),delta=f'달성률 {pct(actual,target)}',delta_color='off')
    cols[2].metric('기간 목표 사업이익',money(profit_target))
    cols[3].metric('기간 사업이익',money(profit),delta=f'달성률 {pct(profit,profit_target)}',delta_color='off')
    if target:st.progress(min(1,max(0,actual/target)),text=f'매출 목표 달성률 {pct(actual,target)}')
    st.caption('목표는 월초에 설정한 가상 사업계획을 조회 일수에 맞게 배분한 값입니다. 사업이익은 발생 RS와 운영·서버·UA 비용을 반영한 사업관리 손익입니다.')
    if len(tr):
        a=tr.groupby('project',as_index=False)[['target','profit_target']].sum()
        b=d.groupby('project',as_index=False).revenue.sum()
        z=a.merge(b,on='project',how='left').fillna(0)
        z['달성률(%)']=np.where(z.target>0,z.revenue/z.target*100,0).round(1)
        z=z.rename(columns={'target':'기간 목표 매출','profit_target':'기간 목표 사업이익','revenue':'기간 실적 매출'})
        if project=='전체':
            total={'project':'TOTAL','기간 목표 매출':z['기간 목표 매출'].sum(),'기간 목표 사업이익':z['기간 목표 사업이익'].sum(),'기간 실적 매출':z['기간 실적 매출'].sum(),'달성률(%)':actual/target*100 if target else 0}
            z=pd.concat([pd.DataFrame([total]),z],ignore_index=True)
        display_table(z)

def month_forecast():
    # 과거 월중 시점으로 재현할 때도 그 이후 데이터는 절대로 예측 입력에 사용하지 않음.
    if not (begin.to_period('M')==end.to_period('M')):return
    st.markdown('#### 조회 종료일 기준 월말 예상 실적')
    rows=[]
    for p in selected:
        r=monthly[(monthly.project==p)&(monthly.month==end.strftime('%Y-%m'))]
        if r.empty:continue
        r=r.iloc[0];ms=end.to_period('M').start_time;me=end.to_period('M').end_time.normalize()
        start=max(ms,LAUNCH[p]);obs=daily[(daily.project==p)&daily.date.between(start,end)]
        n=(end-start).days+1;N=(me-start).days+1
        if n<=0:continue
        gross=(obs.iap+obs.iaa).sum();net=(obs.iap+obs.iaa-obs.refund-obs.market_fee).sum()
        projected=gross*N/n;projected_net=net*N/n
        projected_profit=projected_net*(1-RS[p])-r.staff_cost-r.server_cost-r.ua_budget-r.lf_cost
        if end==me:projected_profit=r.business_profit;projected=r.revenue
        rows.append({'project':p,'월 목표 매출':r.revenue_target,'월말 예상 매출':projected,'월말 예상 사업이익':projected_profit,'예상 달성률(%)':projected/r.revenue_target*100 if r.revenue_target else 0})
    if not rows:return
    z=pd.DataFrame(rows)
    if project=='전체':
        total=z[['월 목표 매출','월말 예상 매출','월말 예상 사업이익']].sum()
        z=pd.concat([pd.DataFrame([{'project':'TOTAL',**total.to_dict(),'예상 달성률(%)':total['월말 예상 매출']/total['월 목표 매출']*100}]),z],ignore_index=True)
    display_table(z)
    st.caption('마감된 월은 확정된 가상 실적입니다. 월중 조회는 조회 종료일까지의 일평균을 월말까지 단순 연장한 시뮬레이션 예측이며 요일·이벤트 효과는 미반영합니다.')


# 모든 자동 해설은 현재 선택한 합성 데이터에서 계산합니다. 생성형 AI API를 호출하지 않습니다.
def insight(title,facts,hypotheses,actions):
    with st.expander('🧭 자동 사업·운영 인사이트 · '+title,expanded=True):
        st.caption('규칙 기반 분석 시뮬레이션 · 실시간 AI API 미사용 · 실제 원인 확정 아님')
        st.markdown('**확인된 수치**')
        for x in facts: st.write('• '+str(x))
        st.markdown('**가능한 해석**')
        for x in hypotheses: st.write('• '+str(x))
        st.markdown('**우선 확인할 사항**')
        for x in actions: st.write('• '+str(x))

def change_percent(current,previous):
    return (current/previous-1)*100 if previous>0 else None

def compare_previous(frame,field,agg='sum'):
    # 조회 기간과 동일한 길이의 직전 기간 비교 (조회 시작 이전도 포함)
    old=pf(daily);old=old[old.date.between(begin-pd.Timedelta(days=span),begin-pd.Timedelta(days=1))]
    now=float(frame[field].sum() if agg=='sum' else frame.groupby('date')[field].sum().mean()) if len(frame) else 0
    prev=float(old[field].sum() if agg=='sum' else old.groupby('date')[field].sum().mean()) if len(old) else 0
    return now,prev,change_percent(now,prev)

def show_delta(v):return f'{v:+.1f}%' if v is not None else '비교 불가'

def overview_insight():
    _,_,rev=compare_previous(d,'revenue')
    _,_,users=compare_previous(d,'dau','mean')
    _,_,cs_delta=compare_previous(d,'cs_count')
    facts=[f'기간 매출 {money(d.revenue.sum())}, 직전 동일 길이 기간 대비 {show_delta(rev)}',f'일평균 타이틀 DAU {d.groupby("date").dau.sum().mean():,.0f}명, 직전 기간 대비 {show_delta(users)}' if len(d) else 'DAU 자료 없음',f'CS 문의 {int(cc["count"].sum()):,}건, 직전 기간 대비 {show_delta(cs_delta)}']
    flags=[]
    if rev is not None and rev<0:flags.append('매출 하락은 UA 집행, 결제자 수, 이벤트 종료 등 복합 요인을 비교해야 합니다.')
    if users is not None and users<0:flags.append('DAU 감소가 신규 유입 감소인지 기존 유저 이탈인지 분리해 확인해야 합니다.')
    if cs_delta is not None and cs_delta>25:flags.append('CS 증가가 운영 장애인지 이벤트 참여 확대인지 유형별로 확인해야 합니다.')
    if not flags:flags=['현재 비교 지표만으로 특정 문제를 확정할 수 없습니다. 프로젝트별 차이를 추가 확인하세요.']
    insight('통합',facts,flags,['사업 성과에서 순매출·UA·RS·LF를 함께 확인','일별 코호트 리텐션과 운영 이력에서 동일 시점의 변화 교차 점검'])

if page=='프로젝트 소개 · AI 활용':
    st.subheader('프로젝트 소개 · AI 활용 과정')
    st.markdown('**게임 퍼블리싱 사업·운영 의사결정 지원을 위한 시뮬레이션 대시보드**')
    st.write('게임 사업·운영 관점에서 매출, 정산, 이용자 유지, CS, 마켓 리뷰, 이벤트 이력을 하나의 조회 흐름으로 연결하는 데 목적이 있습니다.')
    st.markdown('#### 설계 목표')
    st.write('① 수치 조회  ② 이상 징후 확인  ③ 지표 간 교차 분석  ④ 담당자 검증 및 대응 제안')
    st.markdown('#### AI 활용 범위와 기여도')
    st.write('사업 지표 정의, MG·RS·LF 계약 시뮬레이션 가정, 운영 관점의 분석 질문과 요구사항을 정리하고 생성형 AI를 활용해 Python·Streamlit 구현 및 분석 문구 설계를 보조했습니다.')
    st.write('대시보드의 자동 인사이트는 조회 데이터에 반응하는 Python 규칙 기반 시뮬레이션이며, 실시간 AI 모델 분석이나 외부 게임 API 연결은 제공하지 않습니다.')
    st.markdown('#### 주요 활용 사례')
    st.write('• 프로젝트별 매출·손익과 계약 선지급금의 영향 검토')
    st.write('• 유입일별 코호트 이탈과 채널별 유지율 차이 탐색')
    st.write('• 이벤트·업데이트 전후 매출·DAU·CS·리뷰 변화를 비교하고 점검 가설 정리')
    st.info('본 프로젝트는 전부 합성 데이터로 구성한 포트폴리오 시연입니다. 실제 회사·게임의 내부 정보, 실시간 AI API, 실제 마켓 API 데이터는 포함되지 않습니다.')
elif page=='통합 대시보드':
    st.subheader('사업 전체 현황')
    k=st.columns(4)
    for c,(name,v) in zip(k,[('선택 기간 총매출',money(d.revenue.sum())),('IAP 매출',money(d.iap.sum())),('IAA 매출',money(d.iaa.sum())),('일평균 타이틀 DAU',f'{d.groupby("date").dau.sum().mean():,.0f}' if len(d) else '0')]):c.metric(name,v)
    st.caption('TOTAL DAU는 프로젝트별 DAU 합계이며, 게임 간 중복 이용자를 제거한 고유 이용자 수는 아닙니다.')
    period_kpi();month_forecast();overview_insight()
    trend(d,'revenue',f'{freq} 매출 추이 · TOTAL 및 프로젝트별')
    x=d.groupby(['project','month'],as_index=False)[['iap','iaa','revenue']].sum()
    display_table(x,['project','month','iap','iaa','revenue'])

elif page=='사업 성과':
    st.subheader('사업 성과 · 손익 · MG/RS')
    st.info('MG는 발생 RS에서 상계하는 선지급금이며, LF는 RS와 상계하지 않는 별도 비용입니다. 가상 사업관리 기준으로 프로젝트 A의 LF 1억 원을 출시일(2021-10-27)에 일괄 반영합니다. 실제 회계상 비용 인식과 다를 수 있습니다.')
    contract=pd.DataFrame([{'project':p,'출시일':LAUNCH[p].strftime('%Y-%m-%d'),'MG 계약금':MG[p],'LF 계약금':LF[p],'개발사 RS(%)':RS[p]*100,'선지급 합계':MG[p]+LF[p]} for p in selected])
    st.markdown('**프로젝트 계약 구조**');display_table(contract)
    period_kpi();month_forecast()
    insight('사업 성과',[f'조회 기간 매출 {money(d.revenue.sum())}',f'조회 기간 LF 비용 {money(dcost.lf_cost.sum())}',f'조회 기간 발생 RS {money(dcost.rs_accrued.sum())}'],['LF는 출시월에만 손익에 반영됩니다. MG 선지급금과 발생 RS를 중복 비용 처리하지 않습니다.'],['프로젝트별 순매출·UA·LF와 사업이익을 함께 비교','MG 회수율과 RS 실제 지급액을 별도로 검토'])
    k=st.columns(4)
    for c,(name,v) in zip(k,[('기간 총매출',d.revenue.sum()),('기간 순매출',dcost.net_revenue.sum()),('기간 발생 RS',dcost.rs_accrued.sum()),('기간 사업이익',dcost.business_profit.sum())]):c.metric(name,money(v))
    trend(d,'revenue',f'{freq} 매출 추이')
    st.metric('선택 기간 LF 비용',money(dcost.lf_cost.sum()))
    st.markdown('**MG 회수 현황 (조회 종료일 기준)**')
    for p in selected:
        history=monthly[(monthly.project==p)&(monthly.month_date<=end)]
        if history.empty:continue
        remain=int(history.iloc[-1].mg_remaining);rate=1-remain/MG[p]
        st.write(f'{LABELS[p]} | 최초 MG {money(MG[p])} · 잔액 {money(remain)} · 회수율 {rate:.1%}')
        st.progress(min(1,max(0,rate)))
    st.markdown('**선택 기간 정산 상세 (기간 배분 금액)**')
    if len(dcost):
        x=dcost.groupby(['project','month'],as_index=False)[['iap','iaa','refund','market_fee','net_revenue','rs_accrued','staff_cost','server_cost','ua_budget','lf_cost','business_profit']].sum()
        display_table(x)
    st.markdown('**월별 정산 원본 (월 전체 실적)**')
    display_table(mm,['project','month','iap','iaa','refund','market_fee','net_revenue','rs_accrued','mg_offset','rs_paid','mg_remaining','staff_cost','server_cost','ua_budget','lf_cost','business_profit'])
    st.caption('LF는 출시월에만 발생하는 가상 사업관리 비용입니다. 손익 그래프에서 출시월의 일시적 비용을 운영 실적 악화로 단정하지 마세요.')
    st.caption('원본 정산표는 월 전체 기준이며, 위 기간 배분 정산표와 범위가 다를 수 있습니다. MG 상계·실제 RS 지급은 월별 정산 기준으로 관리합니다.')

elif page=='이용자·리텐션':
    st.subheader('이용자 및 코호트 분석')
    k=st.columns(4)
    k[0].metric('일평균 타이틀 DAU',f'{d.groupby("date").dau.sum().mean():,.0f}' if len(d) else '0')
    k[1].metric('포함 월 최대 MAU 합계',f'{mm.groupby("month").mau.sum().max():,.0f}' if len(mm) else '0')
    k[2].metric('마지막 포함 월 MPU 합계',f'{mm[mm.month==mm.month.max()].mpu.sum():,.0f}' if len(mm) else '0')
    co=pf(cohorts);co=co[pd.to_datetime(co.cohort_month+'-01').between(begin.to_period('M').start_time,end)]
    k[3].metric('코호트 기록',f'{len(co):,}개')
    trend(d,'dau',f'{freq} DAU 추이',kind='mean',suffix='명')
    if len(co):
        z=co.groupby(['channel','day'],as_index=False)[['cohort_users','retained_users']].sum()
        z['retention_pct']=z.retained_users/z.cohort_users*100
        fig=go.Figure()
        overall=co.groupby('day',as_index=False)[['cohort_users','retained_users']].sum();overall['rate']=overall.retained_users/overall.cohort_users*100
        fig.add_trace(go.Scatter(x=overall.day,y=overall.rate,name='TOTAL · 전체 채널',line=dict(width=4,color='#e6a34b'),mode='lines+markers',hovertemplate='D%{x}: %{y:,.1f}%<extra></extra>'))
        for channel,g in z.groupby('channel'):fig.add_trace(go.Scatter(x=g.day,y=g.retention_pct,name=channel,mode='lines+markers',hovertemplate='D%{x}: %{y:,.1f}%<extra></extra>'))
        fig.update_layout(title='유입 채널별 코호트 리텐션 (가중 통합)',xaxis_title='경과일',yaxis_title='리텐션 (%)',legend_title_text='')
        st.plotly_chart(fig,use_container_width=True)
    st.markdown('#### 유입일별 코호트 리텐션')
    st.caption('행은 신규 유입일, 열은 경과일입니다. 미도래 D1/D3/D7/D14/D30은 0%가 아니라 N/A로 표시합니다. 조회 기간은 유입일 기준입니다.')
    channel_choice=st.selectbox('코호트 유입 채널',['전체 채널','Organic','Google Ads','Meta Ads'])
    co_day=daily_cohorts[daily_cohorts.project.isin(selected)].copy()
    co_day['cohort_date']=pd.to_datetime(co_day.cohort_date)
    co_day=co_day[co_day.cohort_date.between(begin,end)]
    if channel_choice!='전체 채널':co_day=co_day[co_day.channel==channel_choice]
    if not co_day.empty:
        co_day=co_day[co_day.cohort_date+pd.to_timedelta(co_day.day,unit='D')<=CUTOFF]
        group=co_day.groupby(['cohort_date','day'],as_index=False)[['cohort_users','retained_users']].sum()
        group['rate']=np.where(group.cohort_users>0,group.retained_users/group.cohort_users*100,np.nan)
        pivot=group.pivot(index='cohort_date',columns='day',values='rate').reindex(columns=[1,3,7,14,30])
        if len(pivot)>90:st.caption('가독성을 위해 최신 90개 유입일을 표시합니다. 조회 조건으로 기간을 줄여 보세요.');pivot=pivot.tail(90)
        if len(pivot):
            fig=go.Figure(go.Heatmap(z=pivot.values,x=['D1','D3','D7','D14','D30'],y=pivot.index.strftime('%Y-%m-%d'),colorscale='RdYlGn',zmin=0,zmax=55,hovertemplate='유입일 %{y}<br>%{x}: %{z:.1f}%<extra></extra>',colorbar=dict(title='%')))
            fig.update_layout(height=max(330,min(1250,160+len(pivot)*17)),margin=dict(l=5,r=5,t=15,b=10),yaxis=dict(autorange='reversed'))
            st.plotly_chart(fig,use_container_width=True)
            st.dataframe(pivot.rename(columns=lambda n:f'D{n}').round(1).style.format('{:.1f}%',na_rep='N/A'),use_container_width=True)
        st.markdown('**유입일별 D1 / D7 리텐션 추이**')
        fig=go.Figure()
        for day_n in [1,7]:
            z=group[group.day==day_n]
            fig.add_trace(go.Scatter(x=z.cohort_date,y=z.rate,name=f'D{day_n}',mode='lines+markers'))
        fig.update_layout(yaxis_title='리텐션 (%)',xaxis_title='유입일',hovermode='x unified')
        st.plotly_chart(fig,use_container_width=True)
        sizes=co_day[co_day.day==1].groupby('cohort_date',as_index=False).cohort_users.sum()
        display_table(sizes.tail(31).rename(columns={'cohort_users':'신규 유입 표본 수'}))
        insight('리텐션',[f'분석 코호트 유입일 {co_day.cohort_date.nunique():,}일',f'유입 채널: {channel_choice}'],['리텐션 하락일은 유입 채널 구성, 초기 경험, 이벤트·업데이트 이력의 영향을 함께 확인해야 합니다.'],['표본 수가 적은 유입일의 급격한 변동을 과대 해석하지 않기','이벤트·운영 이력 페이지에서 해당 날짜의 주요 변화를 비교'])
    else:st.info('해당 유입일의 코호트 관측 데이터가 없습니다.')
    st.caption('MAU/MPU는 월 전체의 가상 집계이며, 코호트는 유저 ID 원본이 아닌 합성 예시입니다. 최근 코호트의 미도래 D30은 확정 리텐션으로 해석하지 마세요.')
    display_table(mm,['project','month','mau','mpu'])

elif page=='운영·CS·리뷰':
    st.subheader('운영 · CS · 마켓 리뷰')
    k=st.columns(3);k[0].metric('CS 문의',f'{cc["count"].sum():,}건');k[1].metric('수집 리뷰',f'{len(rr):,}건');k[2].metric('수집 리뷰 평균',f'{rr.rating.mean():.2f}/5' if len(rr) else '—')
    if len(cc):
        x=cc.groupby(['date','project'],as_index=False)['count'].sum()
        trend(x,'count',f'{freq} CS 문의 추이',suffix='건')
        st.markdown('**유형별 문의량**')
        z=cc.groupby(['project','category'],as_index=False)['count'].sum()
        if project=='전체':
            total=z.groupby('category',as_index=False)['count'].sum();total['project']='TOTAL'
            z=pd.concat([total,z],ignore_index=True)
        display_table(z,['project','category','count'])
    if len(rr):
        z=rr.groupby(['project','store','rating']).size().reset_index(name='count')
        if project=='전체':
            total=z.groupby(['store','rating'],as_index=False)['count'].sum();total['project']='TOTAL';z=pd.concat([total,z],ignore_index=True)
        st.markdown('**마켓 리뷰 별점 분포**');display_table(z)
    st.markdown('#### 운영 효율 및 리뷰 변화')
    dau_sum=float(d.dau.sum())
    k=st.columns(3)
    k[0].metric('DAU 1,000명당 문의',f'{cc["count"].sum()/dau_sum*1000:.2f}건' if dau_sum else '—')
    _,_,cs_rate=compare_previous(d,'cs_count')
    k[1].metric('직전 동일 기간 대비 CS',show_delta(cs_rate))
    k[2].metric('1~2점 리뷰 비중',f'{(rr.rating<=2).mean():.1%}' if len(rr) else '—')
    if len(cc):
        st.markdown('**문의 유형별 일별 변화**')
        cats=cc.groupby(['date','category'],as_index=False)['count'].sum()
        fig=go.Figure()
        for category,g in cats.groupby('category'):fig.add_trace(go.Scatter(x=g.date,y=g['count'],name=category,mode='lines',stackgroup='one'))
        fig.update_layout(yaxis_title='문의 건수',hovermode='x unified',xaxis_title='일자')
        st.plotly_chart(fig,use_container_width=True)
    if len(rr):
        st.markdown('**일별 수집 리뷰 평균 및 저평점 비중**')
        byday=rr.groupby('date').agg(avg_rating=('rating','mean'),review_count=('rating','size'),low_count=('rating',lambda x:(x<=2).sum())).reset_index()
        byday['low_pct']=byday.low_count/byday.review_count*100
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=byday.date,y=byday.avg_rating,name='평균 별점',mode='lines+markers'))
        fig.update_layout(yaxis_title='평균 별점 / 5',yaxis=dict(range=[0,5]),xaxis_title='일자')
        st.plotly_chart(fig,use_container_width=True)
        display_table(rr.groupby('topic',as_index=False).size().rename(columns={'topic':'리뷰 유형','size':'리뷰 수'}).sort_values('리뷰 수',ascending=False))
    top=cc.groupby('category')['count'].sum().sort_values(ascending=False) if len(cc) else pd.Series(dtype=float)
    insight('운영·CS·리뷰',[f'총 CS {int(cc["count"].sum()):,}건 / DAU 1,000명당 {cc["count"].sum()/dau_sum*1000:.2f}건' if dau_sum else 'CS 자료 없음',f'주요 문의 유형: {top.index[0]} ({int(top.iloc[0]):,}건)' if len(top) else '문의 유형 자료 없음',f'리뷰 {len(rr):,}건 / 저평점 비중 {(rr.rating<=2).mean():.1%}' if len(rr) else '리뷰 자료 없음'],['문의량은 DAU 규모와 함께 비교해야 합니다. 리뷰는 수집 표본에 따라 평균이 달라집니다.'],['급증일의 문의 유형과 이벤트·업데이트 이력 교차 확인','결제·접속 등 핵심 불만 유형의 실제 로그 확인'])
    st.caption('수집 리뷰 평균은 스토어 전체 평점과 다릅니다. 모든 리뷰는 가상 데이터입니다.')

elif page=='운영 이력 · 영향 분석':
    st.subheader('운영 이력 · 자동 이상 징후 감지')
    st.caption('통계·규칙 기반 탐지 · 생성형 AI API 미사용 · 원인 확정이 아닌 점검 후보 제시')
    findings=[]
    # 비교 기준은 조회 기간 이전의 과거 14일도 포함하며, 미래 정보는 사용하지 않음.
    history=pf(daily);history=history[history.date<=end]
    if project=='전체':
        agg=history.groupby('date',as_index=False)[['revenue','dau','cs_count']].sum();agg['project']='TOTAL';groups=[agg]+[history[history.project==p] for p in selected]
    else:groups=[history]
    for g in groups:
        if g.empty:continue
        p=g.project.iloc[0];g=g.sort_values('date').copy()
        for col,label in [('revenue','매출'),('dau','DAU'),('cs_count','CS 문의')]:
            base=g[col].shift(1).rolling(14,min_periods=7).mean();change=g[col]/base.replace(0,np.nan)-1
            bad=g[g.date.between(begin,end)&((change<-.35) if col!='cs_count' else (change>.80))]
            for idx,r in bad.tail(8).iterrows():findings.append({'일자':r.date.date(),'프로젝트':p,'지표':label,'변동률':f'{change.loc[idx]:+.1%}','점검 제안':'집계 누락·업데이트·UA·장애 이력 확인' if col!='cs_count' else '문의 유형·장애·업데이트 이력 확인'})
    if findings:st.dataframe(pd.DataFrame(findings).sort_values('일자',ascending=False),hide_index=True,use_container_width=True)
    else:st.success('선택 기간에 탐지 기준을 충족하는 이상 징후가 없습니다.')
    st.markdown('**이벤트·업데이트 이력**');display_table(ev,['date','project','category','title'])
    st.markdown('#### 이벤트·업데이트 전후 영향 비교')
    st.caption('선택한 이벤트 전 7일과 이후 7일의 일평균 비교입니다. 관측 일수가 부족한 경우 별도 표시합니다. 상관관계는 인과관계가 아닙니다.')
    if len(ev):
        options=ev.sort_values('date',ascending=False).reset_index(drop=True)
        ix=st.selectbox('분석할 운영 이력',range(len(options)),format_func=lambda i:f'{options.loc[i,"date"]:%Y-%m-%d} · {LABELS[options.loc[i,"project"]]} · {options.loc[i,"title"]}')
        item=options.iloc[ix];p=item.project;t=item.date
        history_p=daily[daily.project==p]
        before=history_p[history_p.date.between(t-pd.Timedelta(days=7),t-pd.Timedelta(days=1))]
        after=history_p[history_p.date.between(t,t+pd.Timedelta(days=6))]
        st.write(f'**{LABELS[p]} | {item.title} | {t:%Y-%m-%d}**')
        cols=st.columns(3)
        for col,field,label in zip(cols,['revenue','dau','cs_count'],['일평균 매출','일평균 DAU','일평균 CS']):
            bv=before[field].mean() if len(before) else 0;av=after[field].mean() if len(after) else 0
            col.metric(label,money(av) if field=='revenue' else f'{av:,.1f}',delta=show_delta(change_percent(av,bv)),delta_color='off')
        st.caption(f'관측일수: 이벤트 전 {len(before)}일 / 이벤트 시작일부터 {len(after)}일. 7일 미만인 경우 해석에 유의하세요.')
        st.markdown('**운영 이력과 KPI 타임라인 (이벤트 전후 14일)**')
        around=history_p[history_p.date.between(t-pd.Timedelta(days=14),t+pd.Timedelta(days=14))].copy()
        fig=go.Figure()
        for field,label in [('revenue','매출'),('dau','DAU'),('cs_count','CS 문의')]:
            base=before[field].mean() if len(before) else 0
            if base>0:fig.add_trace(go.Scatter(x=around.date,y=around[field]/base*100,name=label+' 지수',mode='lines+markers'))
        fig.add_vline(x=t.timestamp()*1000,line_dash='dash',line_color='#e6a34b')
        fig.update_layout(yaxis_title='이벤트 이전 7일 평균 = 100',xaxis_title='일자',hovermode='x unified')
        st.plotly_chart(fig,use_container_width=True)
        related=cs[(cs.project==p)&cs.date.between(t,t+pd.Timedelta(days=6))].groupby('category')['count'].sum().sort_values(ascending=False)
        insight('이벤트 영향',[f'이벤트: {item.title} ({t:%Y-%m-%d})',f'이벤트 전 7일 대비 매출 일평균 {show_delta(change_percent(after.revenue.mean() if len(after) else 0,before.revenue.mean() if len(before) else 0))}',f'이벤트 이후 주요 CS 유형: {related.index[0]}' if len(related) else '이벤트 이후 CS 자료 없음'],['매출·DAU·CS의 동시 변화만으로 이벤트 효과나 장애 원인을 확정할 수 없습니다.'],['이벤트 시작 전후의 UA·결제·문의 유형 확인','요일 및 동기간 다른 운영 이력에 따른 영향 점검'])
    else:st.info('선택 기간에 등록된 운영 이력이 없습니다.')


elif page=='데이터 추출·외부 링크':
    st.subheader('데이터 다운로드')
    st.caption('다운로드 파일은 가상 데이터임을 표시합니다. 일별 자료는 선택 기간만, 월별 원본은 포함된 월 전체를 제공합니다.')
    left,right=st.columns(2)
    with left:
        export('일별 매출·DAU·CS CSV',d.drop(columns=['month']),'demo_daily.csv')
        export('선택 기간 사업 손익 CSV',dcost,'demo_period_profit.csv')
        export('월별 손익·MG/RS CSV',mm.drop(columns=['month_date']),'demo_monthly.csv')
        export('CS 유형별 CSV',cc,'demo_cs.csv')
    with right:
        export('마켓 리뷰 CSV',rr,'demo_reviews.csv')
        export('이벤트·업데이트 CSV',ev,'demo_events.csv')
        co=pf(cohorts);co=co[pd.to_datetime(co.cohort_month+'-01').between(begin.to_period('M').start_time,end)]
        export('리텐션 코호트 CSV',co,'demo_cohorts.csv')
        export('일별 코호트 CSV',daily_cohorts[daily_cohorts.project.isin(selected)],'demo_daily_cohorts.csv')
        export('월별 KPI 계획 CSV',mm[['project','month','revenue_target','profit_target']],'demo_targets.csv')
    st.divider();st.subheader('업무 관련 공식 사이트')
    st.caption('외부 사이트 바로가기이며 계정 또는 API 연동은 활성화되어 있지 않습니다.')
    links={'Google Play Console':'https://play.google.com/console/','App Store Connect':'https://appstoreconnect.apple.com/','Google Ads':'https://ads.google.com/','Google Analytics':'https://analytics.google.com/','Google Cloud Console':'https://console.cloud.google.com/','Meta Ads Manager':'https://adsmanager.facebook.com/','Firebase Console':'https://console.firebase.google.com/'}
    for name,url in links.items():st.link_button(f'↗ {name}',url,use_container_width=True)

st.divider();st.caption('DEMO DASHBOARD · 가상 데이터 — 실제 기업 및 게임의 운영 실적과 무관한 시뮬레이션 환경입니다. 데이터 기준일: 2026-10-31')
