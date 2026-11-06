from datetime import date, timedelta

TRIP = {
    "trip_id": "11111111-1111-1111-1111-111111111111",
    "title": "Paris in spring",
    "description": "Museums and food",
    "destination": "Paris, France",
    "start_date": "2030-05-10",
    "end_date": "2030-05-12",
    "days": 3,
    "budget": 2000.0,
    "trip_style": "BUDGET",
}


def make_days(count: int = 3, start: str = "2030-05-10") -> list[dict]:
    first = date.fromisoformat(start)
    return [
        {
            "day": number,
            "date": (first + timedelta(days=number - 1)).isoformat(),
            "title": f"Paris day {number}",
            "summary": "Museums and food around the city.",
            "activities": [
                {
                    "title": "Louvre Museum",
                    "description": "See the main collection.",
                    "start_time": "10:00:00",
                    "end_time": "12:00:00",
                    "duration_minutes": 120,
                    "location": {"name": "Louvre", "address": "Rue de Rivoli, Paris"},
                    "tips": ["Book a timed slot."],
                }
            ],
        }
        for number in range(1, count + 1)
    ]
