#!/usr/bin/env python3
"""Render Karo carousel / image slides WITH real product visuals (never plain text on a gradient).
Usage: python3 engine/visual.py spec.json outdir [height]      (default 1350 = 4:5, 1080 wide, JPEG)
spec = {"slides":[{"name":"c1","kind":"...", ...}]}

Every slide = one short headline + one big visual (inbox, calendar, phone chat, before/after, notifications).
Kinds and fields:
 inbox      title, sub, badge ("563"), rows [[sender, subject, time], ...] (6 to 9 rows, unread dots)
 calendar   title, sub, hours ["9 AM","10 AM",...], events [[label, startRow, spanRows, col(0-2)], ...], clash ("3 meetings. Same hour.")
 chat       title(optional small), user (what was typed), reply_title, reply_lines [..], chip (optional "Sent" / "Booked")
 beforeafter title, before_count ("563 unread"), after_count ("0 unread"), rows [[sender, subject, time], ...] (3 to 4)
 stat       title(label under number), big ("847"), notifs [[sender, subject], ...] (3 to 5)
 mail       title(optional), mail_to, mail_subject, mail_body (a real-looking sent email card), chip ("Sent by Karo")
 cta        title, sub, user (typed prompt shown in phone), btn (default Comment "Karo")
Brand: indigo #120056, blue #2563EB, orange #F97316 ONLY on the cta button. No em dashes. English names only."""
import sys, json, asyncio, html, os
from playwright.async_api import async_playwright
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launch", "fonts")
COL = ['#2563EB', '#7c3aed', '#0891b2', '#db2777', '#059669', '#d97706', '#4f46e5', '#e11d48']
CSS = f"""
@font-face{{font-family:KI;src:url('file://{FD}/Inter-Medium.otf');font-weight:500}}
@font-face{{font-family:KI;src:url('file://{FD}/Inter-SemiBold.otf');font-weight:600}}
@font-face{{font-family:KI;src:url('file://{FD}/Inter-Bold.otf');font-weight:700}}
@font-face{{font-family:KI;src:url('file://{FD}/Inter-ExtraBold.otf');font-weight:800}}
@font-face{{font-family:KI;src:url('file://{FD}/Inter-Black.otf');font-weight:900}}
*{{margin:0;box-sizing:border-box}}
body{{width:1080px;height:var(--h,1350px);font-family:KI,Arial,sans-serif;background:#120056;color:#fff;position:relative;overflow:hidden}}
.b1{{position:absolute;width:1000px;height:1000px;border-radius:50%;background:#2563EB;filter:blur(170px);opacity:.5;top:-380px;right:-340px}}
.b2{{position:absolute;width:800px;height:800px;border-radius:50%;background:#5b21b6;filter:blur(160px);opacity:.55;bottom:-300px;left:-300px}}
.tag{{position:absolute;top:64px;left:80px;font-size:34px;font-weight:700;display:flex;align-items:center;gap:16px;z-index:5}}
.k{{width:52px;height:52px;border-radius:15px;background:#2563EB;display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:800}}
.pg{{position:absolute;top:74px;right:80px;font-size:28px;opacity:.6;z-index:5}}
.head{{position:absolute;left:80px;right:80px;top:170px;z-index:4}}
h1{{font-size:112px;line-height:1.0;font-weight:900;letter-spacing:-3.5px}}
h1.sm{{font-size:84px;letter-spacing:-2.5px}}
.sub{{font-size:44px;font-weight:500;opacity:.85;margin-top:28px;line-height:1.25}}
.hl{{color:#a5b9ff}}
/* inbox window */
.win{{position:absolute;left:70px;right:70px;background:#fff;color:#111;border-radius:34px;box-shadow:0 50px 110px rgba(0,0,0,.55);overflow:hidden;z-index:2}}
.wbar{{height:76px;background:#f3f4f8;display:flex;align-items:center;padding:0 30px;gap:12px;border-bottom:1px solid #e5e7ee}}
.dot{{width:18px;height:18px;border-radius:50%}}
.wt{{margin-left:20px;font-weight:700;font-size:28px;color:#555}}
.row{{display:flex;align-items:center;gap:24px;padding:24px 32px;border-bottom:1px solid #eef0f5;height:112px}}
.av{{width:68px;height:68px;border-radius:50%;color:#fff;font-weight:800;font-size:32px;display:flex;align-items:center;justify-content:center;flex:none}}
.tx{{flex:1;min-width:0}}
.sn{{font-weight:800;font-size:33px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sj{{font-size:29px;color:#555;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:4px}}
.tm{{font-size:25px;color:#888;font-weight:600;flex:none}}
.ud{{width:18px;height:18px;border-radius:50%;background:#2563EB;flex:none}}
.badge{{position:absolute;z-index:6;background:#e11d48;color:#fff;font-weight:900;font-size:84px;padding:6px 38px;border-radius:70px;box-shadow:0 20px 50px rgba(225,29,72,.5);transform:rotate(-6deg)}}
/* calendar */
.cal{{position:absolute;left:70px;right:70px;background:#fff;color:#111;border-radius:34px;box-shadow:0 50px 110px rgba(0,0,0,.55);overflow:hidden;z-index:2}}
.chd{{height:84px;background:#f3f4f8;display:flex;align-items:center;padding:0 34px;font-weight:800;font-size:32px;color:#333;border-bottom:1px solid #e5e7ee}}
.grid{{position:relative}}
.hr{{position:absolute;left:0;right:0;border-top:1px solid #e7e9f0;font-size:24px;color:#999;font-weight:600;padding:6px 0 0 26px}}
.ev{{position:absolute;border-radius:16px;color:#fff;font-weight:800;font-size:30px;padding:14px 18px;box-shadow:0 10px 24px rgba(0,0,0,.22);overflow:hidden}}
.clash{{position:absolute;z-index:6;background:#e11d48;color:#fff;font-weight:900;font-size:46px;padding:20px 40px;border-radius:60px;box-shadow:0 20px 50px rgba(225,29,72,.5);transform:rotate(-4deg)}}
/* phone */
.ph{{position:absolute;left:150px;right:150px;background:#0b0430;border:10px solid #2b2470;border-radius:84px;box-shadow:0 60px 120px rgba(0,0,0,.6);overflow:hidden;z-index:2}}
.notch{{width:210px;height:44px;background:#000;border-radius:30px;margin:20px auto 0}}
.ph .top{{display:flex;align-items:center;gap:14px;padding:26px 36px 18px;font-weight:800;font-size:36px}}
.ph .top .k{{width:46px;height:46px;font-size:26px;border-radius:13px}}
.msgs{{padding:20px 30px;display:flex;flex-direction:column;gap:26px}}
.u{{align-self:flex-end;background:#fff;color:#120056;font-weight:700;font-size:35px;padding:26px 32px;border-radius:38px 38px 10px 38px;max-width:92%;line-height:1.25}}
.bot{{align-self:flex-start;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);font-weight:500;font-size:33px;padding:28px 32px;border-radius:38px 38px 38px 10px;max-width:96%;line-height:1.35}}
.bot b{{font-weight:800;display:block;margin-bottom:10px;font-size:36px}}
.ok{{display:inline-flex;align-items:center;gap:12px;margin-top:20px;background:#16a34a;color:#fff;font-weight:800;font-size:30px;padding:12px 26px;border-radius:40px}}
.inp{{margin:8px 30px 30px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:60px;padding:24px 34px;font-size:30px;color:rgba(255,255,255,.55);display:flex;justify-content:space-between;align-items:center}}
.send{{width:54px;height:54px;border-radius:50%;background:#2563EB;color:#fff;display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:800}}
/* before after */
.ba{{position:absolute;left:70px;right:70px;z-index:2;display:flex;flex-direction:column;gap:30px}}
.pn{{background:#fff;color:#111;border-radius:30px;overflow:hidden;box-shadow:0 40px 90px rgba(0,0,0,.5)}}
.ph2{{display:flex;justify-content:space-between;align-items:center;padding:22px 32px;font-weight:900;font-size:36px;background:#f3f4f8;border-bottom:1px solid #e5e7ee}}
.pill{{padding:8px 26px;border-radius:40px;color:#fff;font-weight:900;font-size:34px}}
.pn .row{{height:98px;padding:16px 28px}}
.pn .av{{width:58px;height:58px;font-size:27px}}
.pn .sn{{font-size:30px}}.pn .sj{{font-size:26px}}
.clean{{padding:46px 32px;text-align:center;font-weight:800;font-size:40px;color:#16a34a}}
/* notif cards */
.big{{position:absolute;left:0;right:0;text-align:center;font-weight:900;color:#fff;line-height:.9;z-index:3;text-shadow:0 20px 60px rgba(0,0,0,.4)}}
.nf{{position:absolute;z-index:2;background:rgba(255,255,255,.96);color:#111;border-radius:26px;padding:20px 26px;display:flex;align-items:center;gap:18px;box-shadow:0 30px 70px rgba(0,0,0,.45);width:560px}}
.nf .av{{width:56px;height:56px;font-size:26px}}.nf .sn{{font-size:28px}}.nf .sj{{font-size:25px}}
/* mail */
.mail{{position:absolute;left:80px;right:80px;background:#fff;color:#111;border-radius:34px;padding:44px 48px;box-shadow:0 50px 110px rgba(0,0,0,.55);z-index:2}}
.mail .to{{font-size:28px;color:#777;font-weight:600}}.mail .to b{{color:#111}}
.mail .su{{font-size:42px;font-weight:900;margin:14px 0 24px;line-height:1.15}}
.mail .bd{{font-size:34px;line-height:1.45;color:#222}}
.chipg{{display:inline-flex;align-items:center;gap:12px;margin-top:26px;background:#dcfce7;color:#15803d;font-weight:800;font-size:30px;padding:12px 28px;border-radius:40px}}
.btn{{display:inline-block;background:#F97316;color:#fff;font-size:58px;font-weight:900;padding:40px 76px;border-radius:80px;box-shadow:0 24px 60px rgba(249,115,22,.45)}}
"""
def e(s): return html.escape(str(s if s is not None else ""))
def rows_html(rows, unread=True):
    o = ""
    for i, r in enumerate(rows):
        c = COL[(i * 3 + len(r[0])) % len(COL)]
        o += (f'<div class="row"><div class="av" style="background:{c}">{e(r[0][:1])}</div>'
              f'<div class="tx"><div class="sn">{e(r[0])}</div><div class="sj">{e(r[1])}</div></div>'
              f'<div class="tm">{e(r[2] if len(r) > 2 else "")}</div>' + ('<div class="ud"></div>' if unread else '') + '</div>')
    return o
