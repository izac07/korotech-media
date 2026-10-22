#!/usr/bin/env python3
"""Reels « fable 2D » (Mental d'Acier) : petites scènes métaphoriques au trait blanc sur fond noir, enchaînées
(9 s chacune), une phrase par scène en haut, sans voix (musique sombre générée + bruitages). La morale va dans la légende.
Plus simple et plus rapide à rendre que tools/duel3d.py (SVG, pas de 3D).

Scènes (champ "type" de chaque scène du spec, textes modifiables) :
  escalier  à genoux en bas d'un escalier (cœur brisé) ; un 2e personnage (ampoule) lui tend la main ; il se relève
            et monte la 1re marche.                                  textes : [t1, t2]
  piliers   son petit pilier face à un pilier immense (personnage doré) ; le grand disparaît, ses anciens piliers
            plus petits apparaissent : il se retourne pour voir d'où il vient.   textes : [t1, t2]
  portes    deux portes (étiquettes au-dessus, conséquence en dessous) ; il hésite puis prend celle de droite,
            d'où sort une lumière dorée.             textes : [t1, t2], portes : [gauche, gauche_apres, droite, droite_apres]
  sommet    il arrive en haut d'un grand escalier, bras levés ; en bas, quelqu'un lève la tête et commence à monter.
                                                                       textes : [t1, t2]
Usage : python3 tools/fable2d.py <spec.json> <out.mp4>     (ou <spec.json> <page.html> --html)
spec : {"id", "handle", "music_seed", "scenes": [{"type", "textes", ("portes")}, ...],
        "accent": {"base", "clair", "pale", "sombre", "mauvais"}}   (couleurs du compte ; doré de Mental d'Acier par défaut)
"""
import json, os, sys, subprocess, tempfile, shutil, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K
import duel3d as D3

SCENE_DUR = 9.0
W, H = 1080, 1920

