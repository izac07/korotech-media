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
            inner = (f"{pages}{parts}<div class='three' id='three'>3</div><div class='h1' id='h1'>IA <span class='gr'>GRATUITES</span></div>"
                     f"<div class='h2' id='h2'>que presque personne n'utilise 👀</div>")
            ev += [{"k": "whoosh", "at": a + 0.22}, {"k": "impact", "at": a + 0.5}, {"k": "sparkle", "at": a + 0.85}]
        elif ty == "pills":
            pills = "".join(f"<div class='pill' id='pl{k}_{j}'>{H.escape(p)}</div>" for j, p in enumerate(s["pills"]))
            wave = "".join(f"<i id='wv{j}'></i>" for j in range(14))
            inner = (f"<div class='card' id='cd{k}'><div class='hd'><span class='gr num'>{s['num']}</span> · {H.escape(s['name'])}</div>"
                     f"<div class='drop'><div class='pdf' id='pdf{k}'><span>PDF</span>{H.escape(s['file'])}</div></div></div>"
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
    for(let i=0;i<46;i++){{const p=$('pt'+i);const v=(u-.45);const ang=rnd(i)*6.283,sp=300+rnd(i+9)*900;
      if(v<0||v>1.2){{p.style.opacity=0;continue;}}p.style.opacity=1-v/1.2;p.style.left=(700+Math.cos(ang)*sp*eo(v/1.2))+'px';p.style.top=(800+Math.sin(ang)*sp*eo(v/1.2))+'px';}}
    const th=$('three');const k3=back((u-.5)/.5);th.style.opacity=c((u-.5)/.1);th.style.transform=`scale(${{.2+.8*k3+.02*Math.sin(u*3)}})`;
    pop($('h1'),.8,u,.6,0,50);pop($('h2'),1.2,u,.8,0,40);
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
  if(s.ty==='cta'){{for(let j=0;j<3;j++){{const m=$('mi'+j);const kf=back((u-.2-.15*j)/.5);const sh=eo((u-1.8)/.35);
      m.style.opacity=c((u-.2-.15*j)/.1)*(1-sh);m.style.transform=`translateX(${{(j-1)*230*kf*(1-sh)}}px) rotate(${{(j-1)*14*kf*(1-sh)}}deg) scale(${{(.5+.5*kf)*(1-.7*sh)}})`;}}
    const bm=$('bm');const kb=back((u-2.0)/.5);bm.style.opacity=c((u-2.0)/.1);bm.style.transform=`scale(${{.3+.7*kb}})`;
    pop($('logo'),2.6,u,.8,0,30);const f=$('fol');const kf=back((u-2.9)/.4);f.style.transform=`scale(${{u>2.9?.5+.5*kf:0}})`;
    pop($('ct0'),3.2,u,.7,0,40);pop($('ct1'),3.6,u,.7,0,40);}}
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
    ov = []
    for k, s in enumerate(sc):
        a = starts[k]; ty = s["type"]
        if ty == "hook":
            ov.append(f"<div class='cmdl' id='hk'><span class='g'>$ </span><span id='hkt'></span><b class='cur'></b></div>")
            ev += [{"k": "type", "at": a + 0.0, "end": a + 0.55, "text": "./reveler --iceberg"}, {"k": "impact", "at": a + 0.65}]
        elif ty == "surface":
            pos = [(70, 300), (560, 500), (70, 700)]
            for j, (l, (x, y)) in enumerate(zip(s["labels"], pos)):
                ov.append(f"<div class='lab' id='lb{j}' style='left:{x}px;top:{y}px'>&gt; {H.escape(l)}<span class='faux' id='fx{j}'>[FAUX]</span></div>")
                ev += [{"k": "pop", "at": a + 0.6 + 0.9 * j}, {"k": "impact", "at": a + 1.15 + 0.9 * j}]
        elif ty == "process":
            for j in range(3):
                ov.append(f"<div class='blk' id='bk{j}'>[ÉTAPE {j+1}]</div>")
            ov.append("<div class='arr' id='ar0'>→</div><div class='arr' id='ar1'>→</div><div class='chaos' id='chaos'>C H A O S</div><div class='okp' id='okp'>✓ process clair</div>")
            ev += [{"k": "pop", "at": a + 0.5 + 0.3 * j} for j in range(3)] + [{"k": "impact", "at": a + 2.2}, {"k": "click", "at": a + 5.4}]
        elif ty == "logs":
            L = [("ERREUR 401 · API modifiée", RED, 0.5), ("CHAMP VIDE · formulaire", RED, 1.6), ("[ALERTE] → notification envoyée ✓", G, 3.0),
                 ("abonnements :", "#cfe", 4.4), ("  + outil 1", YEL, 4.9), ("  + outil 2", YEL, 5.4), ("  + outil 3…", YEL, 5.9)]
            for j, (txt, col, at) in enumerate(L):
                ov.append(f"<div class='log' id='lg{j}' data-at='{at}' style='top:{360 + 92 * j}px;color:{col}'>{'[x] ' if col == RED else ''}{H.escape(txt)}</div>")
                ev.append({"k": "impact" if col == RED else "pop", "at": a + at})
        elif ty == "cta":
            ov.append("<div class='task' id='task'>[ 1 TÂCHE RÉPÉTITIVE ] <span class='g'>✓</span></div>")
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
 <div class='wlab' id='wl1' style='top:420px'>CE QU'ON TE MONTRE</div>
 <div class='wlab' id='wl2' style='top:1180px;color:{G}'>CE QU'ON TE CACHE ▼</div>
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
 const hk=$('hk');hk.style.opacity=k==0&&u<1.0?1:0;$('hkt').textContent='./reveler --iceberg'.slice(0,Math.floor(c(u/.4)*19));
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
}

