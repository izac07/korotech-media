#!/usr/bin/env python3
"""Reels en motion design (v3).  Usage : python3 tools/motion.py <motion.json> <out.mp4>

Le fichier motion.json est dans le dossier du post (les voix vo_<k>.mp3 aussi) et contient :
  {"id", "layout": "messages", "music_seed", "contact", "scenes": [ {"vo", "title": [{"at":0,"text":"..."}], "events": [...]}, ... ]}
Les instants "at" sont des fractions (0 -> 1) de la durée de la scène, qui est calée sur la voix.
Layout disponible pour l'instant : messages (conversation animée).
"""
import json, os, sys, subprocess, tempfile, shutil, asyncio, re, html as H
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korotech as K

def words_timed(text, t0, dur):
    """Découpe la phrase en mots avec un instant de début (proportionnel au nb de lettres, pauses sur la ponctuation)."""
    ws = text.split()
    weights = [len(w) + (6 if re.search(r"[.,;:!?…]$", w) else 2) for w in ws]
    tot = sum(weights) or 1
    out, t = [], t0
    for w, p in zip(ws, weights):
        out.append((w, t)); t += dur * p / tot
    return out

def caption_chunks(words):
    chunks, cur = [], []
    for w, t in words:
        cur.append((w, t))
        if len(cur) == 3 or re.search(r"[.,;:!?…]$", w):
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks

def rich(s):
    s = K.esc(s)
    parts = s.split("**")
    return "".join(f"<em>{p}</em>" if k % 2 else p for k, p in enumerate(parts))

# ------------------------------------------------------------------ layout « messages »
def messages_page(spec, theme, starts, durs, caps, total):
    a = theme["accent"]
    fonts = K._font_faces(["Playfair Display", "Caveat"])
    css = f"""{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;font-family:Inter,sans-serif;color:#3a0f1c;background:linear-gradient(170deg,#fbeef0 0%,#f3d9de 100%);position:relative}}
.blob{{position:absolute;border-radius:50%;filter:blur(60px);opacity:.55}}
.hdr{{position:absolute;left:60px;right:60px;top:150px;height:130px;display:flex;align-items:center;gap:26px;background:rgba(255,255,255,.75);border-radius:40px;padding:0 30px;box-shadow:0 10px 30px rgba(122,31,53,.08)}}
.av{{width:88px;height:88px;border-radius:50%;background:{a};color:#fff;font:800 46px/88px 'Playfair Display';text-align:center;flex:none}}
.nm{{font:700 36px Inter}} .st{{font:500 28px Inter;color:#9a6070;margin-top:4px}}
.chat{{position:absolute;left:60px;right:60px;top:320px;height:600px;display:flex;flex-direction:column;justify-content:flex-start;gap:24px}}
.b{{max-width:800px;padding:30px 40px;border-radius:44px;font:500 44px/1.35 Inter;display:none;position:relative}}
.them{{align-self:flex-start;background:#fff;border-bottom-left-radius:12px;box-shadow:0 8px 24px rgba(122,31,53,.10)}}
.me{{align-self:flex-end;background:{a};color:#fff;border-bottom-right-radius:12px}}
.strike{{position:absolute;left:24px;top:50%;height:7px;background:#ff4d6d;border-radius:4px;width:0}}
.dots{{display:flex;gap:12px;padding:6px 4px}} .dots i{{width:18px;height:18px;border-radius:50%;background:currentColor;opacity:.6;display:block}}
.th{{align-self:flex-start;max-width:820px;padding:24px 36px;border-radius:40px;border:3px dashed #c98a9a;background:rgba(255,255,255,.55);font:italic 500 40px/1.35 Inter;color:#6b3344;display:none}}
.th:before{{content:'💭 '}}
.emo{{align-self:center;font-size:220px;line-height:1;display:none;margin-top:60px}}
.tag{{align-self:center;font:700 26px Inter;letter-spacing:3px;text-transform:uppercase;color:#9a6070;display:none;margin-top:6px}}
.seen{{align-self:flex-end;font:500 26px Inter;color:#9a6070;display:none;margin-top:-12px}}
.inp{{position:absolute;left:60px;right:60px;top:960px;height:110px;border-radius:55px;background:#fff;display:flex;align-items:center;padding:0 18px 0 44px;font:500 38px Inter;color:#3a0f1c;box-shadow:0 10px 30px rgba(122,31,53,.10)}}
.inp .ph{{color:#c4a1aa}} .inp .send{{margin-left:auto;width:78px;height:78px;border-radius:50%;background:{a};color:#fff;font:800 40px/78px Inter;text-align:center;flex:none}}
.cur{{display:inline-block;width:4px;height:44px;background:{a};vertical-align:-8px;margin-left:3px}}
.big{{position:absolute;left:70px;right:70px;top:1120px;text-align:center}}
.ln{{font:800 92px/1.08 'Playfair Display';display:block;opacity:0}}
.ln em{{font-style:italic;color:{a}}}
.capw{{position:absolute;left:0;right:0;top:1480px;text-align:center}}
.cap{{display:none;background:rgba(255,255,255,.92);border-radius:24px;padding:16px 32px;font:800 48px Inter;color:#3a0f1c}}
.cap .on{{color:{a}}}
.heart{{position:absolute;left:390px;top:420px;width:300px;height:280px;opacity:0}}
.cta{{position:absolute;left:70px;top:1120px;display:flex;flex-direction:column;gap:26px}}
.pill{{background:#fff;border-radius:40px;padding:20px 34px;font:700 42px Inter;box-shadow:0 8px 24px rgba(122,31,53,.10);opacity:0;align-self:flex-start}}
.pill em{{font-style:normal;color:{a}}}
.bar{{position:absolute;left:0;top:0;height:10px;background:{a}}}
"""
    scenes_html, js_scenes = [], []
    for k, sc in enumerate(spec["scenes"]):
        a0, d = starts[k], durs[k]
        T = lambda f: round(a0 + f * d, 3)
        bubbles = []
        for j, ev in enumerate(sc.get("events", [])):
            kind = ev["kind"]; at = T(ev["at"])
            eid = f"e{k}_{j}"
            if kind in ("them", "me"):
                bubbles.append(f"<div class='b {kind}' id='{eid}' data-at='{at}'>{rich(ev['text'])}</div>")
                js_scenes.append({"id": eid, "k": "pop", "at": at})
            elif kind in ("typing_them", "typing_me"):
                who = "them" if kind == "typing_them" else "me"
                bubbles.append(f"<div class='b {who}' id='{eid}'><div class='dots'><i></i><i></i><i></i></div></div>")
                js_scenes.append({"id": eid, "k": "typing", "at": at, "until": T(ev["until"])})
            elif kind == "type_erase":
                bubbles.append(f"<div class='b me' id='{eid}'><span class='tx'></span></div>")
                js_scenes.append({"id": eid, "k": "typeerase", "at": at, "full": T(ev["full"]), "erase": T(ev["erase"]), "gone": T(ev["gone"]), "text": ev["text"]})
            elif kind == "strike":
                js_scenes.append({"id": f"e{k}_{ev['target']}", "k": "strike", "at": at})
            elif kind in ("thought", "emoji", "tag"):
                cls = {"thought": "th", "emoji": "emo", "tag": "tag"}[kind]
                bubbles.append(f"<div class='{cls}' id='{eid}'>{rich(ev['text'])}</div>")
                js_scenes.append({"id": eid, "k": "pop", "at": at})
            elif kind == "seen":
                bubbles.append(f"<div class='seen' id='{eid}'>Vu</div>")
                js_scenes.append({"id": eid, "k": "show", "at": at})
            elif kind == "input":
                js_scenes.append({"id": "inptx", "k": "input", "at": at, "end": T(ev["end"]), "send": T(ev["send"]), "text": ev["text"], "bubble": f"e{k}_{ev['bubble']}"})
            elif kind == "heart":
                js_scenes.append({"id": "heart", "k": "heart", "at": at})
            elif kind == "pill":
                scenes_html.append(f"<div class='pill' id='{eid}' style='position:absolute;left:70px;top:{730 + 112 * ev.get("row", 0)}px'>{rich(ev['text'])}</div>")
                js_scenes.append({"id": eid, "k": "pill", "at": at})
        lines = "".join(f"<span class='ln' data-at='{T(l['at'])}'>{rich(l['text'])}</span>" for l in sc.get("title", []))
        scenes_html.append(f"<div class='chat' id='c{k}' data-a='{a0}' data-b='{a0 + d}'>{''.join(bubbles)}</div>")
        scenes_html.append(f"<div class='big' id='t{k}' data-a='{a0}' data-b='{a0 + d}'>{lines}</div>")
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    heart = f"""<svg class='heart' id='heart' viewBox='0 0 300 280'><path id='hp' d='M150 260 C 40 180 0 120 30 70 C 60 20 130 30 150 80 C 170 30 240 20 270 70 C 300 120 260 180 150 260 Z' fill='none' stroke='{a}' stroke-width='14' stroke-linecap='round' stroke-linejoin='round'/></svg>"""
    contact = H.escape(spec.get("contact", "Une amie"))
    page = f"""<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>
<div class='blob' id='bl1' style='width:600px;height:600px;background:#ffc2cf;left:-150px;top:200px'></div>
<div class='blob' id='bl2' style='width:520px;height:520px;background:#f7a8bb;right:-160px;top:1200px'></div>
<div class='bar' id='bar'></div>
<div class='hdr'><div class='av'>{H.escape(contact[0])}</div><div><div class='nm'>{contact}</div><div class='st' id='st'>en ligne</div></div></div>
{''.join(scenes_html)}{heart}
<div class='inp' id='inp'><span id='inptx' class='ph'>Écris un message…</span><div class='send' id='send'>↑</div></div>
<div class='capw'>{cap_html}</div>
<script>
const EV={json.dumps(js_scenes, ensure_ascii=False)}; const D={total};
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), back=x=>{{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);}};
function esc(s){{return s.replace(/&/g,'&amp;').replace(/</g,'&lt;');}}
window.render=function(t){{
 document.getElementById('bar').style.width=(c(t/D)*1080)+'px';
 document.getElementById('bl1').style.transform=`translate(${{Math.sin(t/2.5)*60}}px,${{Math.cos(t/3)*50}}px)`;
 document.getElementById('bl2').style.transform=`translate(${{Math.cos(t/2.8)*70}}px,${{Math.sin(t/3.5)*50}}px)`;
 for(const el of document.querySelectorAll('.chat,.big')){{const a=+el.dataset.a,b=+el.dataset.b;
   const vin=a<=0?1:eo((t-a)/0.35), vout=1-eo((t-(b-0.25))/0.25); const v=Math.min(vin,vout);
   el.style.opacity=(t>=a-0.001&&t<b)?v:0; el.style.transform=`translateY(${{(1-vin)*60-(1-vout)*80}}px)`;}}
 for(const l of document.querySelectorAll('.ln')){{const at=+l.dataset.at;const k=at<=0.001?1:back((t-at)/0.45);l.style.opacity=at<=0.001?1:c((t-at)/0.15);
   const sh=(t-at>0&&t-at<0.25&&l.querySelector('em'))?Math.sin((t-at)*90)*6*(1-(t-at)/0.25):0;
   l.style.transform=`translateY(${{(1-k)*70}}px) translateX(${{sh}}px)`;}}
 let typing=false; const inp=document.getElementById('inptx'); let inpState=null;
 for(const e of EV){{const el=document.getElementById(e.id);
  if(e.k==='pop'){{el.style.display=t>=e.at-0.001?'block':'none';const q=e.at<=0.001?1:back((t-e.at)/0.35);el.style.transform=`scale(${{0.5+0.5*q}})`;el.style.transformOrigin=el.classList.contains('me')?'right bottom':'left bottom';el.style.opacity=e.at<=0.001?1:c((t-e.at)/0.1);}}
  else if(e.k==='typing'){{const on=t>=e.at&&t<e.until;el.style.display=on?'block':'none';if(on){{typing=el.classList.contains('them');[...el.querySelectorAll('i')].forEach((d,n)=>d.style.transform=`translateY(${{-Math.max(0,Math.sin((t-e.at)*9-n*0.9))*12}}px)`);}}}}
  else if(e.k==='typeerase'){{const on=t>=e.at&&t<e.gone;el.style.display=on?'block':'none';const L=e.text.length;let n;
     if(t<e.full)n=Math.floor(c((t-e.at)/(e.full-e.at))*L);else if(t<e.erase)n=L;else n=Math.floor((1-c((t-e.erase)/Math.max(0.2,e.gone-e.erase-0.1)))*L);
     el.querySelector('.tx').innerHTML=esc(e.text.slice(0,n))+"<span class='cur' style='background:#fff'></span>";}}
  else if(e.k==='strike'){{let s=el.querySelector('.strike');if(!s){{s=document.createElement('div');s.className='strike';el.appendChild(s);}}s.style.width=(eo((t-e.at)/0.4)*(el.offsetWidth-48))+'px';el.style.filter=t>e.at?`saturate(${{1-0.6*eo((t-e.at)/0.4)}})`:'none';}}
  else if(e.k==='show'){{el.style.display=t>=e.at?'block':'none';el.style.opacity=c((t-e.at)/0.2);}}
  else if(e.k==='input'){{if(t>=e.at-0.3&&t<e.send+0.4)inpState=e;}}
  else if(e.k==='heart'){{const h=document.getElementById('heart');const p=document.getElementById('hp');const L=p.getTotalLength();h.style.opacity=t>=e.at?1:0;
     p.style.strokeDasharray=L;p.style.strokeDashoffset=L*(1-eo((t-e.at)/1.1));const f=c((t-e.at-1.1)/0.4);p.setAttribute('fill',f>0?`rgba(122,31,53,${{f*0.9}})`:'none');
     const beat=t>e.at+1.5?1+0.06*Math.max(0,Math.sin((t-e.at-1.5)*7)):1;h.style.transform=`scale(${{beat}})`;}}
  else if(e.k==='pill'){{const q=back((t-e.at)/0.4);el.style.opacity=c((t-e.at)/0.12);el.style.transform=`translateX(${{(1-q)*-120}}px)`;}}
 }}
 const send=document.getElementById('send');
 if(inpState){{const e=inpState;const L=e.text.length;const n=Math.floor(c((t-e.at)/(e.end-e.at))*L);
   if(t<e.send){{inp.className='';const vis=n>34?'…'+e.text.slice(n-33,n):e.text.slice(0,n);inp.innerHTML=esc(vis)+"<span class='cur'></span>";}}
   else{{inp.className='ph';inp.textContent='Écris un message…';}}
   const pulse=(t>e.end&&t<e.send)?1+0.12*Math.abs(Math.sin((t-e.end)*8)):1;send.style.transform=`scale(${{pulse}})`;}}
 else{{inp.className='ph';inp.textContent='Écris un message…';send.style.transform='scale(1)';}}
 document.getElementById('st').textContent=typing?'en train d’écrire…':'en ligne';
 for(const cp of document.querySelectorAll('.cap')){{const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}}
}};render(0);
</script></body></html>"""
    return page

# ------------------------------------------------------------------ layout « terminal »
def terminal_page(spec, theme, starts, durs, caps, total):
    g = theme["accent"]
    fonts = K._font_faces(["Archivo Black", "JetBrains Mono", "Space Grotesk"])
    css = f"""{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;background:#040705;color:#eafff2;font-family:'Space Grotesk',sans-serif;position:relative}}
.grid{{position:absolute;inset:-120px;background-image:linear-gradient(rgba(57,255,136,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(57,255,136,.06) 1px,transparent 1px);background-size:60px 60px}}
.glow{{position:absolute;width:900px;height:900px;border-radius:50%;background:radial-gradient(circle,rgba(57,255,136,.18),transparent 65%)}}
.win{{position:absolute;left:50px;right:50px;top:200px;height:820px;border:2px solid rgba(57,255,136,.4);border-radius:28px;background:rgba(6,12,8,.94);box-shadow:0 0 90px rgba(57,255,136,.15);overflow:hidden}}
.wbar{{height:76px;display:flex;align-items:center;gap:14px;padding:0 30px;border-bottom:2px solid rgba(57,255,136,.18);background:rgba(57,255,136,.05)}}
.wbar i{{width:20px;height:20px;border-radius:50%;display:block}}
.fname{{flex:1;text-align:center;font:400 26px 'JetBrains Mono';color:#7fa891;margin-right:100px}}
.term{{position:absolute;left:44px;right:44px;top:112px;bottom:30px;display:flex;flex-direction:column;gap:22px;font:400 45px/1.42 'JetBrains Mono'}}
.l{{display:none;white-space:pre-wrap}}
.cmd .p{{color:{g}}}
.out{{color:#d6f5e2}} .cm{{color:#5f8a70;font-style:italic}} .warn{{color:#febc2e}} .ok{{color:{g}}}
.spin{{color:{g}}}
.hl{{color:#b6ff3b}}
.cur{{display:inline-block;width:20px;height:40px;background:{g};vertical-align:-6px;margin-left:4px}}
.pbar{{height:26px;border:2px solid {g};border-radius:8px;overflow:hidden;margin-top:6px}} .pbar b{{display:block;height:100%;width:0;background:{g}}}
.big{{position:absolute;left:70px;right:70px;top:1080px}}
.ln{{font:400 96px/1.08 'Archivo Black';display:block;opacity:0}}
.ln em{{font-style:normal;color:{g}}}
.capw{{position:absolute;left:0;right:0;top:1480px;text-align:center}}
.cap{{display:none;background:rgba(6,12,8,.92);border:2px solid rgba(57,255,136,.5);border-radius:18px;padding:14px 30px;font:700 46px 'JetBrains Mono';color:#eafff2}}
.cap .on{{color:{g}}}
.pill{{position:absolute;left:70px;border:3px solid {g};border-radius:18px;padding:18px 30px;font:700 40px 'JetBrains Mono';background:rgba(6,12,8,.95);opacity:0}}
.pill em{{font-style:normal;color:{g}}}
.bar{{position:absolute;left:0;top:0;height:10px;background:{g}}}
"""
    parts, evs = [], []
    for k, sc in enumerate(spec["scenes"]):
        a0, d = starts[k], durs[k]
        T = lambda f: round(a0 + f * d, 3)
        lines = []
        for j, ev in enumerate(sc.get("events", [])):
            kind = ev["kind"]; at = T(ev["at"]); eid = f"e{k}_{j}"
            if kind == "cmd":
                lines.append(f"<div class='l cmd' id='{eid}'><span class='p'>$ </span><span class='tx'></span></div>")
                evs.append({"id": eid, "k": "type", "at": at, "end": T(ev["end"]), "text": ev["text"]})
            elif kind in ("out", "cm", "warn", "ok"):
                txt = ev["text"]
                if kind == "cm": txt = "// " + txt
                lines.append(f"<div class='l {kind}' id='{eid}'>{K.esc(txt)}</div>")
                evs.append({"id": eid, "k": "line", "at": at})
            elif kind == "spin":
                lines.append(f"<div class='l spin' id='{eid}'></div>")
                evs.append({"id": eid, "k": "spin", "at": at, "until": T(ev["until"]), "text": ev.get("text", "génération en cours")})
            elif kind == "check":
                lines.append(f"<div class='l out' id='{eid}'><span class='bx ok'>[ ]</span> {K.esc(ev['text'])}</div>")
                evs.append({"id": eid, "k": "check", "at": at, "tick": T(ev.get("tick", ev["at"] + 0.06))})
            elif kind == "prog":
                lines.append(f"<div class='l ok' id='{eid}'>{K.esc(ev.get('text',''))}<div class='pbar'><b></b></div></div>")
                evs.append({"id": eid, "k": "prog", "at": at, "end": T(ev["end"])})
            elif kind == "pill":
                parts.append(f"<div class='pill' id='{eid}' style='top:{740 + 120 * ev.get("row", 0)}px'>{rich(ev['text'])}</div>")
                evs.append({"id": eid, "k": "pill", "at": at})
        title = "".join(f"<span class='ln' data-at='{T(l['at'])}'>{rich(l['text'])}</span>" for l in sc.get("title", []))
        parts.append(f"<div class='term sc' data-a='{a0}' data-b='{a0 + d}' data-f='{K.esc(sc.get('file', 'terminal'))}'>{''.join(lines)}</div>")
        parts.append(f"<div class='big sc2' data-a='{a0}' data-b='{a0 + d}'>{title}</div>")
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    terms = "".join(p for p in parts if "class='term" in p)
    others = "".join(p for p in parts if "class='term" not in p)
    page = f"""<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>
<div class='grid' id='grid'></div><div class='glow' id='gl' style='left:-300px;top:900px'></div><div class='bar' id='bar'></div>
<div class='win' id='win'><div class='wbar'><i style='background:#ff5f57'></i><i style='background:#febc2e'></i><i style='background:#28c840'></i><div class='fname' id='fn'></div></div>{terms}</div>
{others}<div class='capw'>{cap_html}</div>
<script>
const EV={json.dumps(evs, ensure_ascii=False)}; const D={total};
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), back=x=>{{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);}};
const SP='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏';
function esc(s){{return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\\[([^\\]]*)(\\]|$)/g,(m,a,b)=>"<span class='hl'>["+a+b+"</span>");}}
window.render=function(t){{
 document.getElementById('bar').style.width=(c(t/D)*1080)+'px';
 document.getElementById('grid').style.transform=`translateY(${{(t*12)%60}}px)`;
 document.getElementById('gl').style.transform=`translate(${{Math.sin(t/2)*120}}px,${{Math.cos(t/3)*80}}px)`;
 for(const el of document.querySelectorAll('.sc,.sc2')){{const a=+el.dataset.a,b=+el.dataset.b;const vin=a<=0?1:eo((t-a)/0.3),vout=1-eo((t-(b-0.2))/0.2);
   const on=t>=a-0.001&&t<b;el.style.opacity=on?Math.min(vin,vout):0;el.style.transform=`translateY(${{(1-vin)*40}}px)`;
   if(on&&el.dataset.f)document.getElementById('fn').textContent=el.dataset.f;}}
 for(const l of document.querySelectorAll('.ln')){{const at=+l.dataset.at;const k=at<=0.001?1:back((t-at)/0.4);l.style.opacity=at<=0.001?1:c((t-at)/0.12);
   l.style.transform=`translateX(${{(1-k)*-90}}px)`;}}
 for(const e of EV){{const el=document.getElementById(e.id);
  if(e.k==='type'){{el.style.display=t>=e.at-0.001?'block':'none';const n=Math.floor(c((t-e.at)/(e.end-e.at))*e.text.length);
     el.querySelector('.tx').innerHTML=esc(e.text.slice(0,n))+(t<e.end+0.6?"<span class='cur'></span>":"");}}
  else if(e.k==='line'){{el.style.display=t>=e.at-0.001?'block':'none';el.style.opacity=e.at<=0.001?1:c((t-e.at)/0.12);el.style.transform=`translateX(${{(1-eo((t-e.at)/0.25))*-30}}px)`;}}
  else if(e.k==='spin'){{el.style.display=(t>=e.at&&t<e.until)?'block':'none';el.textContent=SP[Math.floor(t*12)%10]+' '+e.text+'.'.repeat(1+Math.floor(t*3)%3);}}
  else if(e.k==='check'){{el.style.display=t>=e.at?'block':'none';el.style.opacity=c((t-e.at)/0.12);el.querySelector('.bx').textContent=t>=e.tick?'[✓]':'[ ]';
     el.querySelector('.bx').style.transform=`scale(${{t>=e.tick?1+0.4*(1-eo((t-e.tick)/0.3)):1}})`;el.querySelector('.bx').style.display='inline-block';}}
  else if(e.k==='prog'){{el.style.display=t>=e.at?'block':'none';el.querySelector('b').style.width=(eo((t-e.at)/(e.end-e.at))*100)+'%';}}
  else if(e.k==='pill'){{const q=back((t-e.at)/0.4);el.style.opacity=c((t-e.at)/0.12);el.style.transform=`translateX(${{(1-q)*-120}}px)`;}}
 }}
 for(const cp of document.querySelectorAll('.cap')){{const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}}
}};render(0);
</script></body></html>"""
    return page