JS = r"""
const NS='http://www.w3.org/2000/svg', svg=document.getElementById('sv');
const c=x=>Math.max(0,Math.min(1,x)), sm=x=>{x=c(x);return x*x*(3-2*x);};
const back=x=>{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const L2=(a,b,k)=>[a[0]+(b[0]-a[0])*k,a[1]+(b[1]-a[1])*k];
function el(tag,at,parent){const e=document.createElementNS(NS,tag);for(const k in at)e.setAttribute(k,at[k]);(parent||svg).appendChild(e);return e;}
const GOLD='#e8b84f', RED='#e0384a', LW=9;
// ---- personnage en bâtons : tête ronde pleine, membres au trait arrondi ; poses = points clés + IK 2D
function fig(parent,color,s){s=s||1;color=color||'#fff';const g=el('g',{},parent);
  const lim=[0,1,2,3,4].map(()=>el('polyline',{fill:'none',stroke:color,'stroke-width':LW*s,'stroke-linecap':'round','stroke-linejoin':'round'},g));
  return {g,lim,hd:el('circle',{r:24*s,fill:color},g),s};}
function ik2(S,T,a,b,bend){const dx=T[0]-S[0],dy=T[1]-S[1],d=Math.hypot(dx,dy)||1e-3,dd=Math.min(d,a+b-.01);
  const x=(a*a-b*b+dd*dd)/(2*dd),h=Math.sqrt(Math.max(0,a*a-x*x)),ux=dx/d,uy=dy/d;return [S[0]+ux*x-uy*h*bend,S[1]+uy*x+ux*h*bend];}
function draw(f,P){const s=f.s,pts=a=>a.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ');
  f.lim[0].setAttribute('points',pts([P.hip,P.sh]));
  for(let i=0;i<2;i++){const E=ik2(P.sh,P.hands[i],56*s,56*s,P.eb);f.lim[1+i].setAttribute('points',pts([P.sh,E,P.hands[i]]));
    const Kn=P.knees?P.knees[i]:ik2(P.hip,P.feet[i],62*s,62*s,P.kb);f.lim[3+i].setAttribute('points',pts([P.hip,Kn,P.feet[i]]));}
  const ux=P.sh[0]-P.hip[0],uy=P.sh[1]-P.hip[1],l=Math.hypot(ux,uy)||1;
  f.hd.setAttribute('cx',P.sh[0]+ux/l*35*s+P.look[0]);f.hd.setAttribute('cy',P.sh[1]+uy/l*35*s+P.look[1]);
  f.g.setAttribute('opacity',P.op==null?1:P.op);}
// poses locales (tournées vers la droite, sol en y=0, échelle 1) ; P() les place en (gx,gy), sens f (1 droite, -1 gauche), échelle s
const STAND={hip:[0,-124],sh:[2,-219],hands:[[-12,-128],[16,-128]],feet:[[-13,0],[13,0]]};
const KNEEL={hip:[-12,-64],sh:[38,-128],hands:[[70,-3],[58,-3]],knees:[[12,-5],[2,-5]],feet:[[-56,-3],[-64,-3]],look:[10,12]};
const REACH={hip:[0,-124],sh:[8,-217],hands:[[-10,-128],[92,-152]],feet:[[-14,0],[14,0]]};
const ARMSUP={hip:[0,-126],sh:[0,-222],hands:[[-48,-318],[48,-318]],feet:[[-20,0],[20,0]],look:[0,-4]};
const SLUMP={hip:[0,-122],sh:[14,-208],hands:[[4,-120],[20,-118]],feet:[[-12,0],[12,0]],look:[6,10]};
function walkL(ph){const a=Math.sin(ph),b=Math.abs(Math.cos(ph));
  return {hip:[0,-121-4*b],sh:[7,-215-4*b],hands:[[-22*a,-128],[22*a,-128]],feet:[[-24*a,-12*Math.max(0,a)],[24*a,-12*Math.max(0,-a)]]};}
function P(gx,gy,f,d,s,look){s=s||1;const m=p=>[gx+f*p[0]*s,gy+p[1]*s];const lk=look||d.look||[0,0];
  return {hip:m(d.hip),sh:m(d.sh),hands:d.hands.map(m),feet:d.feet.map(m),knees:d.knees?d.knees.map(m):null,look:[f*lk[0]*s,lk[1]*s],kb:-f,eb:f};}
function mix(a,b,k){if(k<=0)return a;if(k>=1)return b;const r={kb:k<.5?a.kb:b.kb,eb:k<.5?a.eb:b.eb,op:(a.op==null?1:a.op)+((b.op==null?1:b.op)-(a.op==null?1:a.op))*k};
  for(const n of ['hip','sh','look'])r[n]=L2(a[n],b[n],k);r.hands=a.hands.map((p,i)=>L2(p,b.hands[i],k));r.feet=a.feet.map((p,i)=>L2(p,b.feet[i],k));
  const ka=a.knees||null,kb2=b.knees||null;if(ka||kb2){const A_=ka||[ik2(a.hip,a.feet[0],62,62,a.kb),ik2(a.hip,a.feet[1],62,62,a.kb)],B_=kb2||[ik2(b.hip,b.feet[0],62,62,b.kb),ik2(b.hip,b.feet[1],62,62,b.kb)];
    r.knees=A_.map((p,i)=>L2(p,B_[i],k));}
  return r;}
// enchaînement : [début, pose (ou fonction du temps), durée de transition]
function seq(t,K){let p=typeof K[0][1]=='function'?K[0][1](t):K[0][1];
  for(let i=1;i<K.length;i++){const [t0,Q,d]=K[i];if(t<=t0)break;p=mix(p,typeof Q=='function'?Q(t):Q,sm((t-t0)/d));}return p;}
// ---- décors
function line(x1,y1,x2,y2,g,w){return el('line',{x1,y1,x2,y2,stroke:'#fff','stroke-width':w||6,'stroke-linecap':'round'},g);}
function stairs(g,x0,y0,w,h,n,xend){let d=`M 0 ${y0} L ${x0} ${y0}`;for(let i=0;i<n;i++)d+=` L ${x0+i*w} ${y0-(i+1)*h} L ${x0+(i+1)*w} ${y0-(i+1)*h}`;
  if(xend)d+=` L ${xend} ${y0-n*h}`;return el('path',{d,fill:'none',stroke:'#fff','stroke-width':6,'stroke-linejoin':'round'},g);}
function stairY(x,x0,y0,w,h,n){return y0-h*c((x-x0+w*.35)/w*1)*0-h*Math.max(0,Math.min(n,Math.floor((x-x0)/w)+1))*(x>=x0?1:0);}
function heart(g){const h=el('g',{},g);
  const l=el('path',{d:'M0,-20 C-30,-46 -52,-6 0,30 L-7,16 L4,4 L-6,-8 Z',fill:RED},h),r=el('path',{d:'M0,-20 C30,-46 52,-6 0,30 L-7,16 L4,4 L-6,-8 Z',fill:RED},h);return {h,l,r};}
function setHeart(o,x,y,s,broken,op){o.h.setAttribute('transform',`translate(${x},${y}) scale(${s})`);o.h.setAttribute('opacity',op);
  o.l.setAttribute('transform',`translate(${-7*broken},${2*broken}) rotate(${-12*broken})`);o.r.setAttribute('transform',`translate(${7*broken},${-2*broken}) rotate(${10*broken})`);}
function bulb(g){const b=el('g',{},g);el('circle',{r:70,fill:'url(#glowGold)'},b);el('circle',{r:19,fill:'#f5c84b'},b);el('rect',{x:-9,y:16,width:18,height:12,rx:3,fill:'#bbb'},b);return b;}
// ---- textes (une ligne en haut par scène)
const TX=[...document.querySelectorAll('.tx')];
function texts(t){for(const e of TX){const a=+e.dataset.a,b=+e.dataset.b;const k=sm((t-a)/.35),o=t<b?k:1-sm((t-b)/.3);e.style.opacity=o;e.style.transform=`translateY(${(1-k)*16}px)`;}}
const SCENES=[];
"""

