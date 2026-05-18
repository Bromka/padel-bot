"""Telegram bot: send or update pinned photo."""
import os
import requests

TG_API = "https://api.telegram.org/bot{token}/{method}"


def _call(token: str, method: str, **kwargs) -> dict:
    url = TG_API.format(token=token, method=method)
    r = requests.post(url, timeout=30, **kwargs)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error [{method}]: {data}")
    return data["result"]


def send_photo(
    token: str,
    chat_id: str,
    image_bytes: bytes,
    thread_id: int | None = None,
    caption: str = "",
) -> int:
    data: dict = {"chat_id": chat_id, "caption": caption}
    if thread_id is not None:
        data["message_thread_id"] = thread_id
    result = _call(
        token, "sendPhoto",
        data=data,
        files={"photo": ("schedule.png", image_bytes, "image/png")},
    )
    return result["message_id"]


def edit_photo(token: str, chat_id: str, message_id: int, image_bytes: bytes) -> bool:
    """Replace photo in an existing message (media edit)."""
    try:
        _call(
            token, "editMessageMedia",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "media": '{"type":"photo","media":"attach://photo"}',
            },
            files={"photo": ("schedule.png", image_bytes, "image/png")},
        )
        return True
    except RuntimeError:
        return False


def pin_message(token: str, chat_id: str, message_id: int) -> None:
    _call(
        token, "pinChatMessage",
        json={"chat_id": chat_id, "message_id": message_id, "disable_notification": True},
    )


def load_pinned_id(filepath: str) -> int | None:
    try:
        with open(filepath) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def save_pinned_id(filepath: str, message_id: int) -> None:
    with open(filepath, "w") as f:
        f.write(str(message_id))
