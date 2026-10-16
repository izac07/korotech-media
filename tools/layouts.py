"""Mises en page de carrousels propres à chaque compte (theme.json -> "layout").

Chaque layout reçoit (i, total, slide, theme, esc, rich, fonts_css) et renvoie une page HTML 1080x1350.
Types de slides gérés : cover, item, cta (même spec que Korotech).
"""
import html as H

def _h(s):
    return H.escape(str(s))

# ------------------------------------------------------------------ terminal (lia.entrepreneur)
def terminal(i, total, s, t, esc, rich, fonts):
    g = t["accent"]
    css = f"""{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:#050806;color:#eafff2;font-family:'Space Grotesk',sans-serif;position:relative;overflow:hidden;
 background-image:linear-gradient(rgba(57,255,136,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(57,255,136,.05) 1px,transparent 1px);background-size:54px 54px}}
.win{{position:absolute;left:60px;right:60px;top:70px;bottom:70px;border:2px solid rgba(57,255,136,.35);border-radius:26px;background:rgba(8,14,10,.92);
 box-shadow:0 0 80px rgba(57,255,136,.12);display:flex;flex-direction:column;overflow:hidden}}
.bar{{height:70px;flex:none;display:flex;align-items:center;gap:14px;padding:0 30px;border-bottom:2px solid rgba(57,255,136,.18);background:rgba(57,255,136,.05)}}
.dot{{width:18px;height:18px;border-radius:50%}}
.fname{{flex:1;text-align:center;font:400 24px 'JetBrains Mono';color:#7fa891;margin-right:90px}}
.in{{flex:1;padding:64px 64px 40px;display:flex;flex-direction:column}}
.mono{{font-family:'JetBrains Mono',monospace}}
.cmt{{font:400 30px 'JetBrains Mono';color:{g}}}
h1{{font:400 104px/1.04 'Archivo Black';margin-top:36px}}
h2{{font:400 80px/1.1 'Archivo Black';margin-top:22px}}
.grad{{color:{g}}}
.hl{{color:#b6ff3b}}
.sub{{font-size:40px;line-height:1.4;color:#c7e8d4;margin-top:40px}}
.body{{font-size:44px;line-height:1.45;color:#d6f5e2;margin-top:36px}}
.idx{{font:700 150px/1 'JetBrains Mono';color:{g};opacity:.95}}
.code{{margin-top:44px;border-radius:18px;background:#020403;border:2px solid rgba(57,255,136,.25);overflow:hidden}}
.tab{{font:400 22px 'JetBrains Mono';color:#7fa891;padding:14px 24px;border-bottom:2px solid rgba(57,255,136,.15)}}
.lines{{display:flex;padding:30px 26px;font:400 34px/1.55 'JetBrains Mono';color:#eafff2}}
.ln{{color:#3d5c48;padding-right:22px;text-align:right;user-select:none}}
.cur{{display:inline-block;width:22px;height:46px;background:{g};vertical-align:-8px;margin-left:8px}}
.next{{margin-top:auto;font:400 28px 'JetBrains Mono';color:{g}}}
.status{{height:58px;flex:none;display:flex;justify-content:space-between;align-items:center;padding:0 30px;font:400 22px 'JetBrains Mono';color:#7fa891;border-top:2px solid rgba(57,255,136,.18)}}
.cta{{font:400 40px/1.3 'JetBrains Mono';margin-top:30px;color:#eafff2}} .cta b{{color:{g};font-weight:400}}
.note{{margin-top:auto;font:400 24px 'JetBrains Mono';color:#7fa891}}
"""
    k = s["type"]
    if k == "cover":
        body = (f"<div class='cmt'>$ ./{_h(t['handle'])} --conseil</div><h1 style='font-size:{s.get('size',104)}px'>{rich(s['title'])}</h1>"
                f"<div class='sub'>{esc(s.get('sub',''))}</div><div class='next'>▶ glisse pour lire la suite<span class='cur'></span></div>")
        fname = "nouveau_post.md"
    elif k == "item":
        num = s.get("num")
        idx = f"<div class='idx'>{'[' + _h(num) + ']' if isinstance(num, int) else _h(num)}</div>" if num is not None else ""
        code = ""
        if s.get("card"):
            rows = esc(s["card"])
            code = (f"<div class='code'><div class='tab'>{_h(s.get('card_label','PROMPT')).lower().replace(' ','_')}.txt</div>"
                    f"<div class='lines'><div class='ln'>1<br>2<br>3<br>4<br>5</div><div>{rows}</div></div></div>")
        body = f"{idx}<div class='cmt' style='margin-top:26px'>// {_h(s.get('when',''))}</div><h2>{rich(s['title'])}</h2>"
        body += (f"<div class='body'>{rich(s['body'])}</div>" if s.get("body") else "") + code
        fname = f"etape_{i-1:02d}.md"
    else:
        rows = "".join(f"<div class='cta'><b>[✓]</b> {rich(x)}</div>" for _, x in s["ctas"])
        body = (f"<div class='cmt'>$ prochaine_etape</div><h1 style='font-size:{s.get('size',96)}px'>{rich(s['title'])}</h1>"
                f"<div style='margin-top:50px'>{rows}</div><div class='note'># {esc(s.get('note',''))}</div>")
        fname = "a_faire.md"
    return f"""<html><head><meta charset='utf-8'><style>{css}</style></head><body><div class='win'>
<div class='bar'><div class='dot' style='background:#ff5f57'></div><div class='dot' style='background:#febc2e'></div><div class='dot' style='background:#28c840'></div><div class='fname'>{fname}</div></div>
<div class='in'>{body}</div><div class='status'><span>● @{_h(t['handle'])}</span><span>{i}/{total}</span></div></div></body></html>"""

