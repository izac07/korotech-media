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
import json, os, re, base64, html as H
import korotech as K

DOSSIER = os.path.dirname(os.path.abspath(__file__))

TPL = r"""<!doctype html><html><head><meta charset='utf-8'><style>__FONTS__
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:__NUIT__;position:relative}
canvas#cv{position:absolute;left:0;top:0}
.hdl{position:absolute;left:56px;top:70px;font:700 32px Inter;color:#fff;opacity:.55;z-index:5}
.band{position:absolute;left:50%;top:235px;transform:translateX(-50%);z-index:6;white-space:nowrap;opacity:0}
.band span{display:block;background:__BANDFOND__;color:__BANDTEXTE__;font:400 76px/1 Anton;letter-spacing:1px;text-transform:uppercase;padding:22px 64px 18px;
  box-shadow:0 10px 0 rgba(0,0,0,.25);clip-path:polygon(0 0,100% 0,96% 50%,100% 100%,0 100%,4% 50%)}
.badge{position:absolute;right:120px;top:390px;z-index:6;background:__BADGEFOND__;border:5px solid __BADGETEXTE__;border-radius:18px;padding:10px 22px 6px;
  display:flex;align-items:baseline;gap:16px;box-shadow:6px 6px 0 __ENCRE__;opacity:0;transform:rotate(3deg)}
.badge b{font:400 34px Anton;color:__BADGETEXTE__;letter-spacing:1px}.badge i{font:400 92px/1 Anton;font-style:normal;color:__ACC__;font-variant-numeric:tabular-nums}
.caps{position:absolute;left:70px;right:120px;top:1180px;z-index:7;display:flex;flex-wrap:wrap;justify-content:center;gap:12px 14px}
.cap{display:none;flex-wrap:wrap;justify-content:center;gap:12px 14px}
.stk{display:inline-block;font:400 70px/1.1 'Archivo Black';padding:8px 18px 10px;border-radius:10px;box-shadow:5px 5px 0 __ENCRE__;opacity:0}
.stk.o{background:__ACC__;color:__TEXTEO__}.stk.y{background:__JAUNE__;color:__ENCRE__}
.tampon{position:absolute;left:50%;top:960px;z-index:8;transform:translateX(-50%) rotate(-7deg);border:9px solid __VERT__;color:__VERT__;border-radius:18px;
  padding:8px 34px 4px;font:400 104px/1 Anton;letter-spacing:2px;white-space:nowrap;opacity:0;background:rgba(10,14,30,.55)}
.fin{position:absolute;left:90px;right:140px;top:640px;z-index:8;display:flex;flex-direction:column;align-items:center;gap:22px;opacity:0}
.fin b{font:400 112px/1 Anton;background:__ACC__;color:__TEXTEO__;padding:16px 44px 10px;border-radius:18px;box-shadow:8px 8px 0 __ENCRE__;transform:rotate(-2deg)}
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
<script type='importmap'>__IMPORTMAP__</script>
<script type='module'>
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {ShaderPass} from 'three/addons/postprocessing/ShaderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {BokehPass} from 'three/addons/postprocessing/BokehPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {GTAOPass} from 'three/addons/postprocessing/GTAOPass.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
const MODELES=__MODELES__;
const EV=__EV__; const D=__D__, SC=__SC__, COL=__COL__;
const c=x=>Math.max(0,Math.min(1,x)), sm=x=>{x=c(x);return x*x*(3-2*x);}, eo=x=>1-Math.pow(1-c(x),3);
const back=x=>{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const $=i=>document.getElementById(i);
const LIN=c_=>new THREE.Color(c_);
const DECORS={
 bureau:{ciel:'nuit',fen:[0,3.5,7.4,5],M:[-.8,1.08,-.15],ecran:{type:'moniteur',x:.75,y:2.05,z:-.55,w:1.9,h:1.19},tel:[-.05,1.08,.5],lampe:[1.85,1.78,-.35],horloge:[-2.2,4.7],objetsBureau:true,
  poussiere:[1.45,1.2,-.7,1.1,1.6,1.3],
  plans:{large:[[-.1,2.5,8.6],[-.1,1.85,-.4]],ecran:[[.75,2.0,4.6],[.75,1.9,-.5]],mascotte:[[-.6,1.9,5.0],[-.6,1.55,-.15]],telephone:[[-.05,1.9,3.9],[-.05,1.6,.5]]},
  meubles:[['desk',{libre:true,w:4.4,h:1.08,d:1.8,x:0,z:0},'BOIS'],['chairDesk',{h:1.35,x:2.15,z:1.25,ry:-2.4}],['computerKeyboard',{w:.95,x:.75,y:1.08,z:.28},'#2b2f45'],
   ['computerMouse',{w:.16,x:1.38,y:1.08,z:.32},'#2b2f45'],['lampRoundTable',{h:.85,x:1.85,y:1.08,z:-.42}],['pottedPlant',{h:1.8,x:-2.9,z:.9}],
   ['plantSmall2',{h:.5,x:-1.45,y:1.08,z:-.55}],['bookcaseOpenLow',{h:1.45,x:3.05,z:-2.55}]]},
 chambre_aube:{ciel:'aube',fen:[-1.5,3.4,3.6,3.2],M:[.3,0,.7],ecran:{type:'tableau',x:1.75,y:2.7,z:-3.18,w:2.1,h:1.31},tel:[1.2,0,1.3],lampe:[-2.05,1.15,-2.6],horloge:[2.95,4.75],
  poussiere:[-3.2,.6,-2.4,3,2.6,1.2],halteres:[1.35,0,-.1],
  plans:{large:[[.2,2.5,9.2],[.2,1.5,-.8]],ecran:[[1.75,2.6,5.2],[1.75,2.6,-3.1]],mascotte:[[.3,1.55,5.6],[.3,.6,.7]],telephone:[[1.0,1.25,4.2],[1.05,.75,1.3]]},
  meubles:[['bedSingle',{h:.95,x:-1.9,z:-1.75}],['sideTable',{h:.55,x:-2.05,z:-2.85}],['lampRoundTable',{h:.6,x:-2.05,y:.55,z:-2.85}],['rugRounded',{w:3.2,x:.3,y:.004,z:.7}],
   ['pottedPlant',{h:1.7,x:3.0,z:-2.4}]]},
 salon:{ciel:'jour',fen:[-1.6,3.3,3.6,2.8],M:[.3,0,.8],ecran:{type:'tele',x:1.7,y:2.45,z:-3.18,w:2.2,h:1.24},tel:[1.2,0,1.35],lampe:[-3.05,2.15,-2.05],
  poussiere:[-1,1,-1,3,2,2],halteres:[1.45,0,.15],tapis:true,
  plans:{large:[[.2,2.5,9.2],[.2,1.5,-.8]],ecran:[[1.7,2.35,5.0],[1.7,2.4,-3.1]],mascotte:[[.3,1.55,5.6],[.3,.6,.8]],telephone:[[1.0,1.25,4.2],[1.05,.75,1.35]]},
  meubles:[['loungeSofa',{h:1.0,x:-1.7,z:-2.45}],['lampRoundFloor',{h:2.1,x:-3.15,z:-2.15}],['pottedPlant',{h:1.8,x:3.0,z:-2.4}],['tableCoffee',{h:.45,x:-1.7,z:-1.2}],
   ['rugRound',{w:3.4,x:.3,y:.004,z:.8}]]},
 chambre_mda:{ciel:'nuit',ciel2:'aube',fen:[-1.25,3.4,3.2,3.1],M:[.6,0,.7],lit:[-1.75,0,-1.05],sol:[.55,0,.65],ecran:{type:'tableau',x:2.0,y:2.7,z:-3.18,w:2.1,h:1.31},tel:[1.35,0,1.25],lampe:[-3.0,1.15,-2.6],horloge:[2.95,4.75],
  poussiere:[-3.4,.8,-2.9,1.2,1.4,.8],halteres:[1.55,0,-.35],
  plans:{large:[[.1,2.3,8.8],[-.3,1.25,-.9]],ecran:[[2.0,2.6,5.2],[2.0,2.6,-3.1]],mascotte:[[.3,1.55,5.6],[.3,.6,.7]],telephone:[[1.15,1.25,4.2],[1.2,.75,1.25]]},
  meubles:[['bedSingle',{h:.95,x:-1.75,z:-2.05},'#4a4a4a'],['sideTable',{h:.55,x:-3.0,z:-2.7}],['lampRoundTable',{h:.6,x:-3.0,y:.55,z:-2.7}],['rugRounded',{w:3.0,x:.5,y:.004,z:.6},'#3a3a3a'],
   ['pottedPlant',{h:1.7,x:3.05,z:-2.45},'#3f5a46']]},
 chambre_nuit:{ciel:'nuit',fen:[1.4,3.4,3.4,3.0],M:[-.6,.5,-.9],ecran:{type:'mobile',x:1.25,y:1.18,z:-.2,w:.62,h:1.1},tel:null,lampe:[-2.25,1.15,-2.55],
  poussiere:[-3,.7,-2.6,1.4,1.2,1],
  plans:{large:[[0,2.4,9.0],[-.2,1.3,-.9]],ecran:[[1.25,1.25,2.6],[1.25,1.18,-.2]],mascotte:[[-.5,1.8,5.0],[-.6,1.05,-.9]],telephone:[[1.25,1.25,2.6],[1.25,1.18,-.2]]},
  meubles:[['bedDouble',{h:1.0,x:-.6,z:-1.65}],['sideTableDrawers',{h:.6,x:-2.25,z:-2.55}],['lampRoundTable',{h:.55,x:-2.25,y:.6,z:-2.55}],['sideTable',{h:.55,x:1.25,z:-.2}],
   ['rugRounded',{w:3.0,x:-.4,y:.004,z:.7}],['plantSmall1',{h:.6,x:2.8,z:-2.6}]]}
};
const DEC=DECORS[COL.decor]||DECORS.bureau;
const R=new THREE.WebGLRenderer({canvas:$('cv'),antialias:true,preserveDrawingBuffer:true});
R.setSize(1080,1920,false);R.outputColorSpace=THREE.SRGBColorSpace;R.toneMapping=THREE.NeutralToneMapping;R.toneMappingExposure=1.05;R.shadowMap.enabled=true;R.shadowMap.type=THREE.PCFSoftShadowMap;
const scene=new THREE.Scene();scene.background=LIN(COL.nuit);scene.fog=new THREE.Fog(LIN(COL.nuit),16,34);
scene.add(new THREE.HemisphereLight(0xa9b8ff,0x3a2414,1.1));
const PM=new THREE.PMREMGenerator(R);scene.environment=PM.fromScene(new RoomEnvironment(),.04).texture;scene.environmentIntensity=.32;
const key=new THREE.DirectionalLight(0xffe0bf,2.6);key.position.set(-3,6,5);scene.add(key);key.target.position.set(0,1,0);scene.add(key.target);
key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-6,right:6,top:6,bottom:-3,near:1,far:22});key.shadow.normalBias=.03;key.shadow.radius=4;
const rim=new THREE.DirectionalLight(0x7f95ff,1.7);rim.position.set(4,3,-3);scene.add(rim);
const lamp=new THREE.PointLight(0xffa860,3.2,7,2);lamp.position.set(...DEC.lampe);scene.add(lamp);
const GRAD=new THREE.DataTexture(new Uint8Array([110,185,255]),3,1,THREE.RedFormat);GRAD.minFilter=GRAD.magFilter=THREE.NearestFilter;GRAD.needsUpdate=true;
const toon=c_=>new THREE.MeshStandardMaterial({color:LIN(c_),roughness:.6,metalness:0});
const OLM=new THREE.MeshBasicMaterial({color:0x0b0d1a,side:THREE.BackSide});
function mk(geo,mat,x,y,z,parent,ol){const m=new THREE.Mesh(geo,mat);m.position.set(x,y,z);(parent||scene).add(m);
  if(ol){const o=new THREE.Mesh(geo,OLM);o.scale.setScalar(ol);m.add(o);}return m;}
const B=(w,h,d)=>new THREE.BoxGeometry(w,h,d);
function canvasTex(w,h){const cv=document.createElement('canvas');cv.width=w;cv.height=h;const t=new THREE.CanvasTexture(cv);t.colorSpace=THREE.SRGBColorSpace;t.userData={cv,x:cv.getContext('2d')};return t;}
let seed=7;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};
// ---- pièce : sol, mur, fenêtre (ciel de nuit, d'aube ou de jour selon le décor)
mk(new THREE.PlaneGeometry(40,40),toon(COL.sol),0,0,0).rotation.x=-Math.PI/2;
mk(new THREE.PlaneGeometry(40,14),toon(COL.mur),0,6,-3.3);
const [fx,fy,fw,fh]=DEC.fen;
const city=canvasTex(1024,700);{const x=city.userData.x;const CI={nuit:[['#0b0f2b',0],['#3a2a6a',1]],aube:[['#3a3478',0],['#ff8f6b',.62],['#ffd08a',1]],jour:[['#79c3ff',0],['#d4f0ff',1]]}[DEC.ciel];
  const g=x.createLinearGradient(0,0,0,700);for(const [cl,o] of CI)g.addColorStop(o,cl);x.fillStyle=g;x.fillRect(0,0,1024,700);
  if(DEC.ciel=='aube'){x.fillStyle='#ffe6b0';x.beginPath();x.arc(690,560,80,0,7);x.fill();}
  if(DEC.ciel=='jour'){x.fillStyle='rgba(255,255,255,.85)';for(const [cx,cy,r] of [[200,150,50],[260,140,60],[320,155,45],[700,230,55],[760,215,65],[820,235,48]]){x.beginPath();x.arc(cx,cy,r,0,7);x.fill();}}
  const BAT={nuit:[['#1a1f48',.25],['#252b5e',.45]],aube:[['#3b2f5e',.08],['#523a6a',.12]],jour:[['#9fb3d6',0],['#b8c8e6',0]]}[DEC.ciel];
  for(const [[cl,lit],hmin,hmax] of [[BAT[0],250,520],[BAT[1],150,420]]){let px=-20;while(px<1024){const w=60+rnd()*110,h=hmin+rnd()*(hmax-hmin);x.fillStyle=cl;x.fillRect(px,700-h,w,h);
    for(let wy=700-h+18;wy<690;wy+=34)for(let wx=px+12;wx<px+w-16;wx+=26){x.fillStyle=rnd()<lit?'#ffd27a':(DEC.ciel=='jour'?'#dbe8f7':'#2f3770');x.fillRect(wx,wy,12,18);}px+=w+6;}}}
mk(new THREE.PlaneGeometry(fw,fh),new THREE.MeshBasicMaterial({map:city}),fx,fy,-3.25);
let ciel2=null;if(DEC.ciel2){const c2=canvasTex(1024,700);const x=c2.userData.x;const g=x.createLinearGradient(0,0,0,700);g.addColorStop(0,'#3a3478');g.addColorStop(.62,'#ff8f6b');g.addColorStop(1,'#ffd08a');
  x.fillStyle=g;x.fillRect(0,0,1024,700);x.fillStyle='#ffe6b0';x.beginPath();x.arc(690,560,80,0,7);x.fill();
  for(const [cl,hmin,hmax] of [['#3b2f5e',250,520],['#523a6a',150,420]]){let px=-20;while(px<1024){const w=60+rnd()*110,h=hmin+rnd()*(hmax-hmin);x.fillStyle=cl;x.fillRect(px,700-h,w,h);px+=w+6;}}
  ciel2=mk(new THREE.PlaneGeometry(fw,fh),new THREE.MeshBasicMaterial({map:c2,transparent:true,opacity:0}),fx,fy,-3.24);}
for(const [w,h,x,y] of [[fw+.4,.22,fx,fy+fh/2+.1],[fw+.4,.22,fx,fy-fh/2-.1],[.22,fh+.3,fx-fw/2-.1,fy],[.22,fh+.3,fx+fw/2+.1,fy],[.12,fh,fx,fy],[fw+.2,.1,fx,fy]])mk(B(w,h,.18),toon(COL.cadre),x,y,-3.2);
// horloge
let hhP=null,mhP=null;if(DEC.horloge){const clock=new THREE.Group();clock.position.set(DEC.horloge[0],DEC.horloge[1],-3.05);scene.add(clock);
  mk(new THREE.CylinderGeometry(.55,.55,.08,40),toon(0xf3e6cf),0,0,0,clock,1.06).rotation.x=Math.PI/2;
  const hh=mk(B(.06,.3,.02),toon(0x1b1b22),0,.12,.06,clock),mh=mk(B(.04,.44,.02),toon(0x1b1b22),0,.19,.07,clock);
  hhP=new THREE.Group();clock.add(hhP);hhP.add(hh);mhP=new THREE.Group();clock.add(mhP);mhP.add(mh);}
// ---- écran du décor (moniteur, tableau au mur, télé ou téléphone posé) : c'est là que s'affiche l'interface de la scène
const E=DEC.ecran;const scr=E.type=='mobile'?canvasTex(640,1136):canvasTex(1024,640);
if(E.type=='moniteur'){mk(B(.14,.45,.14),toon(0x2a2e44),E.x,1.3,E.z+.05);mk(B(.6,.05,.4),toon(0x2a2e44),E.x,1.1,E.z+.05);mk(B(E.w+.15,E.h+.11,.1),toon(0x1a1d2e),E.x,E.y,E.z,null,1.02);}
if(E.type=='tableau')mk(B(E.w+.2,E.h+.2,.06),toon('#6b4a32'),E.x,E.y,E.z,null,1.02);
if(E.type=='tele')mk(B(E.w+.12,E.h+.12,.08),toon(0x14151c),E.x,E.y,E.z,null,1.02);
if(E.type=='mobile')mk(B(E.w+.07,E.h+.1,.06),toon(0x111320),E.x,E.y,E.z,null,1.03);
mk(new THREE.PlaneGeometry(E.w,E.h),new THREE.MeshBasicMaterial({map:scr}),E.x,E.y,E.z+(E.type=='moniteur'?.055:.045));
// objets propres au bureau : tasse, livres
if(DEC.objetsBureau){mk(new THREE.CylinderGeometry(.14,.12,.3,24),toon(COL.tasse),1.85,1.23,.35,null,1.06);
  mk(new THREE.TorusGeometry(.08,.025,10,20),toon(COL.tasse),2.0,1.24,.35);
  [0x4f7cff,0xffd23f,0xff6b6b,0x2fd36b].forEach((cl,i)=>mk(B(.7-i*.05,.1,.45),toon(cl),-1.75,1.13+i*.105,.15,null,1.04).rotation.y=(i%2?.12:-.08));}
// haltères (Mental d'Acier, Zéro Salle) et tapis de sport
if(DEC.halteres){const [hx,hy,hz]=DEC.halteres;for(const dz of [0,.45]){const g=new THREE.Group();g.position.set(hx,hy+.09,hz+dz);g.rotation.y=.4;scene.add(g);
  mk(new THREE.CylinderGeometry(.03,.03,.5,12),toon(0x9aa0aa),0,0,0,g).rotation.z=Math.PI/2;
  for(const sx of [-.2,.2])mk(new THREE.CylinderGeometry(.09,.09,.08,20),toon(0x22252e),sx,0,0,g,1.06).rotation.z=Math.PI/2;}}
if(DEC.tapis)mk(B(1.5,.03,2.3),toon(COL.tapis||'#2fd36b'),DEC.M[0],.016,DEC.M[2]);
// ---- mascotte (couleur, arrondi et accessoire propres au compte)
const M=new THREE.Group();M.position.set(...DEC.M);scene.add(M);const MB=DEC.M[1];
const RB=(w,h,d,r)=>new RoundedBoxGeometry(w,h,d,5,r);
const body=mk(RB(1.05,.95,.85,COL.arrondi||.15),toon(COL.mascotte),0,.475,0,M,1.035);
if(COL.accessoire=='bandeau'||COL.accessoire=='serre')mk(RB(1.09,.13,.89,.05),toon(COL.bandeau||'#1b1b22'),0,.84,0,M);
const eyes=[],lids=[],pups=[];
for(const sx of [-1,1]){const e=mk(B(.24,.28,.02),new THREE.MeshBasicMaterial({color:0xd9d9d9}),sx*.22,.56,.43,M);eyes.push(e);
  pups.push(mk(B(.1,.15,.02),new THREE.MeshBasicMaterial({color:0x14141e}),sx*.22+.02,.54,.442,M));
  lids.push(mk(B(.26,.3,.03),toon(COL.mascotte),sx*.22,.72,.445,M));}
const mouth=mk(B(.18,.045,.02),new THREE.MeshBasicMaterial({color:0x14141e}),0,.32,.435,M);
for(const sx of [-1,1])mk(B(.12,.06,.02),new THREE.MeshBasicMaterial({color:0xff9a8a}),sx*.36,.38,.432,M);
const arms=[-1,1].map(sx=>{const p=new THREE.Group();p.position.set(sx*.6,.62,.05);M.add(p);mk(RB(.16,.44,.16,.07),toon(COL.mascotte),0,-.19,0,p,1.08);
  if(COL.accessoire=='serre')mk(RB(.19,.09,.19,.04),toon(COL.bandeau||'#ffffff'),0,-.33,0,p);return p;});
// ---- personnage humain articulé (Mental d'Acier) : silhouette gris clair, poses selon l'humeur
const HUM=COL.personnage=='humain';let F=null;const NV=(x=0,y=0,z=0)=>new THREE.Vector3(x,y,z);
function ik(S,T,a,b,hint){const d0=NV().subVectors(T,S);let d=d0.length();const dir=d0.clone().normalize();d=Math.min(d,a+b-.001);
  const x_=(a*a-b*b+d*d)/(2*d);const h=Math.sqrt(Math.max(0,a*a-x_*x_));const p=hint.clone().addScaledVector(dir,-hint.dot(dir)).normalize();return S.clone().addScaledVector(dir,x_).addScaledVector(p,h);}
function setL(m,a,b){const d=NV().subVectors(b,a);const L=Math.max(.001,d.length());m.position.copy(a).addScaledVector(d,.5);m.quaternion.setFromUnitVectors(NV(0,1,0),d.clone().normalize());m.scale.set(1,L/m.userData.L+.1,1);}
if(HUM){M.visible=false;const MH=new THREE.MeshStandardMaterial({color:LIN(COL.humain||'#d9d9d9'),roughness:.42,metalness:.05});
  const cap=r=>{const m=new THREE.Mesh(new THREE.CapsuleGeometry(r,1,8,18),MH);m.userData.L=1+2*r;m.castShadow=true;scene.add(m);return m;};
  const bal=r=>{const m=new THREE.Mesh(new THREE.SphereGeometry(r,32,24),MH);m.castShadow=true;scene.add(m);return m;};
  F={torso:cap(.13),head:bal(.2),arms:[[cap(.062),cap(.056)],[cap(.062),cap(.056)]],legs:[[cap(.085),cap(.075)],[cap(.085),cap(.075)]],mains:[bal(.062),bal(.062)],pieds:[cap(.068),cap(.068)]};
  F.phone=mk(B(.09,.17,.016),new THREE.MeshBasicMaterial({color:0x8fa3c8}),0,-10,0);F.pl=new THREE.PointLight(0xcfe0ff,0,2.6,2);scene.add(F.pl);}
function poseF(P){setL(F.torso,P.hip,P.sh);const sd=P.side.clone().normalize();const up=NV().subVectors(P.sh,P.hip).normalize();
  F.head.position.copy(P.sh).addScaledVector(up,.28).add(P.look||NV());
  [0,1].forEach(i=>{const s_=i?1:-1;const S=P.sh.clone().addScaledVector(sd,.17*s_);const E_=ik(S,P.hands[i],.32,.3,P.elbow.clone().addScaledVector(sd,.5*s_));
    setL(F.arms[i][0],S,E_);setL(F.arms[i][1],E_,P.hands[i]);F.mains[i].position.copy(P.hands[i]);
    const Hp=P.hip.clone().addScaledVector(sd,.1*s_);const K=P.knees?P.knees[i]:ik(Hp,P.feet[i],.45,.45,P.knee);setL(F.legs[i][0],Hp,K);setL(F.legs[i][1],K,P.feet[i]);
    const fw=(P.toe||NV(0,0,1)).clone().normalize();setL(F.pieds[i],P.feet[i].clone().addScaledVector(fw,-.03),P.feet[i].clone().addScaledVector(fw,.12));});}
function baseHum(hu){return (hu=='telephone'||hu=='fatigue'||hu=='dort'||hu=='triste')?DEC.lit:DEC.sol;}
function poseHum(hu,t){const b=baseHum(hu);const W=(x,y,z)=>NV(b[0]+x,b[1]+y,b[2]+z);let P;F.phone.position.set(0,-10,0);F.pl.intensity=0;
  if(b===DEC.lit){const br=Math.sin(t*1.6)*.01;const ph=W(0,.98,.4);
    P={hip:W(0,.62,0),sh:W(0,1.1+br,.15),hands:[W(-.05,.95,.36),W(.05,.95,.36)],feet:[W(-.15,.07,.52),W(.15,.07,.52)],knees:[W(-.14,.6,.45),W(.14,.6,.45)],
       knee:NV(0,0,1),elbow:NV(0,-1,.3),side:NV(1,0,0),look:NV(0,-.07,.09)};
    if(hu!='triste'){F.phone.position.copy(ph);F.phone.lookAt(F.head.position);const fl=.85+.15*Math.sin(t*7.3)*Math.sin(t*2.1);F.pl.position.copy(ph).add(NV(0,.08,.12));F.pl.intensity=.7*fl;}}
  else if(hu=='sport'){const u=.5+.5*Math.cos(t*2*Math.PI/1.6);const h=.3+.36*u;const F0=W(-.62,.07,0);const L=1.12;const th=Math.asin(Math.min(.95,(h-.07)/L));
    const dir=NV(Math.cos(th),Math.sin(th),0);const S=F0.clone().addScaledVector(dir,L);
    const HP=F0.clone().addScaledVector(dir,.55);P={hip:HP,sh:S,knees:[0,1].map(i=>NV((HP.x+F0.x)/2,(HP.y+F0.y)/2,b[2]+(i?.1:-.1))),hands:[NV(S.x+.04,.04,b[2]-.26),NV(S.x+.04,.04,b[2]+.26)],feet:[NV(F0.x,.05,b[2]-.1),NV(F0.x,.05,b[2]+.1)],
       knee:NV(0,1,0),elbow:NV(-1,0,0),side:NV(0,0,1),look:dir.clone().multiplyScalar(.04),toe:NV(0,-1,0)};}
  else{const jump=hu=='content'?Math.abs(Math.sin(t*5))*.12:0;const sw=Math.sin(t*1.3)*.02;
    const up_=hu=='content';
    P={hip:W(0,.95+jump,0),sh:W(sw,1.45+jump,0),hands:up_?[W(-.42,1.95+jump+.04*Math.sin(t*8),.05),W(.42,1.95+jump,.05)]:[W(-.28,.95+jump,.06),W(.28,.95+jump,.06)],
       feet:[W(-.13,.05+jump,0),W(.13,.05+jump,0)],knee:NV(0,0,1),elbow:up_?NV(0,0,-1):NV(0,-1,-.4),side:NV(1,0,0),look:NV(0,up_?.04:0,.02)};}
  poseF(P);}
// ---- téléphone (fin)
const P=new THREE.Group();P.position.set(...(DEC.tel||[0,-20,0]));scene.add(P);
mk(B(.7,1.3,.07),toon(0x111320),0,.65,0,P,1.03);
const ph=canvasTex(420,780);const phs=mk(new THREE.PlaneGeometry(.62,1.16),new THREE.MeshBasicMaterial({map:ph}),0,.66,.036,P);
// ---- confettis 3D (en plus des confettis CSS)
const CAM=new THREE.PerspectiveCamera(36,1080/1920,.1,60);
const composer=new EffectComposer(R);composer.addPass(new RenderPass(scene,CAM));
const gtao=new GTAOPass(scene,CAM,1080,1920);gtao.updateGtaoMaterial({radius:.35,distanceExponent:1,thickness:1,scale:1});gtao.blendIntensity=.9;composer.addPass(gtao);
const bloom=new UnrealBloomPass(new THREE.Vector2(1080,1920),.32,.45,.9);composer.addPass(bloom);
const bokeh=new BokehPass(scene,CAM,{focus:5,aperture:.0022,maxblur:.007});composer.addPass(bokeh);
composer.addPass(new OutputPass());
// mode allégé sans carte graphique (rendu logiciel SwiftShader, routines cloud) : pas de flou, ombres plus simples
const gl_=R.getContext(),dbg=gl_.getExtension('WEBGL_debug_renderer_info');
const LEGER=/swiftshader|llvmpipe|software/i.test(dbg?gl_.getParameter(dbg.UNMASKED_RENDERER_WEBGL):'');
if(LEGER){bokeh.enabled=false;gtao.enabled=false;key.shadow.mapSize.set(1024,1024);R.shadowMap.type=THREE.PCFShadowMap;bloom.resolution.set(540,960);}
// ampoule de la lampe (brille grâce au bloom) + poussière dans la lumière
mk(new THREE.SphereGeometry(.07,16,12),new THREE.MeshBasicMaterial({color:0xffe2b0}),DEC.lampe[0],DEC.lampe[1],DEC.lampe[2]-.03);
const NP=140,pp=new Float32Array(NP*3);for(let i=0;i<NP;i++){const Q=DEC.poussiere;pp[i*3]=Q[0]+rnd()*Q[3];pp[i*3+1]=Q[1]+rnd()*Q[4];pp[i*3+2]=Q[2]+rnd()*Q[5];}
const dustG=new THREE.BufferGeometry();dustG.setAttribute('position',new THREE.BufferAttribute(pp,3));
const dust=new THREE.Points(dustG,new THREE.PointsMaterial({color:0xffd9a0,size:.022,transparent:true,opacity:.75,depthWrite:false}));scene.add(dust);
// modèles CC0 (Kenney Furniture Kit), passés en matériau cartoon, posés à la bonne taille
const LD=new GLTFLoader();
function b64buf(s_){const bin=atob(s_);const u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);return u.buffer;}
function modele(nom){return new Promise((ok,ko)=>LD.parse(b64buf(MODELES[nom]),'',g=>ok(g.scene),ko));}
function toonify(o,teinte){o.traverse(m=>{if(m.isMesh){const c_=teinte?LIN(teinte):(m.material.color?m.material.color.clone():new THREE.Color(1,1,1));m.material=new THREE.MeshStandardMaterial({color:c_,roughness:.62,metalness:0});}});}
function poser(o,q){let b=new THREE.Box3().setFromObject(o);const sz=b.getSize(new THREE.Vector3());
  if(q.libre)o.scale.set(q.w/sz.x,q.h/sz.y,q.d/sz.z);else{const k_=q.h?q.h/sz.y:q.w/sz.x;o.scale.setScalar(k_);}
  const g=new THREE.Group();g.add(o);b=new THREE.Box3().setFromObject(o);const c2=b.getCenter(new THREE.Vector3());o.position.sub(new THREE.Vector3(c2.x,b.min.y,c2.z));
  g.position.set(q.x,q.y||0,q.z);g.rotation.y=q.ry||0;scene.add(g);return g;}
async function charger(){
  const P_=DEC.meubles;
  for(const [n,q,teinte] of P_){if(!MODELES[n])continue;const o=await modele(n);toonify(o,teinte=='BOIS'?COL.bois:teinte);poser(o,q);}
  scene.traverse(o=>{if(o.isMesh&&o.material!==OLM&&!(o.material&&o.material.isMeshBasicMaterial)){o.castShadow=true;o.receiveShadow=true;}});}

const PLANS=DEC.plans;
const V=(a)=>new THREE.Vector3(a[0],a[1],a[2]);
function plan(k){if(HUM&&SC[k].plan=='mascotte'){const b=baseHum(SC[k].humeur);return [[b[0]+.55,1.55,b[2]+4.0],[b[0],.9,b[2]]];}return PLANS[SC[k].plan]||PLANS.large;}
// ---- dessin de l'écran selon la scène
function rr(x,X,Y,W,H,r,f){x.beginPath();x.roundRect(X,Y,W,H,r);x.fillStyle=f;x.fill();}
function screenDraw(k,p,t){let kk=k;while(kk>0&&!SC[kk].ecran)kk--;if(kk!=k)p=1;const s=SC[kk].ecran||{type:'vide'};const x=scr.userData.x,SW=scr.userData.cv.width,SH=scr.userData.cv.height;
  const tab=E.type=='tableau';x.fillStyle=tab?'#22322a':'#0f1222';x.fillRect(0,0,SW,SH);
  if(!tab){x.fillStyle='#1a1e36';x.fillRect(0,0,SW,56);['#ff5f57','#febc2e','#28c840'].forEach((cl,i)=>{x.beginPath();x.arc(34+i*30,28,10,0,7);x.fillStyle=cl;x.fill();});
    x.fillStyle='#9aa3c7';x.font='600 26px Inter';x.fillText(s.titre||'Claude',140,37);}
  else{x.fillStyle='#f4ecdc';x.font='700 40px Inter';x.textAlign='center';x.fillText(s.titre||'',SW/2,58);x.textAlign='left';}
  const T=s.type;
  if(T=='bazar'){for(let i=0;i<14;i++){const y=90+i*36;let X=40;for(let j=0;j<6;j++){const w=40+((i*7+j*13)%9)*16+Math.sin(t*3+i+j)*8;rr(x,X,y,w,22,6,['#ff6b6b','#ffd23f','#4f7cff','#2fd36b','#c56bff'][(i+j)%5]);X+=w+10;}}
    x.fillStyle='#ff6b6b';x.font='700 30px Inter';x.fillText('Rendu… '+Math.floor(12+p*70)+' %  (reste '+Math.max(1,5-Math.floor(p*4))+' h)',40,612);}
  if(T=='chat'){let y=90;const ms=s.messages||[];const per=1/Math.max(1,ms.length);const MW=Math.min(620,SW-180);
    ms.forEach((m,i)=>{const q=c((p-i*per)/(per*.8));if(q<=0)return;const txt=m[1].slice(0,Math.ceil(m[1].length*q));x.font='600 34px Inter';
      const lines=[];let cur='';for(const w of txt.split(' ')){if(x.measureText(cur+' '+w).width>MW){lines.push(cur);cur=w;}else cur=cur?cur+' '+w:w;}lines.push(cur);
      const h=30+lines.length*44, W=Math.min(MW+80,Math.max(...lines.map(l=>x.measureText(l).width))+56), X=m[0]=='moi'?SW-W-30:30;
      rr(x,X,y,W,h,26,m[0]=='moi'?COL.acc:'#232842');x.fillStyle='#fff';lines.forEach((l,j)=>x.fillText(l,X+28,y+52+j*44));y+=h+24;});}
  if(T=='montage'){rr(x,362,76,300,230,14,'#232842');rr(x,452,120,120,130,20,COL.mascotte);x.fillStyle='#fff';x.fillRect(478,160,22,28);x.fillRect(524,160,22,28);
    const tr=[['V1',COL.acc],['A1','#4f7cff'],['TXT',COL.jaune]];tr.forEach(([n,cl],i)=>{const y=350+i*82;x.fillStyle='#7e86ad';x.font='700 26px Inter';x.fillText(n,30,y+36);
      const nb=Math.floor(c(p*1.3-i*.12)*7);for(let j=0;j<nb;j++)rr(x,110+j*126,y+8,112,46,8,cl);});
    const ph_=110+c(p)*880;x.fillStyle='#fff';x.fillRect(ph_,330,4,280);
    x.font='700 28px Inter';x.fillStyle='#2fd36b';const tags=['✓ coupes','✓ sous-titres','✓ musique sous la voix'];tags.forEach((g,i)=>{if(p>.25+i*.22)x.fillText(g,700,110+i*52);});}
  if(T=='verif'||T=='liste'){const L=s.lignes||[];const pas=Math.min(104,(SH-130)/Math.max(1,L.length));L.forEach((l,i)=>{const y=100+i*pas;const q=p>(i+.5)/(L.length+.5);rr(x,40,y,SW-80,pas-22,16,tab?'#2d4236':'#1a1e36');
      x.font='600 34px Inter';x.fillStyle=tab?'#f4ecdc':'#e6e9ff';x.fillText(l,120,y+(pas-22)/2+12);x.beginPath();x.arc(78,y+(pas-22)/2,20,0,7);x.fillStyle=q?'#2fd36b':(tab?'#4a6255':'#3a4066');x.fill();
      if(q){x.strokeStyle='#0f1222';x.lineWidth=6;x.beginPath();x.moveTo(68,y+(pas-22)/2);x.lineTo(76,y+(pas-22)/2+9);x.lineTo(90,y+(pas-22)/2-9);x.stroke();}});}
  if(T=='calendrier'){const N=s.jours||30,col=6,rows=Math.ceil(N/col),fait=Math.floor(c(p*1.2)*(s.jusqua??N));const top=90,cw=(SW-80)/col,ch=(SH-top-30)/rows;
    for(let i=0;i<N;i++){const X=40+(i%col)*cw,Y=top+Math.floor(i/col)*ch;const ok=i<fait;rr(x,X+5,Y+5,cw-10,ch-10,12,ok?'#2fd36b':(i==fait?COL.acc:(tab?'#2d4236':'#232842')));
      x.fillStyle=ok?'#0f1222':'#f4ecdc';x.font='700 30px Inter';x.textAlign='center';x.fillText(ok?'✓':String(i+1),X+cw/2,Y+ch/2+10);x.textAlign='left';}}
  if(T=='timer'){const tot=s.secondes||30,rest=Math.max(0,Math.ceil(tot*(1-c(p*1.05))));const cx=SW/2,cy=SH*.56,r=Math.min(SW,SH)*.3;
    x.lineWidth=26;x.strokeStyle='#2a2f4a';x.beginPath();x.arc(cx,cy,r,0,7);x.stroke();x.strokeStyle=COL.acc;x.beginPath();x.arc(cx,cy,r,-Math.PI/2,-Math.PI/2+2*Math.PI*(rest/tot));x.stroke();
    x.fillStyle='#fff';x.font='800 110px Inter';x.textAlign='center';x.fillText(rest+' s',cx,cy+38);x.font='800 46px Inter';x.fillText(s.exo||'',cx,122);
    x.font='600 32px Inter';x.fillStyle='#9aa3c7';x.fillText(s.sous||'',cx,SH-30);x.textAlign='left';}
  scr.needsUpdate=true;}
function phoneDraw(p,t){const x=ph.userData.x;const g=x.createLinearGradient(0,0,0,780);g.addColorStop(0,'#7b5cff');g.addColorStop(1,'#ff5fa2');x.fillStyle=g;x.fillRect(0,0,420,780);
  rr(x,150,230,120,110,26,COL.mascotte);x.fillStyle='#fff';x.fillRect(176,268,20,26);x.fillRect(224,268,20,26);
  rr(x,130,380,160,44,10,COL.jaune);x.fillStyle='#1b2147';x.font='800 24px Inter';x.fillText('MA VIDÉO',150,410);
  x.fillStyle='#fff';x.font='800 30px Inter';x.fillText('♥ '+(1+Math.floor(eo(p)*120)/10).toFixed(1)+' k',150,500);
  rr(x,110,620,200,64,32,'#2fd36b');x.fillStyle='#fff';x.font='800 32px Inter';x.fillText('POSTÉ ✓',140,664);ph.needsUpdate=true;}
const CF=[...document.querySelectorAll('.cf')];
const RENDER=function(t){
  let k=0;SC.forEach((s,i)=>{if(t>=s.a)k=i;});const s=SC[k],p=c((t-s.a)/Math.max(.1,s.b-s.a)),tl=t-s.a;
  // caméra : glisse du plan précédent au plan de la scène, avec une petite respiration
  const to=plan(k),fr=k>0?plan(k-1):[[to[0][0],to[0][1]+.3,to[0][2]*1.12],to[1]];const q=sm(tl/.8);
  CAM.position.copy(V(fr[0]).lerp(V(to[0]),q)).add(new THREE.Vector3(Math.sin(t*.5)*.08,Math.sin(t*.7)*.04,-p*.25));
  const LA=V(fr[1]).lerp(V(to[1]),q);CAM.lookAt(LA);bokeh.uniforms.focus.value=CAM.position.distanceTo(LA);
  CAM.position.x+=Math.sin(t*1.7)*.012+Math.sin(t*3.1)*.006;CAM.position.y+=Math.sin(t*2.3)*.01;  // caméra « tenue à la main »
  // horloge (les heures défilent pendant la scène « bazar »)
  if(hhP){const sp=(s.ecran&&s.ecran.type=='bazar')?2.2:.05;hhP.rotation.z=-t*sp/12;mhP.rotation.z=-t*sp;}
  // mascotte selon l'humeur : normal, fatigue, travail, content, sport (squats), triste, dort, pensif
  const hu=s.humeur||'normal';const tired=(hu=='fatigue'||hu=='triste')?1:0,dort=hu=='dort';
  lids.forEach(l=>{l.position.y=dort?.56:.72-(tired?.12:0)-((t%3.3)<.12?.17:0);});
  pups.forEach((pp,i)=>{pp.position.x=(i?1:-1)*.22+.02+Math.sin(t*.9)*.015*(1-tired);pp.position.y=.54-(tired?.05:0)+(hu=='pensif'?.06:0);});
  body.rotation.z=tired?Math.sin(t*1.2)*.04:0;
  const jump=hu=='content'?Math.abs(Math.sin(t*6)):0,squat=hu=='sport'?Math.abs(Math.sin(t*3.2)):0;M.position.y=MB+jump*.14;
  let sq=1+Math.sin(t*(dort?1.2:2.2))*(dort?.025:.012);if(hu=='content')sq=jump<.25?1-(.25-jump)*.5:1+jump*.05;if(hu=='sport')sq=1-squat*.22;
  M.scale.set(1/Math.sqrt(sq),sq,1/Math.sqrt(sq));  // écrasement / étirement
  M.rotation.y=hu=='travail'?.32:(hu=='content'?Math.sin(t*3)*.12:(hu=='pensif'?-.28:.12));M.rotation.x=hu=='triste'?.12:0;
  mouth.scale.set(hu=='content'?1.6:(hu=='sport'?1.2:1),hu=='content'?2.4:(hu=='sport'?1.8:(tired?.7:1)),1);
  arms.forEach((a,i)=>{a.rotation.x=hu=='travail'?-1.1+Math.sin(t*16+i*2)*.25:(hu=='sport'?-1.45*squat:(hu=='pensif'&&i?-1.9:0));
    a.rotation.z=hu=='content'?(i?-1:1)*(1.9+Math.sin(t*9)*.3):(hu=='triste'?(i?.04:-.04):(i?.12:-.12));});
  if(HUM)poseHum(hu,t);
  if(ciel2){let aube=0;SC.forEach((z,i)=>{if(i<=k&&z.lumiere=='aube')aube=i==k?c(tl/1.5):1;});ciel2.material.opacity=aube;
    key.color.setRGB(.55+.45*aube,.62+.2*aube,.85-.3*aube);key.intensity=.9+1.9*aube;lamp.intensity=3.2*(1-aube)+.4;}
  // téléphone : visible quand la scène le demande
  const showP=(s.plan=='telephone'||(s.tampon&&!HUM))&&DEC.tel;P.visible=!!showP;if(showP){P.scale.setScalar(back(tl/.5));phoneDraw(p,t);}
  screenDraw(k,p,t);
  const dp=dust.geometry.attributes.position;for(let i=0;i<NP;i++){dp.array[i*3+1]=DEC.poussiere[1]+((pp[i*3+1]-DEC.poussiere[1]+t*.05*(1+i%3))%DEC.poussiere[4]);}dp.needsUpdate=true;
  composer.render();
  // habillage HTML
  SC.forEach((z,i)=>{const b=$('bd'+i);if(b){const on=i==k;const kk=back((t-z.a)/.4);b.style.opacity=on?1:0;b.style.transform=`translateX(-50%) rotate(-1.5deg) scale(${on?.6+.4*kk:1})`;}
    const g=$('bg'+i);if(g){const on=i==k;g.style.opacity=on?c((t-z.a-.2)/.2):0;const cc=z.compteur;g.querySelector('i').textContent=cc.fmt?cc.fmt.replace('#',Math.round(cc.de+(cc.a-cc.de)*sm(p*1.15))):Math.round(cc.de+(cc.a-cc.de)*sm(p*1.15));}
    const fn=$('fn'+i);if(fn){const kk=back((t-z.a-.15)/.45);fn.style.opacity=i==k?c((t-z.a-.15)/.15):0;fn.style.transform=`scale(${.6+.4*kk})`;}
    const tp=$('tp'+i);if(tp){const ta=z.a+.25*(z.b-z.a);const kk=c((t-ta)/.18);tp.style.opacity=t>=ta&&i==k?1:0;tp.style.transform=`translateX(-50%) rotate(-7deg) scale(${2.2-1.2*kk})`;}});
  for(const cp of document.querySelectorAll('.cap')){const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'flex':'none';
    for(const w of cp.querySelectorAll('.stk')){const wt=+w.dataset.w;const kk=back((t-wt)/.22);w.style.opacity=t>=wt?1:0;w.style.transform=`rotate(${w.dataset.r}deg) scale(${t>=wt?.5+.5*kk:.5})`;}}
  const ct=SC.findIndex(z=>z.tampon);if(ct>=0){const t0=SC[ct].a+.25*(SC[ct].b-SC[ct].a);CF.forEach((f,i)=>{const u=t-t0-(i%7)*.05;const on=u>0;f.style.opacity=on?1:0;
    if(on){f.style.left=(+f.dataset.x+Math.sin(u*3+i)*40)+'px';f.style.top=(-60+u*(380+(i%5)*60))+'px';f.style.transform=`rotate(${u*(200+i*17)}deg)`;}});}
};
charger().then(()=>{window.render=RENDER;RENDER(0);});
</script></body></html>"""


