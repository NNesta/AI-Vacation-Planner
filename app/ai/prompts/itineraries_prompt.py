from datetime import datetime
from typing import Optional


def get_prompts(
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
        {{
      "title": "Visit Kigali Genocide Memorial",
      "description": "Learn about Rwanda's history and the events of the 1994 Genocide against the Tutsi through exhibits, personal testimonies, and memorial gardens that promote remembrance, education, and reconciliation."
      }},
    {{
      "title": "Explore Kimironko Market",
      "description": "Experience one of Kigali's busiest local markets, where you can browse fresh produce, colorful fabrics, handcrafted goods, and interact with local vendors to gain insight into everyday Rwandan life."
        }}
        ]
             }},
            {{
            "day_number": 2,
            "activities": [
    {{
      "title": "Visit Richard Kandt Museum",
      "description": "Discover the history of Kigali and Rwanda through exhibits at the former residence of Richard Kandt, the first colonial resident of Rwanda. Learn about the country's natural heritage, colonial era, and cultural development."
     }},
     {{
      "title": "Play Basketball at Club Rafiki",
      "description": "Enjoy a friendly basketball session at Club Rafiki, a community-focused sports and recreation center. Practice your skills, join local players, and experience Kigali's vibrant sports culture."
     }}
  ]
         }},
        ]
        """
    else:
        user_prompt = f"""
        Plan a trip with title: {title} that will start from {start_datetime} to {end_datetime}. The destination is {destination} with a budget of {budget}.
        The travel style is {trip_style}.
        example of output: [
            {{
                "day": 1,
                "activities": [
        {{
          "title": "Visit Kigali Genocide Memorial",
          "description": "Learn about Rwanda's history and the events of the 1994 Genocide against the Tutsi through exhibits, personal testimonies, and memorial gardens that promote remembrance, education, and reconciliation."
        }},
        {{
          "title": "Explore Kimironko Market",
          "description": "Experience one of Kigali's busiest local markets, where you can browse fresh produce, colorful fabrics, handcrafted goods, and interact with local vendors to gain insight into everyday Rwandan life."
        }}
      ]
                }},
            {{
                "day_number": 2,
                "activities": [
        {{
          "title": "Visit Richard Kandt Museum",
          "description": "Discover the history of Kigali and Rwanda through exhibits at the former residence of Richard Kandt, the first colonial resident of Rwanda. Learn about the country's natural heritage, colonial era, and cultural development."
        }},
        {{
          "title": "Play Basketball at Club Rafiki",
          "description": "Enjoy a friendly basketball session at Club Rafiki, a community-focused sports and recreation center. Practice your skills, join local players, and experience Kigali's vibrant sports culture."
        }}
      ]
            }},
            ]
            """
    system_prompt = """
        You are an expert Rwanda travel planner. 
        Generate professional itineraries for destinations across Rwanda.
        Focus on:
        - Cultural experiences
        - Nature and wildlife
        - Local cuisine
        - Historical attractions
        - Adventure activities
        Give maximum of 3 activities per day.
        """

    return [
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": "```json"},
    ], system_prompt
