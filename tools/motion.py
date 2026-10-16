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

LAYOUTS = {"messages": messages_page}

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
        if e["k"] in ("pop", "pill"): put(pop, e["at"])
        if e["k"] == "heart": put(chime, e["at"] + 1.0)
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
    K.load_theme(spec_path, spec); theme = K.THEME["raw"]
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
