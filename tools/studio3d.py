#!/usr/bin/env python3
"""Layout « studio3d » (PILOTE 24/10/2026, L'IA Entrepreneur) : une petite scène 3D low poly qui raconte le reel.
Bureau de nuit (ville par la fenêtre, horloge, tasse), mascotte cube « Claude » posée sur le bureau, écran dont
l'interface change selon la scène, téléphone pour la fin ; la caméra va d'un plan à l'autre. Par-dessus : bandeau
titre en papier, badge compteur, sous-titres en étiquettes (un mot par étiquette, au rythme de la voix), tampon
et confettis. Appelé par tools/motion.py (layout "studio3d") : voix, musique, bruitages et contrôle sont communs.

Scènes : {"type": plan ("large" | "ecran" | "mascotte" | "telephone"), "vo", "bandeau",
          "ecran": {"type": "bazar"|"chat"|"montage"|"verif"|"export", "titre"?, "messages"?: [["moi"|"ia", texte]], "lignes"?: [..]},
          "compteur"?: {"label", "de", "a"}, "humeur"?: "fatigue"|"normal"|"travail"|"content", "tampon"?: "PRÊT À POSTER"}
"""
import json, os, html as H
import korotech as K

DOSSIER = os.path.dirname(os.path.abspath(__file__))

