# Rain events -> turbidity rise and clearing at main-stem sites.
import json,datetime as dt,statistics as st,collections
D=json.load(open('hourly.json'))
def ser(k): return D.get(k,{})
RAIN=['02334885:00045','02335000:00045','02335350:00045','02335700:00045','02335810:00045']
TURB={'Buford':'02334500:63680','Medlock':'02335000:63680','PowersFy':'02335880:63680','Atlanta':'02336000:63680'}
DAM=ser('02334430:00060')
hrs=sorted(set().union(*[ser(k).keys() for k in RAIN]))
t0=dt.datetime.fromisoformat(hrs[0]); t1=dt.datetime.fromisoformat(hrs[-1])
def key(t): return t.strftime('%Y-%m-%dT%H')
def rain(t):
  v=[ser(k)[key(t)] for k in RAIN if key(t) in ser(k)]
  return sum(v)/len(v) if len(v)>=2 else None
# hourly basin rain
R={}; t=t0
while t<=t1: R[t]=rain(t); t+=dt.timedelta(hours=1)
T=sorted(R)
# events: rain clusters separated by >=12 dry hours
ev=[]; cur=None; dry=0
for t in T:
  r=R[t] or 0
  if r>=0.01:
    if cur is None: cur=[t,t,0.0]
    cur[1]=t; cur[2]+=r; dry=0
  elif cur:
    dry+=1
    if dry>=12: ev.append(cur); cur=None; dry=0
rows=[]
for s,e,tot in ev:
  if tot<0.2: continue
  # next rain >=0.1" after e (limits clear search)
  nxt=None; t=e+dt.timedelta(hours=12)
  while t<=t1 and t<e+dt.timedelta(days=7):
    if (R.get(t) or 0)>=0.05: nxt=t; break
    t+=dt.timedelta(hours=1)
  lim=nxt or e+dt.timedelta(days=7)
  rel=max([DAM.get(key(s+dt.timedelta(hours=h)),0) for h in range(-24,int((lim-s).total_seconds()/3600))] or [0])
  row={'start':key(s),'end':key(e),'in':round(tot,2),'hrs':int((e-s).total_seconds()/3600)+1,'mon':s.month,'damMax':round(rel),'cut':nxt is not None}
  for name,k in TURB.items():
    S=ser(k); base=[S[key(s-dt.timedelta(hours=h))] for h in range(1,13) if key(s-dt.timedelta(hours=h)) in S]
    if len(base)<6: continue
    b=st.median(base); pk=None; pkt=None; t=s
    while t<=min(lim,e+dt.timedelta(hours=72)):
      v=S.get(key(t))
      if v is not None and (pk is None or v>pk): pk,pkt=v,t
      t+=dt.timedelta(hours=1)
    if pk is None: continue
    # clear: first time after peak turb <= max(base+1, base*1.2) held 3 h
    clr=None; t=pkt; run=0; thr=max(b+1,b*1.2)
    while t<=lim:
      v=S.get(key(t))
      if v is not None and v<=thr:
        run+=1
        if run>=3: clr=t-dt.timedelta(hours=2); break
      elif v is not None: run=0
      t+=dt.timedelta(hours=1)
    # time to under 10 and under 5 FNU
    def under(x):
      if pk<=x: return 0
      t=pkt
      while t<=lim:
        v=S.get(key(t))
        if v is not None and v<x: return round((t-e).total_seconds()/3600)
        t+=dt.timedelta(hours=1)
      return None
    row[name]={'base':round(b,1),'peak':round(pk,1),'add':round(pk-b,1),'lagPk':round((pkt-s).total_seconds()/3600),
      'clrAfterEnd':round((clr-e).total_seconds()/3600) if clr else None,'u10':under(10),'u5':under(5)}
  rows.append(row)
json.dump(rows,open('rain_events.json','w'),indent=0)
print(len(rows),'events >=0.2 in')
bins=[(0.2,0.5),(0.5,1),(1,2),(2,9)]
for name in TURB:
  print('\n==',name)
  print('rain in   n  base  add(med) peak(med)  lag->pk  clear(h after rain ends, med/p75)  <10FNU  <5FNU')
  for lo,hi in bins:
    r=[x[name] for x in rows if name in x and lo<=x['in']<hi]
    if not r: continue
    m=lambda f:[y[f] for y in r if y[f] is not None]
    c=m('clrAfterEnd'); q=lambda a,p: round(sorted(a)[int(p*(len(a)-1))]) if a else '-'
    print(f'{lo}-{hi}  {len(r):3} {st.median(m("base")):5.1f} {st.median(m("add")):7.1f} {st.median(m("peak")):8.1f} {st.median(m("lagPk")):7.0f}   {q(c,.5)}/{q(c,.75)} (n={len(c)})   {q(m("u10"),.5)}  {q(m("u5"),.5)}')