# ------------------------------------------------------------------ layout « cheatsheet » (korotech_fr)
def cheatsheet_page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]; ev = []
    def R(s): return rich(s).replace("<em>", "<span class='gr'>").replace("</em>", "</span>")
    html_sc = []
    for k, s in enumerate(sc):
        a, d = starts[k], durs[k]; ty = s["type"]
        if ty == "hook":
            pages = "".join(f"<div class='page' id='pg{i}'><i style='width:80%'></i><i class='hlb' style='width:65%'></i><i style='width:90%'></i><i style='width:55%'></i><i class='hlb' style='width:75%'></i><i style='width:85%'></i></div>" for i in range(3))
            parts = "".join(f"<b class='pt' id='pt{i}'></b>" for i in range(46))
            big = H.escape(s.get("big", "3")); h1 = R(s["title"]) if s.get("title") else "IA <span class='gr'>GRATUITES</span>"
            h2 = H.escape(s.get("sub", "que presque personne n'utilise 👀"))
            inner = (f"{pages}{parts}<div class='three' id='three'>{big}</div><div class='h1' id='h1'>{h1}</div>"
                     f"<div class='h2' id='h2'>{h2}</div>")
            # hook lisible dès 0,25 s (audit : le pouce décide dans la première demi-seconde)
            ev += [{"k": "whoosh", "at": a + 0.1}, {"k": "impact", "at": a + 0.25}, {"k": "sparkle", "at": a + 0.5}]
        elif ty == "pills":
            pills = "".join(f"<div class='pill' id='pl{k}_{j}'>{H.escape(p)}</div>" for j, p in enumerate(s["pills"]))
            wave = "".join(f"<i id='wv{j}'></i>" for j in range(14))
            inner = (f"<div class='card' id='cd{k}'><div class='hd'><span class='gr num'>{s['num']}</span> · {H.escape(s['name'])}</div>"
                     f"<div class='drop'><div class='pdf' id='pdf{k}'><span>{H.escape(s.get('ext', 'PDF'))}</span>{H.escape(s['file'])}</div></div></div>"
                     f"<div class='pills'>{pills}<div class='wave' id='wave{k}'>{wave}</div></div><div class='bt' id='bt{k}'>{R(s['text'])}</div>")
            ev += [{"k": "pop", "at": a + 0.9}] + [{"k": "pop", "at": a + 1.7 + 0.8 * j} for j in range(len(s["pills"]))]
        elif ty == "diagram":
            lines = "".join(f"<i class='tl' id='tl{k}_{j}' style='width:{w}%'></i>" for j, w in enumerate([92, 85, 96, 70, 88, 94, 60]))
            n = s["nodes"]
            inner = (f"<div class='card tall' id='cd{k}'><div class='hd'><span class='gr num'>{s['num']}</span> · {H.escape(s['name'])}</div>"
                     f"<div class='tblock'>{lines}</div>"
                     f"<svg class='dg' viewBox='0 0 880 520'><defs><linearGradient id='lg' x1='0' x2='1'><stop offset='0' stop-color='#7b5cff'/><stop offset='1' stop-color='#ff4fd8'/></linearGradient></defs>"
                     f"<path id='ln{k}_0' d='M190 130 L440 300' stroke='url(#lg)' stroke-width='8' fill='none' stroke-linecap='round'/>"
                     f"<path id='ln{k}_1' d='M440 300 L690 410' stroke='url(#lg)' stroke-width='8' fill='none' stroke-linecap='round'/></svg>"
                     f"<div class='node' id='nd{k}_0' style='left:60px;top:250px'>{H.escape(n[0])}</div><div class='node' id='nd{k}_1' style='left:310px;top:420px'>{H.escape(n[1])}</div>"
                     f"<div class='node' id='nd{k}_2' style='left:520px;top:530px'>{H.escape(n[2])}</div></div><div class='bt' id='bt{k}'>{R(s['text'])}</div>")
            ev += [{"k": "pop", "at": a + 2.6 + 0.4 * j} for j in range(3)] + [{"k": "whoosh", "at": a + 2.2}]
        elif ty == "search":
            ans = "".join(f"<div class='ans' id='an{k}_{j}'>• {H.escape(x)} <span class='src'>[{j+1}]</span></div>" for j, x in enumerate(s["answers"]))
            inner = (f"<div class='card tall' id='cd{k}'><div class='hd'><span class='gr num'>{s['num']}</span> · {H.escape(s['name'])}</div>"
                     f"<div class='sbar'><span>🔍</span><span id='q{k}'></span><b class='cur' id='cu{k}'></b></div>{ans}"
                     f"<div class='badge' id='bg{k}'>⚠ Vérifie toujours</div></div><div class='bt' id='bt{k}'>{R(s['text'])}</div>")
            ev += [{"k": "type", "at": a + 0.6, "end": a + 2.2, "text": s["q"]}] + [{"k": "pop", "at": a + 2.6 + 0.5 * j} for j in range(3)] + [{"k": "pop", "at": a + 4.9}]
        elif ty == "cta":
            names = [x["name"] for x in sc if x.get("name")]
            minis = "".join(f"<div class='mini' id='mi{j}'><span class='gr'>0{j+1}</span><br>{H.escape(nm)}</div>" for j, nm in enumerate(names))
            ctas = "".join(f"<div class='ctl' id='ct{j}'>{H.escape(x)}</div>" for j, x in enumerate(s["ctas"]))
            inner = (f"{minis}<div class='bm' id='bm'>🔖</div><div class='logo' id='logo'><span class='gr'>∞</span> {H.escape(spec.get('handle','korotech_fr'))}"
                     f"<span class='fol' id='fol'>Suivre</span></div><div class='ctas'>{ctas}</div>")
            ev += [{"k": "whoosh", "at": a + 0.2}, {"k": "click", "at": a + 2.0}, {"k": "pop", "at": a + 2.9}, {"k": "pop", "at": a + 3.2}, {"k": "pop", "at": a + 3.6}]
        html_sc.append(f"<div class='scn' id='s{k}' data-a='{a:.3f}' data-b='{a+d:.3f}' data-ty='{ty}'>{inner}</div>")
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    S = json.dumps([{"a": starts[k], "b": starts[k] + durs[k], "ty": s["type"], "q": s.get("q", "")} for k, s in enumerate(sc)], ensure_ascii=False)
    css = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:#0d0a1c;color:#fff;font-family:Inter,sans-serif;position:relative}
