import json
import re
from openai import OpenAI
from app.config import get_settings
from app.models.schemas import EvalRecord

settings = get_settings()
client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)

EVAL_SYSTEM_PROMPT = """You are a strict quality evaluator for an AI sales assistant.
You will be given the user's question, the catalog context used, and the assistant's response.

Score on these dimensions (0.0 to 1.0):
- groundedness: Is the response factually grounded in the catalog context?
- relevance: Does the response directly address what the user asked?
- confidence: Overall quality confidence

Also set:
- flagged: true if confidence < 0.6 or response contains speculation not in the catalog

Respond ONLY with valid JSON:
{
  "groundedness": <float>,
  "relevance": <float>,
  "confidence": <float>,
  "flagged": <bool>,
  "reasoning": "<one sentence>"
}"""


def evaluate_response(user_message: str, assistant_response: str, catalog_context: str) -> EvalRecord:
    eval_prompt = f"""User question: {user_message}

Catalog context:
{catalog_context}

Assistant response:
{assistant_response}

Score this response."""

    try:
        completion = client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": EVAL_SYSTEM_PROMPT},
                {"role": "user", "content": eval_prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = completion.choices[0].message.content.strip()
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(json_match.group() if json_match else raw)

        return EvalRecord(
            groundedness=float(data.get("groundedness", 0.5)),
            relevance=float(data.get("relevance", 0.5)),
            confidence=float(data.get("confidence", 0.5)),
            flagged=bool(data.get("flagged", False)),
            reasoning=str(data.get("reasoning", "Eval completed.")),
        )
    except Exception as e:
        return EvalRecord(
            groundedness=0.5,
            relevance=0.5,
            confidence=0.5,
            flagged=False,
            reasoning=f"Eval failed: {str(e)}",
        )
