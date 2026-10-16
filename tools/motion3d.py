#!/usr/bin/env python3
"""Reel 3D « écran partagé » (Mental d'Acier) : deux matins, même réveil.
Usage : python3 tools/motion3d.py <spec.json> <out.mp4>
spec : {"id", "music_seed", "top": {"titre","sous"}, "bas": {"titre","sous"}, "fin": ["ligne", "**ligne**"], "cta", "handle"}
Personnage et décor en 3D (three.js), sans voix : musique + bruitages.
"""
import json, os, sys, subprocess, tempfile, shutil, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K

DUR = 30.0
W, H = 1080, 1920
TOP = (220, 840)     # panneau du haut (CSS y0, y1)
BOT = (930, 1550)    # panneau du bas

def page(spec):
    three = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "three.min.js")).read()
    fonts = K._font_faces(["Archivo Black", "JetBrains Mono"])
    fin = "".join(f"<div class='fl' data-at='{24.6 + 0.5 * i}'>{K.rich(l).replace('grad', 'gold')}</div>" for i, l in enumerate(spec["fin"]))
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;background:#070707;overflow:hidden;position:relative;font-family:Inter,sans-serif;color:#fff}}
canvas{{position:absolute;left:0;top:0}}
.lab{{position:absolute;left:44px;text-shadow:0 2px 12px rgba(0,0,0,.8)}}
.lab .t{{font:400 64px 'Archivo Black';color:#e8b84f}} .lab .s{{font:500 40px Inter;color:#ddd;margin-top:4px}}
.lab.b .t{{color:#fff}}
.mid{{position:absolute;left:0;right:0;top:{TOP[1]}px;height:{BOT[0]-TOP[1]}px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px}}
.clk{{font:700 40px 'JetBrains Mono';color:#fff}}
.track{{width:780px;height:8px;border-radius:4px;background:#333;position:relative}}
.fill{{position:absolute;left:0;top:0;bottom:0;background:#e8b84f;border-radius:4px}}
.knob{{position:absolute;top:-8px;width:24px;height:24px;border-radius:50%;background:#e8b84f;margin-left:-12px}}
.cnt{{position:absolute;right:50px;top:{TOP[0]+30}px;font:400 90px 'Archivo Black';color:#e8b84f;opacity:0;text-shadow:0 4px 18px rgba(0,0,0,.7)}}
.z{{position:absolute;font:400 54px 'Archivo Black';color:#bbb;opacity:0}}
.bub{{position:absolute;left:50%;transform:translateX(-50%);background:rgba(10,10,10,.85);border:2px solid #555;border-radius:26px;padding:16px 30px;font:600 40px Inter;white-space:nowrap;opacity:0}}
.stamp{{position:absolute;right:60px;top:{TOP[0]+400}px;border:6px solid #e8b84f;color:#e8b84f;font:400 70px 'Archivo Black';padding:6px 26px;border-radius:14px;transform:rotate(-8deg);opacity:0}}
.flash{{position:absolute;left:0;right:0;top:{TOP[0]}px;height:{TOP[1]-TOP[0]}px;background:#fff;opacity:0}}
.end{{position:absolute;inset:0;background:#070707;opacity:0;display:flex;flex-direction:column;justify-content:center;padding:0 80px}}
.fl{{font:400 104px/1.05 'Archivo Black';text-transform:uppercase;opacity:0}}
.gold{{color:#e8b84f}}
.cta{{margin-top:70px;font:600 46px Inter;color:#ddd;opacity:0}}
.hd{{margin-top:24px;font:400 34px 'JetBrains Mono';color:#888;opacity:0}}
.bar{{position:absolute;left:0;top:0;height:10px;background:#e8b84f}}
</style></head><body>
<canvas id='cv' width='{W}' height='{H}'></canvas>
<div class='flash' id='flash'></div>
<div class='lab' style='top:{TOP[0]+24}px'><div class='t'>{K.esc(spec['top']['titre'])}</div><div class='s'>{K.esc(spec['top']['sous'])}</div></div>
<div class='lab b' style='top:{BOT[0]+24}px'><div class='t'>{K.esc(spec['bas']['titre'])}</div><div class='s'>{K.esc(spec['bas']['sous'])}</div></div>
<div class='mid'><div class='clk' id='clk'>6:00</div><div class='track'><div class='fill' id='fill'></div><div class='knob' id='knob'></div></div></div>
<div class='cnt' id='cnt'>×0</div>
<div class='stamp' id='stamp'>FAIT ✓</div>
<div class='z' id='z1'>Z</div><div class='z' id='z2'>z</div><div class='z' id='z3'>z</div>
<div class='bub' id='bub' style='top:{BOT[0]+470}px'>« Encore 5 minutes… »</div>
<div class='bub' id='bub2' style='top:{BOT[0]+470}px'>Toujours au lit.</div>
<div class='end' id='end'>{fin}<div class='cta' id='cta'>{K.rich(spec['cta']).replace('grad','gold')}</div><div class='hd' id='hd'>@{K.esc(spec['handle'])}</div></div>
<div class='bar' id='bar'></div>
<script>{three}</script>
<script>
const D={DUR}, TOP={list(TOP)}, BOT={list(BOT)};
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), back=x=>{{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);}};
const R=new THREE.WebGLRenderer({{canvas:document.getElementById('cv'),antialias:true,preserveDrawingBuffer:true}});
R.setSize({W},{H},false); R.setClearColor(0x070707); R.outputEncoding=THREE.sRGBEncoding;
const GOLD=new THREE.MeshStandardMaterial({{color:0xd9a441,roughness:.42,metalness:.35}});
function mat(c,r=.9){{return new THREE.MeshStandardMaterial({{color:c,roughness:r}});}}
function cyl(a,b,r,m){{const d=new THREE.Vector3().subVectors(b,a);const L=d.length();const g=new THREE.CapsuleGeometry(r,Math.max(.001,L),6,12);
  const me=new THREE.Mesh(g,m);me.position.copy(a).addScaledVector(d,.5);me.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.clone().normalize());return me;}}
function setCyl(me,a,b){{const d=new THREE.Vector3().subVectors(b,a);const L=d.length();me.position.copy(a).addScaledVector(d,.5);
  me.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.clone().normalize());me.scale.set(1,L/me.userData.L,1);}}
function limb(r,m){{const me=new THREE.Mesh(new THREE.CapsuleGeometry(r,1,6,12),m);me.userData.L=1+2*r;return me;}}
function clockTex(){{const cv=document.createElement('canvas');cv.width=256;cv.height=128;const t=new THREE.CanvasTexture(cv);t.userData.cv=cv;return t;}}
function drawClock(t,txt,on){{const x=t.userData.cv.getContext('2d');x.fillStyle='#111';x.fillRect(0,0,256,128);x.fillStyle=on?'#ffcf5a':'#7a5a1a';x.font='bold 84px monospace';x.textAlign='center';x.textBaseline='middle';x.fillText(txt,128,66);t.needsUpdate=true;}}
function room(){{
  const s=new THREE.Scene();
  s.add(new THREE.AmbientLight(0xffffff,.07));
  const win=new THREE.PointLight(0xffc469,1.8,8);win.position.set(-.4,2.2,-.6);s.add(win);
  const key=new THREE.DirectionalLight(0xfff2dc,.14);key.position.set(3,5,4);s.add(key);
  const lamp=new THREE.SpotLight(0xffd59a,1.5,7,.5,.7);lamp.position.set(.2,3.4,.4);lamp.target.position.set(0,0,0);s.add(lamp);s.add(lamp.target);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(9,9),mat(0x1d1d1d));floor.rotation.x=-Math.PI/2;s.add(floor);
  const back=new THREE.Mesh(new THREE.PlaneGeometry(9,5),mat(0x2a2a2a));back.position.set(0,2.5,-1.4);s.add(back);
  const left=new THREE.Mesh(new THREE.PlaneGeometry(9,5),mat(0x242424));left.rotation.y=Math.PI/2;left.position.set(-2.7,2.5,0);s.add(left);
  // fenêtre lumineuse
  const gc=document.createElement('canvas');gc.width=64;gc.height=128;const gx=gc.getContext('2d');const gr=gx.createLinearGradient(0,0,0,128);gr.addColorStop(0,'#1c1c1c');gr.addColorStop(1,'#f5c869');gx.fillStyle=gr;gx.fillRect(0,0,64,128);
  const wt=new THREE.CanvasTexture(gc);
  for(const dx of [-.33,.33]){{const p=new THREE.Mesh(new THREE.PlaneGeometry(.6,1.05),new THREE.MeshBasicMaterial({{map:wt}}));p.position.set(-.3+dx,2.15,-1.39);s.add(p);}}
  const fr=new THREE.Mesh(new THREE.BoxGeometry(1.45,1.25,.05),mat(0x9a9a9a));fr.position.set(-.3,2.15,-1.42);s.add(fr);
  // lampe plafond
  const lp=new THREE.Mesh(new THREE.CylinderGeometry(.22,.22,.08,20),mat(0x111111));lp.position.set(.2,3.5,.4);s.add(lp);
  // lit
  const bed=new THREE.Mesh(new THREE.BoxGeometry(2.5,.38,1.5),mat(0x3c3c3c));bed.position.set(-1.3,.19,-.62);s.add(bed);
  const mat2=new THREE.Mesh(new THREE.BoxGeometry(2.45,.16,1.45),mat(0x6e6e6e));mat2.position.set(-1.3,.46,-.62);s.add(mat2);
  const head=new THREE.Mesh(new THREE.BoxGeometry(.1,.9,1.5),mat(0x4a4a4a));head.position.set(-2.55,.6,-.62);s.add(head);
  const pil=new THREE.Mesh(new THREE.BoxGeometry(.5,.14,.8),mat(0xb5b5b5));pil.position.set(-2.18,.6,-.62);s.add(pil);
  // table de nuit + réveil
  const ns=new THREE.Mesh(new THREE.BoxGeometry(.6,.62,.55),mat(0x474747));ns.position.set(.35,.31,-1.05);s.add(ns);
  const ct=clockTex();const clk=new THREE.Mesh(new THREE.BoxGeometry(.4,.2,.14),[mat(0x111111),mat(0x111111),mat(0x111111),mat(0x111111),new THREE.MeshBasicMaterial({{map:ct}}),mat(0x111111)]);
  clk.position.set(.35,.72,-1.0);clk.rotation.y=-.35;s.add(clk);
  // ombre douce
  const sh=new THREE.Mesh(new THREE.CircleGeometry(1,32),new THREE.MeshBasicMaterial({{color:0,transparent:true,opacity:.35}}));sh.rotation.x=-Math.PI/2;sh.position.y=.005;s.add(sh);
  return {{s,clk,ct,sh}};
}}
function sleeper(env){{
  const g=new THREE.Group();env.s.add(g);
  const head=new THREE.Mesh(new THREE.SphereGeometry(.27,32,24),GOLD);head.position.set(-2.05,.86,-.62);g.add(head);
  const bl=new THREE.PlaneGeometry(1.9,1.5,40,24);bl.rotateX(-Math.PI/2);const base=bl.attributes.position.array.slice();
  const blanket=new THREE.Mesh(bl,new THREE.MeshStandardMaterial({{color:0x454545,roughness:1,side:THREE.DoubleSide}}));blanket.position.set(-.95,.56,-.62);g.add(blanket);
  const arm=limb(.06,GOLD);g.add(arm);
  return {{g,head,blanket,base,arm}};
}}
function poseSleep(sl,t,reach){{
  const p=sl.blanket.geometry.attributes.position;const br=1+.05*Math.sin(t*2.2);
  for(let i=0;i<p.count;i++){{const x=sl.base[i*3],z=sl.base[i*3+2];let y=.26*Math.exp(-(z*z)/.12)*br*(x<.85?1:Math.max(0,1-(x-.85)*4));
    y-=.25*Math.max(0,Math.abs(z)-.62)*4;p.setY(i,y);}}
  p.needsUpdate=true;sl.blanket.geometry.computeVertexNormals();
  const sh=new THREE.Vector3(-1.75,.78,-.35);const rest=new THREE.Vector3(-1.4,.78,-.3);const clk=new THREE.Vector3(.25,.78,-.95);
  const end=rest.clone().lerp(clk,reach);end.y+=.15*Math.sin(reach*Math.PI);
  sl.arm.visible=reach>0.02;setCyl(sl.arm,sh,end);
  sl.head.position.y=.86+.01*Math.sin(t*2.2);
}}
function pusher(env){{
  const g=new THREE.Group();env.s.add(g);
  const torso=limb(.15,GOLD),head=new THREE.Mesh(new THREE.SphereGeometry(.24,32,24),GOLD);
  const a1=limb(.06,GOLD),a2=limb(.055,GOLD),b1=limb(.06,GOLD),b2=limb(.055,GOLD);
  [torso,head,a1,a2,b1,b2].forEach(m=>g.add(m));return {{g,torso,head,arms:[[a1,a2],[b1,b2]]}};
}}
function posePush(p,h){{
  // h : hauteur des épaules (0.3 bas -> 0.66 haut). Corps des pieds (x=1.3) vers la tête (-x), devant le lit.
  const F=new THREE.Vector3(1.25,.07,.75);const L=1.15;const sy=h-.07;const th=Math.asin(Math.min(.95,sy/L));
  const dir=new THREE.Vector3(-Math.cos(th),Math.sin(th),0);const S=F.clone().addScaledVector(dir,L);
  setCyl(p.torso,F,S.clone().addScaledVector(dir,.05));p.head.position.copy(S).addScaledVector(dir,.3).add(new THREE.Vector3(0,.08,0));
  const a=.33,b=.33;
  [-1,1].forEach((sd,i)=>{{const sh=S.clone().add(new THREE.Vector3(0,0,.2*sd));const hand=new THREE.Vector3(S.x-.05,.04,S.z+.26*sd);
    const d=sh.distanceTo(hand);const mid=sh.clone().lerp(hand,.5);const off=Math.sqrt(Math.max(0,a*a-(d/2)*(d/2)));
    const el=mid.add(new THREE.Vector3(.06,0,sd*off));setCyl(p.arms[i][0],sh,el);setCyl(p.arms[i][1],el,hand);}});
}}
const topE=room(), botE=room();
const slT=sleeper(topE), slB=sleeper(botE), pu=pusher(topE);
topE.sh.scale.set(1.1,.5,1);topE.sh.position.set(.4,.006,.75);botE.sh.visible=false;
const cam=new THREE.PerspectiveCamera(33,{W}/(TOP[1]-TOP[0]),.1,50);cam.position.set(3.3,2.4,3.9);cam.lookAt(-.55,.5,-.2);
function clockTxt(m){{return '6:'+String(Math.min(59,Math.floor(m))).padStart(2,'0');}}
window.render=function(t){{
  const T0=2.2,T1=22.5;const prog=c((t-T0)/(T1-T0));const mins=prog*5;
  // haut
  const up=t>=T0;slT.g.visible=!up;pu.g.visible=up;topE.sh.visible=up;
  if(!up)poseSleep(slT,t,0);
  else{{const ph=(t-T0-.4)/1.55;const k=t<T0+.4?1:.5+.5*Math.cos(ph*2*Math.PI);posePush(pu,.3+.36*k);}}
  // bas
  let reach=0;const r1=[T0,T0+1.0],r2=[12,13.2];
  for(const [a,b] of [r1,r2]){{if(t>=a&&t<b){{const u=(t-a)/(b-a);reach=Math.sin(u*Math.PI);}}}}
  poseSleep(slB,t,reach);
  const ring=t<T0||(t>=11&&t<12.6);
  for(const env of [topE,botE]){{const shake=(env===botE?ring:t<T0)?Math.sin(t*60)*.05:0;env.clk.rotation.z=shake;}}
  drawClock(topE.ct,clockTxt(mins),t<T0?Math.floor(t*4)%2==0:true);
  drawClock(botE.ct,clockTxt(mins),ring?Math.floor(t*4)%2==0:true);
  // caméra : léger travelling
  cam.position.set(3.3-.2*Math.sin(t/6),2.4+.08*Math.sin(t/4),3.9);cam.lookAt(-.55,.5,-.2);
  R.setScissorTest(true);
  const hp=TOP[1]-TOP[0];
  R.setViewport(0,{H}-TOP[1],{W},hp);R.setScissor(0,{H}-TOP[1],{W},hp);R.render(topE.s,cam);
  R.setViewport(0,{H}-BOT[1],{W},BOT[1]-BOT[0]);R.setScissor(0,{H}-BOT[1],{W},BOT[1]-BOT[0]);R.render(botE.s,cam);
  // UI
  document.getElementById('bar').style.width=(c(t/D)*{W})+'px';
  const sec=Math.floor(prog*300);document.getElementById('clk').textContent=t<T0?'⏰ 6:00':Math.floor(sec/60)+':'+String(sec%60).padStart(2,'0')+' / 5:00';
  document.getElementById('fill').style.width=(prog*100)+'%';document.getElementById('knob').style.left=(prog*100)+'%';
  const reps=up?Math.max(0,Math.floor((t-T0-.4)/1.55+.5)):0;const cn=document.getElementById('cnt');cn.style.opacity=up&&t<24?1:0;cn.textContent='×'+Math.min(reps,13);
  const fl=document.getElementById('flash');fl.style.opacity=t>=T0&&t<T0+.25?1-(t-T0)/.25:0;
  const st=document.getElementById('stamp');const sk=back((t-T1)/.35);st.style.opacity=t>=T1&&t<24.4?1:0;st.style.transform=`rotate(-8deg) scale(${{2.2-1.2*sk}})`;
  const zs=['z1','z2','z3'];zs.forEach((id,i)=>{{const e=document.getElementById(id);const ph=((t*0.7+i/3)%1);const vis=(t>T0+1.2&&t<11)||(t>13.5&&t<24.4);
    e.style.opacity=vis?Math.sin(ph*Math.PI):0;e.style.left=(440+ph*80+i*12)+'px';e.style.top=({BOT[0]}+200-ph*150)+'px';e.style.fontSize=(36+ph*30)+'px';}});
  const bb=document.getElementById('bub');bb.style.opacity=t>=13.2&&t<17.5?eo((t-13.2)/.3)*(1-eo((t-17.2)/.3)):0;
  const b2=document.getElementById('bub2');b2.style.opacity=t>=T1&&t<24.4?eo((t-T1)/.3):0;
  const en=document.getElementById('end');en.style.opacity=eo((t-24.2)/.5);
  for(const l of document.querySelectorAll('.fl')){{const at=+l.dataset.at;const k=back((t-at)/.4);l.style.opacity=c((t-at)/.12);l.style.transform=`translateY(${{(1-k)*60}}px)`;}}
  document.getElementById('cta').style.opacity=eo((t-26.6)/.4);document.getElementById('hd').style.opacity=eo((t-27)/.4);
}};render(0);
</script></body></html>"""

async def frames(html_path, fr, dur, fps=30):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await b.new_page(viewport={"width": W, "height": H})
        await pg.goto("file://" + os.path.abspath(html_path)); await pg.wait_for_timeout(800)
        for i in range(int(dur * fps)):
            await pg.evaluate(f"render({i / fps})")
            await pg.screenshot(path=f"{fr}/f_{i:04d}.jpg", type="jpeg", quality=90)
        await b.close()

def sfx(path):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, lfilter
    SR = 48000; n = int(SR * (DUR + 1)); out = np.zeros(n); rng = np.random.default_rng(5)
    def put(sig, t0, g=1.0):
        i = int(t0 * SR); j = min(n, i + len(sig)); out[i:j] += sig[: j - i] * g
    tb = np.arange(int(.09 * SR)) / SR
    beep = np.sign(np.sin(2 * np.pi * 2000 * tb)) * .08 * np.minimum(1, (len(tb) - np.arange(len(tb))) / 400)
    for a, b in ((0, 2.2), (11, 12.6)):
        t = a
        while t < b:
            put(beep, t); put(beep, t + .13); t += .5
    tw = np.arange(int(.5 * SR)) / SR
    b2, a2 = butter(2, [400 / (SR / 2), 5000 / (SR / 2)], "band")
    wh = lfilter(b2, a2, rng.standard_normal(len(tw))) * np.sin(np.pi * tw / tw[-1]) ** 2 * .35
    put(wh, 2.0); put(wh, 24.0)
    th = np.arange(int(.35 * SR)) / SR
    thud = np.sin(2 * np.pi * (90 + 60 * np.exp(-th * 20)) * th) * np.exp(-th * 12) * .5
    put(thud, 22.5)
    out = np.clip(out, -1, 1); wavfile.write(path, SR, (np.stack([out, out], 1) * 32767).astype(np.int16))

def build(spec_path, out):
    spec = json.load(open(spec_path)); tmp = tempfile.mkdtemp()
    hp = os.path.join(tmp, "p.html"); open(hp, "w").write(page(spec))
    fr = os.path.join(tmp, "fr"); os.makedirs(fr)
    asyncio.run(frames(hp, fr, DUR))
    v = os.path.join(tmp, "v.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{fr}/f_%04d.jpg", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", v], check=True)
    mu = os.path.join(tmp, "m.wav"); K.make_music(mu, DUR + 1, int(spec.get("music_seed", 9)))
    fx = os.path.join(tmp, "fx.wav"); sfx(fx)
    fc = (f"[1]atrim=0:{DUR},afade=t=out:st={DUR-1.5}:d=1.5,volume=0.55[m];[2]atrim=0:{DUR}[f];"
          f"[m][f]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5,apad=whole_dur={DUR+3},atrim=0:{DUR}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", mu, "-i", fx, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2]); print("ok")
