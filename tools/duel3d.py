#!/usr/bin/env python3
"""Reels 3D « duel » (Mental d'Acier) : personnages blancs cernés de noir sur fond noir, sol miroir, un seul plan
qui boucle (14 s), sans voix : musique sombre générée + bruitages. Peu de texte : étiquettes + 1 à 3 lignes révélées
en haut ; la morale va dans la légende.

Scènes (champ "scene" du spec) :
  mur     Perfectionniste (polit sa brique au niveau) vs Passe à l'action (monte son mur et s'élève avec lui)
  reveil  Motivé (se recouche, téléphone sous la couette) vs Discipliné (lacets, footing sous la pluie, calendrier J1 -> J180)
  poids   un personnage sous un projecteur, des mains le pointent une à une (étiquettes), il s'effondre ; coupe : 3h07 au lit

Usage : python3 tools/duel3d.py <spec.json> <out.mp4>      (--html à la place de out.mp4 + 3e argument : page seule)
spec : {"id", "scene", "music_seed", "handle", "gauche", "droite",             (étiquettes ; pas pour "poids")
        "textes": [[debut, fin, rang, "TEXTE"], ...],                          (lignes du haut, rang 0 = la plus haute)
        "poids": ["LE PASSÉ", ...]}                                            (8 étiquettes des mains, scène "poids")
"""
import json, os, sys, subprocess, tempfile, shutil, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K

DUR = 14.0
W, H = 1080, 1920