def sportmotion_page(spec, theme, starts, durs, caps, total):
    sc = spec["scenes"]; ev = []; RED = "#ff2d36"
    fonts = K._font_faces(["Anton"])
    S = [{"a": starts[k], "b": starts[k] + durs[k], "ty": s["type"], "ex": s.get("ex", [])} for k, s in enumerate(sc)]
    a0, a1, a2, a3, a4 = starts
    d2 = durs[2]
    ev += [{"k": "type", "at": a0, "end": a0 + 1.5, "text": "x" * 40}, {"k": "glitch", "at": a0 + 1.55}, {"k": "impact", "at": a0 + 1.7}]
    ev += [{"k": "glitch", "at": a1 + 0.1}, {"k": "glitch", "at": a1 + 3.2}, {"k": "impact", "at": a1 + durs[1] * 0.68}]
    exs = [a2 + 1.3 + (d2 - 1.6) / 5 * j for j in range(5)]
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
    def figsvg(id_):
        return (f"<svg class='fig' id='{id_}' viewBox='-20 -40 400 240'><g id='{id_}c' transform='translate(-6,0)' opacity='0'></g><g id='{id_}m' transform='translate(6,0)' opacity='0'></g>"
                f"<g id='{id_}w'></g><line x1='-20' y1='4' x2='380' y2='4' stroke='#444' stroke-width='4'/></svg>")
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
 <div class='big' id='h0' style='top:1000px'>STOP AUX <span class='r'>100 CRUNCHS</span></div>
 <div class='big' id='h1' style='top:1280px;font-size:90px'>⏱ 5 MIN À LA PLACE</div></div>
<div class='scn' id='s1'><div class='tag' id='tg1' style='background:{RED}'>ERREUR</div><div class='timer A' id='tm1' style='top:340px;color:#999'>00:00 / 20:00</div>{figsvg('f1')}
 <svg style='position:absolute;left:0;top:0' width='1080' height='1920'><circle id='nk' cx='340' cy='640' r='60' fill='none' stroke='{RED}' stroke-width='10' opacity='0'/></svg>
 <div class='myth' id='my1' style='top:1060px'>« FONDRE LE VENTRE »</div><div class='stamp' id='st1'>MYTHE</div>
 <div class='bt' id='bt1'>LONG · NUQUE ·<br><span class='r'>ZÉRO FONTE LOCALE</span></div></div>
