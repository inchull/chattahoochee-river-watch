# Pull 3 years of 15-min USGS data for the rain study; save hourly (mean flow/turb, summed rain).
import json,urllib.request,datetime as dt,collections,os,time
SITES='02334430,02334500,02334885,02335000,02335350,02335700,02335810,02335880,02336000'
start=dt.date(2023,11,1); end=dt.date(2026,11,21)
H=collections.defaultdict(lambda: collections.defaultdict(list))  # key site:param -> hourISO -> values
d=start
while d<end:
  e=min(d+dt.timedelta(days=45),end); url=f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={SITES}&parameterCd=00060,63680,00045&startDT={d}&endDT={e}"
  for tryn in range(4):
    try: data=json.loads(urllib.request.urlopen(url,timeout=240).read()); break
    except Exception as ex: print(d,'retry',ex); time.sleep(10); data=None
  if data:
    for ts in data['value']['timeSeries']:
      k=ts['sourceInfo']['siteCode'][0]['value']+':'+ts['variable']['variableCode'][0]['value']
      for blk in ts['values']:
        for v in blk['value']:
          try: x=float(v['value'])
          except: continue
          if x<-1e5: continue
          t=dt.datetime.fromisoformat(v['dateTime']).astimezone(dt.timezone.utc)
          H[k][t.strftime('%Y-%m-%dT%H')].append(x)
    print(d,'ok',flush=True)
  else: print(d,'FAILED',flush=True)
  d=e
out={k:{h:(sum(v) if k.endswith('00045') else sum(v)/len(v)) for h,v in hs.items()} for k,hs in H.items()}
json.dump(out,open('hourly.json','w')); print('done',{k:len(v) for k,v in out.items()})
