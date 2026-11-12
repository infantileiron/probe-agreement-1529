import math

def analyze(x,y):
 if len(x)!=len(y) or len(x)<4:raise ValueError("一致性分析至少需要4组配对")
 if not all(math.isfinite(v) for v in x+y):raise ValueError("读数必须有限")
 n=len(x);means=[(a+b)/2 for a,b in zip(x,y)];diffs=[b-a for a,b in zip(x,y)];bias=math.fsum(diffs)/n
 sd=math.sqrt(math.fsum((d-bias)**2 for d in diffs)/(n-1));low=bias-1.96*sd;high=bias+1.96*sd
 mm=math.fsum(means)/n;ss=math.fsum((m-mm)**2 for m in means)
 if ss==0:proportional={"estimable":False,"slope":None,"intercept":None,"r_squared":None,"reason":"两探头均值读数为常量，比例偏倚回归不可估计"}
 else:
  slope=math.fsum((m-mm)*(d-bias) for m,d in zip(means,diffs))/ss;intercept=bias-slope*mm
  residual_sse=math.fsum((d-intercept-slope*m)**2 for m,d in zip(means,diffs));total_ss=math.fsum((d-bias)**2 for d in diffs)
  proportional={"estimable":True,"slope":slope,"intercept":intercept,"r_squared":None if total_ss==0 else max(0.,min(1.,1-residual_sse/total_ss)),"reason":""}
 return {"n":n,"bias":bias,"sample_sd":sd,"loa_low":low,"loa_high":high,"outside_loa":sum(d<low or d>high for d in diffs),"proportional":proportional,"difference_definition":"y-x","sd_ddof":1,"limits_note":"mean(y-x) ± 1.96 × sample SD；一致性界限不是置信区间，不直接证明设备可互换。"}
