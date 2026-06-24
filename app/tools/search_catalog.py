import json
from pathlib import Path

_CATALOG_PATH = Path(__file__).parent.parent.parent / "catalog.json"


def _load_catalog() -> dict:
    with open(_CATALOG_PATH, "r") as f:
        return json.load(f)


def search_catalog(query: str) -> str:
    query_lower = query.lower()
    catalog = _load_catalog()
    results = []

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

    for faq in catalog.get("faqs", []):
        faq_text = (faq["question"] + " " + faq["answer"]).lower()
        if any(token in faq_text for token in query_lower.split()):
            results.append(f"FAQ: {faq['question']}\nAnswer: {faq['answer']}")

    if not results:
        plans_summary = "; ".join(
            f"{p['name']} ({p['price']}): {', '.join(p['features'])}"
            for p in catalog["plans"]
        )
        return f"No exact match found for '{query}'. Full catalog: {plans_summary}"

    return "\n\n".join(results)