# ------------------------------------------------------------------ sport (zerosallefit)
def sport(i, total, s, t, esc, rich, fonts):
    r = t["accent"]
    tick = ("ZÉRO SALLE · ZÉRO EXCUSE · " * 6)
    css = f"""{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:#0b0b0b;color:#fff;font-family:Inter,sans-serif;position:relative;overflow:hidden}}
.slash{{position:absolute;width:1700px;height:300px;background:{r};transform:rotate(-14deg);left:-300px;top:930px;opacity:.95}}
.slash2{{position:absolute;width:1700px;height:40px;background:#fff;transform:rotate(-14deg);left:-300px;top:1250px;opacity:.08}}
.top{{position:absolute;top:60px;left:72px;right:72px;display:flex;justify-content:space-between;font:800 26px Inter;letter-spacing:3px;text-transform:uppercase}}
.top .c{{color:{r}}}
.ticker{{position:absolute;left:0;right:0;bottom:0;height:86px;background:{r};color:#fff;font:400 40px/86px Anton;white-space:nowrap;letter-spacing:2px;overflow:hidden}}
.wrap{{position:absolute;left:72px;right:72px;top:150px;bottom:130px;display:flex;flex-direction:column}}
h1{{font:400 168px/0.95 Anton;text-transform:uppercase;letter-spacing:1px}}
h2{{font:400 104px/0.98 Anton;text-transform:uppercase;margin-top:20px;position:relative}}
.grad{{color:{r}}}
.hl{{color:{r};font-weight:700}}
.sub{{font:600 40px/1.35 Inter;color:#ddd;margin-top:40px;max-width:820px}}
.tag{{align-self:flex-start;background:{r};color:#fff;font:800 28px Inter;letter-spacing:3px;text-transform:uppercase;padding:14px 26px;border-radius:8px;margin-top:40px}}
.ghost{{position:absolute;right:-20px;bottom:-60px;font:400 640px/1 Anton;color:transparent;-webkit-text-stroke:4px rgba(255,45,54,.55)}}
.body{{font:500 46px/1.42 Inter;color:#eee;margin-top:40px;position:relative;max-width:900px}}
.stat{{margin-top:44px;background:#fff;color:#0b0b0b;border-radius:18px;padding:36px 40px;font:600 36px/1.4 Inter;position:relative}}
.stat .l{{font:800 22px Inter;letter-spacing:3px;color:{r};margin-bottom:10px}}
.cta{{display:flex;align-items:center;gap:26px;font:400 64px/1.1 Anton;text-transform:uppercase;margin-top:30px}}
.cta .b{{width:84px;height:84px;background:{r};border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:42px}}
.note{{margin-top:auto;font:500 26px/1.4 Inter;color:#aaa;position:relative}}
"""
    k = s["type"]
    deco = "<div class='slash'></div><div class='slash2'></div>" if k != "item" else ""
    if k == "cover":
        body = f"<h1 style='font-size:{int(s.get('size',104)*1.6)}px'>{rich(s['title'])}</h1><div class='sub'>{esc(s.get('sub',''))}</div>"
    elif k == "item":
        num = s.get("num")
        ghost = f"<div class='ghost'>{_h(num)}</div>" if num is not None else ""
        body = ghost + f"<div class='tag'>{_h(s.get('when',''))}</div><h2>{rich(s['title'])}</h2>"
        body += f"<div class='body'>{rich(s['body'])}</div>" if s.get("body") else ""
        body += f"<div class='stat'><div class='l'>{_h(s.get('card_label','À FAIRE'))}</div>{esc(s['card'])}</div>" if s.get("card") else ""
    else:
        rows = "".join(f"<div class='cta'><div class='b'>{ic}</div><div>{rich(x)}</div></div>" for ic, x in s["ctas"])
        body = f"<h1 style='font-size:{int(s.get('size',96)*1.45)}px'>{rich(s['title'])}</h1><div style='margin-top:40px'>{rows}</div><div class='note'>{esc(s.get('note',''))}</div>"
    return f"""<html><head><meta charset='utf-8'><style>{css}</style></head><body>{deco}
<div class='top'><span>@{_h(t['handle'])}</span><span class='c'>{i:02d} / {total:02d}</span></div>
<div class='wrap'>{body}</div><div class='ticker'>{tick}</div></body></html>"""

