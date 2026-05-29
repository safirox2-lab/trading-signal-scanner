from src.journal.models import JournalStatus, RecommendationRecord


def outcome_feedback(record: RecommendationRecord, status: JournalStatus) -> str:
    strategies = ", ".join(record.strategy_tags) if record.strategy_tags else "sin estrategia registrada"
    if status == JournalStatus.TP:
        return f"TP alcanzado. Estrategias favorecidas: {strategies}."
    if status == JournalStatus.SL:
        return (
            f"SL alcanzado. Revisar confirmacion, volatilidad, distancia de entrada "
            f"y confluencia de estrategias: {strategies}."
        )
    if status == JournalStatus.WAITING_ENTRY:
        return "Entrada aun no activada. La senal puede estar lejos del precio o requerir mejor gatillo."
    if status == JournalStatus.OPEN:
        return "Entrada activada. Operacion abierta esperando TP o SL."
    return "Resultado no resuelto por datos insuficientes."