<div class='scn' id='s2'><div class='tag' id='tg2' style='background:#fff;color:#0b0b0b'>SOLUTION</div><div class='timer A' id='tm2' style='top:300px;font-size:150px'>5:00</div>
 {''.join(f"<div class='card' id='cd{j}'><div class='idx'>{j+1}</div><div class='sec'>45 s</div>{figsvg('fx'+str(j)).replace('class=\'fig\'', 'class=\'fig\' style=\'left:20px;top:80px;width:800px;height:460px\'')}<div class='nm'>{H.escape(n)}</div></div>" for j, n in enumerate(sc[2]['ex']))}
 <div class='rest' id='rest'>REPOS 15 s</div><div class='dots'>{''.join(f"<i id='dt{j}'></i>" for j in range(5))}</div>
 <div class='bt' id='bt2'>45 s EFFORT / <span class='r'>15 s REPOS</span> × 5</div></div>
<div class='scn' id='s3'>{body_svg}
 <div class='zl' id='zl0' style='left:740px;top:560px'>AVANT</div><div class='zl' id='zl1' style='left:180px;top:560px'>CÔTÉS</div><div class='zl' id='zl2' style='left:740px;top:680px'>PROFOND</div>
 <div class='badge' id='bg0' style='top:960px;font-size:54px'>DOS NEUTRE</div><div class='badge' id='bg1' style='top:1090px;font-size:54px;background:#fff;color:#0b0b0b'>RESPIRE</div>
 <div class='badge' id='bg2' style='top:1220px;font-size:48px'>TROP DUR ? GENOUX AU SOL</div>
 <div class='big' id='t3' style='top:200px;font-size:84px'>TOUTE LA SANGLE,<br><span class='r'>PAS JUSTE LE HAUT</span></div></div>
<div class='scn' id='s4'><div class='timer A' id='tm4' style='top:260px;font-size:200px;color:{RED}'>5:00</div><div class='slash' id='sl4'></div><div class='tick' id='tk4'>{'ZÉRO SALLE · ZÉRO EXCUSE · ' * 6}</div>
 <div class='big' id='h4' style='top:560px;font-size:150px'>ON LE FAIT<br><span class='r'>CE SOIR ?</span></div>
 <div class='cl' id='c40' style='top:900px'>🔖 ENREGISTRE LE CIRCUIT</div><div class='cl' id='c41' style='top:1000px'>💬 T'AS TENU 5 MIN ?</div></div>