# ------------------------------------------------------------------ socle commun (three.js)
COMMUN = r"""
const D=__DUR__, W=__W__, H=__H__;
const c=x=>Math.max(0,Math.min(1,x)), sm=x=>{x=c(x);return x*x*(3-2*x);};
const back=x=>{x=c(x);const s=1.6;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const V=(x,y,z)=>new THREE.Vector3(x,y,z||0);
const lerp=(a,b,k)=>a.clone().lerp(b,k);
const R=new THREE.WebGLRenderer({canvas:document.getElementById('cv'),antialias:true,preserveDrawingBuffer:true});
R.setSize(W,H,false); R.setClearColor(0x000000); R.outputEncoding=THREE.sRGBEncoding; R.autoClear=false;
const scene=new THREE.Scene(), world=new THREE.Group(); scene.add(world);
scene.add(new THREE.AmbientLight(0xffffff,.5));
const key=new THREE.DirectionalLight(0xffffff,.8); key.position.set(-3,6,6); scene.add(key);
const rim=new THREE.DirectionalLight(0xffffff,.3); rim.position.set(4,3,-4); scene.add(rim);
// sol miroir : le monde est rendu une 1re fois retourné sous le sol, puis voilé par un plan noir translucide
const floorScene=new THREE.Scene();
const floor=new THREE.Mesh(new THREE.PlaneGeometry(80,80),new THREE.MeshBasicMaterial({color:0x000000,transparent:true,opacity:.82,depthWrite:false}));
floor.rotation.x=-Math.PI/2; floorScene.add(floor);
// personnage « toon » : blanc + une seule ombre gris clair franche
const GRAD=new THREE.DataTexture(new Uint8Array([105,170,255]),3,1,THREE.RedFormat);GRAD.minFilter=GRAD.magFilter=THREE.NearestFilter;GRAD.needsUpdate=true;
const WHITE=new THREE.MeshToonMaterial({color:0x9c9c9c,gradientMap:GRAD,emissive:0x2a2a2a});

const BRICK=new THREE.MeshStandardMaterial({color:0xb9a98f,roughness:.85,emissive:0x0d0b08});
const GOLD=new THREE.MeshStandardMaterial({color:0xe8b84f,roughness:.25,metalness:.6,emissive:0x5a3c08});
const GREY=c_=>new THREE.MeshStandardMaterial({color:c_,roughness:.9});
const EDGE=new THREE.LineBasicMaterial({color:0x2a2620});
// contour calculé sur l'image : chaque MEMBRE (corps+tête, chaque bras, chaque jambe, chaque main pointée) a un identifiant
// couleur, rendu dans une image cachée ; un filtre trace le trait noir là où l'identifiant change (bord de la silhouette, membre
// devant un autre) ou là où la profondeur saute dans un même membre (avant-bras replié). Pas d'anneaux aux articulations.
const IDV='void main(){gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}';
const IDF='uniform vec4 col;void main(){gl_FragColor=col;}';
let NID=0,CURID=null;const OCC=new THREE.ShaderMaterial({uniforms:{col:{value:new THREE.Vector4(0,0,0,0)}},vertexShader:IDV,fragmentShader:IDF});
function newId(){NID++;return new THREE.ShaderMaterial({uniforms:{col:{value:new THREE.Vector4((NID*37%251)/255,(NID*91%241)/255,(NID*53%239)/255,1)}},vertexShader:IDV,fragmentShader:IDF});}
function capsule(r,parent){const m=new THREE.Mesh(new THREE.CapsuleGeometry(r,1,8,18),WHITE);if(CURID)m.userData.idMat=CURID;
  m.userData.L=1+2*r;(parent||world).add(m);return m;}
const limb=r=>capsule(r);
function setLimb(m,a,b){const d=V().subVectors(b,a);const L=Math.max(.001,d.length());m.position.copy(a).addScaledVector(d,.5);
  m.quaternion.setFromUnitVectors(V(0,1,0),d.clone().normalize());m.scale.set(1,L/m.userData.L+.12,1);}
function ball(r,parent){const m=new THREE.Mesh(new THREE.SphereGeometry(r,32,24),WHITE);if(CURID)m.userData.idMat=CURID;(parent||world).add(m);return m;}
const head=r=>ball(r);
function box(m,w,h,d,edges=true,parent){const g=new THREE.BoxGeometry(w,h,d);const b=new THREE.Mesh(g,m);if(edges)b.add(new THREE.LineSegments(new THREE.EdgesGeometry(g),EDGE));(parent||world).add(b);return b;}
function texCanvas(w,h){const cv=document.createElement('canvas');cv.width=w;cv.height=h;const t=new THREE.CanvasTexture(cv);t.userData.cv=cv;t.userData.x=cv.getContext('2d');return t;}
// IK à 2 segments : coude/genou placé du côté de « hint »
function ik(S,T,a,b,hint){const d0=V().subVectors(T,S);let d=d0.length();const dir=d0.clone().normalize();d=Math.min(d,a+b-.001);
  const x=(a*a-b*b+d*d)/(2*d);const h=Math.sqrt(Math.max(0,a*a-x*x));const p=hint.clone().addScaledVector(dir,-hint.dot(dir)).normalize();
  return S.clone().addScaledVector(dir,x).addScaledVector(p,h);}
// proportions « mascotte » : grosse tête, membres épais, mains rondes, pieds en ovale
function figure(){CURID=newId();const f={torso:limb(.105),head:head(.25),arms:[],mains:[],legs:[],pieds:[]};
  for(let i=0;i<2;i++){CURID=newId();f.arms.push([limb(.078),limb(.072)]);f.mains.push(ball(.085));}
  for(let i=0;i<2;i++){CURID=newId();f.legs.push([limb(.09),limb(.084)]);f.pieds.push(limb(.075));}
  CURID=null;return f;}
function setVisible(f,v){[f.torso,f.head,...f.arms.flat(),...f.legs.flat(),...f.mains,...f.pieds].forEach(m=>m.visible=v);}
// P : hip, sh, hands[2], feet[2], (knees[2]), knee/elbow (indices), look (décalage de la tête), side (axe épaules/hanches, x par défaut)
function pose(f,P){setLimb(f.torso,P.hip,P.sh);const sd_=(P.side||V(1,0,0)).clone().normalize();
  const up=V().subVectors(P.sh,P.hip).normalize();f.head.position.copy(P.sh).addScaledVector(up,.31).add(P.look||V(0,0,0));const toe=(P.toe||V(0,0,1)).clone().normalize();  // pieds légèrement ouverts vers l'extérieur
  [0,1].forEach(i=>{const sd=i?1:-1;const S=P.sh.clone().addScaledVector(sd_,.15*sd);const Hd=P.hands[i];
    const E=ik(S,Hd,.34,.34,P.elbow.clone().addScaledVector(sd_,.5*sd));setLimb(f.arms[i][0],S,E);setLimb(f.arms[i][1],E,Hd);
    const Hp=P.hip.clone().addScaledVector(sd_,.1*sd);const Ft=P.feet[i];const Kn=P.knees&&P.knees[i]?P.knees[i]:ik(Hp,Ft,.44,.44,P.knee);
    setLimb(f.legs[i][0],Hp,Kn);setLimb(f.legs[i][1],Kn,Ft);
    f.mains[i].position.copy(Hd);const tI=toe.clone().addScaledVector(sd_,.4*sd*(1-Math.abs(toe.y))).normalize();setLimb(f.pieds[i],Ft.clone().addScaledVector(tI,-.02),Ft.clone().addScaledVector(tI,.1));});}
const cam=new THREE.PerspectiveCamera(24,W/H,.1,80);
const RT=new THREE.WebGLRenderTarget(W,H,{minFilter:THREE.NearestFilter,magFilter:THREE.NearestFilter});RT.depthTexture=new THREE.DepthTexture(W,H);
const QS=new THREE.Scene(),QC=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const QM=new THREE.ShaderMaterial({transparent:true,depthTest:false,depthWrite:false,uniforms:{tId:{value:RT.texture},tD:{value:RT.depthTexture},px:{value:new THREE.Vector2(1/W,1/H)},n:{value:.1},f:{value:80}},
  vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',
  fragmentShader:`uniform sampler2D tId,tD;uniform vec2 px;uniform float n,f;varying vec2 vUv;
  float L(vec2 uv){float z=texture2D(tD,uv).x*2.-1.;return 2.*n*f/(f+n-z*(f-n));}
  void main(){vec4 a=texture2D(tId,vUv);float da=L(vUv);float e=0.;
    for(int k=0;k<2;k++)for(int i=0;i<8;i++){float an=float(i)*.785398+float(k)*.3927;float r=k==0?2.6:5.2;vec2 uv=vUv+vec2(cos(an),sin(an))*px*r;
      vec4 b=texture2D(tId,uv);if(b.a<.5)continue;float db=L(uv);
      if(a.a<.5||distance(a.rgb,b.rgb)>.02){if(db<da-.02)e+=1.;}else if(db<da-.2)e+=1.;}
    gl_FragColor=vec4(0.,0.,0.,min(1.,e/2.));}`});
QS.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),QM));
const SWAP=[];
function outline(){SWAP.length=0;world.traverse(o=>{if(!o.visible)return;if(o.isLineSegments||o.isLine||o.isPoints||(o.material&&o.material.transparent)||o.isLight){SWAP.push([o,'v']);o.visible=false;return;}
    if(o.isMesh){SWAP.push([o,o.material]);o.material=o.userData.idMat||OCC;}});
  QM.uniforms.n.value=cam.near;QM.uniforms.f.value=cam.far;
  R.setRenderTarget(RT);R.setClearColor(0x000000,0);R.clear();R.render(scene,cam);R.setRenderTarget(null);R.setClearColor(0x000000,1);
  for(const [o,m] of SWAP){if(m==='v')o.visible=true;else o.material=m;}
  R.render(QS,QC);}
function drawMirror(){R.clear();world.scale.y=-1;R.render(scene,cam);R.render(floorScene,cam);world.scale.y=1;R.clearDepth();R.render(scene,cam);outline();}
function drawPlain(){R.clear();R.render(scene,cam);outline();}
const BEATS=[...document.querySelectorAll('.beat')];
function beats(t){for(const b of BEATS){const a=+b.dataset.a,z=+b.dataset.b;const k=c((t-a)/.25);b.style.opacity=t<z?k:Math.max(0,1-(t-z)/.2);
  b.style.transform=`translateY(${(1-k)*18}px)`;}}
const LABS=[...document.querySelectorAll('.lab')];
"""