# ------------------------------------------------------------------ messages (coeurlucide)
def messages(i, total, s, t, esc, rich, fonts):
    a = t["accent"]
    css = f"""{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:linear-gradient(170deg,#fbeef0,#f3d9de);color:#3a0f1c;font-family:Inter,sans-serif;position:relative;overflow:hidden}}
.top{{position:absolute;top:56px;left:0;right:0;text-align:center}}
.av{{width:84px;height:84px;border-radius:50%;background:{a};color:#fff;font:800 44px/84px 'Playfair Display';margin:0 auto}}
.nm{{font:600 26px Inter;margin-top:12px;color:#5a2433}} .st{{font:400 22px Inter;color:#9a6070;margin-top:4px}}
.wrap{{position:absolute;left:70px;right:70px;top:300px;bottom:180px;display:flex;flex-direction:column}}
.ts{{align-self:center;font:600 22px Inter;letter-spacing:2px;color:#9a6070;text-transform:uppercase;margin:6px 0 26px}}
.bub{{max-width:860px;border-radius:46px;padding:38px 48px;font:500 46px/1.42 Inter;margin-top:30px}}
.me{{align-self:flex-end;background:{a};color:#fff;border-bottom-right-radius:12px;font:700 66px/1.18 'Playfair Display'}}
.me .grad{{font-style:italic;color:#ffd6de}}
.them{{align-self:flex-start;background:#fff;color:#3a0f1c;border-bottom-left-radius:12px;box-shadow:0 6px 20px rgba(122,31,53,.08)}}
.them .grad{{color:{a};font-weight:700;font-style:italic}}
.note-h{{font:700 46px 'Caveat';color:#b0465e;margin-bottom:4px}}
.grad{{color:{a};font-style:italic}}
.hl{{color:#b0465e;font-weight:600}}
h1{{font:800 108px/1.06 'Playfair Display';text-align:center;margin-top:90px}}
h1 .grad{{font-weight:700}}
.sub{{font:700 52px/1.25 'Caveat';color:#b0465e;text-align:center;margin-top:40px}}
.q{{font:800 260px/0.6 'Playfair Display';color:rgba(122,31,53,.12);text-align:center;height:120px}}
.input{{position:absolute;left:70px;right:70px;bottom:64px;height:84px;border-radius:42px;background:#fff;display:flex;align-items:center;padding:0 16px 0 40px;font:400 30px Inter;color:#b9919b;box-shadow:0 6px 20px rgba(122,31,53,.08)}}
.input .s{{margin-left:auto;width:58px;height:58px;border-radius:50%;background:{a};color:#fff;font:700 30px/58px Inter;text-align:center}}
"""
    k = s["type"]
    if k == "cover":
        body = f"<div class='q'>“</div><h1 style='font-size:{s.get('size',104)}px'>{rich(s['title'])}</h1><div class='sub'>{esc(s.get('sub',''))}</div>"
        inp = "Glisse pour lire →"
    elif k == "item":
        num = s.get("num")
        ts = f"{_h(s.get('when',''))}" + (f" · {_h(num)}" if isinstance(num, int) else "")
        body = f"<div class='ts'>{ts}</div><div class='bub me'>{rich(s['title'])}</div>"
        if s.get("body"):
            body += f"<div class='bub them'>{rich(s['body'])}</div>"
        if s.get("card"):
            body += f"<div class='bub them'><div class='note-h'>{_h(s.get('card_label','À dire')).capitalize()} :</div>{esc(s['card'])}</div>"
        inp = "Écris un message…"
    else:
        rows = "".join(f"<div class='bub them' style='font-size:40px'>{ic}&nbsp; {rich(x)}</div>" for ic, x in s["ctas"])
        body = f"<div class='bub me'>{rich(s['title'])}</div>{rows}<div class='ts' style='margin-top:auto;text-transform:none;letter-spacing:0;font-weight:400;font-size:24px;text-align:center'>{esc(s.get('note',''))}</div>"
        inp = "Enregistre ce post 🤍"
    return f"""<html><head><meta charset='utf-8'><style>{css}</style></head><body>
<div class='top'><div class='av'>C</div><div class='nm'>@{_h(t['handle'])}</div><div class='st'>{i}/{total}</div></div>
<div class='wrap'>{body}</div><div class='input'>{inp}<div class='s'>↑</div></div></body></html>"""