<div class='scanl' id='scl'></div><div class='flash' id='fl'></div>
<div class='capw'>{cap_html}</div><div class='bar' id='bar'></div>
<script>
const EV={json.dumps(ev, ensure_ascii=False)}; const D={total}; const SC={json.dumps(S, ensure_ascii=False)}; const P={json.dumps(POSES)};
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
 if(k==0){{const n=Math.min(100,Math.floor(Math.pow(c(u/1.5),1.6)*100));$('cnt0').textContent=n;
   const g=u>1.5&&u<1.85;drawFig('f0','crunch',.5+.5*Math.sin(u*(6+u*10)),g);$('f0').style.transform=g?`translateX(${{Math.sin(u*120)*16}}px)`:'none';
   slam($('x0'),1.7,u,2.4);$('h0').style.opacity=1;gl($('h0'),g,u);rise($('h1'),2.2,u);
   if(g)$('fl').style.opacity=.15;}}
 if(k==1){{document.body.style.filter='grayscale(1) contrast(1.1)';$('tg1').style.opacity=Math.floor(u*3)%2?1:.3;$('tg1').style.filter='none';
   const sec=Math.floor(u*9);$('tm1').textContent=String(Math.floor(sec/60)).padStart(2,'0')+':'+String(sec%60).padStart(2,'0')+' / 20:00';
   const g=(u>.1&&u<.35)||(u>3.2&&u<3.45);drawFig('f1','crunch',.5+.5*Math.sin(u*2.4),g,u>2.2?(.5+.5*Math.sin(u*8)):0);
   
   const ms=d*.68;$('my1').style.opacity=u>ms-.8?1:0;slam($('st1'),ms,u,2.6);rise($('bt1'),1.0,u);}}
 if(k==2){{const T0=1.3,step=(d-1.6)/5;slam($('tg2'),0,u,1.6);const rem=Math.max(0,300-Math.floor(c((u-T0)/(d-T0))*15));$('tm2').textContent=Math.floor(rem/60)+':'+String(rem%60).padStart(2,'0');
   let cur=-1;for(let j=0;j<5;j++)if(u>=T0+step*j)cur=j;
   for(let j=0;j<5;j++){{const cd=$('cd'+j);const on=j==cur;const kk=back((u-T0-step*j)/.3);cd.style.opacity=on?1:0;cd.style.transform=`translateX(${{(1-kk)*700}}px) rotate(${{(1-kk)*6}}deg)`;
     const pose=['planche','deadbug','lateral','climber','creuse'][j];const sp=pose=='climber'?5:2.2;drawFig('fx'+j,pose,.5+.5*Math.sin(u*sp),false);
     $('dt'+j).style.background=j<=cur?'{RED}':'transparent';}}
   const r=$('rest');let ro=0;for(let j=1;j<5;j++){{const x=u-(T0+step*j);if(x>-.35&&x<0)ro=1;}}r.style.opacity=ro;r.style.transform=`translateX(${{ro?0:-1200}}px)`;
   rise($('bt2'),.6,u);}}
 if(k==3){{rise($('t3'),.0,u);const zs=[['z0'],['z1a','z1b'],['z2']];
   for(let j=0;j<3;j++){{const on=u>=.5+.8*j;for(const id of zs[j])$(id).setAttribute('opacity',on?(.55+.35*Math.sin(u*5+j)):0);$('zl'+j).style.opacity=on?1:0;}}
   for(let j=0;j<3;j++){{const b=$('bg'+j);const kk=back((u-3.6-.7*j)/.45);b.style.opacity=u>=3.6+.7*j?1:0;b.style.transform=`translateY(${{(1-kk)*-300}}px) rotate(${{(j-1)*3}}deg)`;}}}}
 if(k==4){{const rem=Math.max(0,300-Math.floor(c((u-.1)/1.4)*300));$('tm4').textContent=Math.floor(rem/60)+':'+String(rem%60).padStart(2,'0');
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
            inner += f"<div class='ghost' id='gh{k}'><div class='gb'>Tu es dispo ?</div><div class='gv'>{H.escape(s['ghost'])}</div></div>"
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

LAYOUTS = {"messages": messages_page, "terminal": terminal_page, "cheatsheet": cheatsheet_page, "iceberg": iceberg_page, "sportmotion": sportmotion_page, "nightchat": nightchat_page}

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

def build(spec_path, out):
    spec = json.load(open(spec_path)); vo_dir = os.path.dirname(os.path.abspath(spec_path))
    K.load_theme(spec_path, spec); theme = K.THEME.get("raw", {})
    tmp = tempfile.mkdtemp()
    # voix -> durées des scènes (même logique que le moteur v1)
    vspec = {"scenes": [{"type": "text", "vo": s["vo"], "dur": s.get("dur", 3.0)} for s in spec["scenes"]]}
    voice = K.prepare_voice(vspec, vo_dir, tmp)
    durs = [float(s["dur"]) for s in vspec["scenes"]]
    starts = [sum(durs[:k]) for k in range(len(durs))]; total = sum(durs)
    words = []
    for (t0, w), s in zip(voice, spec["scenes"]):
        words += words_timed(s["vo"], t0, K._dur(w))
    ch = caption_chunks(words)
    caps = [(c, (ch[i + 1][0][1] if i + 1 < len(ch) else total)) for i, c in enumerate(ch)]
    page = LAYOUTS[spec.get("layout", theme.get("layout"))](spec, theme, starts, durs, caps, total)
    hp = os.path.join(tmp, "m.html"); open(hp, "w").write(page)
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
    fc = (dl + f"{vs}amix=inputs={len(voice)}:normalize=0:duration=longest,apad=whole_dur={D+4},loudnorm=I=-15:TP=-1.5,atrim=0:{D}[vo];"
          f"[vo]asplit=2[voa][sc];[1]apad=whole_dur={D+1},atrim=0:{D},afade=t=out:st={D-1.5}:d=1.5,volume=0.25[m];"
          f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];[2]atrim=0:{D},volume=0.9[fx];"
          f"[voa][md][fx]amix=inputs=3:normalize=0:duration=longest,alimiter=limit=0.95,apad=whole_dur={D},atrim=0:{D}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)
    return total

if __name__ == "__main__":
    print("duration", build(sys.argv[1], sys.argv[2]))