# ------------------------------------------------------------------ scène « mur »
MUR = r"""
const COLS=3, ROWS=10, T0=.25, T1=10.4, TL=10.9, NB=COLS*ROWS, DT=(T1-T0)/NB;
const BW=.36,BH=.16,BD=.24;
const PX=-.85;
for(const x of [PX-.36,PX,PX+.36])box(BRICK,BW-.005,BH-.004,BD).position.set(x,BH/2,0);
const tb=box(BRICK,BW-.005,BH-.004,BD);
const level=box(GOLD,.5,.05,.07,false);
const pf=figure();
function posePerf(t){
  const up=sm((t-TL)/.7);
  const lift=t>4.2&&t<6.4?Math.sin(c((t-4.2)/2.2)*Math.PI):0;
  const shim=Math.sin(t*6)*.006*(1-up);
  tb.position.set(PX+shim,BH*1.5+lift*.3,0);tb.rotation.set(0,lift*.35*Math.sin(t*2.5),lift*.08);
  const slide=(1-up)*(1-lift)*.08*Math.sin(t*3.1);
  level.position.copy(tb.position).add(V(slide,BH/2+.025,0));level.rotation.copy(tb.rotation);
  level.visible=up<.5;
  const hip=lerp(V(PX,.46,-.5),V(PX,.86,-.42),up), sh=lerp(V(PX+.02,.92+lift*.12,-.22),V(PX+.02,1.42,-.38),up);
  const onLvl=[level.position.clone().add(V(-.17,.03,0)),level.position.clone().add(V(.17,.03,0))];
  const onBrick=[tb.position.clone().add(V(-.2,0,0)),tb.position.clone().add(V(.2,0,0))];
  const work=lift>0?onBrick.map((p,i)=>lerp(onLvl[i],p,c(lift*3))):onLvl;
  const rest=[V(PX-.26,.78,-.38),V(PX+.26,.78,-.38)];
  const hands=work.map((p,i)=>lerp(p,rest[i],up));
  pose(pf,{hip,sh,hands,feet:[lerp(V(PX-.1,.05,-.75),V(PX-.12,.03,-.42),up),lerp(V(PX+.1,.05,-.75),V(PX+.12,.03,-.42),up)],
    knees:up<.02?[V(PX-.1,.07,-.2),V(PX+.1,.07,-.2)]:null,knee:V(0,0,1),elbow:V(0,-1,.4),
    look:lerp(V(0,-.05,.06),V(.07,.05,0),up)});
}
const WX=.45;
const wall=[];
for(let i=0;i<NB;i++){const r=Math.floor(i/COLS),k=i%COLS;const b=box(BRICK,BW-.006,BH-.004,BD);
  const j=Math.sin(i*12.9898)*43758.5453;const rnd=j-Math.floor(j);
  b.userData.p=V(WX+k*BW+(r%2?BW/2:0)+(rnd-.5)*.02,BH/2+r*BH,(rnd-.5)*.02);b.userData.ry=(rnd-.5)*.06;b.visible=false;wall.push(b);}
const held=[box(BRICK,BW-.006,BH-.004,BD),box(BRICK,BW-.006,BH-.004,BD)];
const ac=figure();
const MIDX=WX+BW*(COLS-1)/2+BW/4;
function poseAction(t){
  const f=c((t-T0)/(T1-T0))*NB;const n=Math.floor(f);const u=f-n;
  wall.forEach((b,i)=>{b.visible=i<n;if(i<n){const a=c((t-(T0+(i+1)*DT))/.08);b.position.copy(b.userData.p).add(V(0,.06*(1-a),0));b.rotation.y=b.userData.ry;}});
  const done=n>=NB;const row=Math.min(ROWS,Math.floor(n/COLS));const wallTop=row*BH+(done?0:(n%COLS)/COLS*BH*.5);
  const fin=sm((t-T1)/.6);
  const feetY=Math.max(0,wallTop-.42)*(1-fin)+ROWS*BH*fin;const fz=-.5+.5*fin;
  const tx=done?MIDX:wall[n].userData.p.x;
  const hx=MIDX+(tx-MIDX)*.45;
  const hip=V(hx,feetY+.55-.13*fin,-.48+.4*fin);
  const bob=done?0:Math.sin(u*Math.PI)*.06;
  const sh=V(hx+(tx-hx)*.25*(1-fin)-.06*fin,hip.y+.42+.02*fin-bob,-.3+.38*fin);
  held.forEach(h=>h.visible=false);
  let hands;
  if(!done){const slot=wall[n].userData.p.clone().add(V(0,.02,0));const side=n%2;
    const grab=V(hx+(side?.32:-.32),hip.y+.25,-.42);
    const hm=grab.clone().lerp(slot,sm(u));hm.y+=.18*Math.sin(u*Math.PI);
    const other=V(hx+(side?-.3:.3),hip.y+.2,-.25);
    hands=side?[other,hm]:[hm,other];held[side].visible=true;held[side].position.copy(hm);held[side].rotation.set(0,0,0);}
  else{hands=[V(hx-.2,feetY+.42,.14),V(hx+.2,feetY+.42,.14)];}
  pose(ac,{hip,sh,hands,feet:[V(hx-.15,feetY+.02,fz),V(hx+.15,feetY+.02,fz)],knee:V(0,.4*fin,1),elbow:V(0,-1,-.2),
    look:lerp(V(0,-.06,.07),V(-.09,-.06,.05),fin)});
}
function update(t){poseAction(t);posePerf(t);
  cam.position.set(-1.2+.1*Math.sin(t/5),2.5,14);cam.lookAt(.38,1.15,0);drawMirror();}
"""

