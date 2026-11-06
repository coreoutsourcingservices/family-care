"""Build-time translation of static public interface labels; never called by the API."""
import argparse, concurrent.futures, json, re, time, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CODES={'as':'as','awadhi':'awa','bhojpuri':'bho','bn':'bn','dogri':'doi','fr':'fr','gu':'gu','hi':'hi','khasi':'kha','kn':'kn','kokborok':'trp','konkani':'gom','maithili':'mai','manipuri':'mni-Mtei','marwari':'mwr','mizo':'lus','ml':'ml','mr':'mr','ne':'ne','or':'or','pa':'pa','santali':'sat','ta':'ta','te':'te','tulu':'tcy','ur':'ur'}
# Identifiers, brands and standard medical abbreviations retain their spelling.
UNCHANGED={'FC','FAMILYCARE','familycare','Familycare','FamilyCare','UIP','IAP','IM','ID','SC','IN','PCOS','PDF','CSV','JSON','OTP','DOB','Email','email','SMS','URL','MBBS','MD','en','hi','N/A'}
def placeholders(s):return sorted(re.findall(r'\{\{.*?\}\}',s))
def translated_batch(keys,target):
 tokens={};prepared=[]
 for i,key in enumerate(keys):
  def protect(m):
   marker=f'XQZ{len(tokens)}ZQX';tokens[marker]=m[0];return marker
  prepared.append(f'{i:04d}: '+re.sub(r'\{\{.*?\}\}',protect,key).replace('\n',' '))
 query=urllib.parse.urlencode({'client':'gtx','sl':'en','tl':target,'dt':'t','q':'\n'.join(prepared)})
 with urllib.request.urlopen('https://translate.googleapis.com/translate_a/single?'+query,timeout=25) as r:data=json.load(r)
 text=''.join(row[0] for row in data[0] if row and row[0])
 matches=list(re.finditer(r'(?m)^\s*(\d{4})\s*[:：.、-]\s*',text))
 result={}
 for n,match in enumerate(matches):
  i=int(match[1]);value=text[match.end():matches[n+1].start() if n+1<len(matches) else len(text)].strip()
  if i>=len(keys):continue
  for marker,original in tokens.items():value=value.replace(marker,original)
  if value and placeholders(value)==placeholders(keys[i]):result[keys[i]]=value
 return result

def translated_one(key,target):
 tokens={}
 def protect(m):
  marker=f'XQZ{len(tokens)}ZQX';tokens[marker]=m[0];return marker
 text=re.sub(r'\{\{.*?\}\}',protect,key)
 query=urllib.parse.urlencode({'client':'gtx','sl':'en','tl':target,'dt':'t','q':text})
 with urllib.request.urlopen('https://translate.googleapis.com/translate_a/single?'+query,timeout=25) as r:data=json.load(r)
 value=''.join(row[0] for row in data[0] if row and row[0]).strip()
 for marker,original in tokens.items():value=value.replace(marker,original)
 return {key:value} if value and placeholders(value)==placeholders(key) else {}

def process(code,keys):
 path=ROOT/'backend/locales'/f'{code}.json';catalog=json.loads(path.read_text(encoding='utf-8'))
 customer=ROOT/'customer/src/localization/compiled'/path.name
 shared=json.loads(customer.read_text(encoding='utf-8')) if customer.exists() else {}
 for key in keys:
  if (key not in catalog or catalog[key]==key) and shared.get(key) and shared[key]!=key:catalog[key]=shared[key]
 todo=[k for k in keys if k not in UNCHANGED and (not catalog.get(k) or catalog[k]==k)]
 batches=[];batch=[];size=0
 for key in todo:
  if batch and (size+len(key)>2200 or len(batch)>=55):batches.append(batch);batch=[];size=0
  batch.append(key);size+=len(key)+8
 if batch:batches.append(batch)
 failed=[]
 for batch in batches:
  try:values=translated_batch(batch,CODES[code])
  except Exception as e:
   if getattr(e,'code',None) in (403,429):raise RuntimeError(f'{code}: translation service denied/rate limited; stop instead of bypassing') from e
   values={}
  for key in batch:
   if key in values:catalog[key]=values[key]
   if key not in values or (catalog.get(key)==key and len(key.split())>=3):
    try:one=translated_one(key,CODES[code]);catalog.update(one)
    except Exception:pass
    if not catalog.get(key) or (catalog[key]==key and len(key.split())>=3):failed.append(key)
  path.write_text(json.dumps({k:catalog.get(k,k) for k in keys},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  time.sleep(.12)
 for key in UNCHANGED:
  if key in keys:catalog[key]=catalog.get(key,key)
 path.write_text(json.dumps({k:catalog.get(k,k) for k in keys},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return {'language':code,'requested':len(todo),'missing':failed,'english_phrases':[k for k in keys if catalog.get(k)==k and len(k.split())>=3 and k not in UNCHANGED]}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--keys',required=True);parser.add_argument('--translate',action='store_true');args=parser.parse_args()
 if not args.translate:parser.error('Use --translate for the explicit build-time public-label translation operation')
 keys=json.loads(Path(args.keys).read_text(encoding='utf-8-sig'))
 english={k:k for k in keys}
 for path in [ROOT/'backend/locales/en.json',ROOT/'admin/src/locales/en.json']:path.write_text(json.dumps(english,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(process,code,keys) for code in CODES]
  for future in concurrent.futures.as_completed(futures):
   result=future.result();results.append(result);print(json.dumps(result,ensure_ascii=True),flush=True)
 report=ROOT/'backend/localization_translation_report.json'
 report.write_text(json.dumps({'provider':'Google Translate, build-time public UI labels only','native_speaker_reviewed':False,'keys':len(keys),'languages':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if any(r['missing'] for r in results):raise SystemExit('Some labels need translation; inspect report')
if __name__=='__main__':main()
