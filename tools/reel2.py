#!/usr/bin/env python3
"""Korotech reel v2: word-synced animated captions, hook visible at frame 0, punchy pacing,
sound effects, Instagram safe zones, loop-friendly ending.

Usage: python3 tools/reel2.py posts/<dossier>/spec.json out.mp4
Same spec as v1 (scenes with "vo"); optional per-scene "cap" overrides caption text
(use **mot** to highlight a word, default: the vo text with no highlight).
"""
import asyncio, json, os, re, sys, subprocess, tempfile, shutil, html as H
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from korotech import BRAND_CSS, esc, rich, prepare_voice, make_music, _frames, DEFAULT_DUR

CSS = """
body{width:1080px;height:1920px}
.glow1{width:1300px;height:1300px;left:-460px;top:-460px}.glow2{width:1300px;height:1300px;right:-520px;bottom:-420px}
.top{position:absolute;top:120px;left:80px;right:180px;font-size:32px}.brand .inf{font-size:60px}
.bar{position:absolute;left:0;top:0;height:12px;background:linear-gradient(90deg,#5b2eff,#e23cc8)}
.sc{position:absolute;inset:0;opacity:0}
.hookwrap{position:absolute;left:80px;right:160px;top:470px}
.hook{font-family:Poppins;font-weight:700;font-size:124px;line-height:1.02;text-transform:uppercase}
.head{position:absolute;left:80px;right:160px;top:300px}
.lbl2{font-size:34px;font-weight:700;letter-spacing:4px;text-transform:uppercase;color:#ff7ae3}
.ttl{font-family:Poppins;font-weight:700;font-size:62px;line-height:1.08;margin-top:14px;color:#e9e4ff}
.capzone{position:absolute;left:80px;right:160px;top:760px;height:560px;display:flex;align-items:center}
.cap{font-family:Poppins;font-weight:700;font-size:104px;line-height:1.08;text-transform:uppercase;opacity:0;position:absolute;left:0;right:0}
.cap .k{background:linear-gradient(90deg,#7b5cff,#ff4fd8);-webkit-background-clip:text;color:transparent}
.cap .k2{color:#ffd84d}
.ctawrap{position:absolute;left:80px;right:160px;top:430px}
.ctat{font-family:Poppins;font-weight:700;font-size:100px;line-height:1.06}
.cta{display:flex;gap:28px;align-items:center;font-size:52px;font-weight:600;line-height:1.25;margin-top:44px;opacity:0}
.ico{width:108px;height:108px;border-radius:28px;font-size:54px}
.flash{position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none}
"""

def words_with_times(text, t0, dur):
    """Split spoken text into caption chunks (<=3 words, break on punctuation) with start/end times
    proportional to characters, with extra weight on pauses."""
    toks = []
    for tk in text.split():
        if toks and re.fullmatch(r"[,;:.!?…»«-]+", tk): toks[-1] += tk   # glue lone punctuation to previous word
        else: toks.append(tk)
    w = []
    for tk in toks:
        wt = len(tk) + 2
        if re.search(r"[,;:]$", tk): wt += 5
        if re.search(r"[.!?…]$", tk): wt += 9
        w.append(wt)
    tot = sum(w) or 1
    chunks, cur, cw = [], [], 0
    for tk, wt in zip(toks, w):
        cur.append(tk); cw += wt
        if len(cur) >= 3 or re.search(r"[,;:.!?…]$", tk):
            chunks.append((cur, cw)); cur, cw = [], 0
    if cur: chunks.append((cur, cw))
    out, t = [], t0
    for c, cw in chunks:
        d = dur * cw / tot
        out.append((" ".join(c), t, t + d)); t += d
    return out

def mark(chunk, keys):
    s = H.escape(chunk.rstrip(",;:"))
    for k in keys:
        s = re.sub(r"(?i)\b(" + re.escape(H.escape(k)) + r")\b", r"<span class='k'>\1</span>", s)
    return s