# ------------------------------------------------------------------ scène « reveil »
REVEIL = r"""
// deux chambres côte à côte, lits dans la profondeur (tête contre le mur du fond), vues un peu d'en haut.
// s=-1 : gauche (Motivé), s=+1 : droite (Discipliné). Chaque personnage enchaîne des poses clés avec des transitions lissées.
const XC=.82, TS=[1.6,2.4,3.8,4.6], TJ0=6.0, TJ1=10.4;
const BED=GREY(0x3a3d44), MAT=GREY(0x9aa0aa), BLK=GREY(0x5d6b85), WOOD=GREY(0x2c2f35);
function room(s){
  const cx=s*XC, o={s,cx};
  box(BED,.74,.26,1.75).position.set(cx,.13,-.1);
  box(WOOD,.78,.62,.07).position.set(cx,.31,-1.0);                  // tête de lit
  box(MAT,.7,.1,1.68).position.set(cx,.31,-.1);
  box(GREY(0xdcdcdc),.5,.09,.28).position.set(cx,.41,-.78);         // oreiller
  const ns=box(WOOD,.28,.32,.28);ns.position.set(cx+s*.58,.16,-.82);
  o.ct=texCanvas(128,64);box(new THREE.MeshBasicMaterial({map:o.ct}),.24,.11,.09,true).position.set(cx+s*.58,.375,-.78);
  box(GREY(0x4a4d55),.66,.76,.05).position.set(cx,1.5,-1.32);
  o.wt=texCanvas(128,160);const gl=new THREE.Mesh(new THREE.PlaneGeometry(.58,.68),new THREE.MeshBasicMaterial({map:o.wt}));gl.position.set(cx,1.5,-1.29);world.add(gl);
  box(GREY(0x4a4d55),.03,.68,.02).position.set(cx,1.5,-1.285);box(GREY(0x4a4d55),.58,.03,.02).position.set(cx,1.5,-1.285);
  box(GREY(0x4a4d55),.74,.04,.12).position.set(cx,1.1,-1.27);       // rebord
  o.blanket=box(BLK,.76,.16,1.0);o.f=figure();return o;}
const L=room(-1), Rr=room(1);
function drawClock(o,t,ring){const x=o.ct.userData.x;x.fillStyle='#0b0b0b';x.fillRect(0,0,128,64);const on=!ring||Math.floor(t*4)%2==0;
  x.fillStyle=on?'#ff3b30':'#4a1210';x.font='bold 44px monospace';x.textAlign='center';x.textBaseline='middle';x.fillText('06:00',64,34);o.ct.needsUpdate=true;}
function drawWindow(o,t,sun){const x=o.wt.userData.x;const g=x.createLinearGradient(0,0,0,160);
  if(sun>0){g.addColorStop(0,`rgb(${40+120*sun},${50+80*sun},${90+30*sun})`);g.addColorStop(1,`rgb(${60+190*sun},${50+140*sun},${60+40*sun})`);}
  else{g.addColorStop(0,'#0d1424');g.addColorStop(1,'#1e2a44');}
  x.fillStyle=g;x.fillRect(0,0,128,160);
  const rain=1-sun;if(rain>0){x.strokeStyle=`rgba(190,210,255,${.55*rain})`;x.lineWidth=2;
    for(let i=0;i<34;i++){const px=(i*37.7)%140-6;const py=((i*53.3)+t*420)%190-20;x.beginPath();x.moveTo(px,py);x.lineTo(px-5,py+16);x.stroke();}}
  o.wt.needsUpdate=true;}
const calT=texCanvas(256,256);const cal=box(new THREE.MeshBasicMaterial({map:calT}),.46,.46,.04);cal.position.set(0,1.62,-1.3);
function drawCal(n,red){const x=calT.userData.x;x.fillStyle=red?'#d22':'#f2f2f2';x.fillRect(0,0,256,256);x.fillStyle=red?'#fff':'#111';x.textAlign='center';
  x.font='bold 46px monospace';x.fillText('JOUR',128,74);x.font='bold 116px monospace';x.fillText(String(n),128,190);calT.needsUpdate=true;}
const cloud=new THREE.Group();world.add(cloud);
for(const [dx,dy,r] of [[-.2,0,.15],[0,.07,.2],[.2,0,.15],[.08,-.05,.14]]){const m=new THREE.Mesh(new THREE.SphereGeometry(r,20,14),GREY(0x6b6f78));m.position.set(dx,dy,0);cloud.add(m);}
const drops=new THREE.LineSegments(new THREE.BufferGeometry(),new THREE.LineBasicMaterial({color:0x9fb4ff,transparent:true,opacity:.75}));
drops.geometry.setAttribute('position',new THREE.BufferAttribute(new Float32Array(36*6),3));world.add(drops);
const shoes=[box(GOLD,.15,.07,.22,false),box(GOLD,.15,.07,.22,false)];
const medal=new THREE.Mesh(new THREE.TorusGeometry(.12,.018,8,24),GOLD);world.add(medal);
const glow=new THREE.PointLight(0x5c8dff,0,1.4);world.add(glow);
const phone=box(new THREE.MeshBasicMaterial({color:0x9cc3ff}),.07,.12,.015,false);
// ---- poses clés (o : chambre). Allongé : tête sur l'oreiller (z -0,8), jambes détendues sous la couette.
function lying(o){const x=o.cx;return {hip:V(x,.47,-.02),sh:V(x,.49,-.5),hands:[V(x-.16,.52,-.22),V(x+.16,.52,-.22)],feet:[V(x-.11,.45,.84),V(x+.11,.45,.84)],
  knee:V(0,1,.2),elbow:V(0,1,0),side:V(1,0,0),look:V(0,.03,0),toe:V(0,1,.3)};}
function sitting(o){const x=o.cx;return {hip:V(x,.46,-.38),sh:V(x,.98,-.46),hands:[V(x-.27,.42,-.32),V(x+.27,.42,-.32)],feet:[V(x-.1,.42,.42),V(x+.1,.42,.42)],
  knee:V(0,1,.3),elbow:V(0,-.4,-1),side:V(1,0,0),look:V(0,.03,-.06),toe:V(0,1,.3)};}
const X=.3;   // le Discipliné se lève côté intérieur et se tient entre les deux lits, face caméra
function edge(o){const x=o.cx;return {hip:V(x-.3,.46,-.28),sh:V(x-.36,.98,-.26),hands:[V(x-.22,.42,-.5),V(x-.22,.42,-.05)],feet:[V(x-.66,.04,-.4),V(x-.66,.04,-.14)],
  knee:V(-1,.3,0),elbow:V(0,-1,0),side:V(0,0,1),look:V(-.04,0,0),toe:V(-1,0,0)};}
const stand={hip:V(X,.86,.1),sh:V(X,1.36,.1),hands:[V(X-.25,.82,.1),V(X+.25,.82,.1)],feet:[V(X-.12,.04,.1),V(X+.12,.04,.1)],knee:V(0,0,1),elbow:V(0,-1,-.2),side:V(1,0,0),look:V(0,0,.04),toe:V(0,0,1)};
const tie={hip:V(X,.6,.12),sh:V(X,.95,.42),hands:[V(X-.12,.1,.3),V(X+.12,.1,.3)],feet:[V(X-.12,.04,.15),V(X+.12,.04,.15)],knee:V(0,.3,1),elbow:V(0,-1,.3),side:V(1,0,0),look:V(0,-.06,.06),toe:V(0,0,1)};
function run(t){const ph=(t-TJ0)*2*Math.PI*2.4,a=Math.sin(ph),lA=Math.max(0,a),lB=Math.max(0,-a);
  return {hip:V(X,.86+.035*Math.abs(a),.12),sh:V(X,1.36+.035*Math.abs(a),.18),hands:[V(X-.24,1.0+.12*a,.16+.16*a),V(X+.24,1.0-.12*a,.16-.16*a)],
    feet:[V(X-.12,.04+.22*lA,.12+.1*lA),V(X+.12,.04+.22*lB,.12+.1*lB)],knee:V(0,.2,1),elbow:V(0,-1,-.3),side:V(1,0,0),look:V(0,-.01,.05),toe:V(0,0,1)};}
const proud={hip:V(X,.88,.1),sh:V(X,1.4,.08),hands:[V(X-.25,.9,.05),V(X+.25,.9,.05)],feet:[V(X-.14,.04,.1),V(X+.14,.04,.1)],knee:V(0,0,1),elbow:V(0,0,-1),side:V(1,0,0),look:V(0,.05,.02),toe:V(0,0,1)};
function mixP(a,b,k){const r={};for(const key_ of ['hip','sh','knee','elbow','side','look','toe'])r[key_]=lerp(a[key_]||V(0,0,1),b[key_]||V(0,0,1),k);
  r.hands=a.hands.map((p,i)=>lerp(p,b.hands[i],k));r.feet=a.feet.map((p,i)=>lerp(p,b.feet[i],k));return r;}
// enchaînement de poses clés : [début, pose (ou fonction du temps), durée de transition]
function seq(t,K){let P=typeof K[0][1]=='function'?K[0][1](t):K[0][1];
  for(let i=1;i<K.length;i++){const [t0,Q,d]=K[i];if(t<=t0)break;P=mixP(P,typeof Q=='function'?Q(t):Q,sm((t-t0)/d));}
  return P;}
function breathe(P,t,ph){const b=.012*Math.sin(t*2.1+ph);P.sh=P.sh.clone().add(V(0,b,0));return P;}
function update(t){
  const ring=t<TS[0];
  [L,Rr].forEach(o=>drawClock(o,t,ring));
  drawWindow(L,t,0);drawWindow(Rr,t,sm((t-TJ1)/1.2));
  // gauche : s'assoit, regarde la pluie, se recouche, couette sur la tête, téléphone allumé
  let P=breathe(seq(t,[[0,lying(L)],[TS[0],sitting(L),.8],[TS[2],lying(L),.9]]),t,0);pose(L.f,P);
  const cover=sm((t-TS[2]-.4)/.7);
  L.blanket.position.set(L.cx,.5+.03*cover,.25-.42*cover);L.blanket.scale.set(1,1+.2*cover,1+.75*cover);
  phone.visible=t>TS[3];phone.position.set(L.cx+.1,.58,-.62);phone.rotation.set(-1.1,0,0);
  glow.position.set(L.cx+.1,.75,-.5);glow.intensity=t>TS[3]?1.4+.5*Math.sin(t*7)*Math.sin(t*2.3):0;
  // droite : s'assoit, se tourne sur le bord, se lève, lace ses baskets, court sous la pluie, se tient fier avec sa médaille
  P=breathe(seq(t,[[0,lying(Rr)],[TS[0],sitting(Rr),.8],[TS[2],edge(Rr),.7],[4.5,stand,.6],[5.1,tie,.5],[5.7,stand,.35],[TJ0,run,.35],[TJ1,proud,.6]]),t,1.3);
  pose(Rr.f,P);
  const off=sm((t-TS[2])/.7);
  Rr.blanket.position.set(Rr.cx+.05*off,.5-.04*off,.25+.12*off);Rr.blanket.scale.set(1,1,1-.2*off);Rr.blanket.rotation.y=.12*off;
  shoes.forEach((s_,i)=>{s_.visible=t>5.4;s_.position.copy(P.feet[i]).add(V(0,-.005,.03));s_.scale.setScalar(back(c((t-5.4)/.3)));});
  const fin=sm((t-TJ1)/.5);medal.visible=fin>0;medal.position.copy(P.sh).add(V(0,-.12,.12));medal.scale.setScalar(back(c((t-TJ1-.2)/.4)));
  const run_=t>TJ0&&t<TJ1+.3?sm((t-TJ0)/.4)*(1-sm((t-TJ1)/.3)):0;
  cloud.visible=run_>0;cloud.position.set(X,2.05,.15);cloud.scale.setScalar(run_);
  const pa=drops.geometry.attributes.position.array;
  for(let i=0;i<36;i++){const x=X-.3+((i*.173)%.6),z=.15+((i*.37)%.3)-.15;const y=1.95-(((i*.29)+t*2.6)%1.9);pa.set([x,y,z,x-.02,y-.12,z],i*6);}
  drops.geometry.attributes.position.needsUpdate=true;drops.visible=run_>0;
  cal.visible=t>TJ0-.3;cal.scale.setScalar(back(c((t-TJ0+.3)/.4)));
  const day=t<TJ0?1:Math.round(1+179*Math.pow(c((t-TJ0)/(TJ1-TJ0-.2)),1.6));drawCal(day,day>=180);
  cam.position.set(.08*Math.sin(t/5),5.0,10.9);cam.lookAt(0,.75,-.4);drawMirror();
}
"""