def head(s, small=False):
    t = e(s.get("title", ""))
    cls = "sm" if small else ""
    sub = f'<div class="sub">{e(s["sub"])}</div>' if s.get("sub") else ""
    return f'<div class="head"><h1 class="{cls}">{t}</h1>{sub}</div>' if t else ""
def phone(top, inner, bottom_input=None, t=640, h=None):
    inp = f'<div class="inp"><span>{e(bottom_input)}</span><div class="send">&#8593;</div></div>' if bottom_input is not None else ""
    return (f'<div class="ph" style="top:{t}px;{"height:%dpx;" % h if h else ""}"><div class="notch"></div>'
            f'<div class="top"><div class="k">K</div>Karo</div><div class="msgs">{inner}</div>{inp}</div>')
def body(s, i, n, H):
    k = s["kind"]; out = ""
    if k == "inbox":
        out = head(s) + f'<div class="win" style="top:700px;height:{H-700+60}px"><div class="wbar"><div class="dot" style="background:#ff5f57"></div><div class="dot" style="background:#febc2e"></div><div class="dot" style="background:#28c840"></div><div class="wt">Inbox</div></div>{rows_html(s["rows"])}</div>'
        if s.get("badge"): out += f'<div class="badge" style="right:90px;top:610px">{e(s["badge"])}</div>'
    elif k == "calendar":
        hrs = s["hours"]; RH = 132; gh = RH * len(hrs)
        g = "".join(f'<div class="hr" style="top:{j*RH}px">{e(h)}</div>' for j, h in enumerate(hrs))
        ev = ""
        for j, (lab, st, sp, col) in enumerate(s["events"]):
            w = 250; left = 170 + col * 262
            ev += f'<div class="ev" style="top:{st*RH+6}px;height:{sp*RH-12}px;left:{left}px;width:{w}px;background:{COL[(j*2+1)%len(COL)]}">{e(lab)}</div>'
        out = head(s) + f'<div class="cal" style="top:640px"><div class="chd">Today</div><div class="grid" style="height:{gh}px">{g}{ev}</div></div>'
        if s.get("clash"): out += f'<div class="clash" style="left:90px;top:1010px">{e(s["clash"])}</div>'
    elif k == "chat":
        rl = "".join(f'{e(x)}<br>' for x in s.get("reply_lines", []))
        chip = f'<div class="ok">&#10003; {e(s["chip"])}</div>' if s.get("chip") else ""
        inner = f'<div class="u">{e(s["user"])}</div><div class="bot"><b>{e(s.get("reply_title",""))}</b>{rl}{chip}</div>'
        top = 500 if s.get("title") else 150
        out = head(s, small=True) + phone(top, inner, "Message Karo...", t=top)
    elif k == "beforeafter":
        out = head(s) + (f'<div class="ba" style="top:560px"><div class="pn"><div class="ph2"><span>Before</span><span class="pill" style="background:#e11d48">{e(s["before_count"])}</span></div>{rows_html(s["rows"], True)}</div>'
              f'<div class="pn"><div class="ph2"><span>After Karo</span><span class="pill" style="background:#16a34a">{e(s["after_count"])}</span></div><div class="clean">&#10003; Inbox cleared</div></div></div>')
    elif k == "stat":
        nf = ""; pos = [(40, 150), (470, 300), (40, 1090), (470, 1190)]
        for j, nt in enumerate(s["notifs"][:4]):
            x, y = pos[j]; c = COL[(j * 3 + 2) % len(COL)]
            nf += f'<div class="nf" style="left:{x}px;top:{y}px;transform:rotate({(-3,3,-2,2,-3)[j]}deg)"><div class="av" style="background:{c}">{e(nt[0][:1])}</div><div class="tx"><div class="sn">{e(nt[0])}</div><div class="sj">{e(nt[1])}</div></div></div>'
        fs = 400 if len(str(s["big"])) <= 3 else 330
        out = nf + f'<div class="big" style="top:420px;font-size:{fs}px">{e(s["big"])}</div><div class="big" style="top:{420+fs}px;font-size:84px;letter-spacing:-2px;line-height:1.05;padding:0 90px">{e(s["title"])}</div>'
    elif k == "mail":
        chip = f'<div class="chipg">&#10003; {e(s["chip"])}</div>' if s.get("chip") else ""
        out = head(s) + f'<div class="mail" style="top:{560 if s.get("title") else 220}px"><div class="to">To: <b>{e(s["mail_to"])}</b></div><div class="su">{e(s["mail_subject"])}</div><div class="bd">{e(s["mail_body"])}</div>{chip}</div>'
    elif k == "cta":
        inner = f'<div class="u">{e(s["user"])}</div>'
        out = head(s) + phone(600, inner, "Message Karo...", t=600) + f'<div style="position:absolute;left:80px;right:80px;top:1090px;z-index:4"><div class="btn">{e(s.get("btn") or "Comment \"Karo\"")}</div></div>'
    pg = f'<div class="pg">{i}/{n}</div>' if n > 1 else ""
    return f'<html style="--h:{H}px"><style>{CSS}</style><body><div class="b1"></div><div class="b2"></div><div class="tag"><div class="k">K</div>Karo</div>{pg}{out}</body></html>'
async def main(spec, out, H=1350):
    sl = spec["slides"]
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": H})
        for i, s in enumerate(sl, 1):
            path = os.path.join(out, "_tmp.html")
            open(path, "w").write(body(s, i, len(sl) if H <= 1400 else 1, H))
            await pg.goto("file://" + os.path.abspath(path)); await pg.wait_for_timeout(300)
            await pg.screenshot(path=os.path.join(out, f'{s["name"]}.jpg'), type="jpeg", quality=93)
        await b.close()
    os.remove(os.path.join(out, "_tmp.html"))
if __name__ == "__main__":
    os.makedirs(sys.argv[2], exist_ok=True)
    asyncio.run(main(json.load(open(sys.argv[1])), sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1350))
