import json
import re
from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.models import Ticket, TicketPriority


@dataclass(frozen=True)
class AIClassification:
    title: str
    summary: str
    suggested_priority: TicketPriority
    suggested_category: str | None
    keywords: list[str]
    source: str
    notice: str | None = None


@dataclass(frozen=True)
class AIReply:
    reply: str
    source: str
    notice: str | None = None


def _extract_json(content: str) -> dict[str, object]:
    """Decode a JSON object even if a provider surrounds it with a code block."""

    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    decoded = json.loads(cleaned)
    if not isinstance(decoded, dict):
        raise ValueError("La risposta AI non contiene un oggetto JSON.")
    return decoded


def _fallback_title(description: str) -> str:
    """Create a useful title when Ollama is temporarily unavailable."""

    compact_description = re.sub(r"\s+", " ", description).strip()
    first_sentence = re.split(r"[.!?]\s|\n", compact_description, maxsplit=1)[0].strip()
    if len(first_sentence) < 5:
        return "Richiesta di assistenza"
    return first_sentence[:200].rstrip(" ,;:-")


def _normalise_title(value: object, description: str) -> str:
    title = re.sub(r"\s+", " ", str(value or "")).strip().strip('"')
    return title[:200].rstrip() if len(title) >= 5 else _fallback_title(description)


def _apply_priority_guardrail(priority: TicketPriority, text: str) -> TicketPriority:
    """Prevent an undersized local model from downgrading clearly critical incidents."""

    normalised_text = text.lower()
    urgent_signals = ("perdita di dati", "data breach", "violazione", "dati sensibili")
    high_signals = ("blocc", "produzione", "tutti gli utenti", "tutti i dipendenti", "impossibile")
    if any(signal in normalised_text for signal in urgent_signals):
        return TicketPriority.URGENT
    if any(signal in normalised_text for signal in high_signals) and priority in {
        TicketPriority.LOW,
        TicketPriority.MEDIUM,
    }:
        return TicketPriority.HIGH
    return priority


def _fallback_classification(
    description: str, title_hint: str | None = None, notice: str | None = None
) -> AIClassification:
    title = _normalise_title(title_hint, description)
    text = f"{title} {description}".lower()
    if any(term in text for term in ("fattura", "pagamento", "rimborso", "addebito")):
        category = "Fatturazione"
    elif any(term in text for term in ("login", "accesso", "password", "account")):
        category = "Account"
    elif any(term in text for term in ("errore", "bug", "blocco", "non funziona", "malfunzionamento")):
        category = "Problema tecnico"
    else:
        category = None

    priority = _apply_priority_guardrail(TicketPriority.MEDIUM, text)

    keywords = [term for term in ("login", "account", "fattura", "pagamento", "errore", "accesso") if term in text]
    summary = description.strip().replace("\n", " ")
    if len(summary) > 240:
        summary = f"{summary[:237].rstrip()}…"
    return AIClassification(title, summary, priority, category, keywords[:5], "fallback", notice)


def _fallback_reply(ticket: Ticket, notice: str | None = None) -> AIReply:
    return AIReply(
        reply=(
            f"Buongiorno, abbiamo preso in carico la richiesta “{ticket.title}”. "
            "Stiamo verificando quanto segnalato e ti aggiorneremo non appena avremo maggiori informazioni."
        ),
        source="fallback",
        notice=notice,
    )


def _request_json(messages: list[dict[str, str]]) -> dict[str, object]:
    """Call the configured provider and return the JSON payload from its answer."""

    settings = get_settings()
    provider = settings.ai_provider.strip().lower()
    timeout = httpx.Timeout(settings.ai_timeout_seconds)

    if provider in {"openai", "openai-compatible", "openrouter"}:
        if not settings.openai_api_key:
            raise RuntimeError("La chiave API del provider AI non è configurata.")
        response = httpx.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return _extract_json(content)

    if provider == "ollama":
        response = httpx.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/chat",
            json={"model": settings.ollama_model, "messages": messages, "format": "json", "stream": False},
            timeout=timeout,
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        return _extract_json(content)

    raise RuntimeError("Nessun provider AI è configurato.")


def _classify_ticket_content(description: str, title_hint: str | None = None) -> AIClassification:
    """Generate title, summary and priority from the customer's description."""

    messages = [
        {
            "role": "system",
            "content": (
                "Sei un assistente per un helpdesk italiano. Rispondi soltanto con JSON valido: "
                '{"title":"...","summary":"...","suggested_priority":"low|medium|high|urgent",'
                '"suggested_category":"... o null","keywords":["..."]}. '
                "Genera un titolo chiaro di 5-120 caratteri, non inventare informazioni e mantieni "
                "il riassunto sotto le 240 battute. Considera urgente solo un blocco grave, un rischio "
                "di sicurezza, una perdita di dati o un impatto diffuso."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Titolo esistente (se presente): {title_hint or 'non disponibile'}\n"
                f"Descrizione: {description}"
            ),
        },
    ]
    try:
        response = _request_json(messages)
        priority = TicketPriority(str(response.get("suggested_priority", TicketPriority.MEDIUM.value)))
        summary = str(response.get("summary", "")).strip()
        if not summary:
            raise ValueError("Riassunto AI mancante.")
        title = _normalise_title(response.get("title"), description)
        priority = _apply_priority_guardrail(priority, f"{title} {description}")
        raw_keywords = response.get("keywords", [])
        keywords = [str(keyword).strip() for keyword in raw_keywords if str(keyword).strip()][:5] if isinstance(raw_keywords, list) else []
        category = response.get("suggested_category")
        return AIClassification(
            title,
            summary[:240],
            priority,
            str(category).strip() if category else None,
            keywords,
            "ai",
        )
    except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        return _fallback_classification(description, title_hint, f"AI non disponibile: {error}")


def analyze_new_ticket(description: str) -> AIClassification:
    """Analyse ticket text before persistence so customers cannot set its priority or title."""

    return _classify_ticket_content(description)


def classify_ticket(ticket: Ticket) -> AIClassification:
    """Recalculate summary and classification metadata for an existing ticket."""

    return _classify_ticket_content(ticket.description, ticket.title)


def suggest_reply(ticket: Ticket) -> AIReply:
    """Generate an editable, customer-facing reply for the support operator."""

    messages = [
        {
            "role": "system",
            "content": (
                "Sei un operatore di assistenza italiano. Scrivi una risposta professionale, breve, "
                "empatica e priva di promesse non verificabili. Rispondi soltanto con JSON valido: "
                '{"reply":"..."}. '
            ),
        },
        {"role": "user", "content": f"Titolo: {ticket.title}\nDescrizione: {ticket.description}"},
    ]
    try:
        response = _request_json(messages)
        reply = str(response.get("reply", "")).strip()
        if not reply:
            raise ValueError("Risposta AI mancante.")
        return AIReply(reply[:3000], "ai")
    except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        return _fallback_reply(ticket, f"AI non disponibile: {error}")
