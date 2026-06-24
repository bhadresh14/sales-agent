"""
search_catalog(query) — keyword search over the product catalog JSON.
Real function, not string injection. Returns matching plans and FAQs as text.
"""
import json
import os
from pathlib import Path

_CATALOG_PATH = Path(__file__).parent.parent.parent / "catalog.json"


def _load_catalog() -> dict:
    with open(_CATALOG_PATH, "r") as f:
        return json.load(f)


def search_catalog(query: str) -> str:
    """
    Search the product catalog for plans and FAQs matching the query.
    Returns a formatted string summarising matching results.
    """
    query_lower = query.lower()
    catalog = _load_catalog()
    results = []

    # Search plans
    for plan in catalog.get("plans", []):
        plan_text = (
            plan["name"] + " " +
            plan["price"] + " " +
            " ".join(plan["features"]) + " " +
            plan.get("description", "")
        ).lower()
        if any(token in plan_text for token in query_lower.split()):
            results.append(
                f"Plan: {plan['name']} — {plan['price']}\n"
                f"Features: {', '.join(plan['features'])}\n"
                f"Details: {plan.get('description', '')}"
            )

    # Search FAQs
    for faq in catalog.get("faqs", []):
        faq_text = (faq["question"] + " " + faq["answer"]).lower()
        if any(token in faq_text for token in query_lower.split()):
            results.append(f"FAQ: {faq['question']}\nAnswer: {faq['answer']}")

    if not results:
        # Return full catalog summary so agent isn't left empty-handed
        plans_summary = "; ".join(
            f"{p['name']} ({p['price']}): {', '.join(p['features'])}"
            for p in catalog["plans"]
        )
        return f"No exact match found for '{query}'. Full catalog: {plans_summary}"

    return "\n\n".join(results)
