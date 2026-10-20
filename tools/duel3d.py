#!/usr/bin/env python3
"""Reel 3D « duel » (Mental d'Acier) : deux personnages, la même tâche, deux attitudes, un seul plan qui boucle.
Gauche : le perfectionniste, à genoux derrière son muret, ajuste sa brique au niveau sans jamais avancer.
Droite : celui qui agit monte son mur en colonne et s'élève avec lui. À la fin, le perfectionniste se lève et regarde le mur.
Aucun texte hors des 2 étiquettes : la morale va dans la légende.
Usage : python3 tools/duel3d.py <spec.json> <out.mp4>   (ajouter --html pour n'écrire que la page)
spec : {"id", "music_seed", "gauche", "droite", "handle"}
Sans voix : musique + bruitages. Fond noir, sol miroir, personnages blancs cernés de noir (three.js).
"""
import json, os, sys, subprocess, tempfile, shutil, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K

DUR = 14.0
W, H = 1080, 1920
COLS, ROWS = 3, 10               # mur de 3 briques x 10 rangs
T0, T1 = 0.25, 10.4              # construction de T0 à T1
T_LEVE = 10.9                    # le perfectionniste se lève et regarde le mur


def page(spec):
    three = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "three.min.js"), encoding="utf-8").read()
    fonts = K._font_faces(["JetBrains Mono"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:#000;overflow:hidden;position:relative;color:#fff}}
canvas{{position:absolute;left:0;top:0}}
.lab{{position:absolute;font:700 40px 'JetBrains Mono';letter-spacing:5px;white-space:nowrap;text-shadow:0 0 16px rgba(255,255,255,.5)}}
.hd{{position:absolute;left:0;right:0;top:1440px;text-align:center;font:400 30px 'JetBrains Mono';letter-spacing:10px;color:#3c3c3c}}
</style></head><body>
<canvas id='cv' width='{W}' height='{H}'></canvas>
<div class='lab' id='lg' style='left:56px;top:640px'>{K.esc(spec['gauche'])}</div>
<div class='lab' id='ld' style='right:60px;top:330px'>{K.esc(spec['droite'])}</div>
<div class='hd'>{K.esc(spec['handle']).upper()}</div>
<script>{three}</script>
<script>
const D={DUR}, COLS={COLS}, ROWS={ROWS}, T0={T0}, T1={T1}, TL={T_LEVE}, NB=COLS*ROWS, DT=(T1-T0)/NB;
const c=x=>Math.max(0,Math.min(1,x)), sm=x=>{{x=c(x);return x*x*(3-2*x);}};
const V=(x,y,z)=>new THREE.Vector3(x,y,z||0);
const R=new THREE.WebGLRenderer({{canvas:document.getElementById('cv'),antialias:true,preserveDrawingBuffer:true}});
R.setSize({W},{H},false); R.setClearColor(0x000000); R.outputEncoding=THREE.sRGBEncoding; R.autoClear=false;
const scene=new THREE.Scene(), world=new THREE.Group(); scene.add(world);
scene.add(new THREE.AmbientLight(0xffffff,.5));
const key=new THREE.DirectionalLight(0xffffff,.8); key.position.set(-3,6,6); scene.add(key);
const rim=new THREE.DirectionalLight(0xffffff,.3); rim.position.set(4,3,-4); scene.add(rim);
// sol miroir : le monde est rendu une 1re fois retourné sous le sol, puis voilé par un plan noir translucide
const floorScene=new THREE.Scene();
const floor=new THREE.Mesh(new THREE.PlaneGeometry(80,80),new THREE.MeshBasicMaterial({{color:0x000000,transparent:true,opacity:.82,depthWrite:false}}));
floor.rotation.x=-Math.PI/2; floorScene.add(floor);
const WHITE=new THREE.MeshStandardMaterial({{color:0xffffff,roughness:.55,emissive:0x5a5a5a}});
const INK=new THREE.MeshBasicMaterial({{color:0x000000,side:THREE.BackSide}});
const BRICK=new THREE.MeshStandardMaterial({{color:0xb9a98f,roughness:.85,emissive:0x0d0b08}});
const GOLD=new THREE.MeshStandardMaterial({{color:0xe8b84f,roughness:.25,metalness:.6,emissive:0x5a3c08}});
const EDGE=new THREE.LineBasicMaterial({{color:0x2a2620}});
function limb(r){{const g=new THREE.CapsuleGeometry(r,1,6,14);const m=new THREE.Mesh(g,WHITE);const o=new THREE.Mesh(g,INK);o.scale.set(1.28,1,1.28);m.add(o);
  m.userData.L=1+2*r;world.add(m);return m;}}
function setLimb(m,a,b){{const d=V().subVectors(b,a);const L=Math.max(.001,d.length());m.position.copy(a).addScaledVector(d,.5);
  m.quaternion.setFromUnitVectors(V(0,1,0),d.clone().normalize());m.scale.set(1,L/m.userData.L+.12,1);}}
function head(r){{const g=new THREE.SphereGeometry(r,32,24);const m=new THREE.Mesh(g,WHITE);const o=new THREE.Mesh(g,INK);o.scale.setScalar(1.13);m.add(o);world.add(m);return m;}}
function box(m,w,h,d,edges=true){{const g=new THREE.BoxGeometry(w,h,d);const b=new THREE.Mesh(g,m);if(edges)b.add(new THREE.LineSegments(new THREE.EdgesGeometry(g),EDGE));world.add(b);return b;}}
// IK à 2 segments : coude/genou placé du côté de « hint »
function ik(S,T,a,b,hint){{const d0=V().subVectors(T,S);let d=d0.length();const dir=d0.clone().normalize();d=Math.min(d,a+b-.001);
  const x=(a*a-b*b+d*d)/(2*d);const h=Math.sqrt(Math.max(0,a*a-x*x));const p=hint.clone().addScaledVector(dir,-hint.dot(dir)).normalize();
  return S.clone().addScaledVector(dir,x).addScaledVector(p,h);}}
function figure(){{return {{torso:limb(.085),head:head(.2),arms:[[limb(.065),limb(.06)],[limb(.065),limb(.06)]],legs:[[limb(.072),limb(.066)],[limb(.072),limb(.066)]]}};}}
function pose(f,P){{setLimb(f.torso,P.hip,P.sh);
  const up=V().subVectors(P.sh,P.hip).normalize();f.head.position.copy(P.sh).addScaledVector(up,.26).add(P.look||V(0,0,0));
  [0,1].forEach(i=>{{const sd=i?1:-1;const S=P.sh.clone().add(V(.15*sd,0,0));const Hd=P.hands[i];const E=ik(S,Hd,.34,.34,P.elbow.clone().add(V(.5*sd,0,0)));
    setLimb(f.arms[i][0],S,E);setLimb(f.arms[i][1],E,Hd);
    const Hp=P.hip.clone().add(V(.1*sd,0,0));const Ft=P.feet[i];const Kn=P.knees?P.knees[i]:ik(Hp,Ft,.44,.44,P.knee);setLimb(f.legs[i][0],Hp,Kn);setLimb(f.legs[i][1],Kn,Ft);}});}}
const BW=.36,BH=.16,BD=.24;
const lerp=(a,b,k)=>a.clone().lerp(b,k);
// ---------- gauche : muret de 4 briques, le perfectionniste à genoux derrière, niveau doré sur la brique du haut
const PX=-.85;
for(const x of [PX-.36,PX,PX+.36])box(BRICK,BW-.005,BH-.004,BD).position.set(x,BH/2,0);
const tb=box(BRICK,BW-.005,BH-.004,BD);
const level=box(GOLD,.5,.05,.07,false);
const pf=figure();
function posePerf(t){{
  const up=sm((t-TL)/.7);                                   // 0 à genoux -> 1 debout
  const lift=t>4.2&&t<6.4?Math.sin(c((t-4.2)/2.2)*Math.PI):0; // il soulève sa brique, la regarde, la repose
  const shim=Math.sin(t*6)*.006*(1-up);                      // petits ajustements
  tb.position.set(PX+shim,BH*1.5+lift*.3,0);tb.rotation.set(0,lift*.35*Math.sin(t*2.5),lift*.08);
  const slide=(1-up)*(1-lift)*.08*Math.sin(t*3.1);
  level.position.copy(tb.position).add(V(slide,BH/2+.025,0));level.rotation.copy(tb.rotation);
  level.visible=up<.5;
  const kHip=V(PX,.46,-.5), sHip=V(PX,.86,-.42);
  const kSh=V(PX+.02,.92+lift*.12,-.22), sSh=V(PX+.02,1.42,-.38);
  const hip=lerp(kHip,sHip,up), sh=lerp(kSh,sSh,up);
  const onLvl=[level.position.clone().add(V(-.17,.03,0)),level.position.clone().add(V(.17,.03,0))];
  const onBrick=[tb.position.clone().add(V(-.2,0,0)),tb.position.clone().add(V(.2,0,0))];
  const work=lift>0?onBrick.map((p,i)=>lerp(onLvl[i],p,c(lift*3))):onLvl;
  const rest=[V(PX-.26,.78,-.38),V(PX+.26,.78,-.38)];
  const hands=work.map((p,i)=>lerp(p,rest[i],up));
  const knees=up<1e-3?[V(PX-.1,.07,-.2),V(PX+.1,.07,-.2)]:null;
  pose(pf,{{hip,sh,hands,feet:[lerp(V(PX-.1,.05,-.75),V(PX-.12,.03,-.42),up),lerp(V(PX+.1,.05,-.75),V(PX+.12,.03,-.42),up)],
    knees:up<.02?[V(PX-.1,.07,-.2),V(PX+.1,.07,-.2)]:null,knee:V(0,0,1),elbow:V(0,-1,.4),
    look:lerp(V(0,-.05,.06),V(.07,.05,0),up)}});
}}
// ---------- droite : mur de COLS x ROWS ; celui qui agit travaille derrière et s'élève avec le mur
const WX=.45;  // x de la 1re brique
const wall=[];
for(let i=0;i<NB;i++){{const r=Math.floor(i/COLS),k=i%COLS;const b=box(BRICK,BW-.006,BH-.004,BD);
  const j=Math.sin(i*12.9898)*43758.5453;const rnd=j-Math.floor(j);
  b.userData.p=V(WX+k*BW+(r%2?BW/2:0)+(rnd-.5)*.02,BH/2+r*BH,(rnd-.5)*.02);b.userData.ry=(rnd-.5)*.06;b.visible=false;wall.push(b);}}
const held=[box(BRICK,BW-.006,BH-.004,BD),box(BRICK,BW-.006,BH-.004,BD)];
const ac=figure();
const MIDX=WX+BW*(COLS-1)/2+BW/4;
function poseAction(t){{
  const f=c((t-T0)/(T1-T0))*NB;const n=Math.floor(f);const u=f-n;     // n briques posées, u : avancée de la suivante
  wall.forEach((b,i)=>{{b.visible=i<n;if(i<n){{const a=c((t-(T0+(i+1)*DT))/.08);b.position.copy(b.userData.p).add(V(0,.06*(1-a),0));b.rotation.y=b.userData.ry;}}}});
  const done=n>=NB;const row=Math.min(ROWS,Math.floor(n/COLS));const wallTop=row*BH+(done?0:(n%COLS)/COLS*BH*.5);
  const fin=sm((t-T1)/.6);                                       // 0 au travail -> 1 accroupi en haut du mur
  const feetY=Math.max(0,wallTop-.42)*(1-fin)+ROWS*BH*fin;const fz=-.5+.5*fin;
  const tx=done?MIDX:wall[n].userData.p.x;
  const hx=MIDX+(tx-MIDX)*.45;
  const hip=V(hx,feetY+.55-.13*fin,-.48+.4*fin);
  const bob=done?0:Math.sin(u*Math.PI)*.06;
  const sh=V(hx+(tx-hx)*.25*(1-fin)-.06*fin,hip.y+.42+.02*fin-bob,-.3+.38*fin);
  held.forEach(h=>h.visible=false);
  let hands;
  if(!done){{const slot=wall[n].userData.p.clone().add(V(0,.02,0));const side=n%2;
    const grab=V(hx+(side?.32:-.32),hip.y+.25,-.42);
    const hm=grab.clone().lerp(slot,sm(u));hm.y+=.18*Math.sin(u*Math.PI);
    const other=V(hx+(side?-.3:.3),hip.y+.2,-.25);
    hands=side?[other,hm]:[hm,other];held[side].visible=true;held[side].position.copy(hm);held[side].rotation.set(0,0,0);
    hands=hands.map((p,i)=>i==side?p:p);}}
  else{{hands=[V(hx-.2,feetY+.42,.14),V(hx+.2,feetY+.42,.14)];}}
  pose(ac,{{hip,sh,hands,feet:[V(hx-.15,feetY+.02,fz),V(hx+.15,feetY+.02,fz)],knee:V(0,.4*fin,1),elbow:V(0,-1,-.2),
    look:lerp(V(0,-.06,.07),V(-.09,-.06,.05),fin)}});
}}
const cam=new THREE.PerspectiveCamera(24,{W}/{H},.1,60);
window.render=function(t){{
  poseAction(t);posePerf(t);
  cam.position.set(-1.2+.1*Math.sin(t/5),2.5,14);cam.lookAt(.38,1.15,0);
  R.clear();
  world.scale.y=-1;R.render(scene,cam);           // reflet
  R.render(floorScene,cam);                        // voile du sol
  world.scale.y=1;R.clearDepth();R.render(scene,cam);
}};render(0);
</script></body></html>"""


def sfx(path):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, lfilter
    SR = 48000; n = int(SR * (DUR + 1)); out = np.zeros(n); rng = np.random.default_rng(7)
    def put(sig, t0, g=1.0):
        i = int(max(0, t0) * SR); j = min(n, i + len(sig)); out[i:j] += sig[: j - i] * g
    NB = COLS * ROWS; dt = (T1 - T0) / NB
    b1, a1 = butter(2, [1200 / (SR / 2), 6000 / (SR / 2)], "band")
    tc = np.arange(int(.05 * SR)) / SR
    clack = lfilter(b1, a1, rng.standard_normal(len(tc))) * np.exp(-tc * 90) * .16
    th = np.arange(int(.3 * SR)) / SR
    thud = np.sin(2 * np.pi * (100 + 70 * np.exp(-th * 25)) * th) * np.exp(-th * 14) * .4
    for i in range(NB):
        t = T0 + (i + 1) * dt
        put(clack, t, .7 + .3 * rng.random())
        if (i + 1) % COLS == 0:
            put(thud, t)  # un rang terminé
    # frottement du niveau, coupé quand il soulève la brique et quand il se lève
    tt = np.arange(n) / SR
    b2, a2 = butter(2, [2500 / (SR / 2), 9000 / (SR / 2)], "band")
    rub = lfilter(b2, a2, rng.standard_normal(n)) * np.abs(np.sin(tt * 3.1)) * .03
    rub *= ((tt < 4.2) | ((tt > 6.4) & (tt < T_LEVE)))
    out += rub
    put(thud, T1 + .6, 1.2)  # il se redresse sur le mur fini
    out = np.clip(out, -1, 1); wavfile.write(path, SR, (np.stack([out, out], 1) * 32767).astype(np.int16))


def build(spec_path, out):
    spec = json.load(open(spec_path, encoding="utf-8")); tmp = tempfile.mkdtemp()
    hp = os.path.join(tmp, "p.html"); open(hp, "w", encoding="utf-8").write(page(spec))
    try:  # audit automatique (texte trop petit, hors zones sûres) : avertit sans bloquer
        import audit as A
        A.afficher(A.auditer(hp, [0.0, 3.5, 7.0, T1, T_LEVE + 1], DUR), spec_path)
        print("  (format sans hook texte : les 2 étiquettes font office de hook)")
    except Exception as e:
        print("audit non réalisé :", e)
    fr = os.path.join(tmp, "fr"); os.makedirs(fr)
    asyncio.run(K._frames(hp, fr, DUR))
    v = os.path.join(tmp, "v.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{fr}/f_%04d.jpg", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", v], check=True)
    mu = os.path.join(tmp, "m.wav"); K.make_music(mu, DUR + 1, int(spec.get("music_seed", 9)))
    fx = os.path.join(tmp, "fx.wav"); sfx(fx)
    fc = (f"[1]atrim=0:{DUR},volume=0.5[m];[2]atrim=0:{DUR}[f];"   # pas de fondu final : la vidéo doit boucler
          f"[m][f]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5,alimiter=limit=0.95,apad=whole_dur={DUR+3},atrim=0:{DUR}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", mu, "-i", fx, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[3] == "--html":
        open(sys.argv[2], "w", encoding="utf-8").write(page(json.load(open(sys.argv[1], encoding="utf-8")))); print("html")
    else:
        build(sys.argv[1], sys.argv[2]); print("ok")
