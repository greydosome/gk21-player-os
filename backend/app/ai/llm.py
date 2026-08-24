
import json

import time

from openai import OpenAI

from app.core.config import settings

# 호출마다 새 OpenAI()를 만들면 매번 새 커넥션 풀/TLS 핸드셰이크가 발생한다.
# 클라이언트를 한 번만 만들어 재사용하고, 응답이 멈춰도 백그라운드 스레드가
# 무한정 블로킹되지 않도록 명시적 timeout을 둔다.
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client

    if _client is None:
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=30.0,
            max_retries=2,
        )

    return _client


def _clean_json_text(text: str):

    cleaned = text.strip()

    if cleaned.startswith("```json"):

        cleaned = cleaned.removeprefix("```json").strip()

    if cleaned.startswith("```"):

        cleaned = cleaned.removeprefix("```").strip()

    if cleaned.endswith("```"):

        cleaned = cleaned.removesuffix("```").strip()

    return cleaned

def call_ai(prompt: str):

    if settings.AI_PROVIDER != "OPENAI":

        raise ValueError(f"Unsupported AI_PROVIDER: {settings.AI_PROVIDER}")

    if not settings.OPENAI_API_KEY:

        raise ValueError("OPENAI_API_KEY is empty")

    started = time.time()

    client = _get_client()

    response = client.responses.create(

        model=settings.AI_MODEL,

        input=prompt

    )

    latency_ms = int((time.time() - started) * 1000)

    output_text = response.output_text

    cleaned_text = _clean_json_text(output_text)

    try:

        parsed = json.loads(cleaned_text)

    except json.JSONDecodeError as exc:

        raise ValueError(f"AI response is not valid JSON: {output_text}") from exc

    usage = getattr(response, "usage", None)

    token_input = None

    token_output = None

    if usage is not None:

        token_input = getattr(usage, "input_tokens", None)

        token_output = getattr(usage, "output_tokens", None)

    return {

        "provider": settings.AI_PROVIDER,

        "model_name": settings.AI_MODEL,

        "prompt_version": settings.AI_PROMPT_VERSION,

        "latency_ms": latency_ms,

        "token_input": token_input,

        "token_output": token_output,

        "raw_text": output_text,

        "analysis": parsed,

    }

