from llama_index.llms.openai import OpenAI as LlamaOpenAI
from loguru import logger

from app.core.config import settings


class LLMService:
    def __init__(self):
        self.llm = LlamaOpenAI(
            model=settings.openai_llm_model,
            api_key=settings.openai_api_key,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
        )

    def generate_response(self, prompt: str) -> str:
        logger.info(f"Generating response using {settings.openai_llm_model}")
        response = self.llm.complete(prompt)
        return response.text

    def generate_response_stream(self, prompt: str):
        logger.info(f"Streaming response using {settings.openai_llm_model}")
        for chunk in self.llm.stream_complete(prompt):
            yield chunk.delta

    def get_token_count(self, prompt: str, response: str) -> dict:
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(settings.openai_llm_model)
            prompt_tokens = len(encoding.encode(prompt))
            response_tokens = len(encoding.encode(response))
            return {
                "prompt": prompt_tokens,
                "completion": response_tokens,
                "total": prompt_tokens + response_tokens,
            }
        except Exception:
            return {"prompt": 0, "completion": 0, "total": 0}


_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
