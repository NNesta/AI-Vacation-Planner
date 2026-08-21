from datetime import datetime

example_itineraries = [
    {
        "day": 1,
        "date": "2026-08-01",
        "title": "Discovering Kigali",
        "summary": "Explore Kigali's history and learn about Rwanda's past.",
        "activities": [
            {
                "title": "Visit Kigali Genocide Memorial",
                "description": "Learn about Rwanda's history and honor the victims of the 1994 Genocide against the Tutsi.",
                "start_time": "09:00:00",
                "end_time": "11:00:00",
                "duration_minutes": 120,
                "location": {
                    "name": "Kigali Genocide Memorial",
                    "address": "KG 14 Ave, Kigali, Rwanda",
                },
                "tips": ["Arrive early to avoid crowds"],
            }
        ],
    }
]


def get_prompts(
    title: str,
    start_datetime: datetime,
    end_datetime: datetime,
    destination: str,
    budget: str,
    trip_style: str,
    description: str | None = None,
):
    if description:
        user_prompt = f"""
        Give itinararies of this trip with title: {title} with this descriprion: {description}. It will start from {start_datetime} to {end_datetime}. The destination is {destination} with a budget of {budget}.
        The travel style is {trip_style}.
        Generate a detailed travel itinerary based on the user's trip information and preferences. 
        The itinerary must return your response as  JSON matching this  exact structure and data types:
        {example_itineraries}
        Respond ONLY with valid JSON. Do not include explanations, comments, Markdown code fences, or any other text or formatting before or after the JSON object.
        """
    else:
        user_prompt = f"""
        Give itinararies of this trip with title: {title} that will start from {start_datetime} to {end_datetime}. The destination is {destination} with a budget of {budget}.
        The travel style is {trip_style}.
        Generate a detailed travel itinerary based on the user's trip information and preferences. 
        The itinerary must return your response as  JSON matching this  exact structure and data types:
        {example_itineraries}
        Respond ONLY with valid JSON. Do not include explanations, comments, Markdown code fences (```json ```), or any other text or formatting before or after the JSON object.
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
        Give maximum of 3 activities per day and maximum of 3 itineraries.
        """

    return [
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": "```json"},
    ], system_prompt


def get_retry_prompt(original_prompt, original_response, error_message):
    retry_prompt = f"""
    This is a request to fix an error in the structure of an llm_response.
    Here is the original request:
    <original_prompt>
    {original_prompt}
    </original_prompt>

    Here is the original llm_response:
    <llm_response>
    {original_response}
    </llm_response>
    
    This response generated an error:
    <error_message>
    {error_message}
    </error_message>

    compare the error message and the llm_response and identify what needs to be fixed or removed in the llm_response to resolve this error.

    Respond ONLY with valid JSON. Do not include explanations, comments, Markdown code fences (```json ```), or any other text or formatting before or after the JSON object.
    """
    return [
        {"role": "user", "content": retry_prompt},
        {"role": "assistant", "content": "```json"},
    ]