ESCALIER = r"""
SCENES.push((function(T0){const g=el('g',{opacity:0});
  const X0=560,Y0=1150,SW=95,SH=85,N=5;stairs(g,X0,Y0,SW,SH,N,1080);
  const hr=heart(g),bl=bulb(g),A=fig(g),B=fig(g);
  function gyA(x){return x<X0?Y0:Y0-SH*Math.min(N,Math.floor((x-X0)/SW)+1);}
  return {g,T0,draw(t){
    // A : à genoux, se relève quand B lui tend la main, puis monte la 1re marche
    const ax=6.8<t?330+sm((t-6.8)/1.8)*300:330, ay=t<7.6?Y0:Y0-SH*sm((t-7.6)/.5);
    const pa=seq(t,[[0,P(330,Y0,1,KNEEL)],[5.6,P(330,Y0,1,SLUMP),.6],[6.2,P(330,Y0,1,STAND),.5],[6.8,u=>P(ax,ay,1,walkL((u-6.8)*9)),.3],[8.6,P(630,Y0-SH,1,STAND),.3]]);
    draw(A,pa);
    const mend=sm((t-6.3)/.5);setHeart(hr,pa.sh[0]+10,pa.sh[1]-110,1.6+.25*back(c((t-6.3)/.4))-.25*c((t-6.7)/.3),1-mend,c(t/.3)*(1-sm((t-7.6)/.5)));
    // B : arrive en marchant (ampoule au-dessus de la tête), tend la main
    const bx=t<2.4?-80:-80+sm((t-2.4)/2)*265;
    const pb=seq(t,[[0,P(-80,Y0,1,STAND)],[2.4,u=>P(bx,Y0,1,walkL((u-2.4)*9)),.2],[4.4,P(185,Y0,1,STAND),.3],[4.7,P(185,Y0,1,REACH),.5]]);
    draw(B,pb);bl.setAttribute('transform',`translate(${pb.sh[0]},${pb.sh[1]-115}) scale(${back(c((t-3.2)/.4))})`);
  }};})(0));
"""

PILIERS = r"""
SCENES.push((function(T0){const g=el('g',{opacity:0});
  const GY=1450;line(0,GY,1080,GY,g);
  const past=[[60,70],[175,130],[290,190],[405,250]].map(([x,h])=>el('rect',{x,y:GY,width:90,height:0,fill:'url(#pil)'},g));
  el('rect',{x:540,y:GY-310,width:120,height:310,fill:'url(#pil)'},g);
  const big=el('g',{},g);el('rect',{x:760,y:GY-780,width:150,height:780,fill:'url(#pil)'},big);
  const me=fig(g,'#fff',.8),oth=fig(big,GOLD,.8);
  return {g,T0,draw(t){
    const fade=1-sm((t-4.3)/1.0);big.setAttribute('opacity',fade);
    draw(oth,P(835,GY-780,-1,STAND,.8));
    // il regarde le grand pilier, baisse la tête, puis se retourne vers ses anciens piliers
    const f=t<6.0?1:-1;
    const pm=seq(t,[[0,P(600,GY-310,1,STAND,.8)],[1.0,P(600,GY-310,1,STAND,.8,[6,-12]),.5],[3.0,P(600,GY-310,1,SLUMP,.8),.6],[6.0,P(600,GY-310,-1,STAND,.8,[2,-2]),.4],[7.2,P(600,GY-310,-1,SLUMP,.8,[4,6]),.5],[7.8,P(600,GY-310,-1,STAND,.8),.6]]);
    draw(me,pm);
    [[60,70],[175,130],[290,190],[405,250]].forEach(([x,h],i)=>{const k=back(c((t-4.9-i*.3)/.5));past[i].setAttribute('y',GY-h*k);past[i].setAttribute('height',Math.max(0,h*k));});
  }};})(0));
"""

