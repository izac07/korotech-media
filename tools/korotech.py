#!/usr/bin/env python3
"""Korotech content engine.

Usage:
  python3 tools/korotech.py carrousel <spec.json> <out_dir>     -> slide_01.jpg ... (1080x1350 JPEG)
  python3 tools/korotech.py reel <spec.json> <out.mp4>           -> 1080x1920 MP4 with original music
  python3 tools/korotech.py music <out.wav> <seconds> [seed]

Spec formats are documented in tools/README.md.
"""
import asyncio, json, os, subprocess, sys, html as H, tempfile, shutil

BRAND_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Inter,sans-serif;color:#fff;background:#0d0a1c;position:relative;overflow:hidden}
.glow1{position:absolute;border-radius:50%;background:radial-gradient(circle,rgba(91,46,255,.45),transparent 65%)}
.glow2{position:absolute;border-radius:50%;background:radial-gradient(circle,rgba(226,60,200,.38),transparent 65%)}
.brand{display:flex;align-items:center;gap:14px;font-weight:600;color:#cfc8ee}
.inf{font-family:Poppins;font-weight:700;line-height:1;background:linear-gradient(90deg,#5b2eff,#e23cc8);-webkit-background-clip:text;color:transparent}
.grad{background:linear-gradient(90deg,#7b5cff,#ff4fd8);-webkit-background-clip:text;color:transparent}
.hl{color:#ff9ae9;font-weight:600}
.lbl{font-weight:700;letter-spacing:3px;color:#9c94c4}
.when{font-weight:700;letter-spacing:4px;text-transform:uppercase;color:#ff7ae3}
.card{background:rgba(255,255,255,.06);border:2px solid rgba(160,130,255,.38);border-radius:34px}
.ico{flex:none;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.08);border:2px solid rgba(160,130,255,.4)}
"""

def esc(s):
    """Escape text but keep [placeholders] highlighted and allow <br>."""
    s = H.escape(s).replace("&lt;br&gt;", "<br>")
    out, i = "", 0
    while i < len(s):
        if s[i] == "[":
            j = s.find("]", i)
            if j > 0:
                out += f"<span class='hl'>{s[i:j+1]}</span>"; i = j + 1; continue
        out += s[i]; i += 1
    return out

def rich(s):
    """Like esc, but **word** becomes gradient text."""
    parts = esc(s).split("**")
    return "".join(f"<span class='grad'>{p}</span>" if k % 2 else p for k, p in enumerate(parts))

# ---------------------------------------------------------------- carrousel
CAR_CSS = """
body{width:1080px;height:1350px}
.glow1{width:900px;height:900px;left:-300px;top:-320px}.glow2{width:900px;height:900px;right:-360px;bottom:-360px}
.wrap{position:absolute;inset:0;padding:96px 88px;display:flex;flex-direction:column}
.top{display:flex;justify-content:space-between;align-items:center;font-size:28px}
.brand .inf{font-size:54px}.count{font-size:26px;color:#9c94c4;font-weight:600;letter-spacing:2px}
h1{font-family:Poppins;font-weight:700;font-size:112px;line-height:1.04;text-transform:uppercase;margin-top:150px}
.sub{font-size:42px;line-height:1.35;color:#d9d3f5;margin-top:44px;font-weight:500}
.pill{align-self:flex-start;margin-top:auto;padding:22px 40px;border-radius:999px;font-size:30px;font-weight:700;background:linear-gradient(90deg,#5b2eff,#e23cc8);letter-spacing:1px}
.mid{margin:auto 0;display:flex;flex-direction:column}
.num{font-family:Poppins;font-weight:700;font-size:230px;line-height:.9}
.when{font-size:32px;margin-top:24px}
h2{font-family:Poppins;font-weight:700;font-size:78px;line-height:1.1;margin-top:18px}
.card{margin-top:52px;padding:52px 56px;font-size:42px;line-height:1.45;color:#f2efff}
.lbl{font-size:24px;margin-bottom:18px}
.body{font-size:44px;line-height:1.45;color:#e6e1fb;margin-top:40px}
.foot{margin-top:auto;font-size:28px;color:#9c94c4;display:flex;justify-content:space-between}
.ctas{margin-top:56px;display:flex;flex-direction:column;gap:30px}
.cta{display:flex;gap:28px;align-items:center;font-size:46px;font-weight:600;line-height:1.25}
.ico{width:92px;height:92px;border-radius:24px;font-size:46px}
.note{margin-top:auto;font-size:28px;color:#9c94c4;line-height:1.4}
"""

def car_page(i, total, body):
    return f"""<html><head><meta charset='utf-8'><style>{BRAND_CSS}{CAR_CSS}</style></head><body>
<div class='glow1'></div><div class='glow2'></div><div class='wrap'>
<div class='top'><div class='brand'><span class='inf'>∞</span>korotech_fr</div><div class='count'>{i:02d}/{total:02d}</div></div>
{body}</div></body></html>"""

def car_slide(s):
    t = s["type"]
    if t == "cover":
        size = s.get("size", 112)
        return f"<h1 style='font-size:{size}px'>{rich(s['title'])}</h1><div class='sub'>{esc(s.get('sub',''))}</div><div class='pill'>GLISSE →</div>"
    if t == "item":
        num = f"<div class='num grad'>{H.escape(str(s['num']))}</div>" if s.get("num") is not None else ""
        card = f"<div class='card'><div class='lbl'>{H.escape(s.get('card_label','LE PROMPT'))}</div>{esc(s['card'])}</div>" if s.get("card") else ""
        body = f"<div class='body'>{rich(s['body'])}</div>" if s.get("body") else ""
        return f"<div class='mid'>{num}<div class='when'>{H.escape(s.get('when',''))}</div><h2>{rich(s['title'])}</h2>{body}{card}</div><div class='foot'><span>{H.escape(s.get('foot','Enregistre pour plus tard'))}</span><span>→</span></div>"
    if t == "cta":
        rows = "".join(f"<div class='cta'><div class='ico'>{i}</div><div>{rich(x)}</div></div>" for i, x in s["ctas"])
        return f"<h1 style='font-size:{s.get('size',100)}px;margin-top:120px'>{rich(s['title'])}</h1><div class='ctas'>{rows}</div><div class='note'>{esc(s.get('note',''))}</div>"
    raise ValueError(t)

async def _shots(pages, out_dir, w, h):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": w, "height": h})
        for n, page in enumerate(pages, 1):
            await pg.set_content(page); await pg.wait_for_timeout(250)
            png = os.path.join(out_dir, f"slide_{n:02d}.png")
            await pg.screenshot(path=png)
        await b.close()

def build_carrousel(spec, out_dir):
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    slides = spec["slides"]
    pages = [car_page(i, len(slides), car_slide(s)) for i, s in enumerate(slides, 1)]
    asyncio.run(_shots(pages, out_dir, 1080, 1350))
    for n in range(1, len(slides) + 1):
        png = os.path.join(out_dir, f"slide_{n:02d}.png")
        Image.open(png).convert("RGB").save(png[:-4] + ".jpg", quality=92); os.remove(png)
    return [f"slide_{n:02d}.jpg" for n in range(1, len(slides) + 1)]

# ---------------------------------------------------------------- reel
REEL_CSS = """
body{width:1080px;height:1920px}
.glow1{width:1200px;height:1200px;left:-420px;top:-420px}.glow2{width:1200px;height:1200px;right:-480px;bottom:-380px}
.top{position:absolute;top:110px;left:88px;right:88px;font-size:32px}.brand .inf{font-size:60px}
.bar{position:absolute;left:0;top:0;height:10px;background:linear-gradient(90deg,#5b2eff,#e23cc8)}
.sc{position:absolute;left:88px;right:88px;top:300px;bottom:420px;display:flex;flex-direction:column;justify-content:center;opacity:0}
.hook{font-family:Poppins;font-weight:700;font-size:112px;line-height:1.04;text-transform:uppercase}
.big{font-family:Poppins;font-weight:700;font-size:96px;line-height:1.08}
.when{font-size:36px;margin-bottom:22px}
.h2{font-family:Poppins;font-weight:700;font-size:78px;line-height:1.1}
.card{margin-top:56px;padding:48px 52px}
.chat{font-size:44px;line-height:1.45;min-height:480px}
.lbl{font-size:26px;margin-bottom:20px}
.cursor{display:inline-block;width:4px;height:48px;background:#ff7ae3;vertical-align:-8px;margin-left:4px}
.li{font-size:44px;line-height:1.35;color:#f2efff;margin-top:26px;display:flex;gap:22px}
.li .dot{flex:none;width:18px;height:18px;border-radius:50%;margin-top:20px;background:linear-gradient(90deg,#7b5cff,#ff4fd8)}
.fh{font-family:Poppins;font-weight:700;font-size:50px;margin-bottom:6px}
.sec{margin-top:26px}.sec .st{font-size:28px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#ff7ae3;margin-bottom:10px}
.sec .tx{font-size:36px;line-height:1.4;color:#f2efff}
.cta{display:flex;gap:30px;align-items:center;font-size:54px;font-weight:600;line-height:1.25;margin-top:44px}
.ico{width:110px;height:110px;border-radius:28px;font-size:56px}
[data-in]{opacity:0}
"""
DEFAULT_DUR = {"hook": 3.4, "chat": 7.0, "list": 6.0, "result": 7.0, "cta": 4.8, "text": 4.5}

def reel_html(spec):
    scenes, t, parts = spec["scenes"], 0.0, []
    for k, s in enumerate(scenes):
        d = float(s.get("dur", DEFAULT_DUR[s["type"]])); a, b = t, t + d; t = b
        sid = f"s{k}"; inner = ""
        lab = f"<div class='when' data-in='{a+0.1:.2f}'>{H.escape(s['label'])}</div>" if s.get("label") else ""
        if s["type"] == "hook":
            for j, line in enumerate(s["lines"]):
                cls = "hook grad" if line.startswith("**") else "hook"
                inner += f"<div class='{cls}' data-in='{a+0.05+j*0.35:.2f}' style='margin-top:{18 if j else 0}px'>{esc(line.strip('*'))}</div>"
        elif s["type"] == "text":
            inner = lab + f"<div class='big' data-in='{a+0.15:.2f}'>{rich(s['title'])}</div>"
        elif s["type"] == "chat":
            ts, td = a + 0.9, max(1.5, d - 2.4)
            inner = lab + f"<div class='h2' data-in='{a+0.2:.2f}'>{rich(s['title'])}</div><div class='card chat' data-in='{a+0.5:.2f}'><div class='lbl'>{H.escape(s.get('card_label','CHATGPT · CLAUDE · GEMINI'))}</div><span data-type='{ts:.2f}' data-tdur='{td:.2f}' data-text='{H.escape(s['text'], quote=True)}'></span><span class='cursor'></span></div>"
        elif s["type"] == "list":
            items = s["items"]; step = max(0.6, (d - 1.8) / max(1, len(items)))
            lis = "".join(f"<div class='li' data-in='{a+1.0+j*step:.2f}'><div class='dot'></div><div>{rich(x)}</div></div>" for j, x in enumerate(items))
            inner = lab + f"<div class='h2' data-in='{a+0.2:.2f}'>{rich(s['title'])}</div><div class='card'>{lis}</div>"
        elif s["type"] == "result":
            secs = s["sections"]; step = max(0.8, (d - 1.8) / max(1, len(secs)))
            body = "".join(f"<div class='sec' data-in='{a+0.9+j*step:.2f}'><div class='st'>{H.escape(x['t'])}</div><div class='tx'>{esc(x['tx'])}</div></div>" for j, x in enumerate(secs))
            inner = lab + f"<div class='card' data-in='{a+0.3:.2f}'><div class='fh'>{esc(s['title'])}</div>{body}</div>"
        elif s["type"] == "cta":
            rows = "".join(f"<div class='cta' data-in='{a+0.7+j*0.7:.2f}'><div class='ico'>{i}</div><div>{rich(x)}</div></div>" for j, (i, x) in enumerate(s["ctas"]))
            inner = f"<div class='big' data-in='{a+0.1:.2f}'>{rich(s['title'])}</div>{rows}"
        parts.append(f"<div class='sc' id='{sid}' data-a='{a:.2f}' data-b='{b:.2f}'>{inner}</div>")
    total = t
    js = """
const c=x=>Math.max(0,Math.min(1,x)), ease=x=>1-Math.pow(1-c(x),3);
const D=%f; const scs=[...document.querySelectorAll('.sc')], ins=[...document.querySelectorAll('[data-in]')], tys=[...document.querySelectorAll('[data-type]')];
function hl(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\\[([^\\]]*)(\\]|$)/g,(m,a,b)=>"<span class='hl'>["+a+b+"</span>");}
window.render=function(t){
 for(const s of scs){const a=+s.dataset.a,b=+s.dataset.b;const al=Math.min(ease((t-a)/0.35),1-ease((t-(b-0.3))/0.3));s.style.opacity=al;s.style.transform=`scale(${0.97+0.03*ease((t-a)/0.5)})`;}
 for(const e of ins){const k=ease((t-(+e.dataset.in))/0.45);e.style.opacity=k;e.style.transform=`translateY(${(1-k)*50}px)`;}
 for(const e of tys){const s=e.dataset.text;const n=Math.floor(c((t-(+e.dataset.type))/(+e.dataset.tdur))*s.length);e.innerHTML=hl(s.slice(0,n));}
 document.getElementById('bar').style.width=(c(t/D)*1080)+'px';
 document.getElementById('g1').style.transform=`translate(${Math.sin(t/3)*60}px,${Math.cos(t/4)*40}px)`;
 document.getElementById('g2').style.transform=`translate(${Math.cos(t/3)*60}px,${Math.sin(t/5)*40}px)`;
};render(0);""" % total
    page = f"""<!doctype html><html><head><meta charset='utf-8'><style>{BRAND_CSS}{REEL_CSS}</style></head><body>
<div class='glow1' id='g1'></div><div class='glow2' id='g2'></div><div class='bar' id='bar'></div>
<div class='top'><div class='brand'><span class='inf'>∞</span>korotech_fr</div></div>
{''.join(parts)}<script>{js}</script></body></html>"""
    return page, total

async def _frames(html_path, fr, dur, fps=30):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + os.path.abspath(html_path)); await pg.wait_for_timeout(500)
        for i in range(int(dur * fps)):
            await pg.evaluate(f"render({i / fps})")
            await pg.screenshot(path=f"{fr}/f_{i:04d}.jpg", type="jpeg", quality=90)
        await b.close()

def build_reel(spec, out):
    page, dur = reel_html(spec)
    tmp = tempfile.mkdtemp()
    hp_ = os.path.join(tmp, "reel.html"); open(hp_, "w").write(page)
    fr = os.path.join(tmp, "frames"); os.makedirs(fr)
    asyncio.run(_frames(hp_, fr, dur))
    silent = os.path.join(tmp, "silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{fr}/f_%04d.jpg", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-maxrate", "4M", "-bufsize", "8M", silent], check=True)
    wav = os.path.join(tmp, "music.wav")
    make_music(wav, dur + 1, int(spec.get("music_seed", sum(map(ord, spec.get("id", "x"))))))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-filter_complex",
                    f"[1]atrim=0:{dur},afade=t=out:st={dur-1.5}:d=1.5,loudnorm=I=-15:TP=-1.5[a]", "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)
    return dur

# ---------------------------------------------------------------- music
def make_music(out, dur, seed=7):
    """Original lo-fi loop, varied by seed (tempo, progression, key, drums)."""
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import butter, lfilter
    SR = 48000; rng = np.random.default_rng(seed); n = int(SR * dur); mix = np.zeros((n, 2))
    def lp(x, f): b, a = butter(2, f / (SR / 2), "low"); return lfilter(b, a, x)
    def hp(x, f): b, a = butter(2, f / (SR / 2), "high"); return lfilter(b, a, x)
    def add(sig, t0, pan=0.0, g=1.0):
        i = int(t0 * SR)
        if i >= n: return
        sig = sig[: n - i] * g; mix[i:i+len(sig), 0] += sig * (1 - pan) * .707; mix[i:i+len(sig), 1] += sig * (1 + pan) * .707
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    progs = [([[53,57,60,64,67],[52,55,59,62],[50,53,57,60,64],[48,52,55,59]],[41,40,38,36]),
             ([[57,60,64,67],[53,57,60,64],[48,52,55,59],[55,59,62,65]],[45,41,36,43]),
             ([[50,53,57,60],[55,59,62,65],[48,52,55,59],[45,48,52,55]],[38,43,36,33]),
             ([[52,55,59,62],[57,60,64,67],[50,53,57,60],[55,59,62,66]],[40,45,38,43])]
    chords, roots = progs[seed % len(progs)]
    shift = int(rng.integers(-2, 3)); bpm = [72, 76, 80, 84, 88][seed % 5]; beat = 60 / bpm; bar = 4 * beat
    swing = 0.55 + 0.06 * rng.random(); bright = 4500 + 2000 * rng.random()
    def ep(f, d):
        t = np.arange(int(d * SR)) / SR; env = np.exp(-t * 1.6) * (1 - np.exp(-t * 60))
        return (np.sin(2*np.pi*f*t) + .35*np.sin(4*np.pi*f*t)*np.exp(-t*3) + .12*np.sin(6*np.pi*f*t)*np.exp(-t*5)) * env * (1 + .08*np.sin(2*np.pi*4.5*t))
    def kick():
        t = np.arange(int(.35 * SR)) / SR; f = 110 * np.exp(-t * 18) + 45
        return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t * 9)
    def snare():
        t = np.arange(int(.25 * SR)) / SR
        return lp(hp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 22), 6000) * .5 + np.sin(2*np.pi*190*t)*np.exp(-t*30)*.3
    def hat():
        t = np.arange(int(.06 * SR)) / SR; return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * 70)
    def bass(f, d):
        t = np.arange(int(d * SR)) / SR; return lp(np.sin(2*np.pi*f*t) + .2*np.sin(4*np.pi*f*t), 400) * np.minimum(1, t*40) * np.exp(-t*.9)
    t = 0.0; k = 0
    while t < dur:
        for j, m in enumerate(chords[k % 4]): add(ep(midi(m + shift), bar * 1.1), t + j * .012, (j - 2) * .25, .11)
        add(bass(midi(roots[k % 4] + shift), bar * .95), t, 0, .32)
        for b in range(4):
            tb = t + b * beat
            if b in (0, 2): add(kick(), tb, 0, .55)
            if b == 2 and k % 2: add(kick(), tb + beat * .75, 0, .35)
            if b in (1, 3): add(snare(), tb + .015, 0, .3)
            for s in range(2): add(hat(), tb + (beat * swing if s else 0), .3, .12 if s == 0 else .07)
        t += bar; k += 1
    cr = np.zeros(n); idx = rng.integers(0, n, int(dur * 25)); cr[idx] = rng.uniform(-1, 1, len(idx))
    cr = hp(cr, 2000) * .05 + lp(rng.standard_normal(n), 3000) * .004
    mix[:, 0] += cr; mix[:, 1] += cr
    mix = np.stack([lp(mix[:, 0], bright), lp(mix[:, 1], bright)], 1)
    fd = int(1.2 * SR); mix[:fd] *= np.linspace(0, 1, fd)[:, None]
    mix = mix / np.max(np.abs(mix)) * .89
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "carrousel":
        print(build_carrousel(json.load(open(sys.argv[2])), sys.argv[3]))
    elif cmd == "reel":
        print("duration", build_reel(json.load(open(sys.argv[2])), sys.argv[3]))
    elif cmd == "music":
        make_music(sys.argv[2], float(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 7)
