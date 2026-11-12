import math

def regress(x,y,variance_ratio):
 if len(x)!=len(y) or len(x)<4:raise ValueError("Deming至少需要4组完整配对")
 if not math.isfinite(variance_ratio) or variance_ratio<=0:raise ValueError("lambda=var(y误差)/var(x误差)须正且有限")
 if not all(math.isfinite(v) for v in x+y):raise ValueError("读数必须有限")
 n=len(x);mx=math.fsum(x)/n;my=math.fsum(y)/n
 vx=math.fsum((v-mx)**2 for v in x)/(n-1);vy=math.fsum((v-my)**2 for v in y)/(n-1);cov=math.fsum((a-mx)*(b-my) for a,b in zip(x,y))/(n-1)
 if vx<=0 or vy<=0:raise ValueError("任一探头读数为常量，无法估计Deming斜率")
 if abs(cov)<=1e-12*math.sqrt(vx*vy):raise ValueError("协方差为零或近零，Deming方向不可稳定估计")
 scale=max(vx,vy);xx,yy,xy=vx/scale,vy/scale,cov/scale
 delta=yy-variance_ratio*xx;root=math.hypot(delta,2*math.sqrt(variance_ratio)*xy)
 slope=(delta+root)/(2*xy) if delta>=0 else 2*variance_ratio*xy/(root-delta)
 intercept=my-slope*mx
 if not all(math.isfinite(v) for v in [slope,intercept]):raise ValueError("参数量级导致数值不可估计")
 residuals=[b-(intercept+slope*a) for a,b in zip(x,y)]
 return {"slope":slope,"intercept":intercept,"lambda":variance_ratio,"x_variance":vx,"y_variance":vy,"covariance":cov,"mean_x":mx,"mean_y":my,"residual_rmse_y":math.sqrt(math.fsum(r*r for r in residuals)/n),"definition":"lambda=var(y measurement error)/var(x measurement error)"}