# ------------------------------------------------------------------ manifeste (mentaldacier)
def manifeste(i, total, s, t, esc, rich, fonts):
    css = f"""{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:#0a0a0a;color:#fff;font-family:Inter,sans-serif;position:relative;overflow:hidden}}
.top{{position:absolute;top:64px;left:80px;right:80px;display:flex;justify-content:space-between;font:400 26px 'JetBrains Mono';color:#8a8a8a}}
.wrap{{position:absolute;left:80px;right:80px;top:170px;bottom:120px;display:flex;flex-direction:column}}
h1{{font:400 132px/0.98 'Archivo Black';text-transform:uppercase;margin-top:auto}}
h2{{font:400 92px/1.0 'Archivo Black';text-transform:uppercase;margin-top:28px}}
.grad{{background:#fff;color:#0a0a0a;padding:0 12px;-webkit-box-decoration-break:clone;box-decoration-break:clone}}
.hl{{text-decoration:underline;text-underline-offset:6px}}
.rule{{height:14px;background:#fff;width:220px;margin-top:56px}}
.sub{{font:500 40px/1.4 Inter;color:#9a9a9a;margin-top:40px}}
.kick{{font:400 30px 'JetBrains Mono';color:#8a8a8a}}
.body{{font:500 42px/1.45 Inter;color:#d0d0d0;margin-top:auto}}
.body .grad{{background:none;color:#fff;padding:0;text-decoration:underline;text-decoration-thickness:3px;text-underline-offset:7px}}
.quote{{margin-top:44px;border-left:10px solid #fff;padding:10px 0 10px 40px;font:500 40px/1.45 Inter;color:#fff}}
.cta{{font:400 54px/1.2 'Archivo Black';text-transform:uppercase;margin-top:22px}}
.cta .grad{{background:none;color:#fff;padding:0}}
.note{{margin-top:auto;font:400 26px 'JetBrains Mono';color:#8a8a8a}}
.bot{{position:absolute;bottom:56px;left:80px;right:80px;display:flex;justify-content:space-between;font:400 24px 'JetBrains Mono';color:#555}}
"""
    k = s["type"]
    if k == "cover":
        body = f"<h1 style='font-size:{int(s.get('size',104)*1.25)}px'>{rich(s['title'])}</h1><div class='rule'></div><div class='sub'>{esc(s.get('sub',''))}</div>"
    elif k == "item":
        num = s.get("num")
        n = f"{num:02d}" if isinstance(num, int) else _h(num or "")
        body = f"<div class='kick'>{n} — {_h(s.get('when',''))}</div><h2>{rich(s['title'])}</h2>"
        body += f"<div class='body'>{rich(s['body'])}</div>" if s.get("body") else ""
        body += f"<div class='quote'>{esc(s['card'])}</div>" if s.get("card") else ""
    else:
        rows = "".join(f"<div class='cta'>→ {rich(x)}</div>" for _, x in s["ctas"])
        body = f"<h1 style='font-size:{int(s.get('size',96)*1.2)}px;margin-top:0'>{rich(s['title'])}</h1><div class='rule' style='margin-bottom:30px'></div>{rows}<div class='note'>{esc(s.get('note',''))}</div>"
    return f"""<html><head><meta charset='utf-8'><style>{css}</style></head><body>
<div class='top'><span>@{_h(t['handle'])}</span><span>N° {i:02d}</span></div><div class='wrap'>{body}</div>
<div class='bot'><span>MENTAL D'ACIER</span><span>{i}/{total}</span></div></body></html>"""

