# Telegram Channel Spoiler Bot

A minimal, single-purpose Telegram bot that watches **one** channel, and
automatically reposts photos/videos with a spoiler overlay enabled, then
deletes the original (non-spoiler) post.

Built for low resource usage, no database, no admin panel, no commands —
just one job, done reliably.

## How it works

1. The bot must be an **admin** of the target channel (needs permission to
   post and to delete messages).
2. When a new channel post containing a photo or video arrives:
   - If it already has a spoiler, it's ignored (prevents infinite loops).
   - It is re-sent to the same channel using its existing `file_id`
     (no downloading/uploading of media — fast and cheap).
   - The new post has `has_spoiler=True`.
   - The original post is deleted.
3. Albums (media groups) are buffered briefly (~1.5s) so all items in the
   album are collected, then reposted together as a single spoilered album,
   and all original messages are deleted.

## Environment variables

| Variable    | Description                                              |
|-------------|-----------------------------------------------------------|
| `BOT_TOKEN` | Telegram bot token from @BotFather                         |
| `CHAT_ID`   | Numeric ID of the target channel (e.g. `-1001234567890`)   |
| `PORT`      | (optional, set automatically by Render) HTTP port to bind   |

## Local run

```bash
pip install -r requirements.txt
export BOT_TOKEN="123456:ABC..."
export CHAT_ID="-1001234567890"
python main.py
```

## Deploying on Render (Web Service)

1. Push this project to a GitHub repo.
2. Create a new **Web Service** on Render, pointing at the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Add environment variables `BOT_TOKEN` and `CHAT_ID` in the Render
   dashboard. Render injects `PORT` automatically — no need to set it.
6. Deploy. Render will hit `/` for health checks; the bot's tiny aiohttp
   server responds `OK` while Telegram polling runs alongside it.

## Notes

- Uses long polling (no webhook setup needed).
- If the connection to Telegram drops, polling automatically retries after
  a short delay.
- Make sure the bot is added as an **administrator** of the channel with
  "Post Messages" and "Delete Messages" permissions, otherwise reposting
  and deleting will silently fail.
