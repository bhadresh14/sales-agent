"""
Eval service — prompts the LLM to self-score every response.
Structured output, always present, logged to DB.
"""
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
You will be given:
- The user's question
- The catalog/tool context used
- The assistant's response

Score the response on these dimensions (0.0 to 1.0):
- groundedness: Is the response factually grounded in the provided catalog context? (1.0 = fully grounded, 0.0 = hallucinated)
- relevance: Does the response directly address what the user asked? (1.0 = perfectly relevant)
- confidence: Overall confidence in the response quality (combination of the above + coherence)

Also decide:
- flagged: true if confidence < 0.6 or if the response contains speculation not in the catalog

Respond ONLY with valid JSON in this exact format:
{
  "groundedness": <float>,
  "relevance": <float>,
  "confidence": <float>,
  "flagged": <bool>,
  "reasoning": "<one sentence explanation>"
}"""


def evaluate_response(
    user_message: str,
    assistant_response: str,
    catalog_context: str,
) -> EvalRecord:
    """
    Calls the LLM to self-evaluate the assistant's response.
    Always returns a structured EvalRecord — never raises.
    """
    eval_user_prompt = f"""User question: {user_message}

Catalog context used:
{catalog_context}

Assistant response:
{assistant_response}

Score this response."""

    try:
        completion = client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": EVAL_SYSTEM_PROMPT},
                {"role": "user", "content": eval_user_prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = completion.choices[0].message.content.strip()

        # Extract JSON even if the model wraps it in markdown fences
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(raw)

        return EvalRecord(
            groundedness=float(data.get("groundedness", 0.5)),
            relevance=float(data.get("relevance", 0.5)),
            confidence=float(data.get("confidence", 0.5)),
            flagged=bool(data.get("flagged", False)),
            reasoning=str(data.get("reasoning", "Eval completed.")),
        )

    except Exception as e:
        # Fallback — never block the response pipeline
        return EvalRecord(
            groundedness=0.5,
            relevance=0.5,
            confidence=0.5,
            flagged=False,
            reasoning=f"Eval failed to parse: {str(e)}",
        )