TPL = r"""<!doctype html><html><head><meta charset='utf-8'><style>__FONTS__
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:__NUIT__;position:relative}
canvas#cv{position:absolute;left:0;top:0}
.hdl{position:absolute;left:56px;top:70px;font:700 32px Inter;color:#fff;opacity:.55;z-index:5}
.band{position:absolute;left:50%;top:235px;transform:translateX(-50%);z-index:6;white-space:nowrap;opacity:0}
.band span{display:block;background:__PAPIER__;color:__ENCRE__;font:400 76px/1 Anton;letter-spacing:1px;text-transform:uppercase;padding:22px 64px 18px;
  box-shadow:0 10px 0 rgba(0,0,0,.25);clip-path:polygon(0 0,100% 0,96% 50%,100% 100%,0 100%,4% 50%)}
.badge{position:absolute;right:120px;top:390px;z-index:6;background:#fff;border:5px solid __ENCRE__;border-radius:18px;padding:10px 22px 6px;
  display:flex;align-items:baseline;gap:16px;box-shadow:6px 6px 0 __ENCRE__;opacity:0;transform:rotate(3deg)}
.badge b{font:400 34px Anton;color:__ENCRE__;letter-spacing:1px}.badge i{font:400 92px/1 Anton;font-style:normal;color:__ACC__;font-variant-numeric:tabular-nums}
.caps{position:absolute;left:70px;right:120px;top:1180px;z-index:7;display:flex;flex-wrap:wrap;justify-content:center;gap:12px 14px}
.cap{display:none;flex-wrap:wrap;justify-content:center;gap:12px 14px}
.stk{display:inline-block;font:400 70px/1.1 'Archivo Black';padding:8px 18px 10px;border-radius:10px;box-shadow:5px 5px 0 __ENCRE__;opacity:0}
.stk.o{background:__ACC__;color:#fff}.stk.y{background:__JAUNE__;color:__ENCRE__}
.tampon{position:absolute;left:50%;top:960px;z-index:8;transform:translateX(-50%) rotate(-7deg);border:9px solid __VERT__;color:__VERT__;border-radius:18px;
  padding:8px 34px 4px;font:400 104px/1 Anton;letter-spacing:2px;white-space:nowrap;opacity:0;background:rgba(10,14,30,.55)}
.fin{position:absolute;left:90px;right:140px;top:640px;z-index:8;display:flex;flex-direction:column;align-items:center;gap:22px;opacity:0}
.fin b{font:400 112px/1 Anton;background:__ACC__;color:#fff;padding:16px 44px 10px;border-radius:18px;box-shadow:8px 8px 0 __ENCRE__;transform:rotate(-2deg)}
.fin span{font:400 54px/1.15 'Archivo Black';background:__JAUNE__;color:__ENCRE__;padding:10px 26px;border-radius:12px;box-shadow:6px 6px 0 __ENCRE__;text-align:center;transform:rotate(1.5deg)}
.cf{position:absolute;width:18px;height:26px;z-index:4;opacity:0}
</style></head><body>
<canvas id='cv' width='1080' height='1920'></canvas>
<div class='hdl'>@__HANDLE__</div>
__BANDS__
__BADGES__
<div class='caps'>__CAPS__</div>
__TAMPONS__
__FINS__
__CONFETTIS__
<script>__THREE__</script>
<script>
const EV=__EV__; const D=__D__, SC=__SC__, COL=__COL__;
const c=x=>Math.max(0,Math.min(1,x)), sm=x=>{x=c(x);return x*x*(3-2*x);}, eo=x=>1-Math.pow(1-c(x),3);
const back=x=>{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const $=i=>document.getElementById(i);
const LIN=c_=>new THREE.Color(c_).convertSRGBToLinear();
const R=new THREE.WebGLRenderer({canvas:$('cv'),antialias:true,preserveDrawingBuffer:true});
R.setSize(1080,1920,false);R.outputEncoding=THREE.sRGBEncoding;
const scene=new THREE.Scene();scene.background=LIN(COL.nuit);scene.fog=new THREE.Fog(LIN(COL.nuit),16,34);
scene.add(new THREE.HemisphereLight(0xa9b8ff,0x3a2414,.45));
const key=new THREE.DirectionalLight(0xffe0bf,.95);key.position.set(-3,6,5);scene.add(key);
const rim=new THREE.DirectionalLight(0x7f95ff,.55);rim.position.set(4,3,-3);scene.add(rim);
const lamp=new THREE.PointLight(0xffa860,.9,7);lamp.position.set(1.9,2.6,.8);scene.add(lamp);
const GRAD=new THREE.DataTexture(new Uint8Array([110,185,255]),3,1,THREE.RedFormat);GRAD.minFilter=GRAD.magFilter=THREE.NearestFilter;GRAD.needsUpdate=true;
const toon=c_=>new THREE.MeshToonMaterial({color:LIN(c_),gradientMap:GRAD});
const OLM=new THREE.MeshBasicMaterial({color:0x0b0d1a,side:THREE.BackSide});
function mk(geo,mat,x,y,z,parent,ol){const m=new THREE.Mesh(geo,mat);m.position.set(x,y,z);(parent||scene).add(m);
  if(ol){const o=new THREE.Mesh(geo,OLM);o.scale.setScalar(ol);m.add(o);}return m;}
const B=(w,h,d)=>new THREE.BoxGeometry(w,h,d);
function canvasTex(w,h){const cv=document.createElement('canvas');cv.width=w;cv.height=h;const t=new THREE.CanvasTexture(cv);t.encoding=THREE.sRGBEncoding;t.userData={cv,x:cv.getContext('2d')};return t;}
let seed=7;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};
// ---- pièce : sol, mur, fenêtre sur la ville la nuit
mk(new THREE.PlaneGeometry(40,40),toon(COL.sol),0,0,0).rotation.x=-Math.PI/2;
mk(new THREE.PlaneGeometry(40,14),toon(COL.mur),0,6,-3.3);
const city=canvasTex(1024,700);{const x=city.userData.x;const g=x.createLinearGradient(0,0,0,700);g.addColorStop(0,'#0b0f2b');g.addColorStop(1,'#3a2a6a');x.fillStyle=g;x.fillRect(0,0,1024,700);
  for(const [cl,hmin,hmax,lit] of [['#1a1f48',250,520,.25],['#252b5e',150,420,.45]]){let px=-20;while(px<1024){const w=60+rnd()*110,h=hmin+rnd()*(hmax-hmin);x.fillStyle=cl;x.fillRect(px,700-h,w,h);
    for(let wy=700-h+18;wy<690;wy+=34)for(let wx=px+12;wx<px+w-16;wx+=26){x.fillStyle=rnd()<lit?'#ffd27a':'#2f3770';x.fillRect(wx,wy,12,18);}px+=w+6;}}}
mk(new THREE.PlaneGeometry(7.4,5),new THREE.MeshBasicMaterial({map:city}),0,3.5,-3.25);
for(const [w,h,x,y] of [[7.8,.22,0,6.05],[7.8,.22,0,.95],[.22,5.3,-3.8,3.5],[.22,5.3,3.8,3.5],[.12,5,0,3.5],[7.6,.1,0,3.5]])mk(B(w,h,.18),toon(COL.cadre),x,y,-3.2);
// horloge
const clock=new THREE.Group();clock.position.set(-2.2,4.7,-3.05);scene.add(clock);
mk(new THREE.CylinderGeometry(.55,.55,.08,40),toon(0xf3e6cf),0,0,0,clock,1.06).rotation.x=Math.PI/2;
const hh=mk(B(.06,.3,.02),toon(0x1b1b22),0,.12,.06,clock),mh=mk(B(.04,.44,.02),toon(0x1b1b22),0,.19,.07,clock);
const hhP=new THREE.Group();clock.add(hhP);hhP.add(hh);const mhP=new THREE.Group();clock.add(mhP);mhP.add(mh);
// ---- bureau
mk(B(4.4,.16,1.8),toon(COL.bois),0,1.0,0,null,1.02);
mk(B(4.4,.95,.08),toon(COL.bois2),0,.5,.86);
// écran
mk(B(.14,.45,.14),toon(0x2a2e44),.75,1.3,-.5);mk(B(.6,.05,.4),toon(0x2a2e44),.75,1.1,-.5);
mk(B(2.05,1.3,.1),toon(0x1a1d2e),.75,2.05,-.55,null,1.02);
const scr=canvasTex(1024,640);mk(new THREE.PlaneGeometry(1.9,1.19),new THREE.MeshBasicMaterial({map:scr}),.75,2.05,-.495);
// tasse, livres
mk(new THREE.CylinderGeometry(.14,.12,.3,24),toon(COL.tasse),1.85,1.23,.35,null,1.06);
mk(new THREE.TorusGeometry(.08,.025,10,20),toon(COL.tasse),2.0,1.24,.35);
[0x4f7cff,0xffd23f,0xff6b6b,0x2fd36b].forEach((cl,i)=>mk(B(.7-i*.05,.1,.45),toon(cl),-1.75,1.13+i*.105,.15,null,1.04).rotation.y=(i%2?.12:-.08));
// ---- mascotte « Claude »
const M=new THREE.Group();M.position.set(-.8,1.08,-.15);scene.add(M);
const body=mk(B(1.05,.95,.85),toon(COL.mascotte),0,.475,0,M,1.04);
const eyes=[],lids=[],pups=[];
for(const sx of [-1,1]){const e=mk(B(.24,.28,.02),new THREE.MeshBasicMaterial({color:0xffffff}),sx*.22,.56,.43,M);eyes.push(e);
  pups.push(mk(B(.1,.15,.02),new THREE.MeshBasicMaterial({color:0x14141e}),sx*.22+.02,.54,.442,M));
  lids.push(mk(B(.26,.3,.03),toon(COL.mascotte),sx*.22,.72,.445,M));}
const mouth=mk(B(.18,.045,.02),new THREE.MeshBasicMaterial({color:0x14141e}),0,.32,.435,M);
for(const sx of [-1,1])mk(B(.12,.06,.02),new THREE.MeshBasicMaterial({color:0xff9a8a}),sx*.36,.38,.432,M);
const arms=[-1,1].map(sx=>{const p=new THREE.Group();p.position.set(sx*.6,.62,.05);M.add(p);mk(B(.15,.42,.15),toon(COL.mascotte),0,-.19,0,p,1.08);return p;});
// ---- téléphone (fin)
const P=new THREE.Group();P.position.set(-.05,1.08,.5);scene.add(P);
mk(B(.7,1.3,.07),toon(0x111320),0,.65,0,P,1.03);
const ph=canvasTex(420,780);const phs=mk(new THREE.PlaneGeometry(.62,1.16),new THREE.MeshBasicMaterial({map:ph}),0,.66,.036,P);
// ---- confettis 3D (en plus des confettis CSS)
const CAM=new THREE.PerspectiveCamera(36,1080/1920,.1,60);
const PLANS={large:[[-.1,2.5,8.6],[-.1,1.85,-.4]],ecran:[[.75,2.0,4.6],[.75,1.9,-.5]],mascotte:[[-.6,1.9,5.0],[-.6,1.55,-.15]],telephone:[[-.05,1.9,3.9],[-.05,1.6,.5]]};
const V=(a)=>new THREE.Vector3(a[0],a[1],a[2]);
function plan(k){return PLANS[SC[k].plan]||PLANS.large;}
// ---- dessin de l'écran selon la scène
function rr(x,X,Y,W,H,r,f){x.beginPath();x.roundRect(X,Y,W,H,r);x.fillStyle=f;x.fill();}
function screenDraw(k,p,t){const s=SC[k].ecran||{type:'vide'};const x=scr.userData.x;x.fillStyle='#0f1222';x.fillRect(0,0,1024,640);
  x.fillStyle='#1a1e36';x.fillRect(0,0,1024,56);['#ff5f57','#febc2e','#28c840'].forEach((cl,i)=>{x.beginPath();x.arc(34+i*30,28,10,0,7);x.fillStyle=cl;x.fill();});
  x.fillStyle='#9aa3c7';x.font='600 26px Inter';x.fillText(s.titre||'Claude',140,37);
  const T=s.type;
  if(T=='bazar'){for(let i=0;i<14;i++){const y=90+i*36;let X=40;for(let j=0;j<6;j++){const w=40+((i*7+j*13)%9)*16+Math.sin(t*3+i+j)*8;rr(x,X,y,w,22,6,['#ff6b6b','#ffd23f','#4f7cff','#2fd36b','#c56bff'][(i+j)%5]);X+=w+10;}}
    x.fillStyle='#ff6b6b';x.font='700 30px Inter';x.fillText('Rendu… '+Math.floor(12+p*70)+' %  (reste '+Math.max(1,5-Math.floor(p*4))+' h)',40,612);}
  if(T=='chat'){let y=90;const ms=s.messages||[];const per=1/Math.max(1,ms.length);
    ms.forEach((m,i)=>{const q=c((p-i*per)/(per*.8));if(q<=0)return;const txt=m[1].slice(0,Math.ceil(m[1].length*q));x.font='600 34px Inter';
      const lines=[];let cur='';for(const w of txt.split(' ')){if(x.measureText(cur+' '+w).width>620){lines.push(cur);cur=w;}else cur=cur?cur+' '+w:w;}lines.push(cur);
      const h=30+lines.length*44, W=Math.min(700,Math.max(...lines.map(l=>x.measureText(l).width))+56), X=m[0]=='moi'?1024-W-40:40;
      rr(x,X,y,W,h,26,m[0]=='moi'?COL.acc:'#232842');x.fillStyle='#fff';lines.forEach((l,j)=>x.fillText(l,X+28,y+52+j*44));y+=h+24;});}
  if(T=='montage'){rr(x,362,76,300,230,14,'#232842');rr(x,452,120,120,130,20,COL.mascotte);x.fillStyle='#fff';x.fillRect(478,160,22,28);x.fillRect(524,160,22,28);
    const tr=[['V1',COL.acc],['A1','#4f7cff'],['TXT',COL.jaune]];tr.forEach(([n,cl],i)=>{const y=350+i*82;x.fillStyle='#7e86ad';x.font='700 26px Inter';x.fillText(n,30,y+36);
      const nb=Math.floor(c(p*1.3-i*.12)*7);for(let j=0;j<nb;j++)rr(x,110+j*126,y+8,112,46,8,cl);});
    const ph_=110+c(p)*880;x.fillStyle='#fff';x.fillRect(ph_,330,4,280);
    x.font='700 28px Inter';x.fillStyle='#2fd36b';const tags=['✓ coupes','✓ sous-titres','✓ musique sous la voix'];tags.forEach((g,i)=>{if(p>.25+i*.22)x.fillText(g,700,110+i*52);});}
  if(T=='verif'){(s.lignes||[]).forEach((l,i)=>{const y=110+i*104;const q=p>(i+.5)/((s.lignes||[]).length+.5);rr(x,60,y,904,80,16,'#1a1e36');
      x.font='600 36px Inter';x.fillStyle='#e6e9ff';x.fillText(l,140,y+52);x.beginPath();x.arc(96,y+40,22,0,7);x.fillStyle=q?'#2fd36b':'#3a4066';x.fill();
      if(q){x.strokeStyle='#0f1222';x.lineWidth=6;x.beginPath();x.moveTo(86,y+40);x.moveTo(84,y+40);x.lineTo(94,y+50);x.lineTo(110,y+30);x.stroke();}});}
  if(T=='export'){const q=c(p*1.4);rr(x,160,220,704,190,24,'#1a1e36');x.fillStyle='#fff';x.font='700 40px Inter';x.fillText(q<1?'Export 9:16…':'Export terminé ✓',200,290);
    rr(x,200,320,624,34,17,'#3a4066');rr(x,200,320,624*q,34,17,q<1?COL.acc:'#2fd36b');x.font='700 30px Inter';x.fillStyle='#9aa3c7';x.fillText(Math.round(q*100)+' %',200,392);}
  scr.needsUpdate=true;}
function phoneDraw(p,t){const x=ph.userData.x;const g=x.createLinearGradient(0,0,0,780);g.addColorStop(0,'#7b5cff');g.addColorStop(1,'#ff5fa2');x.fillStyle=g;x.fillRect(0,0,420,780);
  rr(x,150,230,120,110,26,COL.mascotte);x.fillStyle='#fff';x.fillRect(176,268,20,26);x.fillRect(224,268,20,26);
  rr(x,130,380,160,44,10,COL.jaune);x.fillStyle='#1b2147';x.font='800 24px Inter';x.fillText('MA VIDÉO',150,410);
  x.fillStyle='#fff';x.font='800 30px Inter';x.fillText('♥ '+(1+Math.floor(eo(p)*120)/10).toFixed(1)+' k',150,500);
  rr(x,110,620,200,64,32,'#2fd36b');x.fillStyle='#fff';x.font='800 32px Inter';x.fillText('POSTÉ ✓',140,664);ph.needsUpdate=true;}
const CF=[...document.querySelectorAll('.cf')];
window.render=function(t){
  let k=0;SC.forEach((s,i)=>{if(t>=s.a)k=i;});const s=SC[k],p=c((t-s.a)/Math.max(.1,s.b-s.a)),tl=t-s.a;
  // caméra : glisse du plan précédent au plan de la scène, avec une petite respiration
  const to=plan(k),fr=k>0?plan(k-1):[[to[0][0],to[0][1]+.3,to[0][2]*1.12],to[1]];const q=sm(tl/.8);
  CAM.position.copy(V(fr[0]).lerp(V(to[0]),q)).add(new THREE.Vector3(Math.sin(t*.5)*.08,Math.sin(t*.7)*.04,-p*.25));
  CAM.lookAt(V(fr[1]).lerp(V(to[1]),q));
  // horloge (les heures défilent pendant la scène « bazar »)
  const sp=(s.ecran&&s.ecran.type=='bazar')?2.2:.05;hhP.rotation.z=-t*sp/12;mhP.rotation.z=-t*sp;
  // mascotte selon l'humeur
  const hu=s.humeur||'normal';const tired=hu=='fatigue'?1:0;
  lids.forEach(l=>{l.position.y=.72-(tired?.12:0)-((t%3.3)<.12?.17:0);});
  pups.forEach((pp,i)=>{pp.position.x=(i?1:-1)*.22+.02+Math.sin(t*.9)*.015*(1-tired);pp.position.y=.54-(tired?.05:0);});
  body.rotation.z=tired?Math.sin(t*1.2)*.04:0;M.position.y=1.08+(hu=='content'?Math.abs(Math.sin(t*6))*.12:0);M.rotation.y=hu=='travail'?.32:(hu=='content'?Math.sin(t*3)*.12:.12);
  mouth.scale.set(hu=='content'?1.6:1,hu=='content'?2.4:(tired?.7:1),1);
  arms.forEach((a,i)=>{a.rotation.x=hu=='travail'?-1.1+Math.sin(t*16+i*2)*.25:0;a.rotation.z=hu=='content'?(i?-1:1)*(1.9+Math.sin(t*9)*.3):(i?.12:-.12);});
  // téléphone : visible quand la scène le demande
  const showP=s.plan=='telephone'||s.tampon;P.visible=!!showP;if(showP){P.scale.setScalar(back(tl/.5));phoneDraw(p,t);}
  screenDraw(k,p,t);
  R.render(scene,CAM);
  // habillage HTML
  SC.forEach((z,i)=>{const b=$('bd'+i);if(b){const on=i==k;const kk=back((t-z.a)/.4);b.style.opacity=on?1:0;b.style.transform=`translateX(-50%) rotate(-1.5deg) scale(${on?.6+.4*kk:1})`;}
    const g=$('bg'+i);if(g){const on=i==k;g.style.opacity=on?c((t-z.a-.2)/.2):0;const cc=z.compteur;g.querySelector('i').textContent=cc.fmt?cc.fmt.replace('#',Math.round(cc.de+(cc.a-cc.de)*sm(p*1.15))):Math.round(cc.de+(cc.a-cc.de)*sm(p*1.15));}
    const fn=$('fn'+i);if(fn){const kk=back((t-z.a-.15)/.45);fn.style.opacity=i==k?c((t-z.a-.15)/.15):0;fn.style.transform=`scale(${.6+.4*kk})`;}
    const tp=$('tp'+i);if(tp){const ta=z.a+.25*(z.b-z.a);const kk=c((t-ta)/.18);tp.style.opacity=t>=ta&&i==k?1:0;tp.style.transform=`translateX(-50%) rotate(-7deg) scale(${2.2-1.2*kk})`;}});
  for(const cp of document.querySelectorAll('.cap')){const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'flex':'none';
    for(const w of cp.querySelectorAll('.stk')){const wt=+w.dataset.w;const kk=back((t-wt)/.22);w.style.opacity=t>=wt?1:0;w.style.transform=`rotate(${w.dataset.r}deg) scale(${t>=wt?.5+.5*kk:.5})`;}}
  const ct=SC.findIndex(z=>z.tampon);if(ct>=0){const t0=SC[ct].a+.25*(SC[ct].b-SC[ct].a);CF.forEach((f,i)=>{const u=t-t0-(i%7)*.05;const on=u>0;f.style.opacity=on?1:0;
    if(on){f.style.left=(+f.dataset.x+Math.sin(u*3+i)*40)+'px';f.style.top=(-60+u*(380+(i%5)*60))+'px';f.style.transform=`rotate(${u*(200+i*17)}deg)`;}});}
};render(0);
</script></body></html>"""


