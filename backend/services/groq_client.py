from __future__ import annotations
import json
import os
import re

from groq import Groq

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def _parse_groq_json(text: str) -> dict:
    """
    Strip accidental markdown fences and parse JSON.
    Raises ValueError if the result is not valid JSON after stripping.
    """
    stripped = text.strip()
    # Remove ```json ... ``` or ``` ... ``` fences
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped)
    stripped = stripped.strip()
    return json.loads(stripped)


def _coerce_number(value) -> float:
    """Convert '$1,200.00' or '1200' to float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d.\-]", "", value)
        if cleaned:
            return float(cleaned)
    return 0.0


def _normalize_analysis(data: dict) -> dict:
    """Ensure all financial figures are floats, not strings."""
    for key in ("total_income", "total_expenses", "net_pnl"):
        if key in data:
            data[key] = _coerce_number(data[key])
    txns = data.get("key_transactions", [])
    for txn in txns:
        if "amount" in txn:
            txn["amount"] = _coerce_number(txn["amount"])
    return data


def _normalize_comparison(data: dict) -> dict:
    """Ensure change metric amounts and percents are floats."""
    for key in ("income_change", "expense_change", "net_pnl_change"):
        metric = data.get(key, {})
        if "amount" in metric:
            metric["amount"] = _coerce_number(metric["amount"])
        if "percent" in metric:
            metric["percent"] = _coerce_number(metric["percent"])
    return data


def analyze_single_month(
    context_chunks: list[str],
    month_key: str,
    question: str,
) -> dict:
    """
    Ask Groq to extract financial facts from one month's context.

    Returns dict matching SingleMonthAnalysis schema.
    """
    context = "\n\n".join(context_chunks)
    system_prompt = (
        "You are a financial analyst. Extract precise numerical financial data from the provided statement context. "
        "Return ONLY valid JSON. No markdown, no explanation, no code fences."
    )
    user_prompt = f"""Statement context for {month_key}:
{context}

Question: {question}

Extract the following from the context and return as JSON with exactly these keys:
{{
  "summary": "brief narrative summary of the month",
  "total_income": <number>,
  "total_expenses": <number>,
  "net_pnl": <number>,
  "key_transactions": [{{"description": "...", "amount": <number>}}],
  "insights": ["..."]
}}

Return ONLY valid JSON. No markdown, no explanation, no code fences."""

    client = _get_client()

    def _call(prompt_text: str) -> dict:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.1,
        )
        return _parse_groq_json(response.choices[0].message.content)

    try:
        result = _call(user_prompt)
    except (ValueError, json.JSONDecodeError):
        strict_prompt = user_prompt + "\n\nCRITICAL: Your response must start with { and end with }. Absolutely no other characters outside the JSON object."
        result = _call(strict_prompt)

    return _normalize_analysis(result)


def compare_months(
    current_context: list[str],
    previous_context: list[str],
    current_month: str,
    previous_month: str,
) -> dict:
    """
    Ask Groq to compare two months' financial data.

    Returns dict matching MonthComparisonResult schema.
    If previous_context is empty, returns an error dict immediately.
    """
    if not previous_context:
        return {
            "error": "no_data",
            "message": f"No statement found for {previous_month}",
        }

    current_text = "\n\n".join(current_context)
    previous_text = "\n\n".join(previous_context)

    system_prompt = (
        "You are a financial analyst specializing in month-over-month comparison. "
        "Return ONLY valid JSON. No markdown, no explanation, no code fences."
    )
    user_prompt = f"""Compare the two monthly financial statements below.

=== {current_month} (CURRENT) ===
{current_text}

=== {previous_month} (PREVIOUS) ===
{previous_text}

Return a JSON object with exactly these keys:
{{
  "current_month": "{current_month}",
  "previous_month": "{previous_month}",
  "income_change": {{"amount": <number>, "percent": <number>, "direction": "up"|"down"|"unchanged"}},
  "expense_change": {{"amount": <number>, "percent": <number>, "direction": "up"|"down"|"unchanged"}},
  "net_pnl_change": {{"amount": <number>, "percent": <number>, "direction": "up"|"down"|"unchanged"}},
  "highlights": ["..."],
  "warnings": ["..."],
  "recommendations": ["..."]
}}

amount = absolute change (current minus previous). percent = percentage change relative to previous.
Return ONLY valid JSON. No markdown, no explanation, no code fences."""

    client = _get_client()

    def _call(prompt_text: str) -> dict:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.1,
        )
        return _parse_groq_json(response.choices[0].message.content)

    try:
        result = _call(user_prompt)
    except (ValueError, json.JSONDecodeError):
        strict_prompt = user_prompt + "\n\nCRITICAL: Your response must start with { and end with }. Absolutely no other characters outside the JSON object."
        result = _call(strict_prompt)

    return _normalize_comparison(result)


def answer_question(
    context_chunks: list[str],
    question: str,
) -> str:
    """
    Free-form question answering over cross-month context.
    Returns a plain text answer.
    """
    context = "\n\n".join(context_chunks)
    system_prompt = (
        "You are a financial assistant. Answer user questions based solely on the provided statement context. "
        "Be concise and precise. Use numbers from the context where possible."
    )
    user_prompt = f"""Context from financial statements:
{context}

Question: {question}

Answer:"""

    client = _get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()