ASSETS = os.path.join(DOSSIER, "assets")


def import_map():
    """three.module.js + modules complémentaires (r149) en data: URLs ; les imports relatifs sont réécrits en 'three/addons/...'."""
    base = os.path.join(ASSETS, "three186")
    def url(txt):
        return "data:text/javascript;base64," + base64.b64encode(txt.encode("utf-8")).decode()
    mod = open(os.path.join(base, "build", "three.module.js"), encoding="utf-8").read().replace("'./three.core.js'", "'three/core'")
    m = {"three": url(mod), "three/core": url(open(os.path.join(base, "build", "three.core.js"), encoding="utf-8").read())}
    jsm = os.path.join(base, "jsm")
    for d in sorted(os.listdir(jsm)):
        for f in sorted(os.listdir(os.path.join(jsm, d))):
            txt = open(os.path.join(jsm, d, f), encoding="utf-8").read()
            txt = re.sub(r"from '\./([\w]+\.js)'", lambda x: f"from 'three/addons/{d}/{x.group(1)}'", txt)
            txt = re.sub(r"from '\.\./(\w+)/([\w]+\.js)'", lambda x: f"from 'three/addons/{x.group(1)}/{x.group(2)}'", txt)
            m[f"three/addons/{d}/{f}"] = url(txt)
    return json.dumps({"imports": m})