# ------------------------------------------------------------------ fiche (revenus-malin)
def fiche(i, total, s, t, esc, rich, fonts):
    gold, green = t["accent"], t["bg"]
    css = f"""{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:{green};font-family:Inter,sans-serif;position:relative;overflow:hidden}}
.paper{{position:absolute;left:64px;right:64px;top:70px;bottom:70px;background:#f6efe1;border-radius:22px;box-shadow:0 30px 60px rgba(0,0,0,.35);color:#173d2f;display:flex;flex-direction:column;padding:56px 64px 40px}}
.head{{display:flex;justify-content:space-between;align-items:center;font:800 22px Inter;letter-spacing:4px;color:#7a6a45;padding-bottom:24px;border-bottom:3px dotted #c8b98f}}
.head .tag{{background:{green};color:{gold};padding:10px 18px;border-radius:8px}}
h1{{font:400 112px/1.02 'DM Serif Display';margin-top:70px;color:#123d2e}}
h2{{font:400 86px/1.06 'DM Serif Display';margin-top:24px;color:#123d2e}}
.grad{{color:#b8862b;font-style:italic}}
.hl{{color:#b8862b;font-weight:700}}
.sub{{font:500 38px/1.42 Inter;color:#3f5a4c;margin-top:36px}}
.stamp{{position:absolute;right:60px;bottom:120px;width:190px;height:190px;border-radius:50%;border:5px solid #b8862b;color:#b8862b;transform:rotate(12deg);display:flex;align-items:center;justify-content:center;text-align:center;font:800 26px/1.2 Inter;letter-spacing:2px}}
.num{{font:400 150px/1 'DM Serif Display';color:#b8862b;margin-top:50px}}
.when{{display:inline-block;font:800 22px Inter;letter-spacing:4px;text-transform:uppercase;color:#7a6a45;margin-top:14px}}
.body{{font:500 44px/1.45 Inter;color:#28473a;margin-top:34px}}
.box{{margin-top:40px;border:3px solid #123d2e;border-radius:14px;padding:32px 36px;font:600 40px/1.45 Inter;background:#fffaf0}}
.box .l{{font:800 20px Inter;letter-spacing:4px;color:#7a6a45;margin-bottom:12px}}
.chk{{display:flex;gap:22px;align-items:center;font:600 42px/1.3 Inter;margin-top:26px}}
.chk .c{{flex:none;width:58px;height:58px;border:4px solid #123d2e;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#b8862b;font:800 38px Inter}}
.foot{{margin-top:auto;padding-top:22px;border-top:3px dashed #c8b98f;display:flex;justify-content:space-between;font:600 24px 'JetBrains Mono';color:#7a6a45}}
"""
    k = s["type"]
    if k == "cover":
        body = (f"<div class='stamp'>GUIDE<br>PRATIQUE</div><h1 style='font-size:{int(s.get('size',104)*1.05)}px'>{rich(s['title'])}</h1>"
                f"<div class='sub'>{esc(s.get('sub',''))}</div>")
        tag = "FICHE PRATIQUE"
    elif k == "item":
        num = s.get("num")
        body = f"<div class='num'>{_h(num) if num is not None else ''}</div><div class='when'>{_h(s.get('when',''))}</div><h2>{rich(s['title'])}</h2>"
        body += f"<div class='body'>{rich(s['body'])}</div>" if s.get("body") else ""
        body += f"<div class='box'><div class='l'>{_h(s.get('card_label','À RETENIR'))}</div>{esc(s['card'])}</div>" if s.get("card") else ""
        tag = f"POINT {i-1}"
    else:
        rows = "".join(f"<div class='chk'><div class='c'>✓</div><div>{rich(x)}</div></div>" for _, x in s["ctas"])
        body = f"<h1 style='font-size:{s.get('size',96)}px'>{rich(s['title'])}</h1><div style='margin-top:30px'>{rows}</div><div class='sub' style='font-size:28px;margin-top:50px'>{esc(s.get('note',''))}</div>"
        tag = "À FAIRE"
    return f"""<html><head><meta charset='utf-8'><style>{css}</style></head><body><div class='paper'>
<div class='head'><span>REVENUS MALINS</span><span class='tag'>{tag}</span></div>{body}
<div class='foot'><span>@{_h(t['handle'])}</span><span>{i:02d}/{total:02d}</span></div></div></body></html>"""

