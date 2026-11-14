import asyncio
from playwright.async_api import async_playwright
CSS="""
*{margin:0;box-sizing:border-box}body{width:1080px;height:1350px;font-family:'Inter','Helvetica Neue',Arial,sans-serif;background:#120056;color:#fff;position:relative;overflow:hidden}
.b1{position:absolute;width:900px;height:900px;border-radius:50%;background:#2563EB;filter:blur(160px);opacity:.55;top:-300px;right:-300px}
.b2{position:absolute;width:700px;height:700px;border-radius:50%;background:#4c1d95;filter:blur(150px);opacity:.6;bottom:-250px;left:-250px}
.w{position:absolute;inset:0;padding:110px 90px;display:flex;flex-direction:column;justify-content:center}
.tag{position:absolute;top:70px;left:90px;font-size:34px;font-weight:700;letter-spacing:.5px;display:flex;align-items:center;gap:16px}
.k{width:54px;height:54px;border-radius:15px;background:#2563EB;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:800}
.pg{position:absolute;top:80px;right:90px;font-size:28px;opacity:.6}
h1{font-size:104px;line-height:1.05;font-weight:800;letter-spacing:-2px}
h2{font-size:76px;line-height:1.1;font-weight:800;letter-spacing:-1px}
.sub{font-size:44px;opacity:.8;margin-top:40px;line-height:1.3}
.pill{background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.25);border-radius:70px;padding:34px 44px;font-size:46px;margin-bottom:44px}
.card{background:#fff;color:#111;border-radius:36px;padding:48px;font-size:42px;line-height:1.4;box-shadow:0 40px 90px rgba(0,0,0,.45)}
.card b{color:#2563EB}.chip{display:inline-block;margin-top:30px;background:#e8f0ff;color:#2563EB;font-weight:700;border-radius:40px;padding:14px 30px;font-size:34px}
.big{font-size:230px;font-weight:800;color:#7fb0ff;line-height:1}
.btn{display:inline-block;background:#F97316;color:#fff;font-size:56px;font-weight:800;padding:40px 70px;border-radius:70px;margin-top:60px}
.o{color:#7fb0ff}
"""
def page(inner,n=None):
    pg=f'<div class="pg">{n}/5</div>' if n else ''
    return f'<html><style>{CSS}</style><body><div class="b1"></div><div class="b2"></div><div class="tag"><div class="k">K</div>Karo</div>{pg}<div class="w">{inner}</div></body></html>'
slides={
"c1":page('<h1>Your inbox is not the problem.</h1><div class="sub">Opening it is. Swipe to see what to do instead.</div>',1),
"c2":page('<div class="pill">Reply to Marcus about the invoice</div><div class="card"><b>Draft for Marcus Hill</b><br><br>Hi Marcus, thanks for sending this over. I have checked the invoice and it looks right. Payment goes out on Friday.<br><span class="chip">Written in your tone</span></div>',2),
"c3":page('<div class="pill">Move my call with Elena to Friday at 3 PM</div><div class="card"><b>Call with Elena Ward</b><br>Thursday 11:00 AM  to  <b>Friday 3:00 PM</b><br><span class="chip">Invite sent to Elena</span></div>',3),
"c4":page('<div class="pill">Clear all the newsletters</div><div class="sub" style="margin:0 0 20px">Newsletters</div><div class="big">612 <span style="font-size:90px;color:#fff">to</span> 0</div><div class="sub">Cleared in one message.</div>',4),
"c5":page('<h1>Want it for your own inbox?</h1><div class="sub">We are letting in our first 100 people.</div><div class="btn">Comment "Karo"</div>',5),
"s1":page('<h1>You have <span class="o">1,000</span> unread emails.</h1><div class="sub" style="font-size:56px">You need one sentence, not a free weekend.</div><div class="btn" style="align-self:flex-start">Comment "Karo"</div>'),
}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1080,'height':1350})
        for k,h in slides.items():
            await pg.set_content(h);await pg.wait_for_timeout(200)
            await pg.screenshot(path=k+'.jpg',type='jpeg',quality=93)
        await b.close()
asyncio.run(main())