def modeles():
    d = os.path.join(ASSETS, "modeles")
    return json.dumps({f[:-4]: base64.b64encode(open(os.path.join(d, f), "rb").read()).decode() for f in sorted(os.listdir(d)) if f.endswith(".glb")})


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
    colj = dict(col, decor=spec.get("decor", "bureau"))
    S = [dict(z, lumiere=sc[i].get("lumiere")) for i, z in enumerate(S)]
    colj["bois_hex"] = col["bois"]
    R = {"__FONTS__": K._font_faces(["Anton", "Archivo Black", "Inter"]), "__NUIT__": col["nuit"], "__PAPIER__": col["papier"], "__ENCRE__": col["encre"],
         "__ACC__": col["acc"], "__JAUNE__": col["jaune"], "__VERT__": col["vert"], "__BANDFOND__": col.get("bandeau_fond", col["papier"]), "__BANDTEXTE__": col.get("bandeau_texte", col["encre"]), "__BADGEFOND__": col.get("badge_fond", "#ffffff"), "__BADGETEXTE__": col.get("badge_texte", col["encre"]), "__TEXTEO__": col.get("texte_o", "#ffffff"), "__HANDLE__": H.escape(spec.get("handle", "")),
         "__BANDS__": bands, "__BADGES__": badges, "__CAPS__": cap_html, "__TAMPONS__": tampons, "__FINS__": fins, "__CONFETTIS__": conf,
         "__IMPORTMAP__": import_map(), "__MODELES__": modeles(), "__D__": str(total), "__SC__": json.dumps(S, ensure_ascii=False), "__EV__": json.dumps(ev), "__COL__": json.dumps(colj)}
    out = TPL
    for kk, v in R.items():
        if kk != "__THREE__":
            out = out.replace(kk, v)
    return out