PORTES = r"""
SCENES.push((function(T0){const g=el('g',{opacity:0});
  const GY=1350;line(0,GY,1080,GY,g);
  const doors=[150,690].map(x=>{const d=el('g',{},g);
    const glow=el('rect',{x,y:GY-450,width:240,height:450,fill:'url(#glowDoor)',opacity:0},d);
    el('rect',{x,y:GY-450,width:240,height:450,fill:'none',stroke:'#fff','stroke-width':6},d);
    const pan=el('polygon',{fill:'#0b0b0b',stroke:'#fff','stroke-width':6,'stroke-linejoin':'round'},d);
    const knob=el('circle',{r:9,fill:'#fff'},d);return {x,glow,pan,knob};});
  function setDoor(o,open){const x=o.x,w=240*(1-.82*open),sk=40*open;
    o.pan.setAttribute('points',`${x},${GY-450} ${x+w},${GY-450-sk} ${x+w},${GY+sk*.2} ${x},${GY}`);
    o.knob.setAttribute('cx',x+w-28*(1-open));o.knob.setAttribute('cy',GY-225);o.glow.setAttribute('opacity',open);}
  const F=fig(g);const LB=[...document.querySelectorAll('.dl')];
  return {g,T0,draw(t){
    setDoor(doors[0],0);setDoor(doors[1],sm((t-5.8)/.8));
    const gx=t<5.0?540:540+sm((t-5.0)/1.6)*270, inn=sm((t-6.9)/.9);
    const look=t<1.2?1:(t<2.2?-1:(t<3.2?1:(t<4.2?-1:1)));
    const pf=seq(t,[[0,P(540,GY,1,STAND)],[1.2,P(540,GY,-1,STAND),.25],[2.2,P(540,GY,1,STAND),.25],[3.2,P(540,GY,-1,SLUMP),.3],[4.2,P(540,GY,1,STAND),.3],
      [5.0,u=>P(gx,GY,1,walkL((u-5)*9)),.25],[6.6,u=>{const p=P(810,GY,1,STAND);p.op=1-inn;return p;},.3]]);
    draw(F,pf);
    LB.forEach((e,i)=>{const a=i<2?.4:3.6;e.style.opacity=(t>=a?sm((t-a)/.4):0)*(1-sm((t-8.5)/.4));});
  }};})(0));
"""

SOMMET = r"""
SCENES.push((function(T0){const g=el('g',{opacity:0});
  const X0=120,Y0=1450,SW=110,SH=95,N=7;stairs(g,X0,Y0,SW,SH,N,1080);
  const halo=el('circle',{r:170,fill:'url(#glowGold)',opacity:0},g);
  const A=fig(g),C=fig(g);
  function sy(x){return x<X0?Y0:Y0-SH*Math.min(N,Math.floor((x-X0)/SW)+1);}
  function climb(x0,x1,t0,t1,t){const k=sm((t-t0)/(t1-t0));const x=x0+(x1-x0)*k;const y=sy(x-SW*.15)*(1-.5)+sy(x+SW*.25)*.5;return [x,y];}
  return {g,T0,draw(t){
    const [ax,ay]=climb(560,945,0,2.6,t);
    const pa=seq(t,[[0,u=>{const [x,y]=climb(560,945,0,2.6,u);return P(x,y,1,walkL(u*8));}],[2.6,P(945,Y0-N*SH,1,STAND),.3],[2.9,P(945,Y0-N*SH,1,ARMSUP),.5],[6.0,P(945,Y0-N*SH,-1,STAND,1,[-4,10]),.6]]);
    draw(A,pa);halo.setAttribute('cx',945);halo.setAttribute('cy',Y0-N*SH-170);halo.setAttribute('opacity',.9*sm((t-2.9)/.6));
    const pc=seq(t,[[0,(()=>{const p=P(40,Y0,1,STAND);p.op=0;return p;})()],[3.6,P(40,Y0,1,STAND),.5],[4.4,P(40,Y0,1,STAND,1,[6,-16]),.5],
      [6.2,u=>{const [x,y]=climb(40,300,6.2,8.6,u);return P(x,y,1,walkL((u-6.2)*8));},.3]]);
    draw(C,pc);
  }};})(0));
"""

