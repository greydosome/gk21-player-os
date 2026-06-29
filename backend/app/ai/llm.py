import json
import time

from openai import OpenAI

from app.core.config import settings


def call_ai(prompt: str):

    if settings.AI_PROVIDER != "OPENAI":
        raise ValueError(f"Unsupported AI_PROVIDER: {settings.AI_PROVIDER}")

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is empty")

    started = time.time()

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY
    )

    response = client.responses.create(
        model=settings.AI_MODEL,
        input=prompt
    )

    latency_ms = int((time.time() - started) * 1000)

    output_text = response.output_text

    try:
        parsed = json.loads(output_text)
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