def build(spec, out, vo_dir):
    tmp = tempfile.mkdtemp()
    voice = prepare_voice(spec, vo_dir, tmp)   # adjusts scene durations to the voice
    if not voice:
        raise SystemExit("reel2 attend une voix off (champ vo + fichiers vo_k.mp3)")
    vstart = {}
    vi = 0
    t = 0.0
    scenes = spec["scenes"]
    starts = []
    for k, s in enumerate(scenes):
        d = float(s.get("dur", DEFAULT_DUR[s["type"]]))
        starts.append((t, t + d))
        if s.get("vo"):
            st, w = voice[vi]; vi += 1
            vd = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", w], capture_output=True, text=True).stdout)
            vstart[k] = (st, vd)
        t += d
    total = t
    parts, caps, pops = [], [], []
    for k, s in enumerate(scenes):
        a, b = starts[k]
        keys = [m for m in re.findall(r"\*\*(.+?)\*\*", s.get("cap", ""))]
        if s["type"] == "hook":
            lines = "".join(
                f"<div class='hook{' grad' if ln.startswith('**') else ''}' data-pop='{0 if k == 0 else a:.2f}'>{esc(ln.strip('*'))}</div>"
                for ln in s["lines"])
            parts.append(f"<div class='sc' data-a='{a:.2f}' data-b='{b:.2f}' data-hard='1'><div class='hookwrap'>{lines}</div></div>")
            continue
        if s["type"] == "cta":
            rows = "".join(f"<div class='cta' data-pop='{a + 0.5 + j * 0.6:.2f}'><div class='ico'>{i}</div><div>{rich(x)}</div></div>" for j, (i, x) in enumerate(s["ctas"]))
            parts.append(f"<div class='sc' data-a='{a:.2f}' data-b='{b:.2f}'><div class='ctawrap'><div class='ctat' data-pop='{a:.2f}'>{rich(s['title'])}</div>{rows}</div></div>")
            pops += [a + 0.5 + j * 0.6 for j in range(len(s["ctas"]))]
            continue
        head = (f"<div class='head'><div class='lbl2'>{H.escape(s.get('label', ''))}</div>"
                f"<div class='ttl'>{rich(s.get('title', ''))}</div></div>")
        capdivs = ""
        if k in vstart:
            st, vd = vstart[k]
            text = re.sub(r"\*\*", "", s.get("cap", "")) or s["vo"]
            wt = words_with_times(text, st, vd)
            for j, (c, c0, c1) in enumerate(wt):
                c1 = wt[j + 1][1] if j + 1 < len(wt) else b - 0.15   # keep caption until the next one / scene end
                capdivs += f"<div class='cap' data-c0='{c0:.3f}' data-c1='{c1:.3f}'>{mark(c, keys)}</div>"
                if any(kk.lower() in c.lower() for kk in keys): pops.append(c0)
        parts.append(f"<div class='sc' data-a='{a:.2f}' data-b='{b:.2f}'>{head}<div class='capzone'>{capdivs}</div></div>")
    js = """
const c=x=>Math.max(0,Math.min(1,x)), ease=x=>1-Math.pow(1-c(x),3), back=x=>{x=c(x);const s=1.9;return 1+(s+1)*Math.pow(x-1,3)+s*Math.pow(x-1,2);};
const D=%f; const scs=[...document.querySelectorAll('.sc')], pops=[...document.querySelectorAll('[data-pop]')], caps=[...document.querySelectorAll('.cap')];
window.render=function(t){
 for(const s of scs){const a=+s.dataset.a,b=+s.dataset.b;let al;
   if(s.dataset.hard && t<b-0.12) al=t>=a?1:0; else al=Math.min(t>=a?ease((t-a)/0.12):0, 1-ease((t-(b-0.12))/0.12));
   s.style.opacity=al; let z=1+0.04*Math.max(0,1-(t-a)/0.25); if(s.dataset.hard) z*=1+0.05*c((t-a)/(b-a)); s.style.transform=`scale(${z})`;}
 for(const e of pops){const t0=+e.dataset.pop;const k=t0<=0?1:back((t-t0)/0.28);e.style.opacity=t0<=0?1:c((t-t0)/0.08);e.style.transform=`scale(${0.6+0.4*k})`;e.style.transformOrigin='left center';}
 for(const e of caps){const a=+e.dataset.c0,b=+e.dataset.c1;const on=t>=a&&t<b;e.style.opacity=on?1:0;const k=back((t-a)/0.18);e.style.transform=`scale(${0.75+0.25*k}) rotate(${(1-c((t-a)/0.18))*-2}deg)`;e.style.transformOrigin='left center';}
 document.getElementById('bar').style.width=(c(t/D)*1080)+'px';
 const sh=Math.sin(t*1.7)*90, sv=Math.cos(t*1.3)*70;
 document.getElementById('g1').style.transform=`translate(${sh}px,${sv}px)`;document.getElementById('g2').style.transform=`translate(${-sv}px,${-sh}px)`;
 const f=document.getElementById('fl');let fo=0;for(const s of scs){const a=+s.dataset.a;if(a>0&&t>=a&&t<a+0.1)fo=0.18*(1-(t-a)/0.1);}f.style.opacity=fo;
};render(0);""" % total
    page = f"""<!doctype html><html><head><meta charset='utf-8'><style>{BRAND_CSS}{CSS}</style></head><body>
<div class='glow1' id='g1'></div><div class='glow2' id='g2'></div><div class='bar' id='bar'></div>
<div class='top'><div class='brand'><span class='inf'>∞</span>korotech_fr</div></div>
{''.join(parts)}<div class='flash' id='fl'></div><script>{js}</script></body></html>"""
    hp = os.path.join(tmp, "r.html"); open(hp, "w").write(page)
    fr = os.path.join(tmp, "f"); os.makedirs(fr)
    asyncio.run(_frames(hp, fr, total))
    silent = os.path.join(tmp, "s.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{fr}/f_%04d.jpg", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-maxrate", "4M", "-bufsize", "8M", silent], check=True)
    # sound effects: whoosh at each scene change, soft pop on highlights / CTA items
    SR = 48000; n = int(SR * (total + 1)); fx = np.zeros(n); rng = np.random.default_rng(3)
    def put(sig, t0):
        i = int(t0 * SR)
        if 0 <= i < n: fx[i:i + len(sig)] += sig[: n - i]
    L = int(0.32 * SR); tt = np.arange(L) / SR
    nz = rng.standard_normal(L); env = np.sin(np.pi * tt / 0.32) ** 2
    sweep = np.cumsum(np.interp(tt, [0, 0.32], [300, 4000])) / SR
    whoosh = (nz * 0.6 + np.sin(2 * np.pi * sweep) * 0.2) * env
    from scipy.signal import butter, lfilter
    b_, a_ = butter(2, [400 / (SR / 2), 6000 / (SR / 2)], "band"); whoosh = lfilter(b_, a_, whoosh) * 0.5
    P = int(0.09 * SR); tp = np.arange(P) / SR
    pop = np.sin(2 * np.pi * (900 + 600 * np.exp(-tp * 40)) * tp) * np.exp(-tp * 45) * 0.35
    for a, _ in starts[1:]: put(whoosh, a - 0.12)
    for p in pops: put(pop, p)
    fxw = os.path.join(tmp, "fx.wav"); wavfile.write(fxw, SR, (np.clip(fx, -1, 1) * 32767).astype(np.int16))
    mus = os.path.join(tmp, "m.wav"); make_music(mus, total + 1, int(spec.get("music_seed", 7)))
    ins = ["-i", silent, "-i", mus, "-i", fxw] + sum((["-i", w] for _, w in voice), [])
    dl = "".join(f"[{i + 3}]adelay={int(t * 1000)}|{int(t * 1000)}[v{i}];" for i, (t, _) in enumerate(voice))
    vs = "".join(f"[v{i}]" for i in range(len(voice)))
    fc = (dl + f"{vs}amix=inputs={len(voice)}:normalize=0:duration=longest,apad=whole_dur={total + 4},loudnorm=I=-15:TP=-1.5,atrim=0:{total}[vo];"
          f"[vo]asplit=2[voa][sc];[1]apad=whole_dur={total + 1},atrim=0:{total},volume=0.30[m];"
          f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];[2]atrim=0:{total},aformat=channel_layouts=stereo,volume=0.55[fx];"
          f"[voa][md][fx]amix=inputs=3:normalize=0:duration=longest,alimiter=limit=0.95,apad=whole_dur={total},atrim=0:{total}[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)
    return total

if __name__ == "__main__":
    p = sys.argv[1]
    print("duration", build(json.load(open(p)), sys.argv[2], os.path.dirname(os.path.abspath(p))))
