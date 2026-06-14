from datetime import datetime
from typing import Optional


def get_prompt(
    title: str,
    start_datetime: datetime,
    end_datetime: datetime,
    destination: str,
    budget: str,
    trip_style: str,
    description: Optional[str] = None,
):
    if description:
        user_prompt = f"""
    Give itinarries of this trip with title: {title} with this descriprion: {description}. It will start from {start_datetime} to {end_datetime}. The destination is {destination} with a budget of {budget}.
The travel style is {trip_style}.
example of output: [
{{
      "day": 1,
      "activities": [
        "Visit Kigali Genocide Memorial",
        "Explore Kimironko Market"
      ]
    }},
  {{
    "day_number": 2,
    "activities": ["Visit Richard kandt Museum","Play basketball at lub Rafiki"]
  }},
]
    """
    user_prompt = f"""
    Plan a trip with title: {title} that will start from {start_datetime} to {end_datetime}. The destination is {destination} with a budget of {budget}.
The travel style is {trip_style}.
example: [
{{
      "day": 1,
      "activities": [
        "Visit Kigali Genocide Memorial",
        "Explore Kimironko Market"
      ]
    }},
 {{
    "day_number": 2,
    "activities": ["Visit Richard kandt Museum","Play basketball at lub Rafiki"]
  }},
]
    #     """
    #     system_prompt = f"""
    #     Give the output in json format with the following structure
    #     [
    #   {{
    #     "day_number": ,
    #     "activities": []
    #   }}
    # ]
    #     """

    return {"role": "user", "content": user_prompt}, None
