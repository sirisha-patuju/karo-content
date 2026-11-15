# Karo content engine (read this fully every run)

Goal: grow @karo.app.official and get the first 100 real signups. Karo is an email and Google Calendar assistant (Gmail + Calendar via chat). Signup: https://karo-early-access.lovable.app (link in bio). Instagram captions are not clickable, so the CTA is always: comment "Karo" (a Make scenario auto-replies with the bio-link pointer).

## Hard rules
- VARIETY (Siri, Nov 15): every post is a different real situation (different person, moment, Karo job, hook style) with the same idea underneath. See engine/situations.md. Posts that repeat the generic inbox-overload story, or the same persona or job as a recent post, are not allowed.
- POSITIONING (Siri, Nov 15): Karo is a SERVICE, never described as an AI tool, AI agent, bot, app or software. Say what it does for the person: "takes care of your email and calendar", "handles your inbox", "replies, reschedules and clears the clutter for you". No tech words (AI, LLM, agent, automation) in captions, voice lines, on-screen text or taglines. Write for someone who has never heard of AI: plain benefits, time saved, stress removed. Reel taglines (reveal and cta scenes): e.g. "Your inbox and calendar, taken care of." Reveal voice: "So we built Karo, a service that takes care of your email and calendar."
- No em dashes anywhere. English names only. Never call Karo an "AI agent". Never say "Karo means do it in Hindi".
- Every post: NEW names, numbers, situations. Check logs/content-log.csv and never reuse a name, number or hook. Used so far: Hannah, Alvarez, Brooks, Nguyen, Rachel Moore, Tom Bennett, Chloe Parker, 563, 2041, Olivia, Daniel, Grace, Henry, Isabel, Jack, Karen, Leo, Maya, Noah, Paula, Marcus, Elena, 2316, 1326, 612, 1000.
- Brand: bg indigo #120056, blue #2563EB, orange #F97316 only on the CTA button.
- Open with a strong hook (the first line must stop the scroll). Natural full sentences.
- Don't invent stats or testimonials. No fake user quotes. Claims must be true of Karo (drafts replies in your tone, moves events and sends invites, clears promotions, bulk follow-up drafts, works in Indian languages).
- Never ask the user for keys. Never touch payment. Never post anything that is not Karo content.

## Slots (IST) and formats
08:30 reel, 12:30 carousel, 16:00 image, 19:00 carousel, 21:30 reel. Each run handles ONE slot (named in the task prompt).

## Run procedure
1. add_repo sirisha-patuju/karo-content (push), clone to /home/claude/karo-content (depth 1), read engine/ENGINE.md, logs/content-log.csv, logs/learnings.md.
2. Research (WebSearch standard): 1-2 searches on current Instagram formats/hooks that work for productivity/AI-tool/startup accounts, and what competitors (Fyxer, Superhuman, Shortwave) post. Use learnings.md first: do more of what the weekly review says works.
3. Pick the situation: read engine/situations.md fully (VARIETY is a hard rule). Choose a persona, real moment and Karo job that are NOT in the last 12 rows of logs/content-log.csv (columns persona, job), and a hook style not used in the last 3 posts. Every post must feel like a different real moment from a different person's day, with the same idea underneath. Never write a generic 'too many emails' post.
4. Create assets. Carousel/image: engine/visual.py (read the VISUAL POSTS section below), static pictures only (NO music, NO slideshow reels). Never plain text on a gradient. Reel: follow the REEL section below (story reel with engine/story, never silent). Look at the output before posting (carousel slide, or the reel preview sheet).
5. Save to media/YYYY-MM-DD/<slot>-*.jpg|mp4, commit and push to main.
6. Post: Make scenario 7035693 via scenarios_run (responsive false). Inputs: type (reel|photo|carousel), media_url (raw.githubusercontent.com/sirisha-patuju/karo-content/main/...), caption, thumb_offset (ms, reel cover frame), files (carousel: [{media_type:"IMAGE", image_url}]).
7. After 90 seconds, executions_list / executions_get-detail to confirm SUCCESS. On failure, read the error, fix once, retry once, then log FAILED.
8. Append a row to logs/content-log.csv: date,time_ist,type,hook,names_used,numbers_used,status,persona,job (the log header has these columns; persona = who the post is about, job = what Karo did for them). Commit and push.
9. Log to the Google Sheet "Karo" (id 1IVcI4cNgWWX_ixD18YbeYGyWndT_s9V3WdsbVrop3Zs), tab "Content data", through the same Make scenario 7035693 (scenarios_run, responsive true) with data:
   type "sheet", gs_method "POST", gs_url "spreadsheets/1IVcI4cNgWWX_ixD18YbeYGyWndT_s9V3WdsbVrop3Zs/values/'Content data'!A1:append?valueInputOption=RAW", gs_body (JSON text) {"values":[[date,time_ist,type,hook,caption_first_line,"","","","","",""]]}.
   Columns: Date, Time IST, Type, Hook, Caption, Post ID, Reach, Likes, Saves, Shares, Comments (leave the last 6 empty).
   Make free plan has 1000 operations a month. Use at most 2 Make runs per slot (post + sheet row). Never poll Make in loops.