# ------------------------------------------------------------------ scène « poids »
POIDS = r"""
const TC=8.3;   // coupe : 3h07 au lit
floor.material.opacity=.93;   // reflet plus discret : les pieds restent lisibles
const NOMS=__POIDS__;
const C0=V(0,1.25,0);
// projecteur
const cone=new THREE.Mesh(new THREE.CylinderGeometry(.06,1.15,4.3,40,1,true),new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:.045,depthWrite:false,side:THREE.DoubleSide,blending:THREE.AdditiveBlending}));
cone.position.set(0,2.15,0);world.add(cone);
const spot=new THREE.Mesh(new THREE.CircleGeometry(1.0,48),new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:.07,depthWrite:false}));
spot.rotation.x=-Math.PI/2;spot.position.y=.003;world.add(spot);
const fg=figure();
// mains qui pointent : gant blanc (paume arrondie, 3 doigts repliés, index tendu, pouce), manchette, avant-bras
// chaque doigt a son identifiant -> un trait sépare les doigts, comme un gant de dessin animé
function glove(out){const g=new THREE.Group();world.add(g);
  CURID=newId();const palm=ball(.1,g);palm.scale.set(1.05,1.12,.72);
  for(const [x,y] of [[-.03,.08],[-.07,.06],[-.1,.025]]){CURID=newId();const f=capsule(.035,g);setLimb(f,V(x,y,.015),V(x,y-.04,.08));}
  CURID=newId();const idx=capsule(.037,g);setLimb(idx,V(.045,.06,0),V(.05,.3,0));
  CURID=newId();const th=capsule(.035,g);setLimb(th,V(-.075,-.035,.045),V(-.01,.035,.09));
  CURID=newId();const cuff=new THREE.Mesh(new THREE.CylinderGeometry(.088,.088,.075,24),WHITE);cuff.userData.idMat=CURID;cuff.position.set(0,-.135,0);g.add(cuff);
  CURID=newId();const arm=capsule(.062,g);setLimb(arm,V(0,-.17,0),V(0,-.9,0));CURID=null;
  const y=out.clone().negate(), z=V(0,0,1).addScaledVector(y,-y.z).normalize(), x=V().crossVectors(y,z);
  g.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x,y,z));return g;}
const ANG=[155,25,198,-18,122,58,218,-38];
const hands=ANG.map((a,i)=>{const r=a*Math.PI/180;const out=V(Math.cos(r),Math.sin(r)*1.05,.18*(i%2?1:-1)).normalize();
  return {g:glove(out),out,at:1.0+i*.6};});
// chambre (vue de dessus), loin de la scène principale
const BX=30;
const bedG=new THREE.Group();world.add(bedG);
const fl=new THREE.Mesh(new THREE.PlaneGeometry(6,6),new THREE.MeshBasicMaterial({color:0x010102}));fl.rotation.x=-Math.PI/2;fl.position.set(BX,0,0);world.add(fl);
const moon=new THREE.Mesh(new THREE.PlaneGeometry(.7,1.0),new THREE.MeshBasicMaterial({color:0x9fb8ff,transparent:true,opacity:.18}));moon.rotation.x=-Math.PI/2;moon.position.set(BX+.95,.004,.35);world.add(moon);
box(GREY(0x30333a),1.05,.32,1.95).position.set(BX,.16,0);
box(GREY(0x8d939e),1.0,.1,1.88).position.set(BX,.36,0);
box(GREY(0xd8d8d8),.6,.08,.3).position.set(BX,.45,-.72);
const blk=box(GREY(0x4f5f7e),1.02,.12,1.3);blk.position.set(BX,.53,.33);
box(GREY(0x2e3036),.3,.3,.3).position.set(BX-.72,.15,-.72);
const ct=texCanvas(160,64);box(new THREE.MeshBasicMaterial({map:ct}),.26,.1,.12,true).position.set(BX-.72,.36,-.72);
function drawClock(txt){const x=ct.userData.x;x.fillStyle='#0b0b0b';x.fillRect(0,0,160,64);x.fillStyle='#ff3b30';x.font='bold 46px monospace';x.textAlign='center';x.textBaseline='middle';x.fillText(txt,80,34);ct.needsUpdate=true;}
const fb=figure();
const HL=[...document.querySelectorAll('.hl')];
const pv=V();
function update(t){
  const lit=t>=TC;
  if(!lit){
    const k1=sm((t-3.6)/.6), k2=sm((t-5.9)/.9);
    const hip=V(0,.86-.4*k2,0), sh=V(0,1.36-.42*k2-.04*k1,.18*k2);
    const hd=[V(-.2,1.62,.05),V(.2,1.62,.05)];
    const handsP=[lerp(V(-.25,.82,.04),hd[0],k1),lerp(V(.25,.82,.04),hd[1],k1)].map(p=>p.add(V(0,-.42*k2,.18*k2)));
    pose(fg,{hip,sh,hands:handsP,feet:[V(-.13,.03,.05),V(.13,.03,.05)],knee:V(0,0,1),elbow:V(0,-.3,.6),look:V(0,-.06*k2-.02*k1,.05*k2)});
    hands.forEach((h,i)=>{const a=back(c((t-h.at)/.45));const dist=.85+3.2*(1-a);const tr=.015*Math.sin(t*9+i);
      h.g.position.copy(C0).addScaledVector(h.out,dist+.0).add(V(tr,tr,0));h.g.visible=t>h.at;
      const lab=HL[i];if(!lab)return;pv.copy(C0).addScaledVector(h.out,dist+.35).add(V(Math.sign(h.out.x)*.62,-Math.sign(h.out.y)*.2,0));pv.project(cam);
      let px=(pv.x*.5+.5)*W, py=(-pv.y*.5+.5)*H;const w=lab.offsetWidth;py=Math.max(470,Math.min(1440,py));const mr=py>940?945:W-36;px=Math.max(36+w/2,Math.min(mr-w/2,px));  // colonne des boutons Instagram
      lab.style.left=(px-w/2)+'px';lab.style.top=(py-22)+'px';lab.style.opacity=t>h.at?c((t-h.at-.2)/.25):0;});
    setVisible(fg,true);setVisible(fb,false);   // le dormeur (non posé) resterait sous le sol, sous les pieds
    cam.position.set(.05*Math.sin(t/4),2.1,13.2-.25*sm(t/TC));cam.up.set(0,1,0);cam.lookAt(0,1.15,0);drawMirror();
  }else{
    HL.forEach(l=>l.style.opacity=0);setVisible(fg,false);setVisible(fb,true);hands.forEach(h=>h.g.visible=false);
    const br=.012*Math.sin((t-TC)*2.2);
    pose(fb,{hip:V(BX,.5+br,.2),sh:V(BX,.5+br,-.42),hands:[V(BX-.17,.56+br,-.2),V(BX+.17,.56+br,-.2)],feet:[V(BX-.1,.44,.85),V(BX+.1,.44,.85)],knees:[V(BX-.1,.46,.52),V(BX+.1,.46,.52)],
      knee:V(0,1,0),elbow:V(0,1,0),side:V(1,0,0),look:V(0,.03,0),toe:V(0,1,0)});
    drawClock(t<12.1?'03:07':'03:08');
    const z=sm((t-TC)/(D-TC));cam.position.set(BX+.05,9.6-1.0*z,.02);cam.up.set(0,0,-1);cam.lookAt(BX,0,0);drawPlain();
  }
  document.getElementById('noir').style.opacity=c((t-(D-.45))/.45)+(t<.12?1-t/.12:0);
}
"""