.glow{position:absolute;border-radius:50%;filter:blur(30px)}
.gr{background:linear-gradient(90deg,#7b5cff,#ff4fd8);-webkit-background-clip:text;color:transparent}
.scn{position:absolute;inset:0;opacity:0}
.page{position:absolute;width:420px;height:540px;background:#f3f0ff;border-radius:18px;padding:50px 40px;display:flex;flex-direction:column;gap:30px;box-shadow:0 30px 60px rgba(0,0,0,.5)}
.page i{display:block;height:20px;border-radius:10px;background:#c9c3e6}.page i.hlb{background:#ffe86a}
.pt{position:absolute;width:16px;height:16px;border-radius:50%;background:linear-gradient(90deg,#7b5cff,#ff4fd8);opacity:0}
.three{position:absolute;left:0;right:0;top:330px;text-align:center;font:700 560px/1 Poppins;background:linear-gradient(160deg,#7b5cff,#ff4fd8);-webkit-background-clip:text;color:transparent;opacity:0}
.h1{position:absolute;left:0;right:0;top:960px;text-align:center;font:700 120px/1 Poppins;opacity:0}
.h2{position:absolute;left:0;right:0;top:1110px;text-align:center;font:600 54px Inter;color:#d9d3f5;opacity:0}
.card{position:absolute;left:70px;right:70px;top:300px;height:560px;border-radius:44px;background:rgba(255,255,255,.07);border:2px solid rgba(160,130,255,.45);box-shadow:0 30px 90px rgba(91,46,255,.25)}
.card.tall{height:800px}
.hd{padding:44px 54px 0;font:700 64px Poppins}
.num{font-size:76px}
.drop{position:absolute;left:0;right:0;top:170px;bottom:0;display:flex;justify-content:center}
.pdf{position:absolute;top:60px;width:300px;height:300px;border-radius:28px;background:#fff;color:#2a2440;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;font:600 28px Inter;box-shadow:0 20px 40px rgba(0,0,0,.4)}
.pdf span{background:#e5484d;color:#fff;font:800 56px Inter;padding:10px 30px;border-radius:16px}
.pills{position:absolute;left:70px;right:70px;top:920px;display:flex;flex-direction:column;gap:26px;align-items:flex-start}
.pill{padding:26px 44px;border-radius:999px;background:linear-gradient(90deg,#5b2eff,#e23cc8);font:700 54px Inter;opacity:0}
.wave{position:absolute;left:600px;top:272px;display:flex;gap:10px;align-items:center;height:110px;opacity:0}.wave i{display:block;width:14px;border-radius:7px;background:#ff9ae9}
.bt{position:absolute;left:50px;right:50px;top:1340px;text-align:center;font:700 54px/1.2 Poppins;opacity:0}
.tblock{position:absolute;left:54px;right:54px;top:200px;display:flex;flex-direction:column;gap:28px}
.tl{display:block;height:26px;border-radius:13px;background:rgba(220,210,255,.35);transform-origin:left}
.dg{position:absolute;left:0;top:140px;width:940px;height:556px}
.node{position:absolute;padding:24px 40px;border-radius:30px;background:#1b1535;border:3px solid #a58bff;font:700 46px Inter;opacity:0;box-shadow:0 0 40px rgba(226,60,200,.35)}
.sbar{margin:44px 54px 0;height:110px;border-radius:55px;background:rgba(255,255,255,.95);color:#1d1838;display:flex;align-items:center;gap:18px;padding:0 36px;font:600 35px Inter;white-space:nowrap}
.cur{display:inline-block;width:4px;height:46px;background:#5b2eff}
.ans{margin:34px 54px 0;font:600 44px/1.35 Inter;opacity:0;color:#f2efff}
.src{display:inline-block;padding:4px 14px;border-radius:12px;background:rgba(123,92,255,.35);color:#fff;font:700 34px Inter}
.badge{position:absolute;right:40px;bottom:50px;background:#ffd43b;color:#1d1838;font:800 44px Inter;padding:18px 30px;border-radius:20px;opacity:0}
.mini{position:absolute;left:390px;top:520px;width:300px;height:400px;border-radius:36px;background:rgba(255,255,255,.08);border:2px solid rgba(160,130,255,.5);
 display:flex;align-items:center;justify-content:center;text-align:center;font:700 48px/1.3 Poppins;opacity:0;box-shadow:0 20px 60px rgba(91,46,255,.3)}
.bm{position:absolute;left:0;right:0;top:560px;text-align:center;font-size:260px;opacity:0}
.logo{position:absolute;left:0;right:0;top:920px;text-align:center;font:700 70px Poppins;opacity:0}
.fol{display:inline-block;margin-left:24px;padding:12px 34px;border-radius:20px;background:linear-gradient(90deg,#5b2eff,#e23cc8);font:700 44px Inter;vertical-align:middle}
.ctas{position:absolute;left:0;right:0;top:1100px;display:flex;flex-direction:column;align-items:center;gap:24px}
.ctl{padding:22px 40px;border-radius:26px;background:rgba(255,255,255,.08);border:2px solid rgba(160,130,255,.45);font:700 50px Inter;opacity:0}
.capw{position:absolute;left:0;right:0;top:1500px;text-align:center}
.cap{display:none;background:rgba(13,10,28,.85);border:2px solid rgba(160,130,255,.5);border-radius:22px;padding:14px 32px;font:800 50px Inter}
.cap .on{color:#ff9ae9}
.bar{position:absolute;left:0;top:0;height:10px;background:linear-gradient(90deg,#5b2eff,#e23cc8)}
.sweep{position:absolute;top:0;bottom:0;width:700px;background:linear-gradient(90deg,transparent,rgba(123,92,255,.55),rgba(226,60,200,.55),transparent);opacity:0}
"""
    css = K._font_faces(["Poppins", "Inter"]) + css  # polices embarquées : rendu identique en local et dans le cloud
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>
<div class='glow' id='g1' style='width:900px;height:900px;left:-300px;top:-200px;background:radial-gradient(circle,rgba(91,46,255,.5),transparent 65%)'></div>
<div class='glow' id='g2' style='width:900px;height:900px;right:-350px;bottom:200px;background:radial-gradient(circle,rgba(226,60,200,.4),transparent 65%)'></div>
<div class='sweep' id='sw'></div>
{''.join(html_sc)}<div class='capw'>{cap_html}</div><div class='bar' id='bar'></div>
<script>
const EV={json.dumps(ev, ensure_ascii=False)}; const D={total}; const SC={S};
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), ei=x=>c(x)*c(x)*c(x), back=x=>{{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);}};
const $=id=>document.getElementById(id);
function rnd(i){{const x=Math.sin(i*12.9898)*43758.5453;return x-Math.floor(x);}}
function pop(el,t0,t,from=.4,dx=0,dy=40){{const k=back((t-t0)/.45);el.style.opacity=c((t-t0)/.12);el.style.transform=`translate(${{(1-k)*dx}}px,${{(1-k)*dy}}px) scale(${{from+(1-from)*k}})`;}}
window.render=function(t){{
 $('bar').style.width=(c(t/D)*1080)+'px';
 $('g1').style.transform=`translate(${{Math.sin(t/2)*80}}px,${{Math.cos(t/2.6)*60}}px)`;$('g2').style.transform=`translate(${{Math.cos(t/2.2)*80}}px,${{Math.sin(t/3)*60}}px)`;
 let sw=-1;
 SC.forEach((s,k)=>{{const el=$('s'+k);const on=t>=s.a-0.001&&t<s.b;const u=t-s.a;
  const vin=k==0?1:eo(u/.35), vout=eo((t-(s.b-.3))/.3);
  el.style.opacity=on?1:0; const x=(1-vin)*1080-vout*1080; const bl=Math.abs((1-vin)+vout)>0.02?Math.min(18,40*Math.abs((1-vin)+vout)):0;
  el.style.transform=`translateX(${{x}}px)`;el.style.filter=bl?`blur(${{bl}}px)`:'none';
  if(k>0&&u>=0&&u<.45)sw=u/.45;
  if(!on)return;
  if(s.ty==='hook'){{
    for(let i=0;i<3;i++){{const p=$('pg'+i);const fly=eo((u-.15)/.35);const x0=250+i*40, y0=520+i*30;
      p.style.left=(x0+fly*900)+'px';p.style.top=(y0-fly*120)+'px';p.style.transform=`rotate(${{-8+i*7+fly*25}}deg)`;
      p.style.filter=(u>.15&&u<.5)?`blur(${{14*Math.sin(c((u-.15)/.35)*Math.PI)}}px)`:'none';p.style.opacity=u<.45?1:1-c((u-.45)/.12);}}
    for(let i=0;i<46;i++){{const p=$('pt'+i);const v=(u-.2);const ang=rnd(i)*6.283,sp=300+rnd(i+9)*900;
      if(v<0||v>1.2){{p.style.opacity=0;continue;}}p.style.opacity=1-v/1.2;p.style.left=(700+Math.cos(ang)*sp*eo(v/1.2))+'px';p.style.top=(800+Math.sin(ang)*sp*eo(v/1.2))+'px';}}
    const th=$('three');const k3=back((u-.25)/.5);th.style.opacity=c((u-.25)/.1);th.style.transform=`scale(${{.2+.8*k3+.02*Math.sin(u*3)}})`;
    pop($('h1'),.5,u,.6,0,50);pop($('h2'),.85,u,.8,0,40);
  }}
  if(s.ty==='pills'){{pop($('cd'+k),.0,u+.35,.9,0,60);
    const pd=$('pdf'+k);const kd=back((u-.6)/.5);pd.style.opacity=c((u-.6)/.1);pd.style.transform=`translateY(${{(1-kd)*-500}}px) rotate(${{(1-kd)*-12}}deg)`;
    for(let j=0;j<3;j++)pop($('pl'+k+'_'+j),1.7+.8*j,u,.5,-200,0);
    const w=$('wave'+k);w.style.opacity=c((u-3.4)/.3);for(let j=0;j<14;j++)$('wv'+j).style.height=(14+60*Math.abs(Math.sin(u*6+j*0.7)))+'px';
    pop($('bt'+k),4.2,u,.8,0,40);}}
  if(s.ty==='diagram'){{pop($('cd'+k),.0,u+.35,.9,0,60);
    for(let j=0;j<7;j++){{const l=$('tl'+k+'_'+j);l.style.opacity=c((u-.3-j*.08)/.2)*(1-c((u-2.6)/.2));l.style.transform=`scaleX(${{1-eo((u-2.0-j*.06)/.4)}})`;}}
    for(let j=0;j<3;j++){{const n=$('nd'+k+'_'+j);pop(n,2.6+.4*j,u,.3,0,0);if(u>3.8)n.style.boxShadow=`0 0 ${{30+20*Math.sin(u*4+j)}}px rgba(226,60,200,.55)`;}}
    for(let j=0;j<2;j++){{const p=$('ln'+k+'_'+j);const L=p.getTotalLength();p.style.strokeDasharray=L;p.style.strokeDashoffset=L*(1-eo((u-2.9-.4*j)/.45));}}
    pop($('bt'+k),4.2,u,.8,0,40);}}
  if(s.ty==='search'){{pop($('cd'+k),.0,u+.35,.9,0,60);
    const n=Math.floor(c((u-.6)/1.6)*s.q.length);$('q'+k).textContent=s.q.slice(0,n);$('cu'+k).style.opacity=(u<2.6&&Math.floor(u*3)%2==0)?1:0;
    for(let j=0;j<3;j++){{const an=$('an'+k+'_'+j);pop(an,2.6+.5*j,u,1,-60,0);const sr=an.querySelector('.src');const g=c((u-2.9-.5*j)/.3);
      sr.style.background=`rgba(${{Math.round(123+103*g)}},${{Math.round(92-32*g)}},${{Math.round(255-55*g)}},${{.35+.5*g}})`;}}
    const bg=$('bg'+k);const kb=back((u-4.9)/.45);bg.style.opacity=c((u-4.9)/.1);bg.style.transform=`rotate(${{-6+0*kb}}deg) scale(${{1.8-.8*kb}})`;
    pop($('bt'+k),4.2,u,.8,0,40);}}
  if(s.ty==='cta'){{const w=u*Math.max(1,9/(s.b-s.a));  // scène courte (voix brève) : l'animation est accélérée pour que les lignes (dont le mot-clé) s'affichent pendant la voix
    for(let j=0;j<3;j++){{const m=$('mi'+j);const kf=back((w-.2-.15*j)/.5);const sh=eo((w-1.8)/.35);
      m.style.opacity=c((w-.2-.15*j)/.1)*(1-sh);m.style.transform=`translateX(${{(j-1)*230*kf*(1-sh)}}px) rotate(${{(j-1)*14*kf*(1-sh)}}deg) scale(${{(.5+.5*kf)*(1-.7*sh)}})`;}}
    const bm=$('bm');const kb=back((w-2.0)/.5);bm.style.opacity=c((w-2.0)/.1);bm.style.transform=`scale(${{.3+.7*kb}})`;
    pop($('logo'),2.6,w,.8,0,30);const f=$('fol');const kf=back((w-2.9)/.4);f.style.transform=`scale(${{w>2.9?.5+.5*kf:0}})`;
    pop($('ct0'),3.2,w,.7,0,40);pop($('ct1'),3.6,w,.7,0,40);}}
 }});
 const swe=$('sw');swe.style.opacity=sw>=0?Math.sin(sw*Math.PI):0;swe.style.left=(sw>=0?-700+sw*2480:-800)+'px';
 for(const cp of document.querySelectorAll('.cap')){{const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}}
}};render(0);
</script></body></html>"""

# ------------------------------------------------------------------ layout « iceberg » (lia.entrepreneur, style terminal brut)
def iceberg_page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]; ev = []; G = "#39ff88"; RED = "#ff4d4d"; YEL = "#febc2e"
    fonts = K._font_faces(["JetBrains Mono", "Archivo Black"])
    S = [{"a": starts[k], "b": starts[k] + durs[k], "ty": s["type"]} for k, s in enumerate(sc)]
    ov = []; h0 = next((x for x in sc if x["type"] == "hook"), {})
    hook_cmd = h0.get("cmd", "./reveler --iceberg"); wtop = h0.get("top", "CE QU'ON TE MONTRE"); wbot = h0.get("bottom", "CE QU'ON TE CACHE")
    for k, s in enumerate(sc):
        a = starts[k]; ty = s["type"]
        if ty == "hook":
            ov.append(f"<div class='cmdl' id='hk'><span class='g'>$ </span><span id='hkt'></span><b class='cur'></b></div>")
            ev += [{"k": "type", "at": a + 0.0, "end": a + 0.55, "text": hook_cmd}, {"k": "impact", "at": a + 0.65}]
        elif ty == "surface":
            pos = [(70, 300), (560, 500), (70, 700)]
            for j, (l, (x, y)) in enumerate(zip(s["labels"], pos)):
                ov.append(f"<div class='lab' id='lb{j}' style='left:{x}px;top:{y}px'>&gt; {H.escape(l)}<span class='faux' id='fx{j}'>[FAUX]</span></div>")
                ev += [{"k": "pop", "at": a + 0.6 + 0.9 * j}, {"k": "impact", "at": a + 1.15 + 0.9 * j}]
        elif ty == "process":
            steps = (s.get("steps") or [f"[ÉTAPE {j+1}]" for j in range(3)])[:3]
            for j, stp in enumerate(steps):
                ov.append(f"<div class='blk' id='bk{j}'>{H.escape(stp)}</div>")
            ov.append(f"<div class='arr' id='ar0'>→</div><div class='arr' id='ar1'>→</div><div class='chaos' id='chaos'{'' if len(s.get('chaos', 'CHAOS')) <= 8 else " style='font-size:84px;letter-spacing:2px'"}>{H.escape((' '.join(s.get('chaos', 'CHAOS').upper())) if len(s.get('chaos', 'CHAOS')) <= 8 else s.get('chaos', '').upper())}</div><div class='okp' id='okp'>✓ {H.escape(s.get('ok', 'process clair'))}</div>")
            ev += [{"k": "pop", "at": a + 0.5 + 0.3 * j} for j in range(3)] + [{"k": "impact", "at": a + 2.2}, {"k": "click", "at": a + 5.4}]
        elif ty == "logs":
            if s.get("logs"):
                COL = {"err": RED, "ok": G, "info": "#cfe", "item": YEL}
                n = len(s["logs"][:8]); step = min(1.1, max(0.45, (durs[k] - 1.5) / max(1, n)))
                L = [(("  + " if kd == "item" else "") + tx, COL.get(kd, "#cfe"), round(0.5 + step * j, 2)) for j, (tx, kd) in enumerate(s["logs"][:8])]
            else:
                L = [("ERREUR 401 · API modifiée", RED, 0.5), ("CHAMP VIDE · formulaire", RED, 1.6), ("[ALERTE] → notification envoyée ✓", G, 3.0),
                     ("abonnements :", "#cfe", 4.4), ("  + outil 1", YEL, 4.9), ("  + outil 2", YEL, 5.4), ("  + outil 3…", YEL, 5.9)]
            for j, (txt, col, at) in enumerate(L):
                ov.append(f"<div class='log' id='lg{j}' data-at='{at}' style='top:{360 + 92 * j}px;color:{col}'>{'[x] ' if col == RED else ''}{H.escape(txt)}</div>")
                ev.append({"k": "impact" if col == RED else "pop", "at": a + at})
        elif ty == "cta":
            ov.append(f"<div class='task' id='task'>[ {H.escape(s.get('task', '1 TÂCHE RÉPÉTITIVE'))} ] <span class='g'>✓</span></div>")
            ov.append(f"<div class='cmdl' id='fc' style='top:170px'><span class='g'>$ </span><span id='fct'></span><b class='cur'></b></div><div class='done' id='done'>[✓] enregistré</div>")
            ev += [{"k": "pop", "at": a + 1.2}, {"k": "type", "at": a + 3.0, "end": a + 4.2, "text": "suivre @" + spec.get("handle", "")}, {"k": "click", "at": a + 4.6}]
        ov.append(f"<div class='bt' id='bt{k}'>{s.get('text','')}</div>")
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    berg = ("M540 560 L470 640 L430 760 L390 900 L250 1150 L160 1500 L200 1900 L330 2300 L540 2600 L760 2350 L880 1950 L920 1500 L840 1150 L700 900 L660 780 L610 650 Z")
    crack = "M540 560 L520 760 L560 900 M430 760 L520 760 M390 900 L470 1250 L380 1700 M700 900 L640 1300 L760 1750 M470 1250 L640 1300 M380 1700 L540 2100 L760 1750 M540 2100 L540 2600"
    css = f"""{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;background:#050806;color:#eafff2;font-family:'JetBrains Mono',monospace;position:relative}}
.g{{color:{G}}}
#world{{position:absolute;left:0;top:0;width:1080px;height:3000px;transform-origin:0 0}}
.water{{position:absolute;left:0;right:0;top:900px;border-top:4px dashed {G}}}
.wl{{position:absolute;right:30px;top:850px;font:700 26px 'JetBrains Mono';color:{G}}}
.sea{{position:absolute;left:0;right:0;top:904px;height:2100px;background:repeating-linear-gradient(0deg,rgba(57,255,136,.035) 0 2px,transparent 2px 46px)}}
.wlab{{position:absolute;left:0;right:0;text-align:center;font:700 52px 'JetBrains Mono';letter-spacing:2px}}
svg#bg{{position:absolute;left:0;top:0;width:1080px;height:3000px}}
.gauge{{position:absolute;left:24px;top:300px;height:940px;width:90px;border-left:3px solid rgba(57,255,136,.6)}}
.gauge i{{position:absolute;left:0;width:22px;border-top:3px solid rgba(57,255,136,.6)}}
.dep{{position:absolute;left:34px;top:1260px;font:700 34px 'JetBrains Mono';color:{G}}}
.scan{{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(0,0,0,.25) 0 2px,transparent 2px 5px);pointer-events:none}}
.cmdl{{position:absolute;left:70px;right:70px;top:150px;font:700 50px 'JetBrains Mono';opacity:0}}
.cur{{display:inline-block;width:26px;height:54px;background:{G};vertical-align:-10px;margin-left:6px}}
.lab{{position:absolute;max-width:470px;padding:18px 24px;border:3px solid {G};background:#050806;font:700 38px/1.3 'JetBrains Mono';opacity:0}}
.faux{{display:inline-block;margin-left:14px;color:{RED};border:3px solid {RED};padding:2px 10px;transform:rotate(-8deg);opacity:0}}
.blk{{position:absolute;top:640px;width:270px;padding:28px 0;text-align:center;border:3px solid {G};background:#050806;font:700 40px 'JetBrains Mono';opacity:0}}
.arr{{position:absolute;top:660px;font:700 60px 'JetBrains Mono';color:{G};opacity:0}}
.chaos{{position:absolute;left:0;right:0;top:880px;text-align:center;font:400 120px 'Archivo Black';color:{RED};opacity:0}}
.okp{{position:absolute;left:0;right:0;top:900px;text-align:center;font:700 52px 'JetBrains Mono';color:{G};opacity:0}}
.log{{position:absolute;left:120px;font:700 44px 'JetBrains Mono';white-space:pre;opacity:0;background:#050806;padding:6px 14px}}
.task{{position:absolute;left:0;right:0;top:700px;margin:auto;width:820px;text-align:center;padding:30px;border:4px solid {G};background:#050806;font:700 50px 'JetBrains Mono';opacity:0}}
.done{{position:absolute;left:70px;top:240px;font:700 44px 'JetBrains Mono';color:{G};opacity:0}}
.bt{{position:absolute;left:40px;right:40px;top:1335px;text-align:center;font:700 54px/1.25 'JetBrains Mono';text-transform:uppercase;opacity:0}}
.capw{{position:absolute;left:0;right:0;top:1505px;text-align:center}}
.cap{{display:none;background:#050806;border:3px solid {G};padding:12px 28px;font:700 46px 'JetBrains Mono'}}
.cap .on{{color:{G}}}
.bar{{position:absolute;left:0;top:0;height:10px;background:{G}}}
.flash{{position:absolute;inset:0;background:{G};opacity:0;mix-blend-mode:screen}}
"""
    ticks = "".join(f"<i style='top:{y}px'></i>" for y in range(0, 941, 94))
    page = f"""<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>
<div id='world'>
 <div class='sea'></div>
 <svg id='bg' viewBox='0 0 1080 3000'><path id='berg' d='{berg}' fill='rgba(57,255,136,.05)' stroke='{G}' stroke-width='5' stroke-linejoin='round'/>
 <path id='crk' d='{crack}' fill='none' stroke='rgba(57,255,136,.45)' stroke-width='3'/></svg>
 <div class='water'></div><div class='wl'>~ ~ NIVEAU DE LA MER ~ ~</div>
 <div class='wlab' id='wl1' style='top:420px'>{H.escape(wtop.upper())}</div>
 <div class='wlab' id='wl2' style='top:1180px;color:{G}'>{H.escape(wbot.upper())} ▼</div>
</div>
<div class='gauge'>{ticks}</div><div class='dep' id='dep'>0 m</div>
{''.join(ov)}
<div class='scan' id='scan'></div><div class='flash' id='fl'></div>
<div class='capw'>{cap_html}</div><div class='bar' id='bar'></div>
<script>
const EV={json.dumps(ev, ensure_ascii=False)}; const D={total}; const SC={json.dumps(S)};
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),4), back=x=>{{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);}};
const $=id=>document.getElementById(id);
const CAM={{hook:[780,1],surface:[700,1.55],process:[1450,1],logs:[2150,1],cta:[1580,.42]}};
function show(el,on,t0,t){{if(!el)return;el.style.opacity=on&&t>=t0?1:0;}}
function popx(el,t0,u){{const k=back((u-t0)/.3);el.style.opacity=u>=t0?1:0;el.style.transform=`scale(${{.6+.4*k}})`;}}
window.render=function(t){{
 $('bar').style.width=(c(t/D)*1080)+'px';
 let k=0;for(let i=0;i<SC.length;i++)if(t>=SC[i].a)k=i;const s=SC[k],u=t-s.a;
 const prev=SC[Math.max(0,k-1)];const [cy0,s0]=CAM[prev.ty],[cy1,s1]=CAM[s.ty];const m=k==0?1:eo(u/.45);
 const cy=cy0+(cy1-cy0)*m, sc=s0+(s1-s0)*m;
 $('world').style.transform=`translate(${{540-540*sc}}px,${{780-cy*sc}}px) scale(${{sc}})`;
 const DP={{hook:0,surface:0,process:10,logs:50,cta:0}};const depth=DP[prev.ty]+(DP[s.ty]-DP[prev.ty])*m;$('dep').textContent=(depth<0.5?'0':'-'+Math.round(depth))+' m';
 $('scan').style.backgroundPosition=`0 ${{(t*40)%5}}px`;
 // hook
 const hk=$('hk');hk.style.opacity=k==0&&u<1.0?1:0;const HC={json.dumps(hook_cmd)};$('hkt').textContent=HC.slice(0,Math.floor(c(u/.4)*HC.length));
 const bp=$('berg');bp.style.strokeDasharray='none';
 $('crk').style.opacity=k==0?c((u-.45)/.3):1;
 $('fl').style.opacity=(k==0&&u>=.42&&u<.62)?.35*(1-(u-.42)/.2):0;
 $('wl1').style.opacity=k==0?1:0;$('wl2').style.opacity=k==0?(u<1.3||Math.floor(u*2.5)%2?1:.25):0;
 // surface
 for(let j=0;j<3;j++){{const l=$('lb'+j);if(!l)continue;if(SC[k].ty!=='surface'){{l.style.opacity=0;continue;}}popx(l,.6+.9*j,u);
   const f=$('fx'+j);const kf=back((u-1.15-.9*j)/.3);f.style.opacity=u>=1.15+.9*j?1:0;f.style.transform=`rotate(-8deg) scale(${{2-kf}})`;}}
 // process
 const pr=s.ty==='process';
 for(let j=0;j<3;j++){{const b=$('bk'+j);if(!b)continue;if(!pr){{b.style.opacity=0;continue;}}
   const x0=50+j*360;const jam=u>2.2&&u<5.4;const r=(n)=>Math.sin(n*91.7+j*13.1);
   b.style.left=(x0+(jam?r(1)*90:0))+'px';b.style.top=(640+(jam?r(2)*160:0))+'px';b.style.transform=`rotate(${{jam?r(3)*24:0}}deg)`;b.style.opacity=u>=.5+.3*j?1:0;
   b.style.borderColor=jam?'{RED}':'{G}';}}
 for(let j=0;j<2;j++){{const a=$('ar'+j);if(!a)continue;a.style.left=(330+j*360)+'px';a.style.opacity=pr&&u>1.3&&!(u>2.2&&u<5.4)?1:0;}}
 const ch=$('chaos');if(ch){{ch.style.opacity=pr&&u>2.2&&u<5.4?(Math.floor(u*8)%3?1:.4):0;ch.style.transform=`translateX(${{pr?Math.sin(u*70)*8:0}}px)`;}}
 const ok=$('okp');if(ok)ok.style.opacity=pr&&u>=5.4?1:0;
 // logs
 for(const el of document.querySelectorAll('.log'))el.style.opacity=s.ty==='logs'&&u>=+el.dataset.at?1:0;
 // cta
 const ta=$('task');if(ta){{if(s.ty==='cta')popx(ta,1.2,u);else ta.style.opacity=0;}}
 const fc=$('fc');if(fc){{fc.style.opacity=s.ty==='cta'&&u>=3.0?1:0;$('fct').textContent=('suivre @{spec.get("handle","")}').slice(0,Math.floor(c((u-3.0)/1.2)*30));}}
 const dn=$('done');if(dn)dn.style.opacity=s.ty==='cta'&&u>=4.6?1:0;
 // texte bas
 SC.forEach((x,i)=>{{const b=$('bt'+i);if(!b)return;const on=i==k;const t0=x.ty==='cta'?.6:.4;b.style.opacity=on&&u>=t0?1:0;}});
 for(const cp of document.querySelectorAll('.cap')){{const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}}
}};render(0);
</script></body></html>"""
    return page

# ------------------------------------------------------------------ layout « sportmotion » (zerosallefit)
POSES = {
 "crunch": [{"H":[78,24],"N":[110,22],"P":[200,20],"E1":[120,62],"W1":[86,44],"E2":[122,60],"W2":[88,42],"K1":[258,82],"F1":[312,12],"K2":[262,80],"F2":[316,12]},
            {"H":[104,96],"N":[132,72],"P":[200,20],"E1":[152,106],"W1":[110,88],"E2":[154,104],"W2":[112,86],"K1":[258,82],"F1":[312,12],"K2":[262,80],"F2":[316,12]}],
 "planche": [{"H":[58,72],"N":[90,62],"P":[190,50],"E1":[95,12],"W1":[40,12],"E2":[98,12],"W2":[43,12],"K1":[252,30],"F1":[330,12],"K2":[255,30],"F2":[333,12]},
             {"H":[58,76],"N":[90,66],"P":[190,56],"E1":[95,12],"W1":[40,12],"E2":[98,12],"W2":[43,12],"K1":[252,32],"F1":[330,12],"K2":[255,32],"F2":[333,12]}],
 "deadbug": [{"H":[78,24],"N":[110,22],"P":[210,20],"E1":[110,92],"W1":[110,152],"E2":[114,92],"W2":[114,152],"K1":[210,92],"F1":[270,92],"K2":[214,92],"F2":[274,92]},
             {"H":[78,24],"N":[110,22],"P":[210,20],"E1":[62,46],"W1":[12,40],"E2":[114,92],"W2":[114,152],"K1":[210,92],"F1":[270,92],"K2":[282,44],"F2":[352,34]}],
 "lateral": [{"H":[80,108],"N":[110,92],"P":[200,56],"E1":[112,40],"W1":[62,14],"E2":[112,150],"W2":[112,206],"K1":[262,34],"F1":[330,12],"K2":[264,36],"F2":[332,14]},
             {"H":[80,104],"N":[110,88],"P":[200,46],"E1":[112,40],"W1":[62,14],"E2":[112,146],"W2":[112,202],"K1":[262,30],"F1":[330,12],"K2":[264,32],"F2":[332,14]}],
 "climber": [{"H":[58,132],"N":[90,116],"P":[220,92],"E1":[93,62],"W1":[95,12],"E2":[96,62],"W2":[98,12],"K1":[282,48],"F1":[340,12],"K2":[152,62],"F2":[172,16]},
             {"H":[58,132],"N":[90,116],"P":[220,92],"E1":[93,62],"W1":[95,12],"E2":[96,62],"W2":[98,12],"K1":[152,62],"F1":[172,16],"K2":[282,48],"F2":[340,12]}],
 "creuse": [{"H":[92,62],"N":[122,50],"P":[200,26],"E1":[72,74],"W1":[22,88],"E2":[74,72],"W2":[24,86],"K1":[270,44],"F1":[340,64],"K2":[272,42],"F2":[342,62]},
            {"H":[92,68],"N":[122,56],"P":[200,26],"E1":[72,80],"W1":[22,94],"E2":[74,78],"W2":[24,92],"K1":[270,50],"F1":[340,72],"K2":[272,48],"F2":[342,70]}],
 "squat": [{"H":[180,176],"N":[180,150],"P":[180,92],"E1":[158,136],"W1":[132,134],"E2":[161,136],"W2":[135,134],"K1":[180,52],"F1":[180,12],"K2":[183,52],"F2":[183,12]},
           {"H":[160,130],"N":[170,105],"P":[208,58],"E1":[146,96],"W1":[120,96],"E2":[149,96],"W2":[123,96],"K1":[168,52],"F1":[180,12],"K2":[171,52],"F2":[183,12]}],
 "pompe": [{"H":[58,104],"N":[90,92],"P":[205,55],"E1":[92,52],"W1":[92,12],"E2":[95,52],"W2":[95,12],"K1":[262,34],"F1":[322,12],"K2":[265,34],"F2":[325,12]},
           {"H":[58,52],"N":[90,42],"P":[205,28],"E1":[125,40],"W1":[92,12],"E2":[128,40],"W2":[95,12],"K1":[262,20],"F1":[322,12],"K2":[265,20],"F2":[325,12]}],
 "fente": [{"H":[180,176],"N":[180,150],"P":[180,92],"E1":[180,122],"W1":[180,96],"E2":[183,122],"W2":[183,96],"K1":[180,52],"F1":[180,12],"K2":[183,52],"F2":[183,12]},
           {"H":[195,140],"N":[195,116],"P":[195,60],"E1":[195,90],"W1":[195,66],"E2":[198,90],"W2":[198,66],"K1":[152,58],"F1":[152,12],"K2":[232,20],"F2":[276,12]}],
 "pont": [{"H":[60,24],"N":[95,22],"P":[200,22],"E1":[130,12],"W1":[165,12],"E2":[133,12],"W2":[168,12],"K1":[255,70],"F1":[285,12],"K2":[258,70],"F2":[288,12]},
          {"H":[60,24],"N":[95,26],"P":[200,74],"E1":[130,12],"W1":[165,12],"E2":[133,12],"W2":[168,12],"K1":[255,78],"F1":[285,12],"K2":[258,78],"F2":[288,12]}],
}

def sportmotion_page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]; ev = []; RED = "#ff2d36"
    fonts = K._font_faces(["Anton"])
    S = [{"a": starts[k], "b": starts[k] + durs[k], "ty": s["type"], "ex": s.get("ex", [])} for k, s in enumerate(sc)]
    a0, a1, a2, a3, a4 = starts
    d2 = durs[2]
    def red(x): return K.esc(x).replace("**", "\x00").split("\x00")
    def R_(x): return "".join(f"<span class='r'>{q}</span>" if n % 2 else q for n, q in enumerate(red(x)))
    h, er, so, po, ct = sc
    exn = so.get("ex", [])[:5]; NX = len(exn)
    exp = (so.get("poses") or ["planche", "deadbug", "lateral", "climber", "creuse"])[:NX]
    exp = [q if q in POSES else "planche" for q in exp] + ["planche"] * (NX - len(exp))
    eff, rst = so.get("effort", "45 s"), so.get("rest", "15 s")
    tot = so.get("total", "5:00"); tsec = int(tot.split(":")[0]) * 60 + int(tot.split(":")[1] or 0)
    hpose = h.get("pose", "crunch") if h.get("pose", "crunch") in POSES else "crunch"
    epose = er.get("pose", hpose) if er.get("pose", hpose) in POSES else hpose
    zones = (po.get("zones") or ["AVANT", "CÔTÉS", "PROFOND"])[:3]
    badges = (po.get("badges") or ["DOS NEUTRE", "RESPIRE", "TROP DUR ? GENOUX AU SOL"])[:3]
    ctas = (ct.get("ctas") or ["🔖 ENREGISTRE LE CIRCUIT", "💬 T'AS TENU 5 MIN ?"])[:2]
    ev += [{"k": "type", "at": a0, "end": a0 + 1.5, "text": "x" * 40}, {"k": "glitch", "at": a0 + 1.55}, {"k": "impact", "at": a0 + 1.7}]
    ev += [{"k": "glitch", "at": a1 + 0.1}, {"k": "glitch", "at": a1 + 3.2}, {"k": "impact", "at": a1 + durs[1] * 0.68}]
    exs = [a2 + 1.3 + (d2 - 1.6) / max(1, NX) * j for j in range(NX)]
    ev += [{"k": "impact", "at": a2 + 0.05}] + [{"k": "pop", "at": x} for x in exs] + [{"k": "whoosh", "at": x - 0.2} for x in exs[1:]]
    ev += [{"k": "pop", "at": a3 + 0.5 + 0.8 * j} for j in range(3)] + [{"k": "pop", "at": a3 + 3.6 + 0.7 * j} for j in range(3)]
    ev += [{"k": "beep", "at": a4 + 0.2 + 0.25 * j} for j in range(5)] + [{"k": "whistle", "at": a4 + 1.5}, {"k": "impact", "at": a4 + 1.6},
            {"k": "whoosh", "at": a4 + 2.2}, {"k": "pop", "at": a4 + 2.9}, {"k": "pop", "at": a4 + 3.4}]
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    css = f"""{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;background:#0b0b0b;color:#fff;font-family:Inter,sans-serif;position:relative}}
.A{{font-family:Anton;text-transform:uppercase;letter-spacing:1px}}
.r{{color:{RED}}}
.scn{{position:absolute;inset:0;opacity:0}}
.fig{{position:absolute;left:60px;top:400px;width:960px;height:576px}}
.big{{position:absolute;left:60px;right:60px;text-align:center;font:400 130px/0.95 Anton;text-transform:uppercase}}
.tag{{position:absolute;left:60px;top:250px;padding:12px 28px;border-radius:10px;font:800 40px Inter;letter-spacing:3px}}
.cnt{{position:absolute;left:0;right:0;top:250px;text-align:center;font:400 150px Anton;color:{RED}}}
.x{{position:absolute;left:290px;top:380px;width:500px;height:500px;opacity:0}}
.timer{{position:absolute;left:0;right:0;text-align:center;font:400 120px Anton}}
.stamp{{position:absolute;left:0;right:0;top:1010px;margin:auto;width:560px;text-align:center;border:10px solid {RED};color:{RED};font:400 130px Anton;transform:rotate(-10deg);opacity:0}}
.myth{{position:absolute;left:0;right:0;top:1000px;text-align:center;font:400 72px Anton;color:#888}}
.card{{position:absolute;left:70px;right:70px;top:480px;height:640px;background:#151515;border:4px solid {RED};border-radius:28px;opacity:0}}
.card .nm{{position:absolute;left:0;right:0;bottom:40px;text-align:center;font:400 84px/1 Anton;text-transform:uppercase}}
.card .sec{{position:absolute;right:30px;top:24px;background:{RED};font:400 56px Anton;padding:4px 22px;border-radius:12px}}
.card .idx{{position:absolute;left:30px;top:16px;font:400 90px Anton;color:{RED}}}
.dots{{position:absolute;left:0;right:0;top:1150px;display:flex;justify-content:center;gap:22px}}
.dots i{{display:block;width:34px;height:34px;border-radius:50%;border:4px solid {RED}}}
.rest{{position:absolute;left:0;right:0;top:820px;height:120px;background:#fff;color:#0b0b0b;font:400 80px/120px Anton;text-align:center;opacity:0}}
.body{{position:absolute;left:390px;top:380px;width:300px;height:480px}}
.zl{{position:absolute;font:400 46px Anton;color:#fff;opacity:0}}
.badge{{position:absolute;left:0;right:0;margin:auto;width:fit-content;padding:20px 36px;background:{RED};font:400 60px Anton;border-radius:14px;opacity:0}}
.slash{{position:absolute;width:2200px;height:340px;background:{RED};transform:rotate(-14deg);left:-560px;top:1060px}}
.tick{{position:absolute;width:2300px;height:100px;background:#fff;color:#0b0b0b;font:400 54px/100px Anton;white-space:nowrap;transform:rotate(-14deg);left:-600px;top:1380px}}
.cl{{position:absolute;left:70px;font:400 76px Anton;text-transform:uppercase;opacity:0}}
.bt{{position:absolute;left:40px;right:40px;top:1330px;text-align:center;font:400 72px/1.05 Anton;text-transform:uppercase;opacity:0}}
.capw{{position:absolute;left:0;right:0;top:1500px;text-align:center}}
.cap{{display:none;background:#0b0b0b;border:4px solid {RED};padding:10px 28px;font:400 58px Anton;text-transform:uppercase;letter-spacing:1px}}
.cap .on{{color:{RED}}}
.bar{{position:absolute;left:0;top:0;height:12px;background:{RED}}}
.scanl{{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.05) 0 2px,transparent 2px 6px);opacity:0}}
.flash{{position:absolute;inset:0;background:{RED};opacity:0}}
"""
    STAND = ("squat", "fente")
    def figsvg(id_):
        st = " style='top:520px'" if (id_ == "f0" and hpose in STAND) or (id_ == "f1" and epose in STAND) else ""
        return (f"<svg class='fig'{st} id='{id_}' viewBox='-20 -40 400 240'><g id='{id_}c' transform='translate(-6,0)' opacity='0'></g><g id='{id_}m' transform='translate(6,0)' opacity='0'></g>"
                f"<g id='{id_}w'></g><line x1='-20' y1='154' x2='380' y2='154' stroke='#444' stroke-width='4'/></svg>")
    body_svg = f"""<svg class='body' viewBox='0 0 400 640'>
<circle cx='200' cy='70' r='56' fill='none' stroke='#fff' stroke-width='10'/>
<rect x='110' y='150' width='180' height='300' rx='60' fill='none' stroke='#fff' stroke-width='10'/>
<rect id='z0' x='165' y='210' width='70' height='190' rx='20' fill='{RED}' opacity='0'/>
<rect id='z1a' x='122' y='230' width='36' height='170' rx='16' fill='{RED}' opacity='0'/><rect id='z1b' x='242' y='230' width='36' height='170' rx='16' fill='{RED}' opacity='0'/>
<rect id='z2' x='130' y='330' width='140' height='90' rx='30' fill='none' stroke='{RED}' stroke-width='10' opacity='0'/>
<line x1='150' y1='450' x2='140' y2='620' stroke='#fff' stroke-width='10' stroke-linecap='round'/><line x1='250' y1='450' x2='260' y2='620' stroke='#fff' stroke-width='10' stroke-linecap='round'/></svg>"""
    page = f"""<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>
<div class='scn' id='s0'><div class='cnt A' id='cnt0'>0</div>{figsvg('f0')}
 <svg class='x' id='x0' viewBox='0 0 100 100'><path d='M12 12 L88 88 M88 12 L12 88' stroke='{RED}' stroke-width='14' stroke-linecap='round'/></svg>
 <div class='big' id='h0' style='top:1000px'>{R_(h.get("title", "STOP AUX **100 CRUNCHS**"))}</div>
 <div class='big' id='h1' style='top:1280px;font-size:90px'>{R_(h.get("sub", "⏱ 5 MIN À LA PLACE"))}</div></div>
<div class='scn' id='s1'><div class='tag' id='tg1' style='background:{RED}'>ERREUR</div><div class='timer A' id='tm1' style='top:340px;color:#999'>00:00</div>{figsvg('f1')}
 <svg style='position:absolute;left:0;top:0' width='1080' height='1920'><circle id='nk' cx='340' cy='640' r='60' fill='none' stroke='{RED}' stroke-width='10' opacity='0'/></svg>
 <div class='myth' id='my1' style='top:1060px'>{R_(er.get("myth", "« FONDRE LE VENTRE »"))}</div><div class='stamp' id='st1'>{K.esc(er.get("stamp", "MYTHE"))}</div>
 <div class='bt' id='bt1'>{R_(er.get("text", "LONG · NUQUE ·<br>**ZÉRO FONTE LOCALE**")).replace("&lt;br&gt;", "<br>")}</div></div>
<div class='scn' id='s2'><div class='tag' id='tg2' style='background:#fff;color:#0b0b0b'>SOLUTION</div><div class='timer A' id='tm2' style='top:300px;font-size:150px'>{tot}</div>
 {''.join(f"<div class='card' id='cd{j}'><div class='idx'>{j+1}</div><div class='sec'>{K.esc(eff)}</div>{figsvg('fx'+str(j)).replace('class=\'fig\'', 'class=\'fig\' style=\'left:20px;top:80px;width:800px;height:460px\'')}<div class='nm'>{H.escape(n)}</div></div>" for j, n in enumerate(exn))}
 <div class='rest' id='rest'>REPOS {K.esc(rst)}</div><div class='dots'>{''.join(f"<i id='dt{j}'></i>" for j in range(NX))}</div>
 <div class='bt' id='bt2'>{K.esc(eff)} EFFORT / <span class='r'>{K.esc(rst)} REPOS</span> × {NX}</div></div>
<div class='scn' id='s3'>{body_svg}
 <div class='zl' id='zl0' style='left:740px;top:560px'>{K.esc(zones[0])}</div><div class='zl' id='zl1' style='left:{max(40, 360 - 34 * len(zones[1]))}px;top:560px'>{K.esc(zones[1])}</div><div class='zl' id='zl2' style='left:740px;top:680px'>{K.esc(zones[2])}</div>
 <div class='badge' id='bg0' style='top:960px;font-size:54px'>{K.esc(badges[0])}</div><div class='badge' id='bg1' style='top:1090px;font-size:54px;background:#fff;color:#0b0b0b'>{K.esc(badges[1])}</div>
 <div class='badge' id='bg2' style='top:1220px;font-size:48px'>{K.esc(badges[2])}</div>
 <div class='big' id='t3' style='top:200px;font-size:84px'>{R_(po.get("title", "TOUTE LA SANGLE,<br>**PAS JUSTE LE HAUT**")).replace("&lt;br&gt;", "<br>")}</div></div>
<div class='scn' id='s4'><div class='timer A' id='tm4' style='top:260px;font-size:200px;color:{RED}'>{tot}</div><div class='slash' id='sl4'></div><div class='tick' id='tk4'>{K.esc(ct.get("ticker", "ZÉRO SALLE · ZÉRO EXCUSE")) + (" · " + K.esc(ct.get("ticker", "ZÉRO SALLE · ZÉRO EXCUSE"))) * 5}</div>
 <div class='big' id='h4' style='top:560px;font-size:150px'>{R_(ct.get("title", "ON LE FAIT<br>**CE SOIR ?**")).replace("&lt;br&gt;", "<br>")}</div>
 <div class='cl' id='c40' style='top:900px'>{K.esc(ctas[0])}</div><div class='cl' id='c41' style='top:1000px'>{K.esc(ctas[-1])}</div></div>
<div class='scanl' id='scl'></div><div class='flash' id='fl'></div>
<div class='capw'>{cap_html}</div><div class='bar' id='bar'></div>
<script>
const EV={json.dumps(ev, ensure_ascii=False)}; const D={total}; const SC={json.dumps(S, ensure_ascii=False)}; const P={json.dumps(POSES)}; const NX={NX}, EXP={json.dumps(exp)}, HP={json.dumps(hpose)}, EP={json.dumps(epose)}, CNT={int(h.get("count", 100))}, TS={tsec}, NECK={'true' if er.get('neck', epose == 'crunch') else 'false'};
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), back=x=>{{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);}};
const $=id=>document.getElementById(id);
const SEG=[['N','P'],['N','E1'],['E1','W1'],['N','E2'],['E2','W2'],['P','K1'],['K1','F1'],['P','K2'],['K2','F2']];
function fig(id,pose,k,col){{const A=P[pose][0],B=P[pose][1];const J={{}};for(const n in A)J[n]=[A[n][0]+(B[n][0]-A[n][0])*k,A[n][1]+(B[n][1]-A[n][1])*k];
  const y=v=>160-v;let s='';for(const [a,b] of SEG)s+=`<line x1='${{J[a][0]}}' y1='${{y(J[a][1])}}' x2='${{J[b][0]}}' y2='${{y(J[b][1])}}' stroke='${{col}}' stroke-width='16' stroke-linecap='round'/>`;
  s+=`<circle cx='${{J.H[0]}}' cy='${{y(J.H[1])}}' r='24' fill='${{col}}'/>`;return s;}}
function drawFig(id,pose,k,glitch,neck=0){{$(id+'w').innerHTML=fig(id,pose,k,'#fff')+(neck?`<circle cx='${{(P[pose][0].N[0]+(P[pose][1].N[0]-P[pose][0].N[0])*k)}}' cy='${{160-(P[pose][0].N[1]+(P[pose][1].N[1]-P[pose][0].N[1])*k)}}' r='34' fill='none' stroke='#ff2d36' stroke-width='8' opacity='${{neck}}'/>`:'');
  $(id+'c').innerHTML=glitch?fig(id,pose,k,'#00e5ff'):'';$(id+'m').innerHTML=glitch?fig(id,pose,k,'#ff2d36'):'';
  $(id+'c').setAttribute('opacity',glitch?.8:0);$(id+'m').setAttribute('opacity',glitch?.8:0);
  $(id+'c').setAttribute('transform',`translate(${{glitch?-10:0}},${{glitch?3:0}})`);$(id+'m').setAttribute('transform',`translate(${{glitch?10:0}},${{glitch?-3:0}})`);}}
function slam(el,t0,u,from=2){{const k=back((u-t0)/.3);el.style.opacity=u>=t0?1:0;el.style.transform=`scale(${{from-(from-1)*k}})`;}}
function rise(el,t0,u){{const k=back((u-t0)/.35);el.style.opacity=u>=t0?c((u-t0)/.1):0;el.style.transform=`translateY(${{(1-k)*80}}px)`;}}
function gl(el,on,u){{if(!el)return;el.style.textShadow=on?`${{-6+Math.sin(u*90)*4}}px 0 #00e5ff, ${{6}}px 0 #ff2d36`:'none';el.style.transform=(el.style.transform||'')+(on?` translateX(${{Math.sin(u*130)*10}}px)`:'');}}
window.render=function(t){{
 $('bar').style.width=(c(t/D)*1080)+'px';
 let k=0;for(let i=0;i<SC.length;i++)if(t>=SC[i].a)k=i;const s=SC[k],u=t-s.a,d=s.b-s.a;
 for(let i=0;i<SC.length;i++)$('s'+i).style.opacity=i==k?1:0;
 const cut=u<.12&&k>0;$('scl').style.opacity=(k==1)?.9:(cut?.6:0);
 $('fl').style.opacity=0;document.body.style.filter='none';
 if(k==0){{const n=Math.min(CNT,Math.floor(Math.pow(c(u/1.5),1.6)*CNT));$('cnt0').textContent=n;
   const g=u>1.5&&u<1.85;drawFig('f0',HP,.5+.5*Math.sin(u*(6+u*10)),g);$('f0').style.transform=g?`translateX(${{Math.sin(u*120)*16}}px)`:'none';
   slam($('x0'),1.7,u,2.4);$('h0').style.opacity=1;gl($('h0'),g,u);rise($('h1'),2.2,u);
   if(g)$('fl').style.opacity=.15;}}
 if(k==1){{document.body.style.filter='grayscale(1) contrast(1.1)';$('tg1').style.opacity=Math.floor(u*3)%2?1:.3;$('tg1').style.filter='none';
   const sec=Math.floor(u*9);$('tm1').textContent=String(Math.floor(sec/60)).padStart(2,'0')+':'+String(sec%60).padStart(2,'0');
   const g=(u>.1&&u<.35)||(u>3.2&&u<3.45);drawFig('f1',EP,.5+.5*Math.sin(u*2.4),g,(NECK&&u>2.2)?(.5+.5*Math.sin(u*8)):0);
   
   const ms=d*.68;$('my1').style.opacity=u>ms-.8?1:0;slam($('st1'),ms,u,2.6);rise($('bt1'),1.0,u);}}
 if(k==2){{const T0=1.3,step=(d-1.6)/NX;slam($('tg2'),0,u,1.6);const rem=Math.max(0,TS-Math.floor(c((u-T0)/(d-T0))*15));$('tm2').textContent=Math.floor(rem/60)+':'+String(rem%60).padStart(2,'0');
   let cur=-1;for(let j=0;j<NX;j++)if(u>=T0+step*j)cur=j;
   for(let j=0;j<NX;j++){{const cd=$('cd'+j);const on=j==cur;const kk=back((u-T0-step*j)/.3);cd.style.opacity=on?1:0;cd.style.transform=`translateX(${{(1-kk)*700}}px) rotate(${{(1-kk)*6}}deg)`;
     const pose=EXP[j];const sp=pose=='climber'?5:2.2;drawFig('fx'+j,pose,.5+.5*Math.sin(u*sp),false);
     $('dt'+j).style.background=j<=cur?'{RED}':'transparent';}}
   const r=$('rest');let ro=0;for(let j=1;j<NX;j++){{const x=u-(T0+step*j);if(x>-.35&&x<0)ro=1;}}r.style.opacity=ro;r.style.transform=`translateX(${{ro?0:-1200}}px)`;
   rise($('bt2'),.6,u);}}
 if(k==3){{rise($('t3'),.0,u);const zs=[['z0'],['z1a','z1b'],['z2']];
   for(let j=0;j<3;j++){{const on=u>=.5+.8*j;for(const id of zs[j])$(id).setAttribute('opacity',on?(.55+.35*Math.sin(u*5+j)):0);$('zl'+j).style.opacity=on?1:0;}}
   for(let j=0;j<3;j++){{const b=$('bg'+j);const kk=back((u-3.6-.7*j)/.45);b.style.opacity=u>=3.6+.7*j?1:0;b.style.transform=`translateY(${{(1-kk)*-300}}px) rotate(${{(j-1)*3}}deg)`;}}}}
 if(k==4){{const rem=Math.max(0,TS-Math.floor(c((u-.1)/1.4)*TS));$('tm4').textContent=Math.floor(rem/60)+':'+String(rem%60).padStart(2,'0');
   $('tm4').style.opacity=u<1.6?1:0;if(u>1.5&&u<1.75)$('fl').style.opacity=.8*(1-(u-1.5)/.25);
   slam($('h4'),1.6,u,2.2);const ks=eo((u-2.2)/.35);$('sl4').style.transform=`rotate(-14deg) translateX(${{(1-ks)*-2400}}px)`;
   $('tk4').style.transform=`rotate(-14deg) translateX(${{(1-ks)*2400-((u*160)%600)}}px)`;slam($('c40'),2.9,u,1.8);slam($('c41'),3.4,u,1.8);}}
 for(const cp of document.querySelectorAll('.cap')){{const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}}
}};render(0);
</script></body></html>"""
    return page

# ------------------------------------------------------------------ layout « nightchat » (coeurlucide, POV iOS de nuit)
def nightchat_page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]; ev = []; PINK = "#f4b6c6"; BOR = "#7a1f35"
    S = [{"a": starts[k], "b": starts[k] + durs[k], "ty": s["type"]} for k, s in enumerate(sc)]
    blocks = []
    def B(k, j, txt, extra=""):
        return f"<div class='b' id='b{k}_{j}' {extra}>{H.escape(txt)}</div>"
    for k, s in enumerate(sc):
        a = starts[k]; ty = s["type"]; inner = ""
        if ty == "lock":
            ev += [{"k": "notif", "at": a + 0.05}, {"k": "click", "at": a + 3.0}, {"k": "whoosh", "at": a + 3.3}]
            continue
        if ty == "msgs":
            inner = f"<div class='typ' id='ty{k}_0'><i></i><i></i><i></i></div>{B(k,0,s['bubbles'][0])}<div class='typ' id='ty{k}_1'><i></i><i></i><i></i></div>{B(k,1,s['bubbles'][1])}"
            inner += f"<div class='ghost' id='gh{k}'><div class='gb'>{H.escape(s.get('sent', 'Tu es dispo ?'))}</div><div class='gv'>{H.escape(s['ghost'])}</div></div>"
            ev += [{"k": "pop", "at": a + 1.0}, {"k": "pop", "at": a + 4.2}]
        elif ty == "msgs2":
            for j, t in enumerate(s["bubbles"]):
                inner += f"<div class='typ' id='ty{k}_{j}'><i></i><i></i><i></i></div>{B(k,j,t)}"
            inner += f"<svg class='hs' id='hs{k}' viewBox='0 0 100 92'><path id='hp{k}' d='M50 86 C 14 60 2 40 12 22 C 22 4 44 8 50 26 C 56 8 78 4 88 22 C 98 40 86 60 50 86 Z' fill='none' stroke='{PINK}' stroke-width='6' stroke-linecap='round'/></svg>"
            ev += [{"k": "pop", "at": a + 0.9}, {"k": "pop", "at": a + 3.2}, {"k": "sparkle", "at": a + 3.7}, {"k": "pop", "at": a + 5.5}]
        elif ty == "check":
            items = "".join(f"<div class='ci' id='ci{k}_{j}'><span class='bx' id='bx{k}_{j}'>☐</span> {H.escape(x)}</div>" for j, x in enumerate(s["items"]))
            inner = f"<div class='typ' id='ty{k}_0'><i></i><i></i><i></i></div>{B(k,0,s['title'])}<div class='b chk' id='b{k}_1'>{items}</div>"
            ev += [{"k": "pop", "at": a + 0.8}, {"k": "pop", "at": a + 1.6}] + [{"k": "click", "at": a + t} for t in (2.4, 3.6, 5.4)]
        elif ty == "cta":
            inner = (f"<div class='typ' id='ty{k}_0'><i></i><i></i><i></i></div><div class='b big' id='b{k}_0'>{H.escape(s['last'])}</div>"
                     f"<div class='react' id='rc{k}'><span>❤️</span><span>👍</span><span>😂</span><span>😮</span><span>😢</span><span>🙏</span></div>")
            ev += [{"k": "pop", "at": a + 0.6}, {"k": "pop", "at": a + 1.8}, {"k": "sparkle", "at": a + 2.4}, {"k": "whoosh", "at": a + 3.5}, {"k": "click", "at": a + 4.0}, {"k": "click", "at": a + 4.6}]
        blocks.append(f"<div class='chat' id='c{k}'>{inner}</div>")
    cta = sc[-1]
    hearts = "".join(f"<b class='ht' id='ht{j}'>❤️</b>" for j in range(14))
    share = (f"<div class='share' id='share'><div class='sh'></div>"
             + "".join(f"<div class='sr' id='sr{j}'>{H.escape(x)}</div>" for j, x in enumerate(cta["ctas"])) + "</div>")
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    css = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;background:#1e0d14;color:#fbe9ee;font-family:Inter,sans-serif;position:relative}}
.halo{{position:absolute;width:1200px;height:1200px;border-radius:50%;left:-60px;top:300px;background:radial-gradient(circle,rgba(176,70,94,.35),transparent 62%)}}
.stat{{position:absolute;left:70px;right:70px;top:40px;display:flex;justify-content:space-between;font:700 34px Inter;color:#fbe9ee}}
.lock{{position:absolute;inset:0}}
.ltime{{position:absolute;left:0;right:0;top:250px;text-align:center;font:200 230px/1 Inter;letter-spacing:-6px}}
.ldate{{position:absolute;left:0;right:0;top:220px;text-align:center;font:600 40px Inter;color:#e9c3ce}}
.notif{{position:absolute;left:50px;right:50px;top:620px;border-radius:44px;background:rgba(255,255,255,.14);backdrop-filter:blur(10px);padding:34px 40px;display:flex;gap:28px;align-items:flex-start}}
.nav{{flex:none;width:96px;height:96px;border-radius:24px;background:{BOR};color:#fff;font:800 54px/96px Georgia,serif;text-align:center}}
.nt{{font:800 38px Inter}} .nt span{{float:right;font:500 30px Inter;color:#d9b3bf}} .nb{{font:500 42px/1.3 Inter;margin-top:8px}}
.tap{{position:absolute;width:120px;height:120px;border-radius:50%;background:rgba(255,255,255,.35);left:480px;top:690px;opacity:0}}
.hdr{{position:absolute;left:0;right:0;top:110px;height:170px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;border-bottom:2px solid rgba(255,255,255,.08);opacity:0}}
.hav{{width:96px;height:96px;border-radius:50%;background:{BOR};color:#fff;font:800 52px/96px Georgia,serif;text-align:center}}
.hn{{font:700 34px Inter}} .hs2{{font:500 26px Inter;color:#d9b3bf}}
.chat{{position:absolute;left:46px;right:46px;top:320px;display:flex;flex-direction:column;gap:22px;opacity:0;z-index:3}}
.b{{align-self:flex-start;max-width:880px;background:#3a1a26;border-radius:46px;border-bottom-left-radius:12px;padding:30px 40px;font:500 50px/1.32 Inter;display:none;transform-origin:left bottom}}
.b.big{{font:700 84px/1.2 Inter;background:{BOR};color:#fff;margin-top:230px}}
.chk{{font:600 48px/1.5 Inter}} .bx{{display:inline-block;color:{PINK};width:66px}}
.typ{{align-self:flex-start;background:#3a1a26;border-radius:40px;padding:26px 34px;display:none;gap:12px}}
.typ i{{display:inline-block;width:18px;height:18px;border-radius:50%;background:#d9b3bf;margin:0 5px}}
.ghost{{position:absolute;right:0;top:330px;opacity:0;filter:blur(3px)}}
.gb{{background:#2c6bff;color:#fff;border-radius:40px;border-bottom-right-radius:12px;padding:24px 34px;font:500 42px Inter}} .gv{{text-align:right;font:500 28px Inter;color:#b98a98;margin-top:8px}}
.hs{{position:absolute;width:120px;height:110px;opacity:0}}
.react{{position:absolute;left:0;top:40px;background:#3a1a26;border-radius:60px;padding:16px 26px;display:flex;gap:20px;font-size:62px;opacity:0;box-shadow:0 10px 40px rgba(0,0,0,.5)}}
.react span:first-child{{border-radius:50%;padding:4px}}
.ht{{position:absolute;font-size:70px;opacity:0}}
.inp{{position:absolute;left:46px;right:46px;top:1390px;height:96px;border-radius:48px;border:2px solid rgba(255,255,255,.2);font:500 36px/92px Inter;color:#b98a98;padding-left:40px;opacity:0}}
.share{{position:absolute;left:0;right:0;top:1920px;height:520px;background:#2a1520;border-radius:48px 48px 0 0;padding:34px 46px;box-shadow:0 -10px 50px rgba(0,0,0,.5)}}
.sh{{width:120px;height:10px;border-radius:5px;background:#5a3a46;margin:0 auto 30px}}
.sr{{padding:28px 30px;border-radius:26px;font:700 46px Inter;margin-bottom:18px;background:#3a1a26}}
.dim{{position:absolute;inset:0;background:#000;opacity:0;z-index:2}}
.capw{{position:absolute;left:0;right:0;top:1560px;text-align:center}}
.cap{{display:none;background:rgba(30,13,20,.85);border:2px solid rgba(244,182,198,.45);border-radius:24px;padding:14px 30px;font:700 46px Inter}}
.cap .on{{color:{PINK}}}
.bar{{position:absolute;left:0;top:0;height:8px;background:{PINK}}}
"""
    page = f"""<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>
<div class='halo' id='halo'></div>
<div class='stat'><span id='clk'>23:47</span><span>●●● 🔋</span></div>
<div class='lock' id='lock'><div class='ldate'>Ce soir</div><div class='ltime'>23:47</div>
 <div class='notif' id='notif'><div class='nav'>C</div><div style='flex:1'><div class='nt'>Cœur Lucide <span>maintenant</span></div><div class='nb'>{H.escape(sc[0]['notif'])}</div></div></div>
 <div class='tap' id='tap'></div></div>
<div class='hdr' id='hdr'><div class='hav'>C</div><div class='hn'>Cœur Lucide</div><div class='hs2' id='hst'>en ligne</div></div>
{''.join(blocks)}
<div class='inp' id='inp'>iMessage</div><div class='dim' id='dim'></div>{hearts}{share}
<div class='capw'>{cap_html}</div><div class='bar' id='bar'></div>
<script>
const EV={json.dumps(ev, ensure_ascii=False)}; const D={total}; const SC={json.dumps(S)};
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), back=x=>{{x=c(x);const s=1.5;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);}};
const $=id=>document.getElementById(id);
function bub(id,t0,u){{const e=$(id);if(!e)return;e.style.display=u>=t0?'block':'none';const k=back((u-t0)/.4);e.style.transform=`scale(${{.6+.4*k}})`;e.style.opacity=c((u-t0)/.12);}}
function typ(id,t0,t1,u){{const e=$(id);if(!e)return false;const on=u>=t0&&u<t1;e.style.display=on?'flex':'none';
  if(on)[...e.querySelectorAll('i')].forEach((d,n)=>d.style.transform=`translateY(${{-Math.max(0,Math.sin((u-t0)*8-n*.9))*12}}px)`);return on;}}
window.render=function(t){{
 $('bar').style.width=(c(t/D)*1080)+'px';
 let k=0;for(let i=0;i<SC.length;i++)if(t>=SC[i].a)k=i;const s=SC[k],u=t-s.a,d=s.b-s.a;
 $('halo').style.transform=`scale(${{1+.06*Math.sin(t*1.2)}})`;$('halo').style.opacity=k==2&&u>3.2?1:.8;
 $('clk').textContent=t<20?'23:47':'23:48';
 // lock
 const L=$('lock');const op=k==0?1-eo((u-3.3)/.4):0;L.style.opacity=op;L.style.transform=`scale(${{k==0?1+.15*eo((u-3.3)/.4):1}})`;
 const nk=k==0?(u<.05?1:back(u/.5)):1;$('notif').style.transform=`translateY(${{(1-nk)*-200}}px) scale(${{k==0?1+.04*Math.sin(Math.min(u,3)*3):1}})`;
 const tp=$('tap');tp.style.opacity=k==0&&u>2.9&&u<3.35?.8:0;tp.style.transform=`scale(${{.6+.6*c((u-2.9)/.3)}})`;
 const inchat=k>0||u>3.4;$('hdr').style.opacity=inchat?eo(k>0?1:(u-3.4)/.4):0;$('inp').style.opacity=inchat&&k<4?1:(k==4?1-eo((u-3.4)/.3):0);
 let typing=false;
 SC.forEach((x,i)=>{{const el=$('c'+i);if(!el)return;const on=i==k;const out=i==k-1&&u<.4;el.style.opacity=on?1:(out?1-eo(u/.4):0);
   el.style.transform=`translateY(${{on?0:(out?-eo(u/.4)*300:0)}}px)`;}});
 const ty=s.ty;
 if(ty==='msgs'){{typing=typ('ty1_0',.2,1.0,u)||typ('ty1_1',3.4,4.2,u);bub('b1_0',1.0,u);bub('b1_1',4.2,u);
   const g=$('gh1');g.style.opacity=u>1.6&&u<3.4?(u<3.0?.75:.75*(1-(u-3.0)/.4)):0;g.style.filter=`blur(${{3+8*c((u-2.8)/.6)}}px)`;g.style.transform=`translateY(${{-c((u-2.8)/.6)*60}}px)`;}}
 if(ty==='msgs2'){{typing=typ('ty2_0',.2,.9,u)||typ('ty2_1',2.6,3.2,u)||typ('ty2_2',4.8,5.5,u);bub('b2_0',.9,u);bub('b2_1',3.2,u);bub('b2_2',5.5,u);
   const hs=$('hs2'),b=$('b2_1');if(hs&&u>=3.6){{hs.style.opacity=1;hs.style.left=(b.offsetLeft+b.offsetWidth+20)+'px';hs.style.top=(b.offsetTop+b.offsetHeight/2-55)+'px';
     const p=$('hp2'),Lp=p.getTotalLength();p.style.strokeDasharray=Lp;p.style.strokeDashoffset=Lp*(1-eo((u-3.6)/.8));p.setAttribute('fill',u>4.4?'rgba(244,182,198,.9)':'none');
     hs.style.transform=`scale(${{u>4.4?1+.15*Math.max(0,Math.sin((u-4.4)*6))*(u<5?1:0):1}})`;}}else if(hs)hs.style.opacity=0;}}
 if(ty==='check'){{typing=typ('ty3_0',.2,.8,u);bub('b3_0',.8,u);bub('b3_1',1.6,u);
   [2.4,3.6,5.4].forEach((tt,j)=>{{const bx=$('bx3_'+j);bx.textContent=u>=tt?'☑':'☐';bx.style.transform=`scale(${{u>=tt?1+.5*(1-eo((u-tt)/.3)):1}})`;$('ci3_'+j).style.opacity=u>=tt?1:.6;}});
   const br=u>3.6&&u<5.3?1+.06*Math.sin((u-3.6)/1.7*Math.PI):1;const bb=$('b3_1');if(u>=2)bb.style.transform=`scale(${{br}})`;}}
 if(ty==='cta'){{typing=typ('ty4_0',.1,.6,u);bub('b4_0',.6,u);const bb=$('b4_0');
   const lp=u>1.6&&u<3.5;$('dim').style.opacity=lp?.5:(u>=3.5?.4:0);$('c4').style.zIndex=4;if(u>1.6)bb.style.transform=`scale(${{1.05}})`;bb.style.position='relative';bb.style.zIndex=5;
   const rc=$('rc4');rc.style.opacity=u>1.8&&u<3.4?1:0;rc.style.transform=`scale(${{.5+.5*back((u-1.8)/.35)}})`;rc.style.zIndex=6;
   rc.firstChild.style.background=u>2.4?'rgba(244,182,198,.35)':'none';
   for(let j=0;j<14;j++){{const h=$('ht'+j);const v=u-2.45-j*.06;if(v<0||v>1.6){{h.style.opacity=0;continue;}}
     h.style.opacity=1-v/1.6;h.style.left=(140+((j*137)%800))+'px';h.style.top=(700-v*500-(j%3)*60)+'px';h.style.transform=`scale(${{.6+.6*Math.sin(v*3)}}) rotate(${{(j%2?-1:1)*v*40}}deg)`;h.style.zIndex=7;}}
   const sh=$('share');sh.style.top=(1920-eo((u-3.5)/.45)*560)+'px';sh.style.zIndex=8;
   [4.0,4.6].forEach((tt,j)=>{{$('sr'+j).style.background=u>=tt?'#7a1f35':'#3a1a26';$('sr'+j).style.transform=`scale(${{u>=tt?1+.04*(1-eo((u-tt)/.3)):1}})`;}});}}
 $('hst').textContent=typing?'en train d’écrire…':'en ligne';
 for(const cp of document.querySelectorAll('.cap')){{const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}}
}};render(0);
</script></body></html>"""
    return page

# ------------------------------------------------------------------ layout « notion » (revenus_malin)
NOTION_TPL = r"""<!doctype html><html><head><meta charset='utf-8'><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:#123d2e;color:#37352f;font-family:Inter,sans-serif;position:relative}
.page{position:absolute;left:44px;right:44px;top:200px;height:1240px;background:#fbf8f1;border-radius:22px;box-shadow:0 30px 70px rgba(0,0,0,.35);overflow:hidden}
.crumb{position:absolute;left:50px;top:30px;font:500 32px Inter;color:#9b9a97}
.blk{position:absolute;left:60px;right:60px;top:110px;opacity:0}
h1{font:800 100px/1.1 Inter;color:#1f1e1b;margin-top:20px}
.ico{font-size:150px;line-height:1}
.mk{background:linear-gradient(90deg,#ffe58f 0,#ffe58f 100%) no-repeat 0 85%;background-size:0% 45%;padding:0 4px}
.call{margin-top:44px;display:flex;gap:26px;background:#f1efe9;border-radius:18px;padding:34px 38px;font:600 50px/1.35 Inter;opacity:0}
.call .ci{font-size:48px}
.strike{position:relative;display:inline-block;margin-top:44px;font:500 56px Inter;color:#9b9a97;opacity:0}
.strike i{position:absolute;left:0;top:52%;height:5px;background:#e03e3e;width:0}
.row{display:flex;gap:26px;align-items:flex-start;font:800 60px/1.25 Inter;color:#1f1e1b;margin-top:44px;opacity:0}
.cb{flex:none;width:64px;height:64px;border:4px solid #37352f;border-radius:8px;margin-top:4px;display:flex;align-items:center;justify-content:center;font:900 38px Inter;color:#fff}
.cb.on{background:#2383e2;border-color:#2383e2}
.sub{font:600 48px/1.4 Inter;color:#55534e;margin:18px 0 0 90px;opacity:0}
.tags{display:flex;flex-wrap:wrap;gap:18px;margin:30px 0 0 90px}
.tag{padding:14px 28px;border-radius:12px;font:700 50px Inter;opacity:0}
.quote{margin:34px 0 0 90px;border-left:8px solid #37352f;padding:8px 0 8px 32px;font:700 62px/1.3 Inter;opacity:0}
.li{display:flex;gap:24px;align-items:center;margin:34px 0 0 70px;padding:24px 28px;border-radius:16px;font:700 56px Inter;opacity:0}
.cur{position:absolute;width:70px;height:70px;opacity:0}
.prog{margin:40px 0 0 0;opacity:0}
.pl{display:flex;justify-content:space-between;font:800 54px Inter}
.pbar{margin-top:20px;height:64px;border-radius:12px;background:#ebe9e3;display:flex;gap:6px;padding:6px}
.pbar i{flex:1;border-radius:8px;background:transparent}
.plus{position:absolute;font:800 60px Inter;color:#0f7b6c;opacity:0}
.big{font:800 130px/1.05 Inter;color:#1f1e1b}
.capw{position:absolute;left:0;right:0;top:1505px;text-align:center}
.cap{display:none;background:#fbf8f1;color:#1f1e1b;border-radius:16px;padding:12px 28px;font:800 46px Inter}
.cap .on{background:#ffe58f}
.bar{position:absolute;left:0;top:0;height:10px;background:#e9c46a}
.hd{position:absolute;left:44px;right:44px;top:120px;display:flex;justify-content:space-between;color:#e9c46a;font:700 30px 'JetBrains Mono'}
</style></head><body>
<div class='hd'><span>@__HANDLE__</span><span id='pct'>0/5</span></div>
<div class='page'><div class='crumb'>📄 __CRUMB__</div>
<div class='blk' id='k0'><div class='ico'>__H_ICO__</div><h1>__H_TITLE__</h1>
 <div class='strike' id='st0'>__H_STRIKE__<i id='sti'></i></div>
 <div class='call' id='cl0'><span class='ci'>⚠️</span><span>__H_CALL__</span></div></div>
<div class='blk' id='k1'>
 <div class='row' id='r10'><div class='cb' id='cb1'></div><div>__S1__</div></div>
 <div class='tags'>__TAGS__</div>
 <div class='row' id='r11'><div class='cb' id='cb2'></div><div>__S2__</div></div>
 <div class='quote' id='q1'>__QUOTE__</div></div>
<div class='blk' id='k2'>
 <div class='row' id='r20'><div class='cb' id='cb3'></div><div>__S3__</div></div>
 __ITEMS__
 <svg class='cur' id='mouse' viewBox='0 0 24 24'><path d='M3 2 L3 20 L8 15 L11 22 L14 21 L11 14 L18 14 Z' fill='#111' stroke='#fff' stroke-width='1.2'/></svg></div>
<div class='blk' id='k3'>
 <div class='row' id='r30'><div class='cb' id='cb4'></div><div>__S4__</div></div>
 <div class='prog' id='pg'><div class='pl'><span>🎯 __PG_LABEL__</span><span id='eur'>0</span></div><div class='pbar'>__SEGS__</div><div class='sub' style='opacity:1;margin-left:0'>__PG_NOTE__</div></div>
 <div class='row' id='r31'><div class='cb' id='cb5'></div><div>__S5__</div></div>
 <div class='call' id='cl3'><span class='ci'>🔗</span><span>__CALL3__</span></div></div>
<div class='blk' id='k4'><div class='ico'>✅</div><div class='big' style='margin-top:20px'>__C_TITLE__</div>
 <div class='call' id='c40' style='margin-top:60px'><span class='ci'>🔖</span><span>__C0__</span></div>
 <div class='call' id='c41'><span class='ci'>💬</span><span>__C1__</span></div></div>
<div class='plus' id='plus'>__PLUS__</div>
</div>
<div class='capw'>__CAPS__</div><div class='bar' id='bar'></div>
<script>
const EV=__EV__; const D=__D__; const SC=__SC__; const PG=__PG__;
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), back=x=>{x=c(x);const s=1.6;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const $=id=>document.getElementById(id);
function inn(id,t0,u,dy=30){const e=$(id);if(!e)return;const k=eo((u-t0)/.35);e.style.opacity=u>=t0?k:0;e.style.transform=`translateY(${(1-k)*dy}px)`;}
function pop(id,t0,u){const e=$(id);if(!e)return;const k=back((u-t0)/.35);e.style.opacity=u>=t0?c((u-t0)/.1):0;e.style.transform=`scale(${.5+.5*k})`;}
function mark(id,t0,u){const e=$(id);if(e)e.style.backgroundSize=`${eo((u-t0)/.5)*100}% 45%`;}
function chk(id,on){const e=$(id);if(!e)return;e.className='cb'+(on?' on':'');e.textContent=on?'✓':'';}
window.render=function(t){
 $('bar').style.width=(c(t/D)*1080)+'px';
 let k=0;for(let i=0;i<SC.length;i++)if(t>=SC[i].a)k=i;const u=t-SC[k].a,d=SC[k].b-SC[k].a;
 for(let i=0;i<5;i++){const e=$('k'+i);const on=i==k;const out=i==k-1&&u<.35;e.style.opacity=on?eo(k==0?1:u/.35):(out?1-eo(u/.35):0);
   e.style.transform=`translateX(${on?(1-eo(k==0?1:u/.35))*120:(out?-eo(u/.35)*120:0)}px)`;}
 const done=[0,0,2,3,5][k]+((k==1&&u>d-.6)?2:0)+((k==2&&u>d-.6)?1:0)+((k==3&&u>d-.6)?2:0);$('pct').textContent=Math.min(5,done)+'/5';
 if(k==0){mark('mk0',.3,u);inn('st0',1.0,u);$('sti').style.width=(eo((u-1.5)/.4)*100)+'%';inn('cl0',2.3,u);}
 if(k==1){inn('r10',.2,u);[0,1,2,3].forEach(j=>pop('tg'+j,2.0+.35*j,u));chk('cb1',u>4.2);inn('r11',4.4,u);inn('q1',5.4,u);mark('mk1',6.6,u);chk('cb2',u>d-.6);}
 if(k==2){inn('r20',.2,u);const T=[1.6,2.6,3.6];T.forEach((x,j)=>inn('l'+j,x,u,0));
   const m=$('mouse');let tg=-1;T.forEach((x,j)=>{if(u>=x+.3)tg=j;});m.style.opacity=u>1.4?1:0;
   T.forEach((x,j)=>$('l'+j).style.background=(tg==j)?'#efe9d8':'transparent');
   if(tg>=0){const L=$('l'+tg);m.style.left=(L.offsetLeft+L.offsetWidth-60)+'px';m.style.top=(L.offsetTop+30)+'px';}chk('cb3',u>d-.6);}
 if(k==3){inn('r30',.2,u);inn('pg',1.2,u);let n=0;for(let j=0;j<PG.n;j++){const on=u>=2.0+.42*j;$('sg'+j).style.background=on?'#0f7b6c':'transparent';if(on)n=j+1;}
   $('eur').textContent=PG.pre+(n*PG.v)+PG.suf;const p=$('plus');const lt=2.0+.42*(n-1);p.style.opacity=n>0&&u-lt<.4?1-(u-lt)/.4:0;p.style.left=(150+n*110)+'px';p.style.top=(700-(u-lt)*140)+'px';
   chk('cb4',u>5.2);inn('r31',5.4,u);inn('cl3',6.4,u);chk('cb5',u>d-.6);}
 if(k==4){mark('mk4',.4,u);inn('c40',1.2,u);inn('c41',1.8,u);}
 for(const cp of document.querySelectorAll('.cap')){const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}
};render(0);
</script></body></html>"""

def notion_page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]; a = starts
    S = [{"a": starts[k], "b": starts[k] + durs[k]} for k in range(len(sc))]
    ev = [{"k": "type", "at": a[0], "end": a[0] + .3, "text": "x" * 6}, {"k": "whoosh", "at": a[0] + .3}, {"k": "click", "at": a[0] + 1.5}, {"k": "pop", "at": a[0] + 2.3}]
    ev += [{"k": "pop", "at": a[1] + 2.0 + .35 * j} for j in range(4)] + [{"k": "click", "at": a[1] + 4.2}, {"k": "whoosh", "at": a[1] + 6.6}]
    ev += [{"k": "click", "at": a[2] + x + .3} for x in (1.6, 2.6, 3.6)]
    NP = int(sc[3].get("progress", {}).get("n", 7))
    ev += [{"k": "sparkle" if j == NP - 1 else "pop", "at": a[3] + 2.0 + .42 * j} for j in range(NP)] + [{"k": "click", "at": a[3] + 5.2}]
    ev += [{"k": "whoosh", "at": a[4] + .4}, {"k": "pop", "at": a[4] + 1.2}, {"k": "pop", "at": a[4] + 1.8}]
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    h, s12, s3, s45, ct = sc
    def mk(txt, mark, id_):
        txt = txt.replace(" €", "\u00a0€"); mark = (mark or "").replace(" €", "\u00a0€")
        e = K.esc(txt)
        if mark and K.esc(mark) in e:
            e = e.replace(K.esc(mark), f"<span class='mk' id='{id_}'>{K.esc(mark)}</span>", 1)
        else:
            e += f"<span class='mk' id='{id_}'></span>"
        return e
    TAGC = [("#e3f0e8", "#1c6b3a"), ("#e8ecf8", "#2b4fa8"), ("#fbe9f1", "#a3326b"), ("#fdf1dd", "#9a5b00")]
    tg = s12.get("tags", [])[:4]
    tags = "".join(f"<span class='tag' id='tg{q}' style='background:{TAGC[q][0]};color:{TAGC[q][1]}'>{K.esc(x)}</span>" for q, x in enumerate(tg))
    tags += "".join(f"<span id='tg{q}'></span>" for q in range(len(tg), 4))
    its = ((s3.get("items") or []) + ["", "", ""])[:3]
    items = "".join(f"<div class='li' id='l{q}'>{K.esc(x)}</div>" for q, x in enumerate(its))
    pg = s45.get("progress", {}); PG = {"n": int(pg.get("n", 7)), "v": pg.get("step", 15), "pre": pg.get("prefix", ""), "suf": pg.get("suffix", "\u00a0€")}
    st = s12.get("steps", []) + s3.get("steps", []) + s45.get("steps", [])
    ctas = ct.get("ctas", ["Enregistre la méthode", "Une question ? Commente"])
    R = {"__CRUMB__": K.esc(spec.get("crumb", spec.get("titre", "Méthode"))), "__H_ICO__": h.get("icon", "📌"), "__H_TITLE__": mk(h.get("title", ""), h.get("mark", ""), "mk0"),
         "__H_STRIKE__": K.esc(h.get("strike", "")), "__H_CALL__": K.esc(h.get("callout", "")), "__TAGS__": tags, "__QUOTE__": mk(s12.get("quote", ""), s12.get("quote_mark", ""), "mk1"),
         "__ITEMS__": items, "__PG_LABEL__": K.esc(pg.get("label", "")), "__PG_NOTE__": K.esc(pg.get("note", "")), "__CALL3__": K.esc(s45.get("callout", "")),
         "__C_TITLE__": mk(ct.get("title", "Méthode complète."), ct.get("mark", ""), "mk4"), "__C0__": K.esc(ctas[0]), "__C1__": K.esc(ctas[-1]),
         "__PLUS__": "+" + K.esc(PG["pre"] + str(PG["v"]) + PG["suf"])}
    for q in range(5):
        R[f"__S{q+1}__"] = K.esc(st[q]) if q < len(st) else ""
    page = NOTION_TPL
    for kk, v in R.items():
        page = page.replace(kk, v)
    page = page.replace("__EV__", json.dumps(ev)).replace("__D__", str(total)).replace("__SC__", json.dumps(S)).replace("__PG__", json.dumps(PG, ensure_ascii=False))
    page = page.replace("__CAPS__", cap_html).replace("__HANDLE__", H.escape(spec.get("handle", ""))).replace("__SEGS__", "".join(f"<i id='sg{j}'></i>" for j in range(PG["n"])))
    return page.replace("<style>", "<style>" + K._font_faces(["JetBrains Mono"]), 1)

MANIF3D_TPL = r"""<!doctype html><html><head><meta charset='utf-8'><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:#0a0a0a;color:#fff;font-family:Inter,sans-serif;position:relative}
canvas{position:absolute;left:0;top:0;filter:grayscale(.85) contrast(1.08);opacity:0}
.hd{position:absolute;left:44px;right:44px;top:120px;display:flex;justify-content:space-between;font:700 30px 'JetBrains Mono';color:#9a9a9a;z-index:5}
.hd b{color:#fff}
.bar{position:absolute;left:0;top:0;height:10px;background:#fff;z-index:5}
.blk{position:absolute;left:0;right:0;top:0;bottom:0;opacity:0}
.n30{position:absolute;left:0;right:0;top:330px;text-align:center;font:400 560px/1 'Archivo Black';letter-spacing:-20px}
.jours{position:absolute;left:0;right:0;top:880px;text-align:center;font:400 190px/1 'Archivo Black';letter-spacing:6px}
.inv{display:inline-block;background:#fff;color:#0a0a0a;padding:6px 22px}
.l1{position:absolute;left:70px;right:70px;top:1130px;text-align:center;font:400 66px/1.25 'Archivo Black';text-transform:uppercase}
.l2{position:absolute;left:0;right:0;top:1470px;text-align:center;font:700 46px 'JetBrains Mono';color:#aaa}
.lab{position:absolute;left:44px;font:400 50px 'Archivo Black';z-index:3}
.lab.a{background:#0a0a0a;color:#fff;border:3px solid #fff;padding:6px 18px}
.lab.b{background:#fff;color:#0a0a0a;padding:9px 21px}
.notif{position:absolute;right:44px;background:rgba(245,245,245,.94);color:#111;border-radius:22px;padding:16px 26px;font:700 36px Inter;opacity:0;z-index:3;box-shadow:0 10px 30px rgba(0,0,0,.6)}
.reps{position:absolute;right:50px;font:400 110px 'Archivo Black';z-index:3;text-shadow:0 4px 20px rgba(0,0,0,.6)}
.div{position:absolute;left:0;right:0;height:6px;background:#fff;z-index:3}
.dim{position:absolute;left:0;right:0;top:0;bottom:0;background:#0a0a0a;opacity:0;z-index:4}
.card{position:absolute;left:60px;right:60px;top:640px;z-index:6;opacity:0}
.c1{font:400 70px/1.2 'Archivo Black';color:#8a8a8a;position:relative;display:inline-block}
.c1 i{position:absolute;left:-8px;top:50%;height:10px;background:#fff;width:0}
.c2{margin-top:40px;font:400 92px/1.12 'Archivo Black';text-transform:uppercase}
.c2 span{background:#fff;color:#0a0a0a;padding:4px 18px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.ck{font:700 40px 'JetBrains Mono';color:#9a9a9a;margin-bottom:26px}
.tl{position:absolute;left:60px;right:60px;top:240px;display:flex;gap:14px}
.tl div{flex:1}
.tl .sg{height:22px;border:3px solid #fff;position:relative}
.tl .sg i{position:absolute;left:0;top:0;bottom:0;background:#fff;width:0}
.tl .tx{margin-top:14px;font:700 34px 'JetBrains Mono';color:#777;text-align:center}
.tl .tx.on{color:#fff}
.day{position:absolute;left:60px;top:370px;font:400 150px/1 'Archivo Black'}
.day small{font:700 40px 'JetBrains Mono';color:#9a9a9a;margin-left:18px;letter-spacing:0}
.wk{position:absolute;left:60px;right:60px;background:#fff;color:#0a0a0a;padding:40px 44px;opacity:0;box-shadow:16px 16px 0 #3a3a3a}
.wk .wt{font:400 44px 'JetBrains Mono';font-weight:700;letter-spacing:2px;color:#555}
.wk .wi{margin-top:26px;font:400 76px/1.15 'Archivo Black'}
.cta30{position:absolute;left:0;right:0;top:300px;text-align:center}
.cta30 .j{font:400 120px/1 'Archivo Black';letter-spacing:12px;color:#bbb}
.cta30 .n{font:400 520px/1 'Archivo Black';letter-spacing:-18px}
.obj{position:absolute;left:70px;right:70px;top:1000px;text-align:center;font:400 64px/1.25 'Archivo Black';text-transform:uppercase}
.obj u{text-decoration:none;background:linear-gradient(#fff,#fff) no-repeat 0 100%;background-size:0% 10px;padding-bottom:6px}
.pill{position:absolute;left:110px;right:110px;text-align:center;font:400 50px 'Archivo Black';padding:26px 0;opacity:0}
.pill.w{background:#fff;color:#0a0a0a}.pill.k{border:4px solid #fff}
.capw{position:absolute;left:0;right:0;top:1730px;text-align:center;z-index:7}
.cap{display:none;background:#0a0a0a;color:#fff;border:3px solid #fff;padding:12px 26px;font:400 44px 'Archivo Black';text-transform:uppercase}
.cap .on{background:#fff;color:#0a0a0a}
</style></head><body>
<canvas id='cv' width='1080' height='1920'></canvas>
<div class='hd'><span>@__HANDLE__</span><span><b id='dd'>__CL__ 1</b> / __CMAX__</span></div>
<div class='blk' id='k0'>
 <div class='n30' id='n30'>__HBIG__</div><div class='jours' id='jours'>__HUNIT__</div>
 <div class='l1' id='l1'>__HLINE__</div>
 <div class='l2' id='l2'>// __HSUB__</div></div>
<div class='blk' id='k1'>
 <div class='lab a' style='top:__TA__px'>__LTOP__</div>
 <div class='lab b' style='top:__BA__px'>__LBOT__</div>
 <div class='div' style='top:__DV__px'></div>
 <div class='notif' id='nt0' style='top:__N0__px'>__NT0__</div>
 <div class='notif' id='nt1' style='top:__N1__px'>__NT1__</div>
 <div class='notif' id='nt2' style='top:__N2__px'>__NT2__</div>
 <div class='reps' id='reps' style='top:__RP__px'>×0</div>
 <div class='dim' id='dim'></div>
 <div class='card' id='card'><div class='ck'>// __CK__</div>
  <div class='c1'>≠ __CNO__<i id='cst'></i></div>
  <div class='c2' id='c2'>= <span>__CYES__</span></div></div></div>
<div class='blk' id='kw'>
 <div class='tl'>__SEGS__</div>
 <div class='day' id='day'>__CS__1<small id='dsm'>/ __CMAX__</small></div>
 <div class='wk' id='w0' style='top:620px'><div class='wt' id='w0t'></div><div class='wi' id='w0a'></div><div class='wi' id='w0b'></div></div>
 <div class='wk' id='w1' style='top:1150px'><div class='wt' id='w1t'></div><div class='wi' id='w1a'></div><div class='wi' id='w1b'></div></div></div>
<div class='blk' id='k4'>
 <div class='cta30'><div class='j' id='cj'>__CKICK__</div><div class='n' id='cn'>__CBIG__</div></div>
 <div class='obj' id='obj'>__COBJ__</div>
 <div class='pill w' id='p0' style='top:1320px'>__P0__</div>
 <div class='pill k' id='p1' style='top:1480px'>__P1__</div></div>
<div class='capw'>__CAPS__</div><div class='bar' id='bar'></div>
<script>
const EV=__EV__; const D=__D__; const SC=__SC__; const WK=__WK__; const CF=__CF__; const TOP=__TOP__, BOT=__BOT__;
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), back=x=>{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const $=id=>document.getElementById(id);
function inn(id,t0,u,dy=40){const e=$(id);if(!e)return;const k=eo((u-t0)/.35);e.style.opacity=u>=t0?k:0;e.style.transform=`translateY(${(1-k)*dy}px)`;}
function slam(id,t0,u,s0=2.4){const e=$(id);const k=eo((u-t0)/.22);e.style.opacity=u>=t0?c((u-t0)/.06):0;e.style.transform=`scale(${s0-(s0-1)*k})`;}
</script>
<script>__THREE__</script>
<script>
const R=new THREE.WebGLRenderer({canvas:$('cv'),antialias:true,preserveDrawingBuffer:true});
R.setSize(1080,1920,false);R.setClearColor(0x0a0a0a);R.outputEncoding=THREE.sRGBEncoding;
const WHITE=new THREE.MeshStandardMaterial({color:0xf4f4f4,roughness:.75});
function mat(c,r=.95){return new THREE.MeshStandardMaterial({color:c,roughness:r});}
function setCyl(me,a,b){const d=new THREE.Vector3().subVectors(b,a);const L=d.length();me.position.copy(a).addScaledVector(d,.5);
  me.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.clone().normalize());me.scale.set(1,L/me.userData.L,1);}
function limb(r,m){const me=new THREE.Mesh(new THREE.CapsuleGeometry(r,1,6,12),m);me.userData.L=1+2*r;return me;}
function glowTex(){const cv=document.createElement('canvas');cv.width=cv.height=128;const x=cv.getContext('2d');const g=x.createRadialGradient(64,64,0,64,64,64);
  g.addColorStop(0,'rgba(220,235,255,.95)');g.addColorStop(.25,'rgba(200,220,255,.35)');g.addColorStop(1,'rgba(200,220,255,0)');x.fillStyle=g;x.fillRect(0,0,128,128);return new THREE.CanvasTexture(cv);}
function room(night){
  const s=new THREE.Scene();
  s.add(new THREE.AmbientLight(0xffffff,night?.035:.22));
  if(!night){const key=new THREE.DirectionalLight(0xeef4ff,1.0);key.position.set(2.5,5,4);s.add(key);
    const win=new THREE.PointLight(0xffffff,1.4,8);win.position.set(-.4,2.2,-.6);s.add(win);}
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(9,9),mat(night?0x161616:0x2b2b2b));floor.rotation.x=-Math.PI/2;s.add(floor);
  const back=new THREE.Mesh(new THREE.PlaneGeometry(9,5),mat(night?0x1c1c1c:0x3a3a3a));back.position.set(0,2.5,-1.4);s.add(back);
  const left=new THREE.Mesh(new THREE.PlaneGeometry(9,5),mat(night?0x181818:0x333333));left.rotation.y=Math.PI/2;left.position.set(-2.7,2.5,0);s.add(left);
  const gc=document.createElement('canvas');gc.width=64;gc.height=128;const gx=gc.getContext('2d');const gr=gx.createLinearGradient(0,0,0,128);
  if(night){gr.addColorStop(0,'#050505');gr.addColorStop(1,'#1a1d24');}else{gr.addColorStop(0,'#cfd6df');gr.addColorStop(1,'#ffffff');}
  gx.fillStyle=gr;gx.fillRect(0,0,64,128);const wt=new THREE.CanvasTexture(gc);
  for(const dx of [-.33,.33]){const p=new THREE.Mesh(new THREE.PlaneGeometry(.6,1.05),new THREE.MeshBasicMaterial({map:wt}));p.position.set(-.3+dx,2.15,-1.39);s.add(p);}
  const fr=new THREE.Mesh(new THREE.BoxGeometry(1.45,1.25,.05),mat(0x8a8a8a));fr.position.set(-.3,2.15,-1.42);s.add(fr);
  const bed=new THREE.Mesh(new THREE.BoxGeometry(2.5,.38,1.5),mat(0x2e2e2e));bed.position.set(-1.3,.19,-.62);s.add(bed);
  const m2=new THREE.Mesh(new THREE.BoxGeometry(2.45,.16,1.45),mat(0x5a5a5a));m2.position.set(-1.3,.46,-.62);s.add(m2);
  const head=new THREE.Mesh(new THREE.BoxGeometry(.1,.9,1.5),mat(0x3a3a3a));head.position.set(-2.55,.6,-.62);s.add(head);
  const pil=new THREE.Mesh(new THREE.BoxGeometry(.5,.14,.8),mat(0x9a9a9a));pil.position.set(-2.18,.6,-.62);s.add(pil);
  const ns=new THREE.Mesh(new THREE.BoxGeometry(.6,.62,.55),mat(0x3a3a3a));ns.position.set(.35,.31,-1.05);s.add(ns);
  const sh=new THREE.Mesh(new THREE.CircleGeometry(1,32),new THREE.MeshBasicMaterial({color:0,transparent:true,opacity:.4}));sh.rotation.x=-Math.PI/2;sh.position.set(.4,.006,.75);sh.scale.set(1.1,.5,1);s.add(sh);
  return {s,sh};
}
function sleeper(env){
  const g=new THREE.Group();env.s.add(g);
  const head=new THREE.Mesh(new THREE.SphereGeometry(.27,32,24),WHITE);head.position.set(-2.05,.86,-.62);g.add(head);
  const bl=new THREE.PlaneGeometry(1.9,1.5,40,24);bl.rotateX(-Math.PI/2);const base=bl.attributes.position.array.slice();
  const blanket=new THREE.Mesh(bl,new THREE.MeshStandardMaterial({color:0x4a4a4a,roughness:1,side:THREE.DoubleSide}));blanket.position.set(-.95,.56,-.62);g.add(blanket);
  const a1=limb(.065,WHITE),a2=limb(.06,WHITE);g.add(a1);g.add(a2);
  const phone=new THREE.Mesh(new THREE.BoxGeometry(.11,.2,.014),[mat(0x111111),mat(0x111111),mat(0x111111),mat(0x111111),new THREE.MeshBasicMaterial({color:0xe6eeff}),mat(0x111111)]);g.add(phone);
  const pl=new THREE.PointLight(0xd6e4ff,2.2,3.2);g.add(pl);
  const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:glowTex(),blending:THREE.AdditiveBlending,transparent:true,depthWrite:false}));sp.scale.set(1.1,1.1,1);g.add(sp);
  return {g,head,blanket,base,a1,a2,phone,pl,sp};
}
function poseSleep(sl,t){
  const p=sl.blanket.geometry.attributes.position;const br=1+.04*Math.sin(t*2.2);
  for(let i=0;i<p.count;i++){const x=sl.base[i*3],z=sl.base[i*3+2];let y=.26*Math.exp(-(z*z)/.12)*br*(x<.85?1:Math.max(0,1-(x-.85)*4));
    y-=.25*Math.max(0,Math.abs(z)-.62)*4;p.setY(i,y);}
  p.needsUpdate=true;sl.blanket.geometry.computeVertexNormals();
  const ph=new THREE.Vector3(-1.72,1.28+.012*Math.sin(t*3),-.5);sl.phone.position.copy(ph);sl.phone.lookAt(sl.head.position);
  const sh=new THREE.Vector3(-1.78,.8,-.36),el=new THREE.Vector3(-1.45,.98,-.3),hd=ph.clone().add(new THREE.Vector3(.03,-.08,.03));
  setCyl(sl.a1,sh,el);setCyl(sl.a2,el,hd);
  const fl=.85+.15*Math.sin(t*7.3)*Math.sin(t*2.1);sl.pl.position.copy(ph).add(new THREE.Vector3(-.1,-.05,0));sl.pl.intensity=2.2*fl;
  sl.sp.position.copy(ph).add(new THREE.Vector3(-.05,0,.02));sl.sp.material.opacity=.8*fl;
  sl.head.position.y=.86+.01*Math.sin(t*2.2);
}
function pusher(env){
  const g=new THREE.Group();env.s.add(g);
  const torso=limb(.15,WHITE),head=new THREE.Mesh(new THREE.SphereGeometry(.24,32,24),WHITE);
  const a1=limb(.06,WHITE),a2=limb(.055,WHITE),b1=limb(.06,WHITE),b2=limb(.055,WHITE);
  [torso,head,a1,a2,b1,b2].forEach(m=>g.add(m));return {g,torso,head,arms:[[a1,a2],[b1,b2]]};
}
function posePush(p,h){
  const F=new THREE.Vector3(1.25,.07,.75);const L=1.15;const sy=h-.07;const th=Math.asin(Math.min(.95,sy/L));
  const dir=new THREE.Vector3(-Math.cos(th),Math.sin(th),0);const S=F.clone().addScaledVector(dir,L);
  setCyl(p.torso,F,S.clone().addScaledVector(dir,.05));p.head.position.copy(S).addScaledVector(dir,.3).add(new THREE.Vector3(0,.08,0));
  const a=.33;
  [-1,1].forEach((sd,i)=>{const sh=S.clone().add(new THREE.Vector3(0,0,.2*sd));const hand=new THREE.Vector3(S.x-.05,.04,S.z+.26*sd);
    const d=sh.distanceTo(hand);const mid=sh.clone().lerp(hand,.5);const off=Math.sqrt(Math.max(0,a*a-(d/2)*(d/2)));
    const el=mid.add(new THREE.Vector3(.06,0,sd*off));setCyl(p.arms[i][0],sh,el);setCyl(p.arms[i][1],el,hand);});
}
const topE=room(true),botE=room(false);topE.sh.visible=false;
const sl=sleeper(topE),pu=pusher(botE);
const cam=new THREE.PerspectiveCamera(33,1080/(TOP[1]-TOP[0]),.1,50);
const cam2=new THREE.PerspectiveCamera(33,1080/(BOT[1]-BOT[0]),.1,50);
function draw3d(t,u){
  poseSleep(sl,t);const ph=u/1.5;posePush(pu,.3+.36*(.5+.5*Math.cos(ph*2*Math.PI)));
  cam.position.set(.3-.15*Math.sin(t/5),1.75,1.5);cam.lookAt(-1.85,.95,-.55);
  cam2.position.set(3.3+.2*Math.sin(t/6),2.3,3.9);cam2.lookAt(-.2,.45,0);
  R.setScissorTest(true);
  R.setViewport(0,1920-TOP[1],1080,TOP[1]-TOP[0]);R.setScissor(0,1920-TOP[1],1080,TOP[1]-TOP[0]);R.render(topE.s,cam);
  R.setViewport(0,1920-BOT[1],1080,BOT[1]-BOT[0]);R.setScissor(0,1920-BOT[1],1080,BOT[1]-BOT[0]);R.render(botE.s,cam2);
  $('reps').textContent='×'+Math.max(0,Math.floor(u/1.5+.5));
}
window.render=function(t){
 $('bar').style.width=(c(t/D)*1080)+'px';
 let k=0;for(let i=0;i<SC.length;i++)if(t>=SC[i].a)k=i;const u=t-SC[k].a,d=SC[k].b-SC[k].a;
 const blk=k==0?'k0':k==1?'k1':k==4?'k4':'kw';
 for(const id of ['k0','k1','kw','k4']){const e=$(id);const on=id==blk;const prev=(k>0&&id==({0:'k0',1:'k1',4:'k4'}[k-1]||'kw'))&&id!=blk;
   e.style.opacity=on?(k==0?1:eo(u/.3)):(prev&&u<.3?1-eo(u/.3):0);}
 $('cv').style.opacity=k==1?eo(u/.3):(k==2&&u<.3?1-eo(u/.3):0);
 if(k==1||(k==2&&u<.3))draw3d(t,k==1?u:SC[1].b-SC[1].a);
 let day=1;
 if(k==0){slam('n30',.1,u,2.8);const gl=u>.1&&u<.6?Math.sin(u*90)*14*(1-u/.6):0;$('n30').style.textShadow=`${gl}px 0 #777, ${-gl}px 0 #333`;
   slam('jours',1.3,u,1.8);inn('l1',2.3,u);inn('l2',3.6,u,20);}
 if(k==1){[1.0,2.6,4.2].forEach((x,i)=>{const e=$('nt'+i);const kk=back((u-x)/.35);e.style.opacity=u>=x?c((u-x)/.1)*(1-c((u-SC[1].card+.5)/.3)):0;e.style.transform=`translateX(${(1-kk)*120}px)`;});
   const ct=WK.card;$('dim').style.opacity=.78*eo((u-ct)/.35);inn('card',ct,u);$('cst').style.width=(eo((u-ct-.8)/.35)*105)+'%';inn('c2',ct+1.6,u,30);}
 if(k==2||k==3){const ws=WK[k];const base=(k==2?0:2);
   for(let j=0;j<2;j++){const w=ws[j];$('w'+j+'t').textContent=w.t;$('w'+j+'a').textContent=w.a;$('w'+j+'b').textContent=w.b;$('w'+j+'b').style.display=w.b?'block':'none';
     const e=$('w'+j);const kk=back((u-w.at)/.4);e.style.opacity=u>=w.at?c((u-w.at)/.12):0;e.style.transform=`translateX(${(1-kk)*-140}px) rotate(${(1-kk)*-3}deg)`;}
   $('w1').style.top=($('w0').offsetTop+$('w0').offsetHeight+56)+'px';
   for(let s=0;s<4;s++){let f=0;if(s<base)f=1;else if(s<base+2){const w=ws[s-base];f=eo((u-w.at)/.6);}
     $('sg'+s).style.width=(f*100)+'%';$('tx'+s).className='tx'+(f>0?' on':'');day=Math.max(day,f>0?Math.round(1+(s+f)*(CF.max-1)/4):day);}
   day=Math.min(CF.max-1,day);$('day').firstChild.textContent=CF.short+day;}
 if(k==4){const n=CF.num?(u<.25?CF.big-2:u<.5?CF.big-1:CF.big):CF.bigs;$('cn').textContent=n;slam('cn',.5,u,1.9);inn('cj',.1,u,20);inn('obj',1.0,u);if($('ou'))$('ou').style.backgroundSize=(eo((u-2.6)/.5)*100)+'% 10px';
   const pp=(id,x)=>{const e=$(id);const kk=back((u-x)/.35);e.style.opacity=u>=x?c((u-x)/.1):0;e.style.transform=`scale(${.6+.4*kk})`;};pp('p0',WK.p0);pp('p1',WK.p1);day=CF.max;}
 if(k==1)day=1;
 $('dd').textContent=CF.label+' '+day;
 for(const cp of document.querySelectorAll('.cap')){const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}
};render(0);
</script></body></html>"""

def manifeste3d_page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]; a = starts
    TOP, BOT = (230, 950), (980, 1700)
    words = [(w, t) for ch, _ in caps for (w, t) in ch]
    def wt(pref, t0, t1, nth=0, dflt=None):
        hits = [t for w, t in words if t0 <= t < t1 and w.lower().strip("«»:,.").startswith(pref)]
        return hits[nth] if len(hits) > nth else dflt
    cw = sc[1].get("card_word", "précision").lower()
    card = (wt(cw, a[1], a[1] + durs[1], 0, a[1] + durs[1] * .62) - a[1]) - .1
    S = [{"a": starts[k], "b": starts[k] + durs[k]} for k in range(len(sc))]
    S[1]["card"] = card
    WK = {"card": card}
    for k in (2, 3):
        ws = sc[k]["weeks"]; out = []
        for j, w in enumerate(ws):
            at = (wt(sc[k].get("word", "semaine").lower(), a[k], a[k] + durs[k], j, a[k] + (0.2 if j == 0 else durs[k] * .5)) - a[k])
            out.append({"t": w[0], "a": w[1], "b": w[2], "at": max(.15, at - .15)})
        WK[k] = out
    WK["p0"] = (wt("enregistre", a[4], total, 0, a[4] + 3.5) - a[4]) - .1
    WK["p1"] = (wt("commente", a[4], total, 0, a[4] + 5) - a[4]) - .1
    ev = [{"k": "impact", "at": a[0] + .1}, {"k": "glitch", "at": a[0] + .12}, {"k": "impact", "at": a[0] + 1.3}, {"k": "whoosh", "at": a[0] + 2.2}, {"k": "line", "at": a[0] + 3.6}]
    ev += [{"k": "whoosh", "at": a[1]}] + [{"k": "notif", "at": a[1] + x} for x in (1.0, 2.6, 4.2)]
    ev += [{"k": "impact", "at": a[1] + card}, {"k": "line", "at": a[1] + card + .8}, {"k": "pop", "at": a[1] + card + 1.6}]
    for k in (2, 3):
        ev += [{"k": "whoosh", "at": a[k]}] + [{"k": "check", "at": a[k] + w["at"] + .1} for w in WK[k]]
    ev += [{"k": "click", "at": a[4] + .0}, {"k": "click", "at": a[4] + .25}, {"k": "impact", "at": a[4] + .5}, {"k": "line", "at": a[4] + 2.6},
           {"k": "pop", "at": a[4] + WK["p0"]}, {"k": "pop", "at": a[4] + WK["p1"]}]
    ev.sort(key=lambda e: e["at"])
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    three = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "three.min.js")).read()
    rep = {"__EV__": json.dumps(ev), "__D__": str(total), "__SC__": json.dumps(S), "__WK__": json.dumps(WK, ensure_ascii=False),
           "__TOP__": json.dumps(TOP), "__BOT__": json.dumps(BOT), "__TA__": str(TOP[0] + 30), "__BA__": str(BOT[0] + 30), "__DV__": str(TOP[1] + 12),
           "__N0__": str(TOP[0] + 400), "__N1__": str(TOP[0] + 510), "__N2__": str(TOP[0] + 620), "__RP__": str(BOT[0] + 20),
           "__HANDLE__": H.escape(spec.get("handle", "")), "__CAPS__": cap_html}
    h, av, ct = sc[0], sc[1], sc[-1]
    cnt = spec.get("counter", {}); cmax = int(cnt.get("max", 30)); clab = cnt.get("label", "JOUR"); csh = cnt.get("short", "J")
    def inv(x):  # **texte** = bandeau blanc
        q = K.esc(x).split("**"); return "".join(f"<span class='inv'>{z}</span>" if n % 2 else z for n, z in enumerate(q)).replace("&lt;br&gt;", "<br>")
    def und(x):
        q = K.esc(x).split("**"); return "".join(f"<u id='ou'>{z}</u>" if n % 2 else z for n, z in enumerate(q))
    big = str(ct.get("big", cmax)); nts = (av.get("notifs") or ["", "", ""]) + ["", "", ""]
    tl = (spec.get("timeline") or ["S1", "S2", "S3", "S4"])[:4]
    segs = "".join(f"<div><div class='sg'><i id='sg{q}'></i></div><div class='tx' id='tx{q}'>{K.esc(x)}</div></div>" for q, x in enumerate(tl))
    rep["__SEGS__"] = segs
    rep.update({"__CL__": K.esc(clab), "__CMAX__": str(cmax), "__CS__": K.esc(csh), "__HBIG__": K.esc(str(h.get("big", cmax))), "__HUNIT__": K.esc(h.get("unit", "JOURS")),
        "__HLINE__": inv(h.get("line", "")), "__HSUB__": K.esc(h.get("sub", "")), "__LTOP__": K.esc(av.get("top", "AVANT")), "__LBOT__": K.esc(av.get("bottom", "APRÈS")),
        "__NT0__": K.esc(nts[0]), "__NT1__": K.esc(nts[1]), "__NT2__": K.esc(nts[2]), "__CK__": K.esc(av.get("kicker", "précision")),
        "__CNO__": K.esc(av.get("no", "")), "__CYES__": K.esc(av.get("yes", "")), "__CKICK__": K.esc(ct.get("kicker", clab)), "__CBIG__": K.esc(big),
        "__COBJ__": und(ct.get("obj", "")), "__P0__": K.esc((ct.get("ctas") or ["🔖 ENREGISTRE"])[0]), "__P1__": K.esc((ct.get("ctas") or ["", "💬 COMMENTE"])[-1]),
        "__CF__": json.dumps({"max": cmax, "label": clab, "short": csh, "num": big.isdigit(), "big": int(big) if big.isdigit() else 0, "bigs": big}, ensure_ascii=False)})
    page = MANIF3D_TPL
    for kk, v in rep.items():
        page = page.replace(kk, v)
    page = page.replace("__THREE__", three)
    return page.replace("<style>", "<style>" + K._font_faces(["Archivo Black", "JetBrains Mono"]), 1)


# ------------------------------------------------------------------ layout « claudeflow » (LIA : coulisses d'un système Claude → file → publication)
FLOW_TPL = r"""<!doctype html><html><head><meta charset='utf-8'><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:#050806;color:#eafff2;font-family:'JetBrains Mono',monospace;position:relative}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(57,255,136,.06) 2px,transparent 2px),linear-gradient(90deg,rgba(57,255,136,.06) 2px,transparent 2px);background-size:90px 90px}
.scan{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(0,0,0,.22) 0 2px,transparent 2px 5px)}
.g{color:#39ff88}.y{color:#febc2e}.r{color:#ff4d4d}
.hd{position:absolute;left:50px;right:50px;top:120px;display:flex;justify-content:space-between;font:700 30px 'JetBrains Mono';color:#7fa891}
.blk{position:absolute;inset:0;opacity:0}
.tag{position:absolute;left:60px;top:200px;font:700 36px 'JetBrains Mono';color:#050806;background:#39ff88;padding:8px 20px}
.big{position:absolute;left:60px;right:60px;top:520px;font:400 118px/1.05 'Archivo Black';text-transform:uppercase}
.big em{font-style:normal;color:#39ff88}
.sub{position:absolute;left:60px;right:60px;top:1000px;font:700 48px 'JetBrains Mono';color:#7fa891}
.cur{display:inline-block;width:24px;height:52px;background:#39ff88;vertical-align:-8px;margin-left:8px}
.win{position:absolute;left:50px;right:50px;top:300px;height:1100px;border:3px solid rgba(57,255,136,.55);border-radius:26px;background:rgba(6,14,9,.96);overflow:hidden}
.wbar{height:76px;border-bottom:2px solid rgba(57,255,136,.3);display:flex;align-items:center;gap:14px;padding:0 28px;font:700 30px 'JetBrains Mono';color:#7fa891}
.wbar i{width:20px;height:20px;border-radius:50%;background:#2a3b30}
.ub{position:absolute;right:40px;left:160px;top:120px;background:#16241b;border:2px solid #2d4a37;border-radius:24px 24px 6px 24px;padding:26px 30px;font:600 48px/1.3 Inter,sans-serif;color:#eafff2;opacity:0}
.who{font:700 28px 'JetBrains Mono';color:#7fa891;margin-bottom:8px}
.ar{position:absolute;left:40px;right:50px;font:600 48px/1.3 Inter,sans-serif;color:#d6f5e2}
.ln{opacity:0;margin-top:26px;padding-left:40px;position:relative}
.ln:before{content:'▸';position:absolute;left:0;color:#39ff88}
.row{display:grid;grid-template-columns:120px 130px 1fr 250px;gap:12px;align-items:center;padding:40px 26px;border-bottom:2px solid rgba(57,255,136,.14);font:700 42px/1.2 Inter,sans-serif;opacity:0}
.row.h{opacity:1;font:700 26px 'JetBrains Mono';color:#7fa891;padding:18px 26px}
.st{font:700 32px 'JetBrains Mono';padding:10px 14px;border-radius:10px;text-align:center}
.node{position:absolute;left:290px;width:500px;height:150px;border:4px solid #39ff88;background:#050806;display:flex;align-items:center;justify-content:center;font:400 54px 'Archivo Black';opacity:0}
.node small{display:block;font:700 26px 'JetBrains Mono';color:#7fa891;text-align:center;margin-top:6px}
.wire{position:absolute;left:536px;width:8px;background:rgba(57,255,136,.25)}
.pk{position:absolute;left:526px;width:28px;height:28px;border-radius:50%;background:#39ff88;box-shadow:0 0 24px #39ff88;opacity:0}
.notif{position:absolute;left:90px;right:90px;top:1300px;background:rgba(240,255,245,.95);color:#08130c;border-radius:28px;padding:24px 30px;display:flex;gap:22px;align-items:center;font:700 38px Inter,sans-serif;opacity:0}
.notif b{font-size:58px}
.ctl{position:absolute;left:60px;right:60px;font:700 50px 'JetBrains Mono';opacity:0}
.capw{position:absolute;left:0;right:0;top:1505px;text-align:center;z-index:9}
.cap{display:none;background:#050806;border:3px solid #39ff88;padding:12px 28px;font:700 46px 'JetBrains Mono'}
.cap .on{color:#39ff88}
.bar{position:absolute;left:0;top:0;height:10px;background:#39ff88;z-index:9}
</style></head><body><div class='grid'></div>
<div class='hd'><span>@__HANDLE__</span><span id='stp'></span></div>
<div class='blk' id='k0'><div class='big' id='hk'>__H_TITLE__</div><div class='sub' id='hs'>&gt; <span id='hst'></span><b class='cur'></b></div></div>
<div class='blk' id='k1'><div class='tag'>__C_TAG__</div><div class='win'><div class='wbar'><i></i><i></i><i></i>&nbsp;__C_WIN__</div>
 <div class='ub' id='ub'><div class='who'>toi</div><span id='ubt'></span></div>
 <div class='ar' id='ar' style='top:__AR_TOP__px'><div class='who' style='opacity:0' id='aw'>__C_WHO__</div>__C_LINES__</div></div></div>
<div class='blk' id='k2'><div class='tag'>__T_TAG__</div><div class='win'><div class='wbar'><i></i><i></i><i></i>&nbsp;__T_WIN__</div>
 <div class='row h'><span>JOUR</span><span>HEURE</span><span>POST</span><span>STATUT</span></div>__T_ROWS__</div></div>
<div class='blk' id='k3'><div class='tag'>__P_TAG__</div>__P_NODES__<div class='notif' id='nt'><b>✓</b><span>__P_NOTIF__</span></div></div>
<div class='blk' id='k4'><div class='big' id='cb' style='top:420px'>__CT_TITLE__</div>__CT_LINES__</div>
<div class='scan'></div><div class='capw'>__CAPS__</div><div class='bar' id='bar'></div>
<script>
const EV=__EV__; const D=__D__; const SC=__SC__; const CF=__CF__;
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), back=x=>{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const $=id=>document.getElementById(id);
function inn(id,t0,u,dy=40){const e=$(id);if(!e)return;const k=eo((u-t0)/.35);e.style.opacity=u>=t0?k:0;e.style.transform=`translateY(${(1-k)*dy}px)`;}
const ST={valider:['À valider','#3a3214','#febc2e'],refuse:['Refusé','#3a1414','#ff4d4d'],publie:['Publié ✓','#123a20','#39ff88']};
window.render=function(t){
 $('bar').style.width=(c(t/D)*1080)+'px';
 let k=0;for(let i=0;i<SC.length;i++)if(t>=SC[i].a)k=i;const u=t-SC[k].a,d=SC[k].b-SC[k].a;
 for(let i=0;i<5;i++){const e=$('k'+i);const on=i==k;const out=i==k-1&&u<.3;e.style.opacity=on?(k==0?1:eo(u/.3)):(out?1-eo(u/.3):0);e.style.transform=`translateX(${on?(1-eo(k==0?1:u/.3))*80:(out?-eo(u/.3)*80:0)}px)`;}
 $('stp').textContent=['','ÉTAPE 1/3','ÉTAPE 2/3','ÉTAPE 3/3','✓'][k];
 if(k==0){const hk=$('hk');const kk=back(u/.35);hk.style.transform=`scale(${1.6-.6*kk})`;hk.style.opacity=c(u/.08);
   $('hst').textContent=CF.hsub.slice(0,Math.floor(c((u-1.0)/1.2)*CF.hsub.length));}
 if(k==1){$('ub').style.opacity=u>=.3?1:0;$('ubt').textContent=CF.prompt.slice(0,Math.floor(c((u-.3)/CF.ptime)*CF.prompt.length));
   const a0=.3+CF.ptime+.3;$('aw').style.opacity=u>=a0?1:0;const n=CF.nl;const st=(d-a0-.6)/Math.max(1,n);
   for(let j=0;j<n;j++){const e=$('al'+j);const k2=eo((u-a0-st*j)/.3);e.style.opacity=u>=a0+st*j?k2:0;e.style.transform=`translateX(${(1-k2)*30}px)`;}}
 if(k==2){const n=CF.nr;const st=Math.min(.7,(d*.45)/Math.max(1,n));
   for(let j=0;j<n;j++){const e=$('rw'+j);const t0=.4+st*j;const k2=eo((u-t0)/.3);e.style.opacity=u>=t0?k2:0;e.style.transform=`translateY(${(1-k2)*30}px)`;
     const s=$('rs'+j);let v='valider';const fin=CF.rows[j];if(u>=d*.62+.25*j&&fin!='valider')v=fin;const S=ST[v];s.textContent=S[0];s.style.background=S[1];s.style.color=S[2];}}
 if(k==3){const n=CF.nn;const st=(d*.5)/Math.max(1,n);
   for(let j=0;j<n;j++){inn('nd'+j,.2+st*j,u,30);}
   for(let j=0;j<n-1;j++){const p=$('pk'+j);const t0=.2+st*(j+1)-.35;const y0=CF.ny[j]+150,y1=CF.ny[j+1];const kk=c((u-t0)/.4);p.style.opacity=u>=t0&&kk<1?1:0;p.style.top=(y0+(y1-y0)*kk-14)+'px';}
   const tn=.2+st*n;const kn=back((u-tn)/.4);$('nt').style.opacity=u>=tn?c((u-tn)/.1):0;$('nt').style.transform=`translateY(${(1-kn)*-120}px)`;}
 if(k==4){const cb=$('cb');const kk=back(u/.35);cb.style.opacity=c(u/.1);cb.style.transform=`scale(${1.4-.4*kk})`;
   for(let j=0;j<CF.nc;j++)inn('cl'+j,1.2+.6*j,u,30);}
 for(const cp of document.querySelectorAll('.cap')){const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}
};render(0);
</script></body></html>"""

def claudeflow_page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]; a = starts
    h, ch, tb, pp, ct = sc
    def em(x):
        q = K.esc(x).split("**"); return "".join(f"<em>{z}</em>" if n % 2 else z for n, z in enumerate(q)).replace("&lt;br&gt;", "<br>")
    lines = ch.get("reply", [])[:6]
    rows = tb.get("rows", [])[:7]
    nodes = pp.get("nodes", ["CLAUDE", "MAKE", "INSTAGRAM"])[:4]
    ny = [330 + j * (780 // max(1, len(nodes) - 1)) for j in range(len(nodes))] if len(nodes) > 1 else [600]
    nodes_html = ""
    for j, nd in enumerate(nodes):
        lab, sub = (nd if isinstance(nd, list) else [nd, ""])[:2]
        nodes_html += f"<div class='node' id='nd{j}' style='top:{ny[j]}px'><div>{K.esc(lab)}<small>{K.esc(sub)}</small></div></div>"
        if j < len(nodes) - 1:
            nodes_html += f"<div class='wire' style='top:{ny[j]+150}px;height:{ny[j+1]-ny[j]-150}px'></div><div class='pk' id='pk{j}'></div>"
    rows_html = ""
    for j, r in enumerate(rows):
        day, hr, lab = (r + ["", "", ""])[:3]
        rows_html += f"<div class='row' id='rw{j}'><span class='g'>{K.esc(day)}</span><span>{K.esc(hr)}</span><span>{K.esc(lab)}</span><span class='st' id='rs{j}'></span></div>"
    fin = [(r[3] if len(r) > 3 else "valider") for r in rows]
    prompt = ch.get("prompt", "")
    ctl = ct.get("ctas", [])[:3]
    ct_html = "".join(f"<div class='ctl' id='cl{j}' style='top:{1000 + 110 * j}px'>{K.esc(x)}</div>" for j, x in enumerate(ctl))
    S = [{"a": starts[k], "b": starts[k] + durs[k]} for k in range(len(sc))]
    ptime = min(2.2, max(1.0, len(prompt) / 45))
    CF = {"hsub": h.get("sub", ""), "prompt": prompt, "ptime": ptime, "nl": len(lines), "nr": len(rows), "rows": fin, "nn": len(nodes), "ny": ny, "nc": len(ctl)}
    ev = [{"k": "impact", "at": a[0] + .05}, {"k": "type", "at": a[0] + 1.0, "end": a[0] + 2.2, "text": h.get("sub", "x")}]
    ev += [{"k": "type", "at": a[1] + .3, "end": a[1] + .3 + ptime, "text": prompt}]
    a0 = .3 + ptime + .3; st = (durs[1] - a0 - .6) / max(1, len(lines))
    ev += [{"k": "pop", "at": a[1] + a0 + st * j} for j in range(len(lines))]
    st2 = min(.7, (durs[2] * .45) / max(1, len(rows)))
    ev += [{"k": "pop", "at": a[2] + .4 + st2 * j} for j in range(len(rows))]
    ev += [{"k": ("impact" if f == "refuse" else "check"), "at": a[2] + durs[2] * .62 + .25 * j} for j, f in enumerate(fin) if f != "valider"]
    st3 = (durs[3] * .5) / max(1, len(nodes))
    ev += [{"k": "pop", "at": a[3] + .2 + st3 * j} for j in range(len(nodes))] + [{"k": "notif", "at": a[3] + .2 + st3 * len(nodes)}]
    ev += [{"k": "impact", "at": a[4] + .05}] + [{"k": "pop", "at": a[4] + 1.2 + .6 * j} for j in range(len(ctl))]
    ev.sort(key=lambda e: e["at"])
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    R = {"__HANDLE__": H.escape(spec.get("handle", "")), "__H_TITLE__": em(h.get("title", "")),
         "__C_TAG__": K.esc(ch.get("tag", "ÉTAPE 1 · CLAUDE ÉCRIT")), "__C_WIN__": K.esc(ch.get("window", "claude — nouvelle conversation")),
         "__C_WHO__": K.esc(ch.get("who", "claude")), "__AR_TOP__": str(ch.get("reply_top", 420)),
         "__C_LINES__": "".join(f"<div class='ln' id='al{j}'>{em(x)}</div>" for j, x in enumerate(lines)),
         "__T_TAG__": K.esc(tb.get("tag", "ÉTAPE 2 · JE VALIDE")), "__T_WIN__": K.esc(tb.get("window", "file d'attente")), "__T_ROWS__": rows_html,
         "__P_TAG__": K.esc(pp.get("tag", "ÉTAPE 3 · PUBLICATION")), "__P_NODES__": nodes_html, "__P_NOTIF__": K.esc(pp.get("notif", "Publié sur Instagram")),
         "__CT_TITLE__": em(ct.get("title", "")), "__CT_LINES__": ct_html, "__CAPS__": cap_html}
    page = FLOW_TPL
    for kk, v in R.items():
        page = page.replace(kk, v)
    page = page.replace("__EV__", json.dumps(ev, ensure_ascii=False)).replace("__D__", str(total)).replace("__SC__", json.dumps(S)).replace("__CF__", json.dumps(CF, ensure_ascii=False))
    return page.replace("<style>", "<style>" + K._font_faces(["JetBrains Mono", "Archivo Black"]), 1)


# ------------------------------------------------------------------ layout « malin » (Revenus Malins : structures qui se remplissent — liste, tier list, bocaux, calcul)
MALIN_TPL = r"""<!doctype html><html><head><meta charset='utf-8'><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:#0f3326;color:#fbf8f1;font-family:Inter,sans-serif;position:relative}
.bgd{position:absolute;inset:0;background:radial-gradient(1200px 900px at 50% 30%,#175a42 0,#0f3326 60%,#0a241b 100%)}
.hd{position:absolute;left:50px;right:50px;top:120px;display:flex;justify-content:space-between;font:700 30px 'JetBrains Mono';color:#9fd9bf}
.blk{position:absolute;inset:0;opacity:0}
.ttl{position:absolute;left:60px;right:60px;top:220px;font:900 76px/1.08 Inter;color:#fbf8f1;text-align:center}
.mk{background:linear-gradient(90deg,#e9c46a,#e9c46a) no-repeat 0 100%;background-size:0% 22%;padding:0 6px;color:#ffe58f}
.hk{position:absolute;left:60px;right:60px;top:560px;font:900 118px/1.04 Inter;text-align:center}
.hk em{font-style:normal;color:#ffe58f}
.hs{position:absolute;left:80px;right:80px;top:1080px;font:700 48px/1.3 Inter;text-align:center;color:#cfe9dc}
/* liste */
.ls{position:absolute;left:70px;right:70px;top:470px}
.li{display:flex;align-items:center;gap:26px;height:150px;border-bottom:3px solid rgba(251,248,241,.18)}
.li .n{flex:none;width:96px;font:900 76px Inter;color:#ffe58f}
.li .t{font:800 56px/1.15 Inter;opacity:0}
.li .t small{display:block;font:600 36px Inter;color:#cfe9dc;margin-top:6px}
.li .ok{margin-left:auto;flex:none;width:64px;height:64px;border-radius:50%;background:#0f7b6c;color:#fff;font:900 40px/64px Inter;text-align:center;opacity:0}
/* tier */
.tr{position:absolute;left:50px;right:50px;top:440px}
.tw{display:flex;height:150px;margin-bottom:12px;background:#0b2a1f;border:3px solid rgba(251,248,241,.25)}
.tw .lt{flex:none;width:130px;display:flex;align-items:center;justify-content:center;font:900 80px Inter;color:#111}
.tw .cs{flex:1;display:flex;flex-wrap:wrap;align-content:center;gap:12px;padding:0 16px}
.chip{background:#fbf8f1;color:#1f1e1b;border-radius:14px;padding:12px 22px;font:800 38px Inter;opacity:0}
/* bocaux */
.jr{position:absolute;left:30px;right:30px;top:470px;display:flex;justify-content:space-around;align-items:flex-start}
.jw{display:flex;flex-direction:column;align-items:center}
.jar{position:relative;width:290px;height:540px;border:8px solid #fbf8f1;border-top:none;border-radius:0 0 50px 50px;overflow:hidden;opacity:0}
.jar:before{content:'';position:absolute;left:-8px;right:-8px;top:0;height:22px;background:#fbf8f1;opacity:.6}
.jar .fl{position:absolute;left:0;right:0;bottom:0;height:0;background:linear-gradient(#ffe58f,#e9c46a)}
.jar .pc{position:absolute;left:0;right:0;top:38%;text-align:center;font:900 82px Inter;color:#fbf8f1;text-shadow:0 3px 12px rgba(0,0,0,.6)}
.jl{margin-top:24px;text-align:center;font:800 46px/1.2 Inter;opacity:0}
.jl small{display:block;font:700 44px Inter;color:#ffe58f;margin-top:6px}
/* calcul */
.mt{position:absolute;left:60px;right:60px;top:440px;display:flex;flex-direction:column;align-items:center;gap:14px}
.cell{display:flex;flex-direction:column;align-items:center;opacity:0}
.cell .lb{background:#fbf8f1;color:#1f1e1b;font:800 40px Inter;padding:8px 26px;border-radius:12px}
.cell .vl{margin-top:10px;background:#fbf8f1;color:#1f1e1b;font:900 92px Inter;padding:10px 46px;border-radius:22px;min-width:520px;text-align:center}
.cell.res .vl{background:#ffe58f}
.op{font:900 70px/1 Inter;color:#ffe58f;opacity:0}
.cta{position:absolute;left:80px;right:80px;font:800 52px/1.25 Inter;opacity:0;text-align:center}
.note{position:absolute;left:60px;right:60px;top:1400px;text-align:center;font:600 34px Inter;color:#9fd9bf;opacity:0}
.capw{position:absolute;left:0;right:0;top:1520px;text-align:center;z-index:9}
.cap{display:none;background:#fbf8f1;color:#1f1e1b;border-radius:16px;padding:12px 28px;font:800 46px Inter}
.cap .on{background:#ffe58f}
.bar{position:absolute;left:0;top:0;height:10px;background:#ffe58f;z-index:9}
</style></head><body><div class='bgd'></div>
<div class='hd'><span>@__HANDLE__</span><span id='stp'></span></div>
__BLOCKS__
<div class='capw'>__CAPS__</div><div class='bar' id='bar'></div>
<script>
const EV=__EV__; const D=__D__; const SC=__SC__;
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), back=x=>{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const $=id=>document.getElementById(id);
function inn(e,t0,u,dy=40){if(!e)return;const k=eo((u-t0)/.35);e.style.opacity=u>=t0?k:0;e.style.transform=`translateY(${(1-k)*dy}px)`;}
function pop(e,t0,u,s0=.4){if(!e)return;const k=back((u-t0)/.35);e.style.opacity=u>=t0?c((u-t0)/.1):0;e.style.transform=`scale(${s0+(1-s0)*k})`;}
function fmt(n){return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g,'\u00a0');}
window.render=function(t){
 $('bar').style.width=(c(t/D)*1080)+'px';
 let k=0;for(let i=0;i<SC.length;i++)if(t>=SC[i].a)k=i;const s=SC[k],u=t-s.a,d=s.b-s.a;
 for(let i=0;i<SC.length;i++){const e=$('k'+i);const on=i==k;const out=i==k-1&&u<.3;e.style.opacity=on?(k==0?1:eo(u/.3)):(out?1-eo(u/.3):0);}
 const mk=$('mk'+k);if(mk)mk.style.backgroundSize=`${eo((u-.3)/.5)*100}% 22%`;
 if(s.ty=='hook'){pop($('hk'),.05,u,1.4);inn($('hs'),1.4,u);}
 if(s.ty=='list'){for(let j=0;j<s.n;j++){const tt=s.at[j];const e=$('lt'+k+'_'+j);const kk=eo((u-tt)/.35);e.style.opacity=u>=tt?kk:0;e.style.transform=`translateX(${(1-kk)*60}px)`;pop($('lo'+k+'_'+j),tt+.4,u);}}
 if(s.ty=='tier'){for(let j=0;j<s.n;j++){const tt=s.at[j];const e=$('ch'+k+'_'+j);const kk=back((u-tt)/.4);e.style.opacity=u>=tt?c((u-tt)/.1):0;e.style.transform=`translateY(${(1-kk)*-260}px) rotate(${(1-kk)*-8}deg)`;}}
 if(s.ty=='jars'){for(let j=0;j<s.n;j++){const tt=s.at[j];inn($('ja'+k+'_'+j),.2+.15*j,u,60);const f=eo((u-tt)/1.0);$('jf'+k+'_'+j).style.height=(f*s.p[j])+'%';$('jp'+k+'_'+j).textContent=Math.round(f*s.p[j])+'%';inn($('jl'+k+'_'+j),tt+.6,u,20);}}
 if(s.ty=='math'){for(let j=0;j<s.n;j++){const tt=s.at[j];pop($('mc'+k+'_'+j),tt,u,.6);const v=$('mv'+k+'_'+j);const f=eo((u-tt)/.8);v.textContent=s.pre[j]+fmt(f*s.v[j])+s.suf[j];if(j>0)pop($('mo'+k+'_'+j),tt-.25,u,.3);}}
 if(s.ty=='cta'){pop($('hk'+k),.05,u,1.3);for(let j=0;j<s.n;j++)inn($('ct'+k+'_'+j),1.0+.5*j,u,30);}
 const nt=$('nt'+k);if(nt)inn(nt,Math.max(.8,d*.55),u,10);
 for(const cp of document.querySelectorAll('.cap')){const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}
};render(0);
</script></body></html>"""

def malin_page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]
    words = [(w, t) for ch, _ in caps for (w, t) in ch]
    def em(x, id_=None):
        q = K.esc(x).split("**")
        return "".join((f"<span class='mk'{(' id=' + chr(39) + id_ + chr(39)) if id_ else ''}>{z}</span>" if id_ else f"<em>{z}</em>") if n % 2 else z for n, z in enumerate(q)).replace("&lt;br&gt;", "<br>")
    def wt(word, t0, t1, nth, dflt):
        hits = [t for w, t in words if t0 <= t < t1 and w.lower().strip("«»:,.!?").startswith(word.lower())]
        return hits[nth] if len(hits) > nth else dflt
    def spread(n, d, a):
        st = (d - 1.6) / max(1, n); return [round(.7 + st * j, 2) for j in range(n)]
    blocks, S, ev = [], [], []
    for k, s in enumerate(sc):
        a, d, ty = starts[k], durs[k], s["type"]; info = {"a": a, "b": a + d, "ty": ty}
        title = f"<div class='ttl'>{em(s.get('title', ''), 'mk' + str(k))}</div>" if s.get("title") else ""
        note = f"<div class='note' id='nt{k}'>{K.esc(s['note'])}</div>" if s.get("note") else ""
        if ty == "hook":
            h = f"<div class='hk' id='hk'>{em(s.get('big', ''))}</div><div class='hs' id='hs'>{K.esc(s.get('sub', ''))}</div>"
            ev += [{"k": "impact", "at": a + .05}, {"k": "whoosh", "at": a + 1.4}]
            blocks.append(f"<div class='blk' id='k{k}'>{h}</div>"); S.append(info); continue
        if ty == "list":
            items = s.get("items", [])[:6]; n = len(items)
            at = spread(n, d, a)
            if s.get("cue"):
                at = [round(max(.5, wt(s["cue"][j], a, a + d, 0, a + at[j]) - a - .1), 2) if j < len(s["cue"]) and s["cue"][j] else at[j] for j in range(n)]
            rows = ""
            for j, it in enumerate(items):
                tx, sub = (it if isinstance(it, list) else [it, ""])[:2]
                rows += f"<div class='li'><div class='n'>{j+1}.</div><div class='t' id='lt{k}_{j}'>{K.esc(tx)}{'<small>' + K.esc(sub) + '</small>' if sub else ''}</div><div class='ok' id='lo{k}_{j}'>✓</div></div>"
            for j in range(n, s.get("slots", n)):
                rows += f"<div class='li'><div class='n'>{j+1}.</div><div class='t'></div></div>"
            info.update({"n": n, "at": at}); ev += [{"k": "pop", "at": a + x} for x in at] + [{"k": "check", "at": a + x + .4} for x in at]
            blocks.append(f"<div class='blk' id='k{k}'>{title}<div class='ls' style='top:{s.get('top', 470)}px'>{rows}</div>{note}</div>")
        elif ty == "tier":
            COL = {"S": "#ff6b6b", "A": "#ffb36b", "B": "#ffe58f", "C": "#8ee59a", "D": "#7cc4ff", "E": "#b79cff", "F": "#ff8fd1"}
            rows = s.get("rows", {}); order = [r for r in "SABCDEF" if r in rows or s.get("all_rows")]
            chips = [(r, x) for r in order for x in rows.get(r, [])]
            if s.get("order"):
                chips = sorted(chips, key=lambda rc: s["order"].index(rc[1]) if rc[1] in s["order"] else 99)
            n = len(chips); at = spread(n, d, a)
            idx = {rc: j for j, rc in enumerate(chips)}
            html = ""
            for r in order:
                html += f"<div class='tw'><div class='lt' style='background:{COL[r]}'>{r}</div><div class='cs'>" + "".join(f"<span class='chip' id='ch{k}_{idx[(r, x)]}'>{K.esc(x)}</span>" for x in rows.get(r, [])) + "</div></div>"
            info.update({"n": n, "at": at}); ev += [{"k": "impact" if r in "SF" else "pop", "at": a + at[idx[(r, x)]]} for r, x in chips]
            blocks.append(f"<div class='blk' id='k{k}'>{title}<div class='tr'>{html}</div>{note}</div>")
        elif ty == "jars":
            jars = s.get("jars", [])[:4]; n = len(jars); at = spread(n, d, a)
            if s.get("cue"):
                at = [round(max(.5, wt(s["cue"][j], a, a + d, 0, a + at[j]) - a - .1), 2) if j < len(s["cue"]) and s["cue"][j] else at[j] for j in range(n)]
            w = 290 if n <= 3 else 220
            html = "".join(f"<div class='jw'><div class='jar' id='ja{k}_{j}' style='width:{w}px'><div class='fl' id='jf{k}_{j}'></div><div class='pc' id='jp{k}_{j}'>0%</div></div><div class='jl' id='jl{k}_{j}'>{K.esc(jj.get('label', ''))}<small>{K.esc(jj.get('amount', '').replace(' €', chr(160) + '€'))}</small></div></div>" for j, jj in enumerate(jars))
            info.update({"n": n, "at": at, "p": [int(jj.get("pct", 0)) for jj in jars]}); ev += [{"k": "pop", "at": a + x} for x in at]
            blocks.append(f"<div class='blk' id='k{k}'>{title}<div class='jr'>{html}</div>{note}</div>")
        elif ty == "math":
            cells = s.get("cells", [])[:3]; n = len(cells); at = spread(n, d, a)
            html, pre, suf, vals = "", [], [], []
            for j, cl in enumerate(cells):
                lb, val = cl[0], cl[1]; op = cl[2] if len(cl) > 2 else ""
                import re as _re
                m = _re.match(r"^(\D*?)(\d[\d\s\u202f\u00a0]*\d|\d)(.*)$", val)
                p0, num, s0 = (m.group(1), int(_re.sub(r"\D", "", m.group(2))), m.group(3)) if m else ("", 0, val)
                s0 = s0.strip(); s0 = ("\u00a0" + s0) if s0 else ""
                pre.append(p0); suf.append(s0); vals.append(num)
                if j > 0: html += f"<div class='op' id='mo{k}_{j}'>{K.esc(op or '−')}</div>"
                html += f"<div class='cell{' res' if j == n - 1 and s.get('result', True) and n > 1 else ''}' id='mc{k}_{j}'><div class='lb'>{K.esc(lb)}</div><div class='vl' id='mv{k}_{j}'>0</div></div>"
            info.update({"n": n, "at": at, "pre": pre, "suf": suf, "v": vals}); ev += [{"k": "pop", "at": a + x} for x in at]
            blocks.append(f"<div class='blk' id='k{k}'>{title}<div class='mt'>{html}</div>{note}</div>")
        elif ty == "cta":
            ctas = s.get("ctas", [])[:3]
            html = f"<div class='hk' id='hk{k}' style='top:520px'>{em(s.get('big', ''))}</div>" + "".join(f"<div class='cta' id='ct{k}_{j}' style='top:{1000 + 120 * j}px'>{K.esc(x)}</div>" for j, x in enumerate(ctas))
            info.update({"n": len(ctas)}); ev += [{"k": "impact", "at": a + .05}] + [{"k": "pop", "at": a + 1.0 + .5 * j} for j in range(len(ctas))]
            blocks.append(f"<div class='blk' id='k{k}'>{html}{note}</div>")
        S.append(info)
    ev.sort(key=lambda e: e["at"])
    cap_html = "".join(
        f"<span class='cap' data-a='{c[0][1]:.3f}' data-b='{c_next:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in c) + "</span>"
        for c, c_next in caps)
    page = MALIN_TPL.replace("__BLOCKS__", "\n".join(blocks)).replace("__CAPS__", cap_html).replace("__HANDLE__", H.escape(spec.get("handle", "")))
    page = page.replace("__EV__", json.dumps(ev, ensure_ascii=False)).replace("__D__", str(total)).replace("__SC__", json.dumps(S, ensure_ascii=False))
    return page.replace("<style>", "<style>" + K._font_faces(["JetBrains Mono"]), 1)


# ------------------------------------------------------------------ layout « boucle » (PILOTE, format court 6-10 s)
def boucle_page(spec, theme, starts, durs, caps, total):
    """Une phrase par scène, qui se construit mot à mot ; le fond bascule à chaque mot entre 2 couleurs.
    Coupes sèches, texte visible dès la 1re image, fin sur la couleur du début pour boucler. Pas de voix ni de sous-titres."""
    pas = float(spec.get("pas", 0.3))
    coul = spec.get("couleurs", [["#fbedf1", "#8d0323"], ["#16181f", "#ffffff"]])
    police = spec.get("police", "Georgia, 'Times New Roman', serif")
    S, html_sc, ev = [], [], []
    for k, s in enumerate(spec["scenes"]):
        mots = s["texte"].split()
        html_sc.append(f"<div class='scn' id='s{k}'><div class='txt'>" + " ".join(f"<span id='w{k}_{j}'>{rich(m)}</span>" for j, m in enumerate(mots)) + "</div></div>")
        S.append({"a": starts[k], "b": starts[k] + durs[k], "n": len(mots)})
        ev += [{"k": "pop", "at": starts[k] + j * pas} for j in range(len(mots))]
    css = f"""*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;background:{coul[0][0]};font-family:{police}}}
.scn{{position:absolute;inset:0;display:none}}
.txt{{position:absolute;left:96px;right:96px;top:380px;font-weight:700;font-size:{int(spec.get('taille', 120))}px;line-height:1.12}}
.txt span{{visibility:hidden}} .txt em{{font-style:normal;text-decoration:underline;text-decoration-thickness:8px}}"""
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>
{''.join(html_sc)}
<script>
const EV={json.dumps(ev)}; const D={total}; const SC={json.dumps(S)}; const P={pas}; const C={json.dumps(coul)};
window.render=function(t){{
 SC.forEach((s,k)=>{{const el=document.getElementById('s'+k);const on=t>=s.a-0.001&&(t<s.b||k==SC.length-1&&t<=D);
  el.style.display=on?'block':'none';if(!on)return;
  // nombre de pas écoulés ; la dernière scène retombe sur la couleur 0 dans son dernier pas pour boucler
  let q=Math.max(0,Math.floor((t-s.a)/P+1e-6)); if(k==SC.length-1&&t>=s.b-P)q=0;
  const [bg,fg]=C[q%C.length];document.body.style.background=bg;el.style.color=fg;
  const vis=Math.floor((t-s.a)/P+1e-6);
  for(let j=0;j<s.n;j++)document.getElementById('w'+k+'_'+j).style.visibility=j<=vis?'visible':'hidden';
 }});
}};render(0);
</script></body></html>"""


# ------------------------------------------------------------------ layout « carnet » (PILOTE 23/10/2026, tous comptes)
CARNET_TPL = r"""<!doctype html><html><head><meta charset='utf-8'><style>__FONTS__
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:__BUREAU__;position:relative;font-family:Inter,sans-serif;color:__ENCRE__}
.cam{position:absolute;inset:0;transform-origin:50% 45%}
.page{position:absolute;left:46px;right:46px;top:70px;bottom:120px;background-color:__PAPIER__;border-radius:18px;
  background-image:linear-gradient(__GRILLE__ 2px,transparent 2px),linear-gradient(90deg,__GRILLE__ 2px,transparent 2px);background-size:56px 56px;background-position:-2px 30px;
  box-shadow:0 30px 60px rgba(60,40,10,.28),0 4px 0 rgba(0,0,0,.05)}
.marge{position:absolute;left:118px;top:0;bottom:0;width:3px;background:rgba(232,120,120,.55)}
.ring{position:absolute;top:-22px;width:30px;height:62px;border-radius:15px;border:6px solid #8d8a86;background:transparent;z-index:70}
.tape{position:absolute;z-index:70;width:190px;height:58px;background:rgba(255,214,120,.75);transform:rotate(-8deg);box-shadow:0 2px 6px rgba(0,0,0,.08)}
.hd{position:absolute;left:150px;top:160px;font:700 46px Caveat;color:__ENCRE__;opacity:.75;z-index:60}
/* chaque scène = une feuille opaque qui glisse par-dessus la précédente (page qu'on tourne) */
.sc{position:absolute;left:0;right:0;top:0;bottom:0;border-radius:18px;opacity:0;padding:250px 70px 330px 150px;display:flex;flex-direction:column;justify-content:center;
  background-color:__PAPIER__;background-image:linear-gradient(__GRILLE__ 2px,transparent 2px),linear-gradient(90deg,__GRILLE__ 2px,transparent 2px);background-size:56px 56px;background-position:-2px 30px;
  box-shadow:-18px 0 40px rgba(60,40,10,.18)}
.sc::before{content:'';position:absolute;left:118px;top:0;bottom:0;width:3px;background:rgba(232,120,120,.55)}
.hw{font-family:Caveat;font-weight:700;color:__ENCRE__;display:block}
.ln{display:inline-block;clip-path:inset(-20% 100% -20% 0)}
.t1{font-size:136px;line-height:1.05}
.t2{font-size:104px;line-height:1.12;margin-bottom:26px}
.l{font-size:84px;line-height:1.25;margin-top:22px}
.sub{font-size:70px;opacity:.8;margin-top:28px}
mark{background:none;color:inherit;background-repeat:no-repeat;padding:0 6px;border-radius:6px;
  background-image:linear-gradient(transparent 52%,var(--hl) 52%,var(--hl) 94%,transparent 94%);background-size:0% 100%}
.it{display:flex;align-items:flex-start;gap:30px;margin-top:34px}
.bx{flex:none;width:70px;height:70px;border:5px solid __ENCRE__;border-radius:10px;margin-top:14px;position:relative}
.bx svg{position:absolute;left:-10px;top:-22px;width:90px;height:90px;overflow:visible}
.pi{position:relative;margin:20px 0 0 -20px;width:760px;min-height:560px;background:__POSTIT__;padding:70px 56px 50px;transform:rotate(-3deg);
  box-shadow:0 26px 40px rgba(80,60,0,.22);opacity:0}
.pi .hw{font-size:92px;line-height:1.18}
.pi .tp{position:absolute;left:250px;top:-26px;width:200px;height:56px;background:rgba(255,255,255,.55);transform:rotate(3deg)}
.btn{display:inline-block;margin-top:44px;padding:22px 46px;border:5px solid __ENCRE__;border-radius:26px 18px 30px 16px;font:700 80px Caveat;white-space:nowrap;opacity:0}
svg.doo{position:absolute;overflow:visible;pointer-events:none}
svg.doo path{fill:none;stroke:__ENCRE__;stroke-width:7;stroke-linecap:round;stroke-linejoin:round}
.caps{position:absolute;left:60px;right:60px;top:1418px;text-align:center;z-index:9}
.cap{display:none;background:#fff;border:4px solid __ENCRE__;border-radius:20px;padding:12px 30px;font:800 46px Inter;color:__ENCRE__;box-shadow:6px 6px 0 rgba(31,42,68,.18)}
.cap span.on{color:__ACC__}
.bar{position:absolute;left:46px;top:40px;height:8px;border-radius:4px;background:__ACC__;z-index:9}
</style></head><body>
<div class='cam' id='cam'><div class='page'><div class='marge'></div>__RINGS__
<div class='tape' style='right:70px;top:150px'></div>
<div class='hd'>@__HANDLE__</div>
__SCENES__
</div></div>
<div class='caps'>__CAPS__</div><div class='bar' id='bar'></div>
<script>
const EV=__EV__; const D=__D__; const SC=__SC__; const EL=__EL__;
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), $=i=>document.getElementById(i);
const back=x=>{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
window.render=function(t){
 const cam=$('cam');cam.style.transform=`rotate(${Math.sin(t/3.7)*.6}deg) scale(${1.015+.012*Math.sin(t/5.3)}) translate(${Math.sin(t/4.1)*6}px,${Math.cos(t/3.3)*5}px)`;
 SC.forEach((s,k)=>{const el=$('s'+k);const on=t>=s.a-.001&&(t<s.b+.55||k==SC.length-1);
   const kin=k==0?1:eo((t-s.a)/.5);el.style.zIndex=10+k;
   el.style.opacity=on?1:0;el.style.transform=`translateX(${(1-kin)*1000}px) rotate(${(1-kin)*4}deg)`;});
 for(const e of EL){const n=$(e.id);if(!n)continue;
   if(e.k=='ln'){const k=c((t-e.at)/e.d);n.style.clipPath=`inset(-20% ${100-100*k}% -20% 0)`;
     for(const m of n.querySelectorAll('mark'))m.style.backgroundSize=`${100*eo((t-e.at-e.d)/.45)}% 100%`;}
   else if(e.k=='chk'){const p=n.querySelector('path');const L=150;p.style.strokeDasharray=L;p.style.strokeDashoffset=L*(1-eo((t-e.at)/.35));}
   else if(e.k=='pi'){const k=back((t-e.at)/.45);n.style.opacity=c((t-e.at)/.12);n.style.transform=`rotate(-3deg) scale(${1.25-.25*k})`;}
   else if(e.k=='btn'){const k=back((t-e.at)/.4);n.style.opacity=c((t-e.at)/.1);n.style.transform=`scale(${.6+.4*k}) rotate(${e.r||0}deg)`;}
   else if(e.k=='doo'){const p=n.querySelector('path');const L=p.getTotalLength();p.style.strokeDasharray=L;p.style.strokeDashoffset=L*(1-eo((t-e.at)/e.d));}}
 $('bar').style.width=(c(t/D)*988)+'px';
 for(const cp of document.querySelectorAll('.cap')){const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   for(const w of cp.querySelectorAll('[data-w]'))w.className=(t>=+w.dataset.w)?'on':'';}
};render(0);
</script></body></html>"""


def carnet_page(spec, theme, starts, durs, caps, total):
    """Carnet à petits carreaux : le texte s'écrit à la main au rythme de la voix, coups de surligneur (**mot**),
    cases qui se cochent, post-it, boutons dessinés, doodles ; la page bouge doucement comme filmée au-dessus d'un bureau.
    Scènes (ordre libre) : hook {titre, sous?}, note {titre, lignes}, liste {titre, items}, postit {texte, titre?}, cta {titre, ctas}."""
    sc = spec["scenes"]; col = {"papier": "#fbf7ee", "encre": "#1f2a44", "bureau": "#d8ccb6", "grille": "rgba(120,150,190,.16)",
                                 "postit": "#ffe98a", "acc": "#e8553d", "surligneurs": ["#ffe45c", "#ffb3a7", "#a8e8cc"]} | spec.get("couleurs", {})
    HL = col["surligneurs"]; nh = [0]
    def hl(s):  # **mot** -> surligneur (couleurs en rotation)
        def rep(m):
            nh[0] += 1; return f"<mark style='--hl:{HL[(nh[0] - 1) % len(HL)]}'>{m.group(1)}</mark>"
        return re.sub(r"\*\*(.+?)\*\*", rep, K.esc(s))
    html, EL, ev = [], [], []
    for k, s in enumerate(sc):
        a, d = starts[k], durs[k]; ty = s["type"]; parts = []; seq = []   # seq : (id, kind, poids)
        def ln(txt, cls, ident):
            parts.append(f"<span class='hw {cls}'><span class='ln' id='{ident}'>{hl(txt)}</span></span>"); seq.append((ident, "ln", max(1, len(txt) / 18)))
        if ty in ("hook", "note", "liste", "cta") and s.get("titre"):
            for j, part in enumerate(s["titre"].split("<br>")):
                ln(part, "t1" if ty == "hook" else "t2", f"s{k}t{j}")
            parts.append(f"<svg class='doo' id='s{k}u' style='left:0;width:640px;height:40px;margin-top:-6px;position:relative;display:block' viewBox='0 0 640 40'>"
                         "<path d='M6 26 C 120 6, 260 34, 380 18 S 560 10, 630 22'/></svg>"); seq.append((f"s{k}u", "doo", .8))
        if ty == "hook" and s.get("sous"):
            ln(s["sous"], "sub", f"s{k}s")
        if ty == "note":
            for j, x in enumerate(s.get("lignes", [])): ln("→ " + x, "l", f"s{k}l{j}")
        if ty == "liste":
            for j, x in enumerate(s.get("items", [])):
                parts.append(f"<div class='it'><div class='bx' id='s{k}b{j}'><svg viewBox='0 0 90 90'><path d='M14 48 L36 70 L84 6' stroke='{col['acc']}' stroke-width='11' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg></div>"
                             f"<span class='hw l' style='margin-top:0'><span class='ln' id='s{k}i{j}'>{hl(x)}</span></span></div>")
                seq.append((f"s{k}i{j}", "ln", max(1, len(x) / 18))); seq.append((f"s{k}b{j}", "chk", .35))
        if ty == "postit":
            if s.get("titre"): ln(s["titre"], "t2", f"s{k}t0")
            parts.append(f"<div class='pi' id='s{k}p'><div class='tp'></div><span class='hw'>{hl(s['texte']).replace(chr(10), '<br>')}</span></div>"); seq.append((f"s{k}p", "pi", 1.2))
        if ty == "cta":
            for j, x in enumerate(s.get("ctas", [])[:2]):
                parts.append(f"<div><span class='btn' id='s{k}c{j}' style='background:{HL[(j + 2) % len(HL)]}'>{K.esc(x)}</span></div>"); seq.append((f"s{k}c{j}", "btn", .6))
        # minutage : les éléments se répartissent sur la scène, au rythme de la voix
        tot = sum(w for _, _, w in seq) or 1; t0 = a + (0 if k == 0 else .5); span = max(1.0, d - (.9 if k < len(sc) - 1 else 1.4) - (t0 - a))
        for ident, kind, w in seq:
            dur = span * w / tot
            e = {"id": ident, "k": kind, "at": round(t0, 3), "d": round(max(.35, dur * .8) if not (k == 0 and ident == 's0t0') else .4, 3)}
            if kind == "btn": e["r"] = -2 if ident.endswith("0") else 2
            EL.append(e)
            ev.append({"k": {"ln": "line", "chk": "check", "pi": "pop", "btn": "pop", "doo": "line"}[kind], "at": round(t0, 3)})
            t0 += dur
        html.append(f"<div class='sc' id='s{k}'>{''.join(parts)}</div>")
    if sc and sc[-1]["type"] == "cta": ev.append({"k": "sparkle", "at": round(starts[-1] + durs[-1] - 1.2, 3)})
    cap_html = "".join(f"<span class='cap' data-a='{cc[0][1]:.3f}' data-b='{cn:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in cc) + "</span>"
                       for cc, cn in caps)
    rings = "".join(f"<div class='ring' style='left:{150 + 62 * i}px'></div>" for i in range(13))
    S = [{"a": starts[k], "b": starts[k] + durs[k]} for k in range(len(sc))]
    R = {"__FONTS__": K._font_faces(["Caveat", "Inter"]), "__BUREAU__": col["bureau"], "__PAPIER__": col["papier"], "__ENCRE__": col["encre"], "__GRILLE__": col["grille"],
         "__POSTIT__": col["postit"], "__ACC__": col["acc"], "__RINGS__": rings, "__HANDLE__": H.escape(spec.get("handle", "")), "__SCENES__": "".join(html),
         "__CAPS__": cap_html, "__EV__": json.dumps(ev), "__D__": str(total), "__SC__": json.dumps(S), "__EL__": json.dumps(EL)}
    page = CARNET_TPL
    for kk, v in R.items():
        page = page.replace(kk, v)
    return page


# ------------------------------------------------------------------ layout « interface » (PILOTE 23/10/2026, tous comptes)
INTERFACE_TPL = r"""<!doctype html><html><head><meta charset='utf-8'><style>__FONTS__
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;overflow:hidden;background:__FOND__;position:relative;font-family:Inter,sans-serif;color:__ENCRE__}
.blob{position:absolute;border-radius:50%;filter:blur(120px);opacity:.75}
.top{position:absolute;left:60px;right:60px;top:90px;display:flex;align-items:center;justify-content:space-between;z-index:30}
.hdl{font:700 34px Inter;color:__ENCRE__;opacity:.55}
.dots{display:flex;gap:10px}.dots i{display:block;width:16px;height:16px;border-radius:8px;background:rgba(27,27,34,.18)}.dots i.on{width:44px;background:__ACC__}
.num{font:800 34px Inter;font-variant-numeric:tabular-nums;opacity:.6}
.sc{position:absolute;left:60px;right:110px;top:190px;height:1150px;display:flex;flex-direction:column;justify-content:center;gap:46px;opacity:0}
.ti{font:900 92px/1.04 Inter;letter-spacing:-3px;opacity:0}
.ti.big{font-size:118px;letter-spacing:-4px}
.ti em,.cta em{font-style:normal;color:__ACC__}
.chip{align-self:flex-start;background:#fff;border-radius:999px;padding:18px 34px;font:800 44px Inter;box-shadow:0 14px 34px rgba(80,60,120,.16);opacity:0}
.chip b{color:__ACC__}
.card{background:#fff;border-radius:44px;padding:40px 46px;box-shadow:0 34px 80px rgba(80,60,120,.20);opacity:0}
.ch{display:flex;align-items:center;gap:20px;margin-bottom:14px}.ch i{width:30px;height:30px;border-radius:15px;background:__ACC__}
.ch b{font:800 48px Inter}.ch small{font:500 30px Inter;opacity:.45;margin-left:auto}
.row{display:flex;align-items:center;gap:24px;padding:26px 0;border-top:2px solid #f0edf3;font:700 44px Inter;--k:0}
.row .lb{flex:1}
.who{position:relative;width:120px;height:40px;font:700 30px Inter;text-align:right}
.who em{position:absolute;right:0;top:4px;font-style:normal}.who .w0{opacity:calc(1 - var(--k));color:#9a96a3}.who .w1{opacity:var(--k);color:__ACC__}
.tg{position:relative;flex:none;width:100px;height:58px;border-radius:29px;background:#dcd7e3;overflow:hidden}
.tg .on{position:absolute;inset:0;background:__ACC__;opacity:var(--k)}
.tg .kn{position:absolute;left:6px;top:6px;width:46px;height:46px;border-radius:23px;background:#fff;box-shadow:0 3px 8px rgba(0,0,0,.2);transform:translateX(calc(var(--k)*42px))}
.chat{display:flex;flex-direction:column;gap:24px}
.bub{max-width:84%;padding:26px 34px;border-radius:36px;font:600 42px/1.3 Inter;opacity:0;white-space:pre-line}
.bub.moi{align-self:flex-end;background:__ACC__;color:#fff;border-bottom-right-radius:10px}
.bub.ia{align-self:flex-start;background:#f2eff6;border-bottom-left-radius:10px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:26px}
.tile{height:230px;border-radius:30px;color:#fff;font:900 50px/1.05 Inter;display:flex;align-items:center;justify-content:center;text-align:center;padding:20px;text-transform:uppercase;opacity:0;box-shadow:0 14px 30px rgba(0,0,0,.12)}
.cnt{display:flex;align-items:center;gap:40px;margin:10px 0 18px}
.ring{position:relative;width:230px;height:230px;flex:none}.ring svg{position:absolute;inset:0;transform:rotate(-90deg)}
.ring .n{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:900 100px Inter;font-variant-numeric:tabular-nums}
.cl{font:800 50px/1.15 Inter}
.tag{flex:none;color:__ACC__;font:800 40px Inter;min-width:80px}
.lrow{opacity:0}
.cta{display:flex;flex-direction:column;gap:34px;align-items:flex-start}
.btn{padding:34px 54px;border-radius:999px;font:800 58px Inter;white-space:nowrap;opacity:0;box-shadow:0 18px 40px rgba(80,60,120,.18)}
.btn.b0{background:#fff;border:5px solid __ENCRE__}.btn.b1{background:__ACC__;color:#fff}
.nt{display:flex;gap:26px;align-items:center;background:rgba(255,255,255,.92);border-radius:36px;padding:30px 36px;box-shadow:0 24px 60px rgba(80,60,120,.18);opacity:0}
.nt .ic{flex:none;width:96px;height:96px;border-radius:24px;background:__ACC__;display:flex;align-items:center;justify-content:center;font-size:56px}
.nt b{display:block;font:800 34px Inter;opacity:.5;margin-bottom:6px}.nt span{font:700 44px/1.2 Inter}
.caps{position:absolute;left:60px;right:60px;top:1370px;text-align:center;z-index:40}
.cap{display:none;background:#fff;border-radius:22px;padding:14px 32px;font:800 52px Inter;color:__ENCRE__;box-shadow:0 10px 30px rgba(80,60,120,.18)}
.cap span.on{color:__ACC__}
</style></head><body>
__BLOBS__
<div class='top'><span class='hdl'>@__HANDLE__</span><span class='dots' id='dots'>__DOTS__</span><span class='num' id='num'></span></div>
__SCENES__
<div class='caps'>__CAPS__</div>
<script>
const EV=__EV__; const D=__D__; const SC=__SC__; const EL=__EL__; const BL=__BL__;
const c=x=>Math.max(0,Math.min(1,x)), eo=x=>1-Math.pow(1-c(x),3), $=i=>document.getElementById(i);
const back=x=>{x=c(x);const s=1.7;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const RC=2*Math.PI*100;
window.render=function(t){
 BL.forEach((b,i)=>{$('bl'+i).style.transform=`translate(${Math.sin(t/b.p+i)*b.a}px,${Math.cos(t/(b.p*1.3)+i*2)*b.a}px)`;});
 let cur=0;
 SC.forEach((s,k)=>{const el=$('s'+k);const last=k==SC.length-1;if(t>=s.a)cur=k;
   const kin=k==0?1:eo((t-s.a)/.4), kout=last?0:c((t-s.b)/.25);
   el.style.opacity=(t>=s.a-.001&&(t<s.b+.25||last))?1-kout:0;
   el.style.transform=`translateY(${(1-kin)*90-kout*70}px) scale(${.95+.05*kin})`;});
 $('num').textContent=String(cur+1).padStart(2,'0')+' / '+String(SC.length).padStart(2,'0');
 document.querySelectorAll('#dots i').forEach((d,k)=>d.className=k==cur?'on':'');
 for(const e of EL){const n=$(e.id);if(!n)continue;const p=(t-e.at)/e.d;
   if(e.k=='pop'){n.style.opacity=c(p*4);n.style.transform=`scale(${.7+.3*back(p)})`;}
   else if(e.k=='rise'){const k=eo(p);n.style.opacity=k;n.style.transform=`translateY(${(1-k)*50}px)`;}
   else if(e.k=='row'){const k=eo(p);n.style.opacity=k;n.style.transform=`translateX(${(1-k)*-60}px)`;}
   else if(e.k=='tog'){n.style.setProperty('--k',eo(p));}
   else if(e.k=='type'){n.style.opacity=t>=e.at?1:0;const f=n.dataset.full;n.textContent=f.slice(0,Math.round(f.length*c(p)));}
   else if(e.k=='count'){const k=eo(p);n.querySelector('.n').textContent=Math.round(e.v*k);n.querySelector('circle.fg').style.strokeDashoffset=RC*(1-k);}}
 for(const cp of document.querySelectorAll('.cap')){const a=+cp.dataset.a,b=+cp.dataset.b;cp.style.display=(t>=a&&t<b)?'inline-block':'none';
   const ws=[...cp.querySelectorAll('[data-w]')];ws.forEach((w,i)=>{const nx=ws[i+1];w.className=(t>=+w.dataset.w&&(!nx||t<+nx.dataset.w))?'on':'';});}
};render(0);
</script></body></html>"""


def interface_page(spec, theme, starts, durs, caps, total):
    """Interfaces d'appli animées sur fond pastel (style « outil IA ») : une carte blanche par scène, un seul accent.
    Scènes (ordre libre), toutes avec `titre` optionnel (**mot** = accent) :
    hook {titre, sous?} ; toggles {carte, items: [libellé | [libellé, false]]} (Toi -> IA, false = reste « Toi ») ;
    chat {messages: [["moi"|"ia", texte]]} ; grille {cartes: [4 textes]} ; compteur {valeur, label, lignes: [[tag, texte]]} ; cta {ctas}."""
    sc = spec["scenes"]; col = {"fond": "#f4eff8", "encre": "#1b1b22", "acc": "#ff5a36", "tuiles": ["#ff5a36", "#3b5bdb", "#f2a516", "#1f9d6e"],
                                 "blobs": ["#cdb9ff", "#ffc7a6", "#ffb6cf"], "de": "Toi", "a": "Claude"} | spec.get("couleurs", {})
    html, EL, ev = [], [], []
    for k, s in enumerate(sc):
        a, d = starts[k], durs[k]; ty = s["type"]; parts = []; seq = []   # seq : (id, kind, poids, extra)
        if s.get("titre"):
            parts.append(f"<div class='ti{' big' if ty == 'hook' else ''}' id='s{k}ti'>{rich(s['titre'])}</div>"); seq.append((f"s{k}ti", "rise", .5, {}))
        if ty == "hook" and s.get("sous"):
            parts.append(f"<div class='chip' id='s{k}so'>{rich(s['sous']).replace('<em>', '<b>').replace('</em>', '</b>')}</div>"); seq.append((f"s{k}so", "pop", .6, {}))
        if ty == "hook" and s.get("notif"):  # notification façon téléphone : [icône, appli, texte]
            ic, app, tx = (list(s["notif"]) + ["", "", ""])[:3]
            parts.append(f"<div class='nt' id='s{k}nt'><div class='ic'>{K.esc(ic)}</div><div><b>{K.esc(app)}</b><span>{K.esc(tx)}</span></div></div>"); seq.append((f"s{k}nt", "pop", .7, {}))
        if ty == "toggles":
            rows = []
            for j, it in enumerate(s.get("items", [])):
                lb, flip = (it, True) if isinstance(it, str) else (it[0], it[1] if len(it) > 1 else True)
                rows.append(f"<div class='row' id='s{k}r{j}'><span class='lb'>{K.esc(lb)}</span><span class='who'><em class='w0'>{K.esc(col['de'])}</em>"
                            f"<em class='w1'>{K.esc(col['a'])}</em></span><span class='tg'><span class='on'></span><span class='kn'></span></span></div>")
                seq.append((f"s{k}r{j}", "tog" if flip else "wait", .8, {}))
            parts.append(f"<div class='card' id='s{k}c'><div class='ch'><i></i><b>{K.esc(s.get('carte', ''))}</b><small>{K.esc(s.get('carte_sous', ''))}</small></div>{''.join(rows)}</div>")
            seq.insert(len(seq) - len(rows), (f"s{k}c", "pop", .5, {}))
        if ty == "chat":
            bubs = []
            for j, (who, txt) in enumerate(s.get("messages", [])):
                bubs.append(f"<div class='bub {'moi' if who == 'moi' else 'ia'}' id='s{k}m{j}' data-full='{H.escape(txt, quote=True)}'></div>")
                seq.append((f"s{k}m{j}", "type", max(.8, len(txt) / 30), {"text": txt}))
            parts.append(f"<div class='card chat' id='s{k}c'>{''.join(bubs)}</div>"); seq.insert(len(seq) - len(bubs), (f"s{k}c", "pop", .4, {}))
        if ty == "grille":
            tl = "".join(f"<div class='tile' id='s{k}g{j}' style='background:{col['tuiles'][j % len(col['tuiles'])]}'>{K.esc(x)}</div>" for j, x in enumerate(s.get("cartes", [])))
            parts.append(f"<div class='grid'>{tl}</div>"); seq += [(f"s{k}g{j}", "pop", .7, {}) for j in range(len(s.get("cartes", [])))]
        if ty == "compteur":
            v = int(s.get("valeur", 0))
            rows = "".join(f"<div class='row lrow' id='s{k}l{j}'><span class='tag'>{K.esc(tg)}</span><span class='lb'>{K.esc(tx)}</span></div>" for j, (tg, tx) in enumerate(s.get("lignes", [])))
            parts.append(f"<div class='card' id='s{k}c'><div class='cnt' id='s{k}n'><div class='ring'><svg viewBox='0 0 230 230'><circle cx='115' cy='115' r='100' fill='none' stroke='#efeaf4' stroke-width='22'/>"
                         f"<circle class='fg' cx='115' cy='115' r='100' fill='none' stroke='{col['acc']}' stroke-width='22' stroke-linecap='round' stroke-dasharray='628.3' stroke-dashoffset='628.3'/></svg>"
                         f"<div class='n'>0</div></div><div class='cl'>{K.esc(s.get('label', ''))}</div></div>{rows}</div>")
            seq += [(f"s{k}c", "pop", .4, {}), (f"s{k}n", "count", 1.4, {"v": v})] + [(f"s{k}l{j}", "row", .7, {}) for j in range(len(s.get("lignes", [])))]
        if ty == "cta":
            bt = "".join(f"<span class='btn b{j}' id='s{k}b{j}'>{K.esc(x)}</span>" for j, x in enumerate(s.get("ctas", [])[:2]))
            parts.append(f"<div class='cta'>{bt}</div>"); seq += [(f"s{k}b{j}", "pop", .7, {}) for j in range(len(s.get("ctas", [])[:2]))]
        # minutage : les éléments se répartissent sur la voix de la scène (un changement à l'écran toutes les 1 à 2 s)
        tot = sum(w for _, _, w, _ in seq) or 1; t0 = a + (0 if k == 0 else .35); span = max(1.0, d - (.9 if k < len(sc) - 1 else 1.4) - (t0 - a))
        for ident, kind, w, x in seq:
            dur = span * w / tot
            e = {"id": ident, "k": kind, "at": round(t0, 3), "d": round(.35 if kind in ("rise", "pop", "row") else max(.4, dur * .85), 3)}
            if kind == "count": e["v"] = x["v"]
            if kind != "wait": EL.append(e)
            sfx = {"rise": "whoosh", "pop": "pop", "row": "line", "tog": "click", "count": "beep"}.get(kind)
            if kind == "type": ev.append({"k": "type", "at": round(t0, 3), "end": round(t0 + e["d"], 3), "text": x["text"]})
            elif kind == "count": ev.append({"k": "beep", "at": round(t0 + e["d"], 3)})
            elif sfx and not (k == 0 and kind == "rise"): ev.append({"k": sfx, "at": round(t0, 3)})
            t0 += dur
        html.append(f"<div class='sc' id='s{k}'>{''.join(parts)}</div>")
    if sc and sc[-1]["type"] == "cta": ev.append({"k": "sparkle", "at": round(starts[-1] + durs[-1] - 1.2, 3)})
    cap_html = "".join(f"<span class='cap' data-a='{cc[0][1]:.3f}' data-b='{cn:.3f}'>" + " ".join(f"<span data-w='{t:.3f}'>{H.escape(w)}</span>" for w, t in cc) + "</span>"
                       for cc, cn in caps)
    pos = [(-180, 160, 760), (520, 700, 700), (60, 1300, 800)]
    blobs = "".join(f"<div class='blob' id='bl{i}' style='left:{x}px;top:{y}px;width:{w}px;height:{w}px;background:{col['blobs'][i % len(col['blobs'])]}'></div>" for i, (x, y, w) in enumerate(pos))
    S = [{"a": starts[k], "b": starts[k] + durs[k]} for k in range(len(sc))]
    R = {"__FONTS__": K._font_faces(["Inter"]), "__FOND__": col["fond"], "__ENCRE__": col["encre"], "__ACC__": col["acc"], "__BLOBS__": blobs,
         "__DOTS__": "<i></i>" * len(sc), "__HANDLE__": H.escape(spec.get("handle", "")), "__SCENES__": "".join(html), "__CAPS__": cap_html,
         "__EV__": json.dumps(ev), "__D__": str(total), "__SC__": json.dumps(S), "__EL__": json.dumps(EL), "__BL__": json.dumps([{"p": 3.1 + i, "a": 70 + 20 * i} for i in range(len(pos))])}
    page = INTERFACE_TPL
    for kk, v in R.items():
        page = page.replace(kk, v)
    return page


LAYOUTS = {"interface": interface_page, "carnet": carnet_page,"boucle": boucle_page, "malin": malin_page, "claudeflow": claudeflow_page, "manifeste3d": manifeste3d_page, "messages": messages_page, "terminal": terminal_page, "cheatsheet": cheatsheet_page, "iceberg": iceberg_page, "sportmotion": sportmotion_page, "nightchat": nightchat_page, "notion": notion_page}

# ------------------------------------------------------------------ rendu
def sfx_track(path, total, events, starts):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, lfilter
    SR = 48000; n = int(SR * (total + 1)); out = np.zeros(n); rng = np.random.default_rng(3)
    def put(sig, t0, g=1.0):
        i = int(max(0, t0) * SR); j = min(n, i + len(sig)); out[i:j] += sig[: j - i] * g
    tp = np.arange(int(0.12 * SR)) / SR
    pop = np.sin(2 * np.pi * (700 + 500 * np.exp(-tp * 40)) * tp) * np.exp(-tp * 40) * 0.35
    tk = np.arange(int(0.025 * SR)) / SR
    b, a = butter(2, 2500 / (SR / 2), "high"); tick = lfilter(b, a, rng.standard_normal(len(tk))) * np.exp(-tk * 260) * 0.12
    tw = np.arange(int(0.45 * SR)) / SR
    b2, a2 = butter(2, [500 / (SR / 2), 5000 / (SR / 2)], "band")
    whoosh = lfilter(b2, a2, rng.standard_normal(len(tw))) * np.sin(np.pi * tw / tw[-1]) ** 2 * 0.35
    th = np.arange(int(1.2 * SR)) / SR
    chime = sum(np.sin(2 * np.pi * f * th) * np.exp(-th * 3) for f in (880, 1320, 1760)) * 0.06
    for s in starts[1:]: put(whoosh, s - 0.2)
    for e in events:
        if e["k"] in ("pop", "pill", "check"): put(pop, e.get("tick", e["at"]))
        if e["k"] == "line": put(pop, e["at"], 0.45)
        if e["k"] == "type":
            L = len(e["text"]); step = (e["end"] - e["at"]) / max(1, L)
            for q in range(0, L, 2): put(tick, e["at"] + q * step, 0.8)
        if e["k"] == "heart": put(chime, e["at"] + 1.0)
        if e["k"] == "sparkle": put(chime, e["at"], 0.8)
        if e["k"] == "notif":
            tn = np.arange(int(.35 * SR)) / SR
            n1 = np.sin(2 * np.pi * 1175 * tn) * np.exp(-tn * 9) * .25
            put(n1, e["at"]); put(np.sin(2 * np.pi * 1568 * tn) * np.exp(-tn * 9) * .25, e["at"] + .14)
        if e["k"] == "glitch":
            tg = np.arange(int(.22 * SR)) / SR
            put(np.sign(np.sin(2 * np.pi * 180 * tg)) * (rng.random(len(tg)) > .5) * .18 * np.exp(-tg * 6), e["at"])
        if e["k"] == "beep":
            tb = np.arange(int(.12 * SR)) / SR
            put(np.sin(2 * np.pi * 1320 * tb) * .25 * np.minimum(1, (len(tb) - np.arange(len(tb))) / 300), e["at"])
        if e["k"] == "whistle":
            tw2 = np.arange(int(.6 * SR)) / SR
            put(np.sin(2 * np.pi * (2900 + 120 * np.sin(2 * np.pi * 32 * tw2)) * tw2) * .18 * np.minimum(1, (len(tw2) - np.arange(len(tw2))) / 2000), e["at"])
        if e["k"] == "whoosh": put(whoosh, e["at"] - 0.05)
        if e["k"] == "click": put(tick * 3, e["at"]); put(pop, e["at"] + 0.03)
        if e["k"] == "impact":
            ti = np.arange(int(.5 * SR)) / SR
            put(np.sin(2 * np.pi * (70 + 80 * np.exp(-ti * 18)) * ti) * np.exp(-ti * 7) * .6, e["at"])
        if e["k"] == "input":
            L = len(e["text"]); step = (e["end"] - e["at"]) / max(1, L)
            for q in range(0, L, 2): put(tick, e["at"] + q * step, 0.8)
            put(whoosh, e["send"] - 0.05, 0.6)
        if e["k"] == "typeerase":
            L = len(e["text"]); step = (e["full"] - e["at"]) / max(1, L)
            for q in range(0, L, 2): put(tick, e["at"] + q * step, 0.7)
    out = np.clip(out, -1, 1)
    wavfile.write(path, SR, (np.stack([out, out], 1) * 32767).astype(np.int16))

MOTS_PAR_S = 2.6  # débit de Brian / Alice, pour estimer les durées quand les voix n'existent pas encore

def prepare(spec_path, tmp, estime=False):
    """Voix -> durées des scènes -> page HTML. estime=True : sans fichiers vo_<k>.mp3, durées estimées
    depuis le nombre de mots (pour verifier/auditer AVANT de payer les voix)."""
    spec = json.load(open(spec_path, encoding="utf-8")); vo_dir = os.path.dirname(os.path.abspath(spec_path))
    K.load_theme(spec_path, spec); theme = K.THEME.get("raw", {})
    if spec.get("layout") == "boucle":  # pilote : durée = un pas par mot + tenue de la phrase complète
        for s in spec["scenes"]:
            s.setdefault("vo", "")
            s.setdefault("dur", round(len(s["texte"].split()) * float(spec.get("pas", 0.3)) + float(spec.get("tenue", 1.2)), 2))
    vspec = {"scenes": [{"type": "text", "vo": s["vo"], "dur": s.get("dur", 3.0)} for s in spec["scenes"]]}
    if estime and any(s["vo"] for s in vspec["scenes"]):
        voice, t = [], 0.0
        for s in vspec["scenes"]:
            d = len(s["vo"].split()) / MOTS_PAR_S
            s["dur"] = round(max(float(s["dur"]), d + 0.9), 2); voice.append((t + 0.25, d)); t += s["dur"]
    else:
        voice = K.prepare_voice(vspec, vo_dir, tmp)
    durs = [float(s["dur"]) for s in vspec["scenes"]]
    starts = [sum(durs[:k]) for k in range(len(durs))]; total = sum(durs)
    words = []
    for (t0, w), s in zip(voice, spec["scenes"]):
        words += words_timed(s["vo"], t0, w if estime else K._dur(w))
    ch = caption_chunks(words)
    caps = [(c, (ch[i + 1][0][1] if i + 1 < len(ch) else total)) for i, c in enumerate(ch)]
    page = LAYOUTS[spec.get("layout", theme.get("layout"))](spec, theme, starts, durs, caps, total)
    hp = os.path.join(tmp, "m.html"); open(hp, "w", encoding="utf-8").write(page)
    return spec, page, hp, starts, durs, total, ([] if estime else voice)

def build(spec_path, out):
    tmp = tempfile.mkdtemp()
    spec, page, hp, starts, durs, total, voice = prepare(spec_path, tmp)
    try:  # audit automatique (texte trop petit, hors zones sûres, hook tardif) : avertit sans bloquer
        import audit as A
        A.afficher(A.auditer(hp, starts, total), spec_path)
    except Exception as e:
        print("audit non réalisé :", e)
    fr = os.path.join(tmp, "fr"); os.makedirs(fr)
    asyncio.run(K._frames(hp, fr, total))
    silent = os.path.join(tmp, "v.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{fr}/f_%04d.jpg", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", silent], check=True)
    music = os.path.join(tmp, "mu.wav"); K.make_music(music, total + 1, int(spec.get("music_seed", 5)))
    evs = json.loads(re.search(r"const EV=(\[.*?\]); const D", page, re.S).group(1))
    sfx = os.path.join(tmp, "sfx.wav"); sfx_track(sfx, total, evs, starts)
    inputs = ["-i", silent, "-i", music, "-i", sfx] + sum((["-i", w] for _, w in voice), [])
    dl = "".join(f"[{i+3}]adelay={int(t*1000)}|{int(t*1000)}[v{i}];" for i, (t, _) in enumerate(voice))
    vs = "".join(f"[v{i}]" for i in range(len(voice)))
    D = total
    vm = 0 if spec.get("sans_musique") else 1   # sans_musique : voix + bruitages seuls, pour ajouter un son tendance dans l'app
    if voice:
        fc = (dl + f"{vs}amix=inputs={len(voice)}:normalize=0:duration=longest,apad=whole_dur={D+4},loudnorm=I=-15:TP=-1.5,atrim=0:{D}[vo];"
              f"[vo]asplit=2[voa][sc];[1]apad=whole_dur={D+1},atrim=0:{D},afade=t=out:st={D-1.5}:d=1.5,volume={0.25*vm}[m];"
              f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];[2]atrim=0:{D},volume=0.9[fx];"
              f"[voa][md][fx]amix=inputs=3:normalize=0:duration=longest,alimiter=limit=0.95,apad=whole_dur={D},atrim=0:{D}[a]")
    else:  # reel sans voix (layout boucle) : musique plus présente + bruitages, pas de fondu final (la boucle doit raccorder)
        fc = (f"[1]apad=whole_dur={D+1},atrim=0:{D},volume={0.45*vm}[m];[2]atrim=0:{D},volume=0.6[fx];"
              f"[m][fx]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-16:TP=-1.5,alimiter=limit=0.95,apad=whole_dur={D},atrim=0:{D}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)
    return total

if __name__ == "__main__":
    print("duration", build(sys.argv[1], sys.argv[2]))