def page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]
    col = {"nuit": "#141a3a", "sol": "#2a2148", "mur": "#232a5c", "cadre": "#3a2f5a", "bois": "#5e3b2c", "bois2": "#43281e", "tasse": "#e8743b",
           "mascotte": "#e8794a", "acc": "#ff7a3d", "jaune": "#ffd23f", "vert": "#2fd36b", "papier": "#f4e7cf", "encre": "#1b2147"} | spec.get("couleurs", {})
    hexi = lambda h: int(h.lstrip("#"), 16)
    S = [{"a": round(starts[k], 3), "b": round(starts[k] + durs[k], 3), "plan": s.get("type", "large"), "ecran": s.get("ecran"),
          "humeur": s.get("humeur"), "tampon": s.get("tampon"), "compteur": s.get("compteur")} for k, s in enumerate(sc)]
    bands = "".join(f"<div class='band' id='bd{k}'><span>{K.esc(s.get('bandeau', ''))}</span></div>" for k, s in enumerate(sc) if s.get("bandeau"))
    badges = "".join(f"<div class='badge' id='bg{k}'><b>{K.esc(s['compteur'].get('label', ''))}</b><i>0</i></div>" for k, s in enumerate(sc) if s.get("compteur"))
    fins = "".join(f"<div class='fin' id='fn{k}'><b>{K.esc(s['carte'][0])}</b>" + (f"<span>{K.esc(s['carte'][1])}</span>" if len(s['carte']) > 1 else '') + "</div>" for k, s in enumerate(sc) if s.get("carte"))
    tampons = "".join(f"<div class='tampon' id='tp{k}'>✓ {K.esc(s['tampon'])}</div>" for k, s in enumerate(sc) if s.get("tampon"))
    pal = [col["acc"], col["jaune"], col["vert"], "#4f7cff", "#ff5fa2"]
    conf = "".join(f"<div class='cf' data-x='{(i * 137) % 1040}' style='background:{pal[i % 5]}'></div>" for i in range(70)) if any(s.get("tampon") for s in sc) else ""
    n = [0]
    def stk(w, t):
        n[0] += 1
        return f"<span class='stk {'o' if n[0] % 2 else 'y'}' data-w='{t:.3f}' data-r='{((n[0] * 37) % 7) - 3}'>{H.escape(w)}</span>"
    cap_html = "".join(f"<div class='cap' data-a='{cc[0][1]:.3f}' data-b='{cn:.3f}'>" + "".join(stk(w, t) for w, t in cc) + "</div>" for cc, cn in caps)
    ev = []
    for k, s in enumerate(sc):
        e = s.get("ecran") or {}
        if e.get("type") == "chat":
            for j, (_, txt) in enumerate(e.get("messages", [])):
                a = starts[k] + durs[k] * j / max(1, len(e["messages"]))
                ev.append({"k": "type", "at": round(a, 3), "end": round(a + durs[k] * .8 / max(1, len(e["messages"])), 3), "text": txt})
        if e.get("type") == "verif":
            nl = len(e.get("lignes", []))
            ev += [{"k": "click", "at": round(starts[k] + durs[k] * (i + .5) / (nl + .5), 3)} for i in range(nl)]
        if s.get("tampon"):
            ta = starts[k] + .25 * durs[k]
            ev += [{"k": "impact", "at": round(ta, 3)}, {"k": "sparkle", "at": round(ta + .1, 3)}]
    colj = {kk: (hexi(v) if kk in ("nuit", "sol", "mur", "cadre", "bois", "bois2", "tasse", "mascotte") else v) for kk, v in col.items()}
    three = open(os.path.join(DOSSIER, "three.min.js"), encoding="utf-8").read()
    R = {"__FONTS__": K._font_faces(["Anton", "Archivo Black", "Inter"]), "__NUIT__": col["nuit"], "__PAPIER__": col["papier"], "__ENCRE__": col["encre"],
         "__ACC__": col["acc"], "__JAUNE__": col["jaune"], "__VERT__": col["vert"], "__HANDLE__": H.escape(spec.get("handle", "")),
         "__BANDS__": bands, "__BADGES__": badges, "__CAPS__": cap_html, "__TAMPONS__": tampons, "__FINS__": fins, "__CONFETTIS__": conf,
         "__D__": str(total), "__SC__": json.dumps(S, ensure_ascii=False), "__EV__": json.dumps(ev), "__COL__": json.dumps(colj)}
    out = TPL
    for kk, v in R.items():
        if kk != "__THREE__":
            out = out.replace(kk, v)
    return out.replace("__THREE__", three)
