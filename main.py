import asyncio

from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InputMediaPhoto, InputMediaVideo, Message

from config import BOT_TOKEN, CHAT_ID, PORT

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties())
dp = Dispatcher()

# media_group_id -> {"messages": [Message, ...], "task": asyncio.Task}
_albums: dict[str, dict] = {}

ALBUM_DEBOUNCE_SECONDS = 1.5


def _is_spoilered(msg: Message) -> bool:
    return bool(getattr(msg, "has_media_spoiler", False))


async def _send_single(msg: Message) -> None:
    try:
        if msg.photo:
            await bot.send_photo(
                CHAT_ID,
                msg.photo[-1].file_id,
                has_spoiler=True,
                caption=msg.caption,
                caption_entities=msg.caption_entities,
            )
        elif msg.video:
            await bot.send_video(
                CHAT_ID,
                msg.video.file_id,
                has_spoiler=True,
                caption=msg.caption,
                caption_entities=msg.caption_entities,
            )
        else:
            return
        await bot.delete_message(CHAT_ID, msg.message_id)
    except TelegramAPIError:
        pass


async def _send_album(media_group_id: str) -> None:
    await asyncio.sleep(ALBUM_DEBOUNCE_SECONDS)

    group = _albums.pop(media_group_id, None)
    if not group:
        return

    messages: list[Message] = sorted(group["messages"], key=lambda m: m.message_id)

    media_payload = []
    caption_used = False
    for m in messages:
        caption = None
        caption_entities = None
        if not caption_used and m.caption:
            caption = m.caption
            caption_entities = m.caption_entities
            caption_used = True

        if m.photo:
            media_payload.append(
                InputMediaPhoto(
                    media=m.photo[-1].file_id,
                    has_spoiler=True,
                    caption=caption,
                    caption_entities=caption_entities,
                )
            )
        elif m.video:
            media_payload.append(
                InputMediaVideo(
                    media=m.video.file_id,
                    has_spoiler=True,
                    caption=caption,
                    caption_entities=caption_entities,
                )
            )

    if not media_payload:
        return

    try:
        await bot.send_media_group(CHAT_ID, media_payload)
    except TelegramAPIError:
        return

    for m in messages:
        try:
            await bot.delete_message(CHAT_ID, m.message_id)
        except TelegramAPIError:
            pass


@dp.channel_post(
    F.chat.id == CHAT_ID,
    F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO}),
)
async def handle_channel_post(msg: Message) -> None:
    if _is_spoilered(msg):
        return

    if msg.media_group_id:
        group_id = msg.media_group_id
        group = _albums.setdefault(group_id, {"messages": [], "task": None})
        group["messages"].append(msg)

        if group["task"] is not None:
            group["task"].cancel()
        group["task"] = asyncio.create_task(_send_album(group_id))
    else:
        await _send_single(msg)


async def _health(_request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def _run_http_server() -> None:
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()

    # Keep the server alive forever
    await asyncio.Event().wait()


async def _run_bot() -> None:
    while True:
        try:
            await dp.start_polling(bot, handle_signals=False)
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(5)


async def main() -> None:
    await asyncio.gather(_run_http_server(), _run_bot())


if __name__ == "__main__":
    asyncio.run(main())
