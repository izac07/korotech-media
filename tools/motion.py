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

LAYOUTS = {"messages": messages_page, "terminal": terminal_page, "cheatsheet": cheatsheet_page}

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
