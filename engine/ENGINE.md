# Karo content engine (read this fully every run)

Goal: grow @karo.app.official and get the first 100 real signups. Karo is an email and Google Calendar assistant (Gmail + Calendar via chat). Signup: https://karo-early-access.lovable.app (link in bio). Instagram captions are not clickable, so the CTA is always: comment "Karo" (a Make scenario auto-replies with the bio-link pointer).

## Hard rules
- No em dashes anywhere. English names only. Never call Karo an "AI agent". Never say "Karo means do it in Hindi".
- Every post: NEW names, numbers, situations. Check logs/content-log.csv and never reuse a name, number or hook. Used so far: Olivia, Daniel, Grace, Henry, Isabel, Jack, Karen, Leo, Maya, Noah, Paula, Marcus, Elena, 2316, 1326, 612, 1000.
- Brand: bg indigo #120056, blue #2563EB, orange #F97316 only on the CTA button.
- Open with a strong hook (the first line must stop the scroll). Natural full sentences.
- Don't invent stats or testimonials. No fake user quotes. Claims must be true of Karo (drafts replies in your tone, moves events and sends invites, clears promotions, bulk follow-up drafts, works in Indian languages).
- Never ask the user for keys. Never touch payment. Never post anything that is not Karo content.

## Slots (IST) and formats
08:30 reel, 12:30 carousel, 16:00 image, 19:00 carousel, 21:30 reel. Each run handles ONE slot (named in the task prompt).

## Run procedure
1. add_repo sirisha-patuju/karo-content (push), clone to /home/claude/karo-content (depth 1), read engine/ENGINE.md, logs/content-log.csv, logs/learnings.md.
2. Research (WebSearch standard): 1-2 searches on current Instagram formats/hooks that work for productivity/AI-tool/startup accounts, and what competitors (Fyxer, Superhuman, Shortwave) post. Use learnings.md first: do more of what the weekly review says works.
3. Pick an angle: pain point (inbox overload, follow-ups, scheduling back and forth, promotions pile, writing in the right tone), format, hook. Rotate angles so no two posts in a day repeat.
4. Create assets with engine/render.py (carousel/image) or engine/reel.py (reel). Look at at least one output image before posting.
5. Save to media/YYYY-MM-DD/<slot>-*.jpg|mp4, commit and push to main.
6. Post: Make scenario 7035693 via scenarios_run (responsive false). Inputs: type (reel|photo|carousel), media_url (raw.githubusercontent.com/sirisha-patuju/karo-content/main/...), caption, thumb_offset (ms, reel cover frame), files (carousel: [{media_type:"IMAGE", image_url}]).
7. After 90 seconds, executions_list / executions_get-detail to confirm SUCCESS. On failure, read the error, fix once, retry once, then log FAILED.
8. Append a row to logs/content-log.csv: date,time,type,hook,caption_first_line,names_used,numbers_used,status. Commit and push.
9. One-line report only.

## Caption pattern
Line 1 hook (feeling or pain, not a product description). 2-3 short lines. CTA: first 100 people, comment "Karo". 3-4 hashtags. Different wording every time.