LIB = {"escalier": ESCALIER, "piliers": PILIERS, "portes": PORTES, "sommet": SOMMET}


def page(spec):
    fonts = K._font_faces(["Inter", "JetBrains Mono"])
    sc = spec["scenes"]; total = SCENE_DUR * len(sc)
    tx, dl = "", ""
    for k, s in enumerate(sc):
        t0 = k * SCENE_DUR; tt = s.get("textes", [])
        cuts = [.3, 4.8 if s["type"] != "portes" else 6.8][: len(tt)]
        for j, txt in enumerate(tt):
            a = t0 + cuts[j]; b = t0 + (cuts[j + 1] - .4 if j + 1 < len(tt) else SCENE_DUR - .35)   # la 1re phrase sort avant que la 2e entre
            tx += f"<div class='tx' data-a='{a:.2f}' data-b='{b:.2f}'>{K.esc(txt)}</div>"
        if s["type"] == "portes":
            g, ga, d, da = s["portes"]
            dl += (f"<div class='dl up' style='left:90px;width:360px'>{K.esc(g)}</div><div class='dl up' style='left:630px;width:360px'>{K.esc(d)}</div>"
                   f"<div class='dl dn' style='left:90px;width:360px;color:__MAUVAIS__'>{K.esc(ga)}</div><div class='dl dn' style='left:640px;width:310px;color:#e8b84f'>{K.esc(da)}</div>")
    js = JS + "".join(LIB[s["type"]] for s in sc)
    html = f"""<!doctype html><html><head><meta charset='utf-8'><style>{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:#000;overflow:hidden;position:relative;color:#fff;font-family:Inter,sans-serif}}
svg{{position:absolute;left:0;top:0}}
.tx{{position:absolute;left:50px;right:50px;top:330px;text-align:center;font:600 50px/1.2 Inter;opacity:0}}
.dl{{position:absolute;text-align:center;font:700 30px 'JetBrains Mono';letter-spacing:0;white-space:nowrap;opacity:0}}
.dl.up{{top:850px}} .dl.dn{{top:1380px;font-weight:600;font-size:30px}}
.hd{{position:absolute;left:0;right:0;top:250px;text-align:center;font:400 30px 'JetBrains Mono';letter-spacing:10px;color:#3a3a3a}}
#noir{{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none}}
</style></head><body>
<svg id='sv' width='{W}' height='{H}' viewBox='0 0 {W} {H}'><defs>
<linearGradient id='pil' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#a5a5a5'/><stop offset='1' stop-color='#0d0d0d'/></linearGradient>
<radialGradient id='glowGold'><stop offset='0' stop-color='#ffd877' stop-opacity='.85'/><stop offset='.45' stop-color='#e8b84f' stop-opacity='.25'/><stop offset='1' stop-color='#e8b84f' stop-opacity='0'/></radialGradient>
<radialGradient id='glowDoor' cx='.5' cy='.6' r='.7'><stop offset='0' stop-color='#fff2c4'/><stop offset='.6' stop-color='#e8b84f'/><stop offset='1' stop-color='#6b4d12'/></radialGradient>
</defs></svg>
{tx}{dl}
<div class='hd'>{K.esc(spec['handle']).upper()}</div>
<div id='noir'></div>
<script>{js}
const SD={SCENE_DUR}, D={total};
window.render=function(t){{
  document.querySelectorAll('.dl').forEach(e=>e.style.opacity=0);   // étiquettes des portes : seulement dans leur scène
  SCENES.forEach((s,k)=>{{const a=k*SD,on=t>=a&&t<a+SD;s.g.setAttribute('opacity',on?1:0);if(on)s.draw(t-a);}});
  texts(t);
  // fondu au noir entre deux scènes et en fin de boucle
  let n=0;for(let k=1;k<=SCENES.length;k++){{const b=k*SD;n=Math.max(n,1-Math.min(1,Math.abs(t-b)/.35));}}
  if(t<.15)n=Math.max(n,1-t/.15);document.getElementById('noir').style.opacity=n;
}};render(0);
</script></body></html>"""
    # couleurs du compte : l'accent doré par défaut (Mental d'Acier) est remplacé par celui du spec (« accent »)
    pal = {"base": "#e8b84f", "clair": "#ffd877", "pale": "#fff2c4", "sombre": "#6b4d12", "mauvais": "#e0384a"} | spec.get("accent", {})
    for ancien, cle in (("#e8b84f", "base"), ("#ffd877", "clair"), ("#f5c84b", "clair"), ("#fff2c4", "pale"), ("#6b4d12", "sombre"), ("__MAUVAIS__", "mauvais")):
        html = html.replace(ancien, pal[cle])
    return html, total


