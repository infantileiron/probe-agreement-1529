import csv,io,math

def parse_csv(text):
 rows=list(csv.DictReader(io.StringIO(text)));required={"pair_id","range_label","x","y"}
 if not rows or len(rows)>5000 or not required.issubset(rows[0]):raise ValueError("CSV需1至5000行并包含pair_id,range_label,x,y")
 seen=set();result=[]
 for index,row in enumerate(rows,2):
  ident=(row.get("pair_id") or "").strip();band=(row.get("range_label") or "").strip()
  if not ident or len(ident)>80 or ident in seen:raise ValueError(f"第{index}行配对ID为空、过长或重复")
  if band not in ["low","middle","high"]:raise ValueError(f"第{index}行量程应为low/middle/high")
  seen.add(ident);values={}
  for key in ["x","y"]:
   try:value=float(row.get(key))
   except Exception:raise ValueError(f"第{index}行{key}需要有效数值")
   if not math.isfinite(value) or abs(value)>1e9:raise ValueError(f"第{index}行{key}必须有限且绝对值不超过1e9")
   values[key]=value
  result.append({"pair_id":ident,"range_label":band,**values})
 return result

def validate_pairs(pairs):
 if len(pairs)<4:raise ValueError("至少需要4组成对读数")
 x=[r["x"] for r in pairs];y=[r["y"] for r in pairs]
 if not all(math.isfinite(v) for v in x+y):raise ValueError("读数必须有限")
 return x,y
