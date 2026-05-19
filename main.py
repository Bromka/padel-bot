"""Entry point — fetch data, render image, update Telegram."""
import sys
import traceback

import config
from yclients import fetch_club_schedule
from weather import fetch_hourly_forecast
from renderer import render_schedule
from bot import edit_photo, get_pinned_message_id, pin_message, send_photo


def run():
    # 1. Fetch weather
    try:
        forecast = fetch_hourly_forecast(
            config.OPENWEATHER_API_KEY,
            config.WEATHER_CITY,
            config.WEATHER_TIMEZONE,
        )
        print(f"Weather: {len(forecast)} hourly entries fetched")
    except Exception as e:
        print(f"Weather fetch failed: {e}", file=sys.stderr)
        forecast = {}

    # 2. Fetch schedule for each club
    clubs_data = []
    for club_cfg in config.CLUBS:
        print(f"Fetching {club_cfg['name']} (company {club_cfg['company_id']})…")
        try:
            schedule = fetch_club_schedule(club_cfg["company_id"], config.YCLIENTS_TOKEN)
            clubs_data.append({**club_cfg, **schedule})
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            clubs_data.append({**club_cfg, "error": str(e)})

    # 3. Render image
    image_bytes = render_schedule(
        clubs_data=clubs_data,
        forecast=forecast,
        hours_after_rain=config.HOURS_AFTER_RAIN,
        start_h=config.SCHEDULE_START_HOUR,
        end_h=config.SCHEDULE_END_HOUR,
        timezone=config.WEATHER_TIMEZONE,
    )
    print(f"Image rendered: {len(image_bytes):,} bytes")

    # 4. Send or update Telegram message
    # Ask Telegram directly what's pinned — no local file needed
    pinned_id = get_pinned_message_id(config.TG_BOT_TOKEN, config.TG_CHAT_ID)
    print(f"Current pinned message: {pinned_id}")

    if pinned_id:
        updated = edit_photo(config.TG_BOT_TOKEN, config.TG_CHAT_ID, pinned_id, image_bytes)
        if updated:
            print(f"Updated pinned message {pinned_id}")
            return
        print("Edit failed, sending fresh…")

    msg_id = send_photo(
        config.TG_BOT_TOKEN, config.TG_CHAT_ID,
        image_bytes, thread_id=config.TG_THREAD_ID,
    )
    pin_message(config.TG_BOT_TOKEN, config.TG_CHAT_ID, msg_id)
    print(f"Sent and pinned new message {msg_id}")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
