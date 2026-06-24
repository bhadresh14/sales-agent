"""
Sales Agent — calls tools directly (no LLM function-calling syntax),
then injects results into the prompt for the final answer.
This approach works reliably with Groq/Llama models.
"""
import uuid
from typing import List

from openai import OpenAI
from sqlalchemy.orm import Session as DBSession

from app.config import get_settings
from app.memory.memory_factory import get_memory
from app.tools.search_catalog import search_catalog
from app.tools.get_user_memory import get_user_memory
from app.tools.flag_for_human import flag_for_human
from app.services.eval_service import evaluate_response
from app.models.schemas import ChatResponse, EvalRecord

settings = get_settings()
client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)

SYSTEM_PROMPT = """You are a knowledgeable and helpful B2B SaaS sales assistant.
Answer questions about the product catalog accurately and concisely.

RULES:
- Use only the catalog and memory context provided below to answer.
- Be professional, friendly, and direct.
- If the answer is not in the context, say so honestly — never guess.
- Never make up features, prices, or guarantees."""


def run_agent(user_id: str, user_message: str, db: DBSession) -> ChatResponse:
    """
    Agent loop:
    1. Call tools directly (search_catalog + get_user_memory)
    2. Inject tool results into LLM prompt
    3. Get final answer from LLM
    4. Self-evaluate the response
    5. Persist to DB
    6. Return ChatResponse
    """
    session_id = str(uuid.uuid4())
    memory = get_memory(db)
    tools_called: List[str] = []

    # ── Tool 1: get_user_memory ───────────────────────────────────────────────
    memory_context = get_user_memory(user_id, db)
    tools_called.append("get_user_memory")

    # ── Tool 2: search_catalog ────────────────────────────────────────────────
    catalog_context = search_catalog(user_message)
    tools_called.append("search_catalog")

    # ── Build prompt with tool results injected ───────────────────────────────
    context_block = f"""
=== USER MEMORY (past conversation) ===
{memory_context}

=== CATALOG SEARCH RESULTS ===
{catalog_context}
""".strip()

    # Recent conversation history for multi-turn continuity
    prior_context = memory.get_recent_context(user_id, limit=8)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context_block},
    ]
    messages.extend(prior_context)
    messages.append({"role": "user", "content": user_message})

    # ── LLM generates final answer ────────────────────────────────────────────
    response = client.chat.completions.create(
        model=settings.model_name,
        messages=messages,
        temperature=0.3,
        max_tokens=512,
    )
    final_text = response.choices[0].message.content.strip()

    # ── Bonus: flag if response seems uncertain ───────────────────────────────
    uncertainty_phrases = ["i don't know", "i'm not sure", "cannot answer", "not in the catalog"]
    if any(phrase in final_text.lower() for phrase in uncertainty_phrases):
        flag_for_human(
            user_id=user_id,
            session_id=session_id,
            reason="Agent expressed uncertainty in response.",
            db=db,
        )
        tools_called.append("flag_for_human")

    # ── Self-evaluation ───────────────────────────────────────────────────────
    eval_record: EvalRecord = evaluate_response(
        user_message=user_message,
        assistant_response=final_text,
        catalog_context=catalog_context,
    )

    # ── Persist to DB ─────────────────────────────────────────────────────────
    memory.save_message(user_id, session_id, "user", user_message)
    memory.save_message(
        user_id,
        session_id,
        "assistant",
        final_text,
        tools_called=tools_called,
        eval_data=eval_record.model_dump(),
    )

    return ChatResponse(
        response=final_text,
        eval=eval_record,
        tools_called=tools_called,
        session_id=session_id,
        user_id=user_id,
    )
