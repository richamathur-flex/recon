"""Groq client factory and helpers."""

from groq import Groq

from src.config import settings


def get_groq_client() -> Groq:
    """Return a configured Groq client."""
    return Groq(api_key=settings.groq_api_key)


def chat_json(
    system: str,
    user: str,
    *,
    model: str | None = None,
    temperature: float = 0.2,
) -> str:
    """Run a chat completion in JSON mode and return the raw JSON string.

    JSON mode forces the model to output valid JSON. We still need to
    parse and validate it with Pydantic afterward.
    """
    client = get_groq_client()
    response = client.chat.completions.create(
        model=model or settings.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or "{}"