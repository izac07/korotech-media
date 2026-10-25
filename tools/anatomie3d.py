#!/usr/bin/env python3
"""Layout « anatomie3d » (PILOTE 25/10/2026, Zéro Salle) : mannequin humain en argile sur fond studio sombre, qui fait l'exercice ;
la zone qui travaille s'allume en orange (muscle strié qui pulse), compteur « DAY » + semaine en haut à gauche, sous-titres mot par mot.
Inspiré du format « Vital Mechanism ». Mannequin et animations : Quaternius Universal Animation Library (CC0, tools/assets/humains/).
Les poses d'exercice (pompes, gainage, squat, suspension) sont calculées par cinématique inverse à deux os ; les autres viennent des clips.
Appelé par tools/motion.py (layout "anatomie3d") : voix, musique, bruitages et contrôle sont communs. Rendu sur le PC de Goat (carte graphique).

Spec : {"layout": "anatomie3d", "serie"?: {"label": "DAY", "de": 0, "a": 30}, "couleurs"?: {"acc", "jaune", "fond"},
        "scenes": [{"type": plan ("large" | "face" | "cote" | "muscle" | "orbite"), "vo", "exercice": "pompes" | "gainage" | "squat" |
                    "suspension" | <clip> ("Idle_Loop", "Sitting_Idle_Loop", "Crouch_Idle_Loop", "Jump_Loop", "Jog_Fwd_Loop"…),
                    "reps"?: répétitions pendant la scène (0 = position tenue), "muscle"?: "avant-bras" | "bras" | "epaules" | "pectoraux" |
                    "abdos" | "cuisses" | "mollets" | "fessiers", "jour"?: valeur du compteur à la fin de la scène, "bandeau"?, "question"?, "carte"?}]}
"""
import json, os, base64, html as H
import korotech as K
import studio3d as S3

DOSSIER = os.path.dirname(os.path.abspath(__file__))
MANNEQUIN = os.path.join(DOSSIER, "assets", "humains", "mannequin.glb")
EXERCICES = ("pompes", "gainage", "squat", "suspension")
MUSCLES = {"avant-bras": ["forearm.L", "forearm.R", "hand.L", "hand.R"], "bras": ["upper_arm.L", "upper_arm.R"],
           "epaules": ["shoulder.L", "shoulder.R"], "pectoraux": ["spine.003"], "abdos": ["spine.001", "spine.002"],
           "cuisses": ["thigh.L", "thigh.R"], "mollets": ["shin.L", "shin.R"], "fessiers": ["hips"]}

TPL = r"""<!doctype html><html><head><meta charset='utf-8'><style>__FONTS__
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:__FOND__;position:relative}
canvas#cv{position:absolute;left:0;top:0}
.hdl{position:absolute;left:56px;bottom:70px;font:700 30px Inter;color:#fff;opacity:.45;z-index:5}
.hud{position:absolute;left:56px;top:150px;z-index:6;color:#fff;opacity:0}
.hud .l{font:400 34px Anton;letter-spacing:4px;opacity:.85}.hud .n{font:400 120px/1 Anton;font-variant-numeric:tabular-nums;letter-spacing:2px}
.hud .bar{width:300px;height:10px;border-radius:6px;background:rgba(255,255,255,.18);margin-top:12px;overflow:hidden}.hud .bar i{display:block;height:100%;width:0;background:__ACC__;border-radius:6px}
.wk{position:absolute;right:60px;top:170px;z-index:6;font:400 40px Anton;letter-spacing:3px;color:__FOND__;background:__JAUNE__;padding:8px 22px 4px;border-radius:10px;opacity:0}
.caps{position:absolute;left:60px;right:60px;top:440px;z-index:7;display:flex;justify-content:center}
.cap{display:none;flex-wrap:wrap;justify-content:center;gap:6px 22px;max-width:960px}
.w{font:400 96px/1.08 'Archivo Black';color:#fff;text-transform:lowercase;text-shadow:0 6px 0 rgba(0,0,0,.55),0 0 30px rgba(0,0,0,.6);opacity:0}
.w.h{color:__JAUNE__}
.band{position:absolute;left:50%;top:330px;transform:translateX(-50%);z-index:6;white-space:nowrap;opacity:0;font:400 54px Anton;letter-spacing:2px;color:#fff;
  background:rgba(0,0,0,.55);border:3px solid __ACC__;padding:10px 30px 6px;border-radius:12px;text-transform:uppercase}
.q{position:absolute;left:70px;right:70px;top:1270px;z-index:8;text-align:center;opacity:0}
.q span{display:inline-block;font:400 70px/1.12 Anton;text-transform:uppercase;color:__FOND__;background:__JAUNE__;padding:16px 34px 10px;border-radius:16px;box-shadow:0 10px 0 rgba(0,0,0,.45)}
.fin{position:absolute;left:90px;right:90px;top:1180px;z-index:8;display:flex;flex-direction:column;align-items:center;gap:22px;opacity:0}
.fin b{font:400 108px/1 Anton;background:__ACC__;color:#fff;padding:16px 44px 10px;border-radius:18px;box-shadow:0 10px 0 rgba(0,0,0,.45)}
.fin span{font:400 52px/1.15 'Archivo Black';background:#fff;color:#111;padding:10px 26px;border-radius:12px;text-align:center}
</style></head><body>
<canvas id='cv' width='1080' height='1920'></canvas>
<div class='hdl'>@__HANDLE__</div>
<div class='hud' id='hud'><div class='l'>__LABEL__</div><div class='n' id='hn'>00</div><div class='bar'><i id='hb'></i></div></div>
<div class='wk' id='wk'>WEEK 1</div>
<div class='caps'>__CAPS__</div>
__BANDS__
__QUESTIONS__
__FINS__
<script type='importmap'>__IMPORTMAP__</script>
<script type='module'>
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {BokehPass} from 'three/addons/postprocessing/BokehPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const D=__D__, SC=__SC__, COL=__COL__, SERIE=__SERIE__, MUSCLES=__MUSCLES__;
const c=x=>Math.max(0,Math.min(1,x)), sm=x=>{x=c(x);return x*x*(3-2*x);};
const back=x=>{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const $=i=>document.getElementById(i);
const LEGER=/swiftshader|llvmpipe/i.test((()=>{const g=document.createElement('canvas').getContext('webgl');const e=g&&g.getExtension('WEBGL_debug_renderer_info');return e?g.getParameter(e.UNMASKED_RENDERER_WEBGL):'';})());
const R=new THREE.WebGLRenderer({canvas:$('cv'),antialias:true,preserveDrawingBuffer:true});
R.setSize(1080,1920,false);R.toneMapping=THREE.NeutralToneMapping;R.shadowMap.enabled=true;
const scene=new THREE.Scene();
// fond studio : halo chaud derrière le mannequin, bords presque noirs
{const cv=document.createElement('canvas');cv.width=512;cv.height=1024;const x=cv.getContext('2d');const g=x.createRadialGradient(256,470,30,256,560,720);
 g.addColorStop(0,COL.halo);g.addColorStop(.55,COL.fond2);g.addColorStop(1,'#050403');x.fillStyle=g;x.fillRect(0,0,512,1024);
 const t=new THREE.CanvasTexture(cv);t.colorSpace=THREE.SRGBColorSpace;scene.background=t;}
const pm=new THREE.PMREMGenerator(R);scene.environment=pm.fromScene(new RoomEnvironment(),.04).texture;scene.environmentIntensity=.22;
const key=new THREE.DirectionalLight(0xffe6cc,3.0);key.position.set(2.5,4.5,3);key.castShadow=true;key.shadow.mapSize.set(2048,2048);
Object.assign(key.shadow.camera,{left:-3,right:3,top:3,bottom:-3});key.shadow.bias=-.0004;scene.add(key);
const rim1=new THREE.DirectionalLight(0xffb27a,4);rim1.position.set(-3,2.5,-3);scene.add(rim1);
const rim2=new THREE.DirectionalLight(0xffd6b0,2.2);rim2.position.set(3,2,-3);scene.add(rim2);
scene.add(new THREE.HemisphereLight(0x3a2a20,0x050403,.6));
const sol=new THREE.Mesh(new THREE.CircleGeometry(9,64),new THREE.ShadowMaterial({opacity:.5}));sol.rotation.x=-Math.PI/2;sol.receiveShadow=true;scene.add(sol);
const cam=new THREE.PerspectiveCamera(30,1080/1920,.05,60);
const comp=new EffectComposer(R);comp.addPass(new RenderPass(scene,cam));
const bloom=new UnrealBloomPass(new THREE.Vector2(540,960),.55,.55,.82);comp.addPass(bloom);
const bokeh=LEGER?null:new BokehPass(scene,cam,{focus:2.5,aperture:.0016,maxblur:.006});if(bokeh)comp.addPass(bokeh);
comp.addPass(new OutputPass());
// argile + muscle lumineux : la zone est choisie par les poids de peau (os du squelette), stries orange qui pulsent
const U={uI:{value:new Array(8).fill(-1)},uG:{value:0},uT:{value:0}};
const argile=new THREE.MeshPhysicalMaterial({color:new THREE.Color(COL.argile),roughness:.66,metalness:0,sheen:.5,sheenRoughness:.55,sheenColor:new THREE.Color(0xffd2a8)});
argile.onBeforeCompile=sh=>{Object.assign(sh.uniforms,U);
  sh.vertexShader=sh.vertexShader.replace('#include <common>','#include <common>\nuniform float uI[8];varying float vG;varying vec3 vP;')
    .replace('#include <skinning_vertex>','#include <skinning_vertex>\nvG=0.;vP=position;\n#ifdef USE_SKINNING\nfor(int i=0;i<4;i++){for(int j=0;j<8;j++){if(abs(skinIndex[i]-uI[j])<.5)vG+=skinWeight[i];}}\n#endif\nvG=smoothstep(.25,.85,vG);');
  sh.fragmentShader=sh.fragmentShader.replace('#include <common>','#include <common>\nuniform float uG,uT;varying float vG;varying vec3 vP;')
    .replace('#include <emissivemap_fragment>',`#include <emissivemap_fragment>
      // stries fines dans le sens des membres (axe vertical du maillage au repos = z), légèrement ondulées
      float fib=.5+.5*sin((vP.x*.8+vP.y)*520.+sin(vP.z*38.+vP.x*60.)*1.8);fib=pow(fib,3.);
      float gl=vG*uG;vec3 mus=mix(vec3(.5,.04,.01),vec3(1.,.42,.1),fib);
      diffuseColor.rgb=mix(diffuseColor.rgb,mus*.45,gl*.95);
      totalEmissiveRadiance+=mus*gl*(.3+1.6*fib);`);};
const metal=new THREE.MeshStandardMaterial({color:0x1b1715,roughness:.35,metalness:.8});
const buf=Uint8Array.from(atob('__GLB__'),ch=>ch.charCodeAt(0)).buffer;
__POSES__
let P=null,MESH=null,BONE=null,corps=null;
const charger=()=>new Promise(ok=>new GLTFLoader().parse(buf,'',gl=>{const m=gl.scene;
  m.traverse(o=>{if(o.isMesh){o.material=argile;o.castShadow=true;o.receiveShadow=true;o.frustumCulled=false;if(o.isSkinnedMesh)MESH=o;}});
  corps=new THREE.Group();corps.add(m);scene.add(corps);P=creerPoses(THREE,corps,m,gl.animations,scene,metal);ok();}));
// plans de caméra (cadrés sur le corps), transitions douces entre scènes
const box=new THREE.Box3(),ctr=new THREE.Vector3(),siz=new THREE.Vector3();
function plan(s,t,p){P.poser(s.exercice||'Idle_Loop',s.u,t);box.setFromObject(corps,true);if(P.barre.visible)box.expandByObject(P.barre);box.getCenter(ctr);box.getSize(siz);
  // recul nécessaire en hauteur ET en largeur (format vertical 9:16) : un corps allongé (pompes) se cadre par sa longueur
  const lw=s.plan=='cote'?siz.z:s.plan=='face'?siz.x:Math.max(siz.x,siz.z*.8),h=Math.max(siz.y,lw/cam.aspect*.92,.9),dist=h/(2*Math.tan(THREE.MathUtils.degToRad(15)))*1.12;
  const o=new THREE.Vector3(),l=ctr.clone();
  if(s.plan=='muscle'&&s.muscle){const zs=MUSCLES[s.muscle]||[],zl=zs.filter(n=>n.endsWith('.L'));const os=(zl.length?zl:zs).map(n=>P.B(n)).filter(Boolean);const mp=new THREE.Vector3();os.forEach(b=>mp.add(P.wp(b)));mp.divideScalar(Math.max(1,os.length));
    // gros plan sur un seul côté (sinon on vise le milieu, la tête), de 3/4, un peu au-dessus quand la zone est haute
    l.copy(mp);const a=(zl.length?.95:.6)+.25*p;o.set(Math.sin(a),mp.y>ctr.y+.3?.3:.15,Math.cos(a)).normalize().multiplyScalar(1.05);}
  else if(s.plan=='cote'){o.set(dist*.97,h*.12,dist*.22);}
  else if(s.plan=='face'){o.set(dist*.08,h*.1,dist);}
  else if(s.plan=='orbite'){const a=-.6+1.2*p;o.set(Math.sin(a)*dist,h*.15,Math.cos(a)*dist);}
  else{o.set(dist*.55,h*.18,dist*.84);}
  o.multiplyScalar(1-.05*p);return [l.clone().add(o),l];}
const RENDER=function(t){
  let k=SC.findIndex(z=>t>=z.a&&t<z.b);if(k<0)k=t<SC[0].a?0:SC.length-1;const s=SC[k],tl=t-s.a,p=c(tl/Math.max(.1,s.b-s.a));
  // mouvement de l'exercice : répétitions (aller-retour) ou position tenue avec un léger tremblement
  const reps=s.reps??0;s.u=reps>0?.5-.5*Math.cos(2*Math.PI*reps*p):(s.exercice=='suspension'?0:s.exercice=='squat'?.95:0)+.012*Math.sin(t*9);
  const [cp,cl]=plan(s,t,p);   // coupe franche entre les scènes (comme la référence), mouvement lent à l'intérieur
  cam.position.copy(cp);cam.lookAt(cl);window.DBG={k,cp:cp.toArray().map(v=>+v.toFixed(2)),cl:cl.toArray().map(v=>+v.toFixed(2)),ctr:ctr.toArray().map(v=>+v.toFixed(2)),siz:siz.toArray().map(v=>+v.toFixed(2))};if(bokeh)bokeh.uniforms.focus.value=cp.distanceTo(cl);
  // muscle : indices des os de la zone, s'allume en entrant dans la scène et pulse avec l'effort
  const ids=(MUSCLES[s.muscle]||[]).map(n=>MESH.skeleton.bones.indexOf(P.B(n))).filter(i=>i>=0);U.uI.value=ids.concat(new Array(8).fill(-1)).slice(0,8);
  U.uG.value=s.muscle?sm(tl/.8)*(.75+.35*(reps>0?s.u:.5+.5*Math.sin(t*5))):0;U.uT.value=t;
  comp.render();
  // compteur DAY + semaine
  const hud=$('hud');if(SERIE){let j0=SERIE.de,j1=SERIE.de;SC.forEach((z,i)=>{if(i<k&&z.jour!=null)j0=z.jour;});j1=s.jour??j0;
    const j=Math.round(j0+(j1-j0)*sm(p*1.4));hud.style.opacity=s.carte?0:c(t/.3);$('hn').textContent=String(j).padStart(2,'0');
    $('hb').style.width=(100*j/Math.max(1,SERIE.a))+'%';const wk=$('wk');wk.style.opacity=hud.style.opacity;wk.textContent='WEEK '+Math.max(1,Math.ceil(Math.max(j,1)/7));}
  else{hud.style.opacity=0;$('wk').style.opacity=0;}
  SC.forEach((z,i)=>{const b=$('bd'+i);if(b){b.style.opacity=i==k?c(tl/.25):0;}
    const q=$('q'+i);if(q){const on=i==k&&tl>.2;q.style.opacity=on?1:0;q.style.transform=`scale(${on?.6+.4*back((tl-.2)/.4):.6}) rotate(-2deg)`;}
    const fn=$('fn'+i);if(fn){fn.style.opacity=i==k?c((tl-.15)/.15):0;fn.style.transform=`scale(${.6+.4*back((tl-.15)/.45)})`;}});
  for(const cp_ of document.querySelectorAll('.cap')){const a=+cp_.dataset.a,b=+cp_.dataset.b;const on=t>=a&&t<b&&!s.carte;cp_.style.display=on?'flex':'none';
    if(on)for(const w of cp_.querySelectorAll('.w')){const wt=+w.dataset.w;const kk=back((t-wt)/.18);w.style.opacity=t>=wt?1:0;w.style.transform=`scale(${t>=wt?.7+.3*kk:.7})`;}}
};
charger().then(()=>{window.render=RENDER;RENDER(0);});
</script></body></html>"""


def poses_js():
    return open(os.path.join(DOSSIER, "anatomie3d_poses.js"), encoding="utf-8").read()


def page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]
    col = {"acc": theme.get("accent", "#ff2d36"), "jaune": "#ffd23f", "fond": "#0b0807", "fond2": "#15100c", "halo": "#3a2b20", "argile": "#cdb59a"} | spec.get("couleurs", {})
    S = [{"a": round(starts[k], 3), "b": round(starts[k] + durs[k], 3), "plan": s.get("type", "large"), "exercice": s.get("exercice", "Idle_Loop"),
          "reps": s.get("reps", 0), "muscle": s.get("muscle"), "jour": s.get("jour"), "carte": bool(s.get("carte"))} for k, s in enumerate(sc)]
    bands = "".join(f"<div class='band' id='bd{k}'>{K.esc(s['bandeau'])}</div>" for k, s in enumerate(sc) if s.get("bandeau"))
    qs = "".join(f"<div class='q' id='q{k}'><span>{K.esc(s['question'])}</span></div>" for k, s in enumerate(sc) if s.get("question"))
    fins = "".join(f"<div class='fin' id='fn{k}'><b>{K.esc(s['carte'][0])}</b>" + (f"<span>{K.esc(s['carte'][1])}</span>" if len(s['carte']) > 1 else '') + "</div>" for k, s in enumerate(sc) if s.get("carte"))
    fort = lambda w: any(ch.isdigit() for ch in w) or w.lower().strip(".,!?") in {"jours", "days", "secondes", "minutes", "semaines"}
    cap_html = "".join(f"<div class='cap' data-a='{cc[0][1]:.3f}' data-b='{cn:.3f}'>" + "".join(
        f"<span class='w{' h' if fort(w) else ''}' data-w='{tt:.3f}'>{H.escape(w)}</span>" for w, tt in cc) + "</div>" for cc, cn in caps)
    R = {"__FONTS__": K._font_faces(["Anton", "Archivo Black", "Inter"]), "__FOND__": col["fond"], "__ACC__": col["acc"], "__JAUNE__": col["jaune"],
         "__HANDLE__": H.escape(spec.get("handle", "")), "__LABEL__": H.escape((spec.get("serie") or {}).get("label", "DAY")),
         "__CAPS__": cap_html, "__BANDS__": bands, "__QUESTIONS__": qs, "__FINS__": fins, "__POSES__": poses_js(),
         "__IMPORTMAP__": S3.import_map(), "__GLB__": base64.b64encode(open(MANNEQUIN, "rb").read()).decode(),
         "__D__": str(total), "__SC__": json.dumps(S, ensure_ascii=False), "__COL__": json.dumps(col), "__SERIE__": json.dumps(spec.get("serie")),
         "__MUSCLES__": json.dumps(MUSCLES)}
    out = TPL
    for kk, v in R.items():
        out = out.replace(kk, v)
    return out
