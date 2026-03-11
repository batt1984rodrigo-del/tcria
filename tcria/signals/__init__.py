from .currency_detector import count_currency_values
from .date_detector import count_dates
from .entity_detector import detect_entity_signals


def detect_signals(text: str) -> dict[str, object]:
    signals = {
        "dates_found": count_dates(text),
        "currency_values_found": count_currency_values(text),
        "transaction_terms": _count_transaction_terms(text),
        "contains_objetivo_label": _contains_objetivo_label(text),
        "contains_autor_label": _contains_autor_label(text),
        "contains_summary_label": _contains_summary_label(text),
        "legal_pattern_counts": {"legal_strong": 0, "legal_medium": 0, "accusation": 0},
        "density_scores": {"legal_refs_density": 0.0, "accusation_density": 0.0},
        "legal_refs_density": 0.0,
        "legal_terms_density": 0.0,
        "accusation_density": 0.0,
    }
    signals.update(detect_entity_signals(text))
    return signals


def _count_transaction_terms(text: str) -> int:
    text_l = text.lower()
    return sum(text_l.count(k) for k in ("transa", "fatura", "extrato", "lançamento", "lancamento"))


def _contains_objetivo_label(text: str) -> bool:
    text_l = text.lower()
    return "objetivo:" in text_l or "finalidade:" in text_l


def _contains_autor_label(text: str) -> bool:
    text_l = text.lower()
    return "autor:" in text_l or "responsável" in text_l or "responsavel" in text_l


def _contains_summary_label(text: str) -> bool:
    text_l = text.lower()
    return "resumo" in text_l or "sumário" in text_l or "sumario" in text_l


__all__ = ["detect_signals"]
