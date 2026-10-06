from anthropic import Anthropic
from app.core.config import settings


client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