def sfx(path, spec, total):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, lfilter
    SR = 48000; n = int(SR * (total + 1)); out = np.zeros(n); rng = np.random.default_rng(11)
    def put(sig, t0, g=1.0):
        i = int(max(0, t0) * SR); j = min(n, i + len(sig)); out[i:j] += sig[: j - i] * g
    def band(lo, hi, d):
        b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, rng.standard_normal(int(d * SR)))
    tw = np.arange(int(.5 * SR)) / SR; whoosh = band(400, 5000, .5) * np.sin(np.pi * tw / tw[-1]) ** 2 * .28
    tp = np.arange(int(.12 * SR)) / SR; pop = np.sin(2 * np.pi * (700 + 500 * np.exp(-tp * 40)) * tp) * np.exp(-tp * 40) * .3
    tc = np.arange(int(1.4 * SR)) / SR; chime = sum(np.sin(2 * np.pi * f * tc) * np.exp(-tc * 3) for f in (880, 1320, 1760)) * .05
    tk = np.arange(int(.05 * SR)) / SR; step = band(150, 1200, .05) * np.exp(-tk * 60) * .25
    for k, s in enumerate(spec["scenes"]):
        t0 = k * SCENE_DUR
        if k: put(whoosh, t0 - .3)
        ty = s["type"]
        if ty == "escalier":
            put(pop, t0 + .3); put(pop, t0 + 3.2); put(chime, t0 + 6.3, .8)
            for q in np.arange(2.4, 4.4, .35): put(step, t0 + q, .6)
            for q in np.arange(6.8, 8.6, .35): put(step, t0 + q)
        elif ty == "piliers":
            for i in range(4): put(pop, t0 + 4.9 + i * .3, .7)
        elif ty == "portes":
            for q in np.arange(5.0, 6.6, .35): put(step, t0 + q)
            put(whoosh, t0 + 5.8, .9); put(chime, t0 + 6.2, .7)
        elif ty == "sommet":
            for q in np.arange(0, 2.6, .39): put(step, t0 + q)
            put(chime, t0 + 2.9)
            for q in np.arange(6.2, 8.6, .39): put(step, t0 + q, .7)
    out = np.clip(out, -1, 1); wavfile.write(path, SR, (np.stack([out, out], 1) * 32767).astype(np.int16))


def build(spec_path, out):
    spec = json.load(open(spec_path, encoding="utf-8")); tmp = tempfile.mkdtemp()
    html, total = page(spec)
    hp = os.path.join(tmp, "p.html"); open(hp, "w", encoding="utf-8").write(html)
    try:  # audit automatique (texte trop petit, hors zones sûres) : avertit sans bloquer
        import audit as A
        A.afficher(A.auditer(hp, [k * SCENE_DUR for k in range(len(spec["scenes"]))], total), spec_path)
    except Exception as e:
        print("audit non réalisé :", e)
    fr = os.path.join(tmp, "fr"); os.makedirs(fr)
    asyncio.run(K._frames(hp, fr, total))
    v = os.path.join(tmp, "v.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{fr}/f_%04d.jpg", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", v], check=True)
    mu = os.path.join(tmp, "m.wav"); D3.musique(mu, total, int(spec.get("music_seed", 0)), pulse=spec.get("pulse", True))
    fx = os.path.join(tmp, "fx.wav"); sfx(fx, spec, total)
    fc = (f"[1]atrim=0:{total},volume=0.6[m];[2]atrim=0:{total}[f];"
          f"[m][f]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5,alimiter=limit=0.95,apad=whole_dur={total+3},atrim=0:{total}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", mu, "-i", fx, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)
    return total


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[3] == "--html":
        open(sys.argv[2], "w", encoding="utf-8").write(page(json.load(open(sys.argv[1], encoding="utf-8")))[0]); print("html")
    else:
        print("duration", build(sys.argv[1], sys.argv[2]))
