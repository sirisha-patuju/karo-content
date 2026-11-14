#!/usr/bin/env python3
"""Render Karo posts. Usage: python3 engine/render.py spec.json outdir
spec = {"slides":[{"name":"c1","kind":"hook|ask|stat|cta","title":"","sub":"","prompt":"","card_title":"","card_body":"","chip":"","big":"","btn":""}]}
Brand: indigo #120056 bg, blue #2563EB, orange #F97316 ONLY for CTA button. 1080x1350 JPEG."""
import sys, json, asyncio, html
from playwright.async_api import async_playwright
CSS="""*{margin:0;box-sizing:border-box}body{width:1080px;height:var(--h,1350px);font-family:'Inter','Helvetica Neue',Arial,sans-serif;background:#120056;color:#fff;position:relative;overflow:hidden}
.b1{position:absolute;width:900px;height:900px;border-radius:50%;background:#2563EB;filter:blur(160px);opacity:.55;top:-300px;right:-300px}
.b2{position:absolute;width:700px;height:700px;border-radius:50%;background:#4c1d95;filter:blur(150px);opacity:.6;bottom:-250px;left:-250px}
.w{position:absolute;inset:0;padding:110px 90px;display:flex;flex-direction:column;justify-content:center}
.tag{position:absolute;top:70px;left:90px;font-size:34px;font-weight:700;display:flex;align-items:center;gap:16px}
.k{width:54px;height:54px;border-radius:15px;background:#2563EB;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:800}
.pg{position:absolute;top:80px;right:90px;font-size:28px;opacity:.6}
h1{font-size:104px;line-height:1.05;font-weight:800;letter-spacing:-2px}
.sub{font-size:44px;opacity:.8;margin-top:40px;line-height:1.3}
.pill{background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.25);border-radius:70px;padding:34px 44px;font-size:46px;margin-bottom:44px}
.card{background:#fff;color:#111;border-radius:36px;padding:48px;font-size:42px;line-height:1.4;box-shadow:0 40px 90px rgba(0,0,0,.45)}
.card b{color:#2563EB}.chip{display:inline-block;margin-top:30px;background:#e8f0ff;color:#2563EB;font-weight:700;border-radius:40px;padding:14px 30px;font-size:34px}
.big{font-size:230px;font-weight:800;color:#7fb0ff;line-height:1}
.btn{display:inline-block;background:#F97316;color:#fff;font-size:56px;font-weight:800;padding:40px 70px;border-radius:70px;margin-top:60px;align-self:flex-start}"""
def e(s): return html.escape(s or "")
def body(s,i,n):
    k=s.get("kind","hook"); out=""
    if k=="hook": out=f'<h1>{e(s["title"])}</h1><div class="sub">{e(s.get("sub"))}</div>'
    elif k=="ask": out=f'<div class="pill">{e(s["prompt"])}</div><div class="card"><b>{e(s.get("card_title"))}</b><br><br>{e(s.get("card_body"))}'+(f'<br><span class="chip">{e(s["chip"])}</span>' if s.get("chip") else '')+'</div>'
    elif k=="stat": out=f'<div class="pill">{e(s["prompt"])}</div><div class="big">{e(s["big"])}</div><div class="sub">{e(s.get("sub"))}</div>'
    elif k=="cta": out=f'<h1>{e(s["title"])}</h1><div class="sub">{e(s.get("sub"))}</div><div class="btn">{e(s.get("btn") or "Comment \"Karo\"")}</div>'
    pg=f'<div class="pg">{i}/{n}</div>' if n>1 else ''
    return f'<html><style>{CSS}</style><body><div class="b1"></div><div class="b2"></div><div class="tag"><div class="k">K</div>Karo</div>{pg}<div class="w">{out}</div></body></html>'
async def main(spec,out,H=1350):
    sl=spec["slides"]
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={"width":1080,"height":H})
        for i,s in enumerate(sl,1):
            await pg.set_content(body(s,i,1 if H>1400 else len(sl)).replace('<html>',f'<html style="--h:{H}px">')); await pg.wait_for_timeout(200)
            await pg.screenshot(path=f'{out}/{s["name"]}.jpg',type="jpeg",quality=93)
        await b.close()
if __name__=="__main__":
    import os; os.makedirs(sys.argv[2],exist_ok=True)
    asyncio.run(main(json.load(open(sys.argv[1])),sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1350))
