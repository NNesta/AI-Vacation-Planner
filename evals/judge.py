from deepeval.models import DeepEvalBaseLLM

from app.agents.graph import final_text
from app.agents.llm import get_chat_model
from app.core.config import settings


class ClaudeJudge(DeepEvalBaseLLM):
    """Scores DeepEval metrics with the project's own configured model."""

    def __init__(self) -> None:
        super().__init__(settings.LLM_MODEL)

    def load_model(self):
        return get_chat_model(temperature=0)

    def get_model_name(self) -> str:
        return settings.LLM_MODEL

    def _runnable(self, schema):
        return self.model.with_structured_output(schema) if schema else self.model

    def generate(self, prompt: str, schema=None):
        result = self._runnable(schema).invoke(prompt)
        return result if schema else final_text([result])

    async def a_generate(self, prompt: str, schema=None):
        result = await self._runnable(schema).ainvoke(prompt)
        return result if schema else final_text([result])