SCENES = {"mur": MUR, "reveil": REVEIL, "poids": POIDS}
# étiquettes par défaut (position CSS) selon la scène
LABELS = {"mur": [("left:56px;top:640px", "gauche"), ("right:60px;top:330px", "droite")],
          "reveil": [("left:70px;top:418px", "gauche"), ("right:70px;top:418px", "droite")],
          "poids": []}


def page(spec):
    sc = spec.get("scene", "mur")
    three = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "three.min.js"), encoding="utf-8").read()
    fonts = K._font_faces(["JetBrains Mono"])
    labs = "".join(f"<div class='lab' style='{pos}'>{K.esc(spec[k])}</div>" for pos, k in LABELS[sc] if spec.get(k))
    beats = "".join(f"<div class='beat' data-a='{a}' data-b='{b}' style='top:{212 + 66 * r}px'>{K.esc(txt)}</div>" for a, b, r, txt in spec.get("textes", []))
    hl = "".join(f"<div class='hl'>{K.esc(x)}</div>" for x in spec.get("poids", []))
    js = (COMMUN + SCENES[sc]).replace("__DUR__", str(DUR)).replace("__W__", str(W)).replace("__H__", str(H)).replace("__POIDS__", json.dumps(spec.get("poids", [])))
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:#000;overflow:hidden;position:relative;color:#fff}}
canvas{{position:absolute;left:0;top:0}}
.lab{{position:absolute;font:700 40px 'JetBrains Mono';letter-spacing:5px;white-space:nowrap;text-shadow:0 0 16px rgba(255,255,255,.5)}}
.beat{{position:absolute;left:40px;right:40px;text-align:center;font:700 50px 'JetBrains Mono';letter-spacing:4px;white-space:nowrap;opacity:0;text-shadow:0 0 18px rgba(255,255,255,.35)}}
.hl{{position:absolute;font:700 32px 'JetBrains Mono';letter-spacing:3px;white-space:nowrap;opacity:0;background:rgba(0,0,0,.82);padding:4px 10px;border-radius:6px}}
.hd{{position:absolute;left:0;right:0;top:1440px;text-align:center;font:400 30px 'JetBrains Mono';letter-spacing:10px;color:#3c3c3c}}
#noir{{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none}}
</style></head><body>
<canvas id='cv' width='{W}' height='{H}'></canvas>
{labs}{beats}{hl}
<div class='hd'>{K.esc(spec['handle']).upper()}</div>
<div id='noir'></div>
<script>{three}</script>
<script>{js}
window.render=function(t){{update(t);beats(t);}};render(0);
</script></body></html>"""


# ------------------------------------------------------------------ son
def musique(out, dur, seed=0, pulse=True):
    """Piano sombre en la mineur (i-VI-III-VII), nappe et sous-basse, réverbération ; 4 mesures = durée du reel,
    la queue de réverbération est repliée sur le début pour que la boucle raccorde sans coupure."""
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, lfilter
    SR = 48000; tail = 3.0; n = int(SR * (dur + tail)); mix = np.zeros(n); rng = np.random.default_rng(seed)
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    def add(sig, t0, g=1.0):
        i = int(t0 * SR)
        if i >= n: return
        s = sig[: n - i] * g; mix[i:i + len(s)] += s
    def piano(f, d=3.2):
        t = np.arange(int(d * SR)) / SR
        s = sum(np.sin(2 * np.pi * f * k * (1 + .0004 * k * k) * t) * np.exp(-t * (1.1 + .9 * k)) / k ** 1.4 for k in range(1, 7))
        return s * np.minimum(1, t * 300)
    def pad(fs, d):
        t = np.arange(int(d * SR)) / SR; env = np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / 1.0)
        s = sum(np.sin(2 * np.pi * f * (1 + dt) * t) for f in fs for dt in (-.003, .003)) / (2 * len(fs))
        b, a = butter(2, 900 / (SR / 2), "low"); return lfilter(b, a, s) * env
    shift = [0, -2, 3, -5][seed % 4]
    prog = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]
    nb = 4 * max(1, round(dur / 14))          # 4 mesures par tranche de ~14 s : même tempo pour un reel de 14 s ou de 40 s
    bar = dur / nb; beat = bar / 4
    melo = [[76, None, 72, None], [72, None, 69, 71], [67, None, 72, None], [71, None, 74, 71]]
    for k in range(nb):
        root, ch = prog[k % 4]; t0 = k * bar
        add(pad([midi(m + shift - 12) for m in ch], bar + .4), t0, .22)
        sub_t = np.arange(int(bar * SR)) / SR
        add(np.sin(2 * np.pi * midi(root + shift - 12) * sub_t) * np.minimum(1, sub_t * 8) * np.exp(-sub_t * .4), t0, .28)
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12] * 2
        for j, m in enumerate(arp):
            add(piano(midi(m + shift)), t0 + j * beat / 2 + rng.uniform(0, .012), .07 + .03 * (j % 4 == 0))
        for j, m in enumerate(melo[k % 4]):
            if m: add(piano(midi(m + shift), 4.0), t0 + j * beat + .01, .16)
        if pulse:
            for b_ in (0, 2):
                tp = np.arange(int(.4 * SR)) / SR
                add(np.sin(2 * np.pi * (52 + 40 * np.exp(-tp * 30)) * tp) * np.exp(-tp * 9), t0 + b_ * beat, .35)
    # réverbération (Schroeder : 4 peignes + 2 passe-tout)
    wet = np.zeros(n)
    for dly, g in ((1687, .78), (1949, .76), (2251, .74), (2617, .72)):
        a = np.zeros(dly + 1); a[0] = 1; a[-1] = -g; wet += lfilter([1], a, mix)
    for dly, g in ((347, .7), (113, .7)):
        bb = np.zeros(dly + 1); bb[0] = -g; bb[-1] = 1; aa = np.zeros(dly + 1); aa[0] = 1; aa[-1] = -g; wet = lfilter(bb, aa, wet)
    b, a = butter(2, 5000 / (SR / 2), "low"); wet = lfilter(b, a, wet)
    y = mix + .22 * wet
    m = int(dur * SR); loop = y[:m].copy(); loop[: n - m] += y[m:]     # boucle : la queue revient au début
    loop = loop / np.max(np.abs(loop)) * .9
    wavfile.write(out, SR, (np.stack([loop, loop], 1) * 32767).astype(np.int16))


def sfx(path, sc):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, lfilter
    SR = 48000; n = int(SR * (DUR + 1)); out = np.zeros(n); rng = np.random.default_rng(7)
    def put(sig, t0, g=1.0):
        i = int(max(0, t0) * SR); j = min(n, i + len(sig)); out[i:j] += sig[: j - i] * g
    def band(lo, hi, d):
        b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, rng.standard_normal(int(d * SR)))
    tt = np.arange(n) / SR
    th = np.arange(int(.3 * SR)) / SR
    thud = np.sin(2 * np.pi * (100 + 70 * np.exp(-th * 25)) * th) * np.exp(-th * 14) * .4
    tw = np.arange(int(.45 * SR)) / SR
    whoosh = band(400, 5000, .45) * np.sin(np.pi * tw / tw[-1]) ** 2 * .3
    tch = np.arange(int(1.2 * SR)) / SR
    chime = sum(np.sin(2 * np.pi * f * tch) * np.exp(-tch * 3) for f in (880, 1320, 1760)) * .05
    if sc == "mur":
        NB, T0, T1 = 30, .25, 10.4; dt = (T1 - T0) / NB
        tc = np.arange(int(.05 * SR)) / SR; clack = band(1200, 6000, .05) * np.exp(-tc * 90) * .16
        for i in range(NB):
            t = T0 + (i + 1) * dt; put(clack, t, .7 + .3 * rng.random())
            if (i + 1) % 3 == 0: put(thud, t)
        rub = band(2500, 9000, DUR + 1) * np.abs(np.sin(tt * 3.1)) * .03
        out += rub * ((tt < 4.2) | ((tt > 6.4) & (tt < 10.9)))
        put(thud, T1 + .6, 1.2)
    elif sc == "reveil":
        tb = np.arange(int(.09 * SR)) / SR; beep = np.sign(np.sin(2 * np.pi * 2000 * tb)) * .07 * np.minimum(1, (len(tb) - np.arange(len(tb))) / 400)
        t = 0.0
        while t < 1.55: put(beep, t); put(beep, t + .13); t += .5
        out += band(800, 7000, DUR + 1) * .018 * (1 - .8 * np.clip((tt - 10.4) / 1.2, 0, 1))   # pluie
        ph0 = 5.9
        k = 0
        while True:
            t = ph0 + k / (2 * 2.6)
            if t > 10.3: break
            put(thud, t, .35); k += 1
        put(chime, 10.4); put(whoosh, 3.8, .5)
    elif sc == "poids":
        for i in range(8): put(whoosh, 1.0 + i * .6 - .05, .7)
        put(thud, 5.9, .8)
        tk = np.arange(int(.03 * SR)) / SR; tick = band(2000, 8000, .03) * np.exp(-tk * 120) * .2
        for s in range(9, 14): put(tick, s)
        put(tick * 2, 12.1)
        hb = np.arange(int(.25 * SR)) / SR; heart = np.sin(2 * np.pi * 55 * hb) * np.exp(-hb * 16) * .45
        t = 3.0
        while t < 8.2: put(heart, t); put(heart, t + .22, .7); t += max(.45, .95 - (t - 3) * .09)
    out = np.clip(out, -1, 1); wavfile.write(path, SR, (np.stack([out, out], 1) * 32767).astype(np.int16))


def build(spec_path, out):
    spec = json.load(open(spec_path, encoding="utf-8")); tmp = tempfile.mkdtemp(); sc = spec.get("scene", "mur")
    hp = os.path.join(tmp, "p.html"); open(hp, "w", encoding="utf-8").write(page(spec))
    try:  # audit automatique (texte trop petit, hors zones sûres) : avertit sans bloquer
        import audit as A
        A.afficher(A.auditer(hp, [0.0, 3.5, 7.0, 10.5, 12.5], DUR), spec_path)
    except Exception as e:
        print("audit non réalisé :", e)
    fr = os.path.join(tmp, "fr"); os.makedirs(fr)
    asyncio.run(K._frames(hp, fr, DUR))
    v = os.path.join(tmp, "v.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{fr}/f_%04d.jpg", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", v], check=True)
    mu = os.path.join(tmp, "m.wav"); musique(mu, DUR, int(spec.get("music_seed", 0)), pulse=spec.get("pulse", True))
    fx = os.path.join(tmp, "fx.wav"); sfx(fx, sc)
    vm = 0 if spec.get("sans_musique") else 0.6   # sans_musique : bruitages seuls, pour ajouter un son tendance dans l'app
    fc = (f"[1]atrim=0:{DUR},volume={vm}[m];[2]atrim=0:{DUR}[f];"   # pas de fondu final : la vidéo doit boucler
          f"[m][f]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5,alimiter=limit=0.95,apad=whole_dur={DUR+3},atrim=0:{DUR}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", mu, "-i", fx, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[3] == "--html":
        open(sys.argv[2], "w", encoding="utf-8").write(page(json.load(open(sys.argv[1], encoding="utf-8")))); print("html")
    elif len(sys.argv) > 2 and sys.argv[1] == "musique":   # écoute seule : duel3d.py musique out.wav [seed]
        musique(sys.argv[2], DUR, int(sys.argv[3]) if len(sys.argv) > 3 else 0); print("ok")
    else:
        build(sys.argv[1], sys.argv[2]); print("ok")