LAYOUTS = {"terminal": terminal, "sport": sport, "messages": messages, "manifeste": manifeste, "fiche": fiche}
LAYOUT_FONTS = {"terminal": ["Archivo Black", "Space Grotesk", "JetBrains Mono"], "sport": ["Anton"], "messages": ["Playfair Display", "Caveat"],
                "manifeste": ["Archivo Black", "JetBrains Mono"], "fiche": ["DM Serif Display", "JetBrains Mono"]}

# ------------------------------------------------------------------ reels : habillage par layout
# (CSS ajouté après le thème + éléments de décor insérés dans la page du reel)
REEL_CSS = {
 "terminal": """
.glow1,.glow2{display:none}
body{background:#050806;background-image:linear-gradient(rgba(57,255,136,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(57,255,136,.05) 1px,transparent 1px);background-size:60px 60px}
.rwin{position:absolute;left:56px;right:56px;top:230px;bottom:360px;border:2px solid rgba(57,255,136,.35);border-radius:28px;background:rgba(8,14,10,.92);box-shadow:0 0 80px rgba(57,255,136,.12)}
.rbar{height:74px;display:flex;align-items:center;gap:14px;padding:0 30px;border-bottom:2px solid rgba(57,255,136,.18)}
.rbar i{width:20px;height:20px;border-radius:50%;display:block}
.sc{left:110px;right:110px;top:330px;bottom:420px}
.when{font-family:'JetBrains Mono';letter-spacing:0;text-transform:none}
.when:before{content:'// '}
.hook,.big,.h2{font-family:'Archivo Black';font-weight:400;text-transform:none}
.chat{font-family:'JetBrains Mono';font-size:38px}
.card{background:#020403;border-radius:18px}
.top{top:130px}
""",
 "sport": """
.glow1,.glow2{display:none}
.rslash{position:absolute;width:2200px;height:380px;background:#ff2d36;transform:rotate(-14deg);left:-500px;top:1380px}
.rtick{position:absolute;left:0;right:0;top:1640px;height:96px;background:#fff;color:#0b0b0b;font:400 46px/96px Anton;white-space:nowrap;overflow:hidden;transform:rotate(-14deg);transform-origin:left;width:1400px}
.hook{font-family:Anton;font-weight:400;font-size:190px;line-height:.95}
.big,.h2{font-family:Anton;font-weight:400;text-transform:uppercase;font-size:120px;line-height:.98}
.when{background:#ff2d36;color:#fff !important;align-self:flex-start;padding:12px 24px;border-radius:8px;font-weight:800}
.card{background:#fff;color:#0b0b0b;border:0}
.card .li,.card .tx,.card .chat{color:#0b0b0b}
.cta{font-family:Anton;font-weight:400;text-transform:uppercase;font-size:70px}
""",
 "messages": """
.glow1,.glow2{display:none}
body{background:linear-gradient(170deg,#fbeef0,#f3d9de)}
.sc{justify-content:center}
.hook{text-align:center;font-size:120px}
.h2,.big{align-self:flex-end;background:#7a1f35;color:#fff;border-radius:50px;border-bottom-right-radius:14px;padding:36px 48px;font-size:70px;max-width:900px}
.h2 .grad,.big .grad{color:#ffd6de}
.card{background:#fff;border:0;border-radius:50px;border-bottom-left-radius:14px;box-shadow:0 8px 24px rgba(122,31,53,.10);align-self:flex-start;max-width:900px}
.when{align-self:center;text-transform:uppercase;letter-spacing:3px;color:#9a6070 !important}
.lbl{font-family:Caveat;font-size:48px;letter-spacing:0;text-transform:none;color:#b0465e}
.rinput{position:absolute;left:70px;right:70px;top:1500px;height:96px;border-radius:48px;background:#fff;display:flex;align-items:center;padding:0 18px 0 44px;font:400 34px Inter;color:#b9919b;box-shadow:0 8px 24px rgba(122,31,53,.10)}
.rinput b{margin-left:auto;width:66px;height:66px;border-radius:50%;background:#7a1f35;color:#fff;font:700 34px/66px Inter;text-align:center}
.cta{background:#fff;border-radius:40px;padding:22px 34px;align-self:flex-start;box-shadow:0 8px 24px rgba(122,31,53,.08)}
""",
 "manifeste": """
.glow1,.glow2{display:none}
.hook{font-size:150px;line-height:.98}
.big,.h2{text-transform:uppercase;font-size:104px;line-height:1.0}
.rrule{position:absolute;left:88px;top:1430px;width:260px;height:16px;background:#fff}
.card{background:none;border:0;border-left:10px solid #fff;border-radius:0;padding:10px 0 10px 40px}
.when{font-family:'JetBrains Mono';letter-spacing:0;color:#8a8a8a !important;text-transform:none}
.li .dot{border-radius:0;background:#fff}
""",
 "fiche": """
.glow1,.glow2{display:none}
.rpaper{position:absolute;left:56px;right:56px;top:220px;bottom:340px;background:#f6efe1;border-radius:24px;box-shadow:0 30px 60px rgba(0,0,0,.35)}
.rhead{position:absolute;left:110px;right:110px;top:270px;display:flex;justify-content:space-between;font:800 24px Inter;letter-spacing:4px;color:#7a6a45;padding-bottom:22px;border-bottom:3px dotted #c8b98f}
.sc{left:110px;right:110px;top:360px;bottom:400px;color:#123d2e}
.hook,.big,.h2,.fh{color:#123d2e}
.grad{color:#b8862b !important;font-style:italic}
.when,.sec .st{color:#7a6a45 !important}
.card{background:#fffaf0;border:3px solid #123d2e}
.li,.tx,.chat,.sub{color:#28473a !important}
.li .dot{background:#b8862b;border-radius:4px}
.top .brand{color:#f3ead8}
.cta{color:#123d2e}
""",
}

def reel_decor(layout, theme):
    h = _h(theme.get("handle", ""))
    if layout == "terminal":
        return ("<div class='rwin'><div class='rbar'><i style='background:#ff5f57'></i><i style='background:#febc2e'></i><i style='background:#28c840'></i>"
                f"<span style=\"flex:1;text-align:center;font:400 26px 'JetBrains Mono';color:#7fa891;margin-right:90px\">{h}.sh</span></div></div>")
    if layout == "sport":
        return f"<div class='rslash'></div><div class='rtick'>{'ZÉRO SALLE · ZÉRO EXCUSE · ' * 4}</div>"
    if layout == "messages":
        return "<div class='rinput'>Écris un message…<b>↑</b></div>"
    if layout == "manifeste":
        return "<div class='rrule'></div>"
    if layout == "fiche":
        return "<div class='rpaper'></div><div class='rhead'><span>REVENUS MALINS</span><span>FICHE PRATIQUE</span></div>"
    return ""
