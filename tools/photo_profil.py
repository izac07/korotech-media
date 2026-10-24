#!/usr/bin/env python3
"""Photo de profil d'un compte (mascotte 3D de studio3d, de face, fond nuit + halo) : PNG carré 1080x1080, lisible
une fois recadré en rond par Instagram. Usage : python3 tools/photo_profil.py <out.png> [couleur_mascotte] [couleur_halo]"""
import os, sys, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K

HTML = r"""<!doctype html><html><head><meta charset='utf-8'><style>*{margin:0}body{width:1080px;height:1080px;overflow:hidden;
background:radial-gradient(circle at 50% 46%,__HALO__ 0,#3a2a6a 34%,#141a3a 66%)}canvas{position:absolute;left:0;top:0}</style></head><body>
<canvas id='cv' width='1080' height='1080'></canvas><script>__THREE__</script><script>
const R=new THREE.WebGLRenderer({canvas:document.getElementById('cv'),antialias:true,alpha:true,preserveDrawingBuffer:true});
R.setSize(1080,1080,false);R.outputEncoding=THREE.sRGBEncoding;R.setClearColor(0x000000,0);
const LIN=c=>new THREE.Color(c).convertSRGBToLinear();
const scene=new THREE.Scene();scene.add(new THREE.HemisphereLight(0xa9b8ff,0x3a2414,.5));
const key=new THREE.DirectionalLight(0xffe0bf,1.0);key.position.set(-3,4,6);scene.add(key);
const rim=new THREE.DirectionalLight(0x7f95ff,.7);rim.position.set(4,3,-3);scene.add(rim);
const GRAD=new THREE.DataTexture(new Uint8Array([110,185,255]),3,1,THREE.RedFormat);GRAD.minFilter=GRAD.magFilter=THREE.NearestFilter;GRAD.needsUpdate=true;
const toon=c=>new THREE.MeshToonMaterial({color:LIN(c),gradientMap:GRAD});
const OLM=new THREE.MeshBasicMaterial({color:0x0b0d1a,side:THREE.BackSide});
const B=(w,h,d)=>new THREE.BoxGeometry(w,h,d);
function mk(g,m,x,y,z,p,ol){const o=new THREE.Mesh(g,m);o.position.set(x,y,z);(p||scene).add(o);if(ol){const q=new THREE.Mesh(g,OLM);q.scale.setScalar(ol);o.add(q);}return o;}
const M=new THREE.Group();scene.add(M);M.rotation.y=-.28;M.rotation.x=.06;
const MC='__MASCOTTE__';
mk(B(1.05,.95,.85),toon(MC),0,0,0,M,1.045);
const W=new THREE.MeshBasicMaterial({color:0xffffff}),K_=new THREE.MeshBasicMaterial({color:0x14141e});
for(const sx of [-1,1]){mk(B(.24,.28,.02),W,sx*.22,.08,.43,M);mk(B(.1,.15,.02),K_,sx*.22+.03,.07,.442,M);
  mk(B(.12,.06,.02),new THREE.MeshBasicMaterial({color:0xff9a8a}),sx*.36,-.1,.432,M);}
// sourire : 3 petits blocs
mk(B(.2,.05,.02),K_,0,-.2,.435,M);mk(B(.05,.05,.02),K_,-.12,-.165,.435,M);mk(B(.05,.05,.02),K_,.12,-.165,.435,M);
// antenne (étincelle) et petits bras
mk(B(.06,.22,.06),toon(MC),0,.58,0,M);const s=mk(B(.16,.16,.16),toon('#ffd23f'),0,.74,0,M,1.12);s.rotation.set(.6,.6,0);
const a1=mk(B(.15,.42,.15),toon(MC),-.62,.02,.05,M,1.08);a1.rotation.z=-.5;
const a2=mk(B(.15,.42,.15),toon(MC),.64,.18,.05,M,1.08);a2.rotation.z=2.4;
const cam=new THREE.PerspectiveCamera(30,1,.1,50);cam.position.set(0,.15,4.2);cam.lookAt(0,.08,0);
R.render(scene,cam);window.done=true;
</script></body></html>"""


async def rendre(out, mascotte, halo):
    from playwright.async_api import async_playwright
    three = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "three.min.js"), encoding="utf-8").read()
    page_html = HTML.replace("__MASCOTTE__", mascotte).replace("__HALO__", halo).replace("__THREE__", three)
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=angle", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1080})
        await pg.set_content(page_html)
        await pg.wait_for_function("window.done===true")
        await pg.screenshot(path=out)
        await b.close()


if __name__ == "__main__":
    asyncio.run(rendre(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "#e8794a", sys.argv[3] if len(sys.argv) > 3 else "#ff7a3d"))
    print("ok")
