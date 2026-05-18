"""YCLIENTS booking API client."""
import datetime
import requests

API_BASE = "https://api.yclients.com/api/v1"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.yclients.v2+json",
        "Content-Type": "application/json",
    }


def get_services(company_id: int, token: str) -> list[dict]:
    """Returns list of services for a company (e.g. 'Падел 1 час')."""
    r = requests.get(
        f"{API_BASE}/book_services/{company_id}",
        headers=_headers(token),
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("data", {}).get("services", [])


def get_staff(company_id: int, token: str, service_id: int | None = None) -> list[dict]:
    """Returns courts/resources for a company."""
    params = {}
    if service_id:
        params["service_id"] = service_id
    r = requests.get(
        f"{API_BASE}/book_staff/{company_id}",
        headers=_headers(token),
        params=params,
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("data", [])


def get_available_dates(
    company_id: int,
    token: str,
    staff_id: int,
    service_id: int,
) -> list[str]:
    """Returns list of available dates (YYYY-MM-DD)."""
    r = requests.get(
        f"{API_BASE}/book_dates/{company_id}",
        headers=_headers(token),
        params={"staff_id": staff_id, "service_ids[]": service_id},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("data", {}).get("booking_dates", [])


def get_time_slots(
    company_id: int,
    token: str,
    staff_id: int,
    service_id: int,
    date: str,  # YYYY-MM-DD
) -> list[dict]:
    """Returns available time slots for a specific court and date."""
    r = requests.get(
        f"{API_BASE}/book_times/{company_id}/{staff_id}/{date}",
        headers=_headers(token),
        params={"service_ids[]": service_id},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("data", [])


def fetch_club_schedule(company_id: int, token: str) -> dict:
    """
    Returns a dict with:
      club_name, courts list, today's slots per court.

    slots_by_court = {
        "Корт 1": {"10:00": True, "10:30": False, ...},
        ...
    }
    """
    today = datetime.date.today().isoformat()

    services = get_services(company_id, token)
    if not services:
        return {"error": "No services found"}

    # Берём первую услугу (обычно «Аренда корта 1 час»)
    service = services[0]
    service_id = service["id"]

    courts = get_staff(company_id, token, service_id)
    if not courts:
        return {"error": "No courts found"}

    slots_by_court = {}
    for court in courts:
        court_name = court["name"]
        staff_id = court["id"]

        available_dates = get_available_dates(company_id, token, staff_id, service_id)
        if today not in available_dates:
            slots_by_court[court_name] = {}
            continue

        raw_slots = get_time_slots(company_id, token, staff_id, service_id, today)
        # raw_slots: [{"time": "10:00:00", "seance_length": 3600, ...}, ...]
        slots_by_court[court_name] = {
            s["time"][:5]: True for s in raw_slots  # "10:00:00" → "10:00"
        }

    return {
        "service_name": service["title"],
        "slots_by_court": slots_by_court,
    }