10. At the 08:30 slot only: read signups with Google Drive read_file_content on the same sheet (tab "Sign ups"), count real rows (ignore sirishashankar2020@gmail.com test), append "signups_total=N on DATE" to logs/learnings.md, commit and push.
11. One-line report only.

## Caption pattern
Line 1 hook (feeling or pain, not a product description). 2-3 short lines. CTA: first 100 people, comment "Karo". 3-4 hashtags. Different wording every time.


## REEL (story reels, mandatory for every reel slot)
Siri's rules (Nov 15): every reel is a completely DIFFERENT story with different visuals, never the same video with new words. Under 30 seconds (the builder enforces 20 to 29.8). Starts with a hook, ends with the CTA scene. People must FEEL something: a real person, a real moment, a small relief at the end. Karo is a service, never "AI", "agent", "tool" or "app", and no tech talk. Never the same persona, job, visual order, theme or voice lines as the last reels.
Engine: engine/story/ (build.py, template.html, sound.py, example_spec.json). Voice: Kokoro af_heart (warm), speed 1.0 (spec fields "voice", "speed"; never am_michael). Captions follow the voice word by word. Sound is soft: warm piano bed, gentle swish between scenes, tiny typing ticks, a soft chime on success. No drums, no risers, no loud effects.
Needs: pip install kokoro-onnx soundfile scipy numpy pillow --break-system-packages (playwright, chromium, ffmpeg are preinstalled). build.py downloads the voice model from GitHub the first time (about 350 MB, a minute).
Procedure:
1. Pick the situation from engine/situations.md (persona, real moment, Karo job; not in the last 12 rows of the log).
2. Write a NEW spec JSON (see engine/story/example_spec.json for every field): 5 or 6 scenes, each = ONE short voice line (5 to 14 words) + ONE visual. Total voice about 45 to 60 words (about 2.5 words per second). Story arc: (1) the hook, the problem moment with a time stamp kicker; (2) the stakes; (3) the one sentence the person typed (chat); (4) the result shown (calendar events moving from f to t, a sent mail, an inbox clearing, notifications with checks); (5) the feeling payoff (moment scene: a time and one human line); (6) cta scene, last, voice: "Karo takes care of your <their thing>. Comment Karo for early access." in different wording each time. Visual kinds: inbox, calendar, chat, mail, notifs, moment, cta. Change the kinds, the order, the theme (indigo, midnight, violet, ocean), the seed and the key (0 to 2) every reel. All names, senders, subjects, numbers are the persona's own and NEW. English names only, no em dashes. Voice lines are natural spoken sentences a person would say to a friend, no technical words. Chat user text under 45 characters.
3. Preview: python3 engine/story/build.py spec.json /tmp/reel1 --preview (about 40 s). Read /tmp/reel1/preview.jpg and fix overflow, wrapped or cut-off text.
4. Full build: python3 engine/story/build.py spec.json /tmp/reel1 (about 4 to 6 minutes; start early). It fails by itself if the length is outside 20 to 29.8 s: shorten or lengthen the voice lines. Output: reel.mp4, cover.jpg, reel.json (thumb_offset_ms).
5. Look at cover.jpg. Copy reel.mp4 and cover.jpg to media/YYYY-MM-DD/<slot>-reel.mp4 and beside it. Commit and push. Post with type "reel", media_url raw URL, caption, thumb_offset = thumb_offset_ms.
6. If the render fails, fix once and retry once. If it still fails, post NOTHING for this slot, log FAILED with the reason, and say so in the report. Never post a silent or fallback reel.
7. Instagram caption for a reel: a hook line about the person's moment, 2-3 short lines, CTA: first 100 people, comment "Karo", 3-4 hashtags.

## VISUAL POSTS (carousels and the 16:00 image, mandatory)
Siri's rule (Nov 15): people must SEE something, not read a text post. Every slide shows a real product-style visual: an inbox full of emails, a calendar clash, a phone chat with Karo, a before and after inbox, a flood of notification cards around a big number, a sent follow-up email, or a phone with the typed prompt. Never a slide that is only text on a background. Max one short headline per slide (under 8 words) and one big visual.
Engine: engine/visual.py. Run: python3 engine/visual.py spec.json /tmp/post1  (about 10 s, writes c1.jpg ...; 1080x1350). Kinds and fields are in the docstring at the top of visual.py: inbox, calendar, chat, beforeafter, stat, mail, cta.
Carousel (5 to 7 slides): slide 1 = scroll-stopper visual (inbox badge number, calendar clash or stat flood), slides 2 to 5 = the story told with chat / mail / beforeafter visuals (a different kind on each slide, never the same kind twice in a row), last slide = cta (orange button, comment "Karo"). The 16:00 image post = ONE slide, the strongest visual (inbox with badge, stat flood or beforeafter) plus a one-line hook.
All names, numbers, subjects and replies in the visuals are NEW every time (see used list), English names only, no em dashes, no AI words (service positioning). Reply text must be true of Karo. Read the output pictures with the Read tool (contact sheet is fine) and fix overlap or cut-off text before posting.
