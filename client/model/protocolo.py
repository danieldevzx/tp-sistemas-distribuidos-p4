# Tipos de requisição (cliente / servidor)
LOGIN          = "LOGIN"
REGISTER       = "REGISTER"
GET_FIELD      = "GET_FIELD"
ADD_STRUCTURE  = "ADD_STRUCTURE"

# Tipos de resposta/broadcast (servidor / cliente)
FIELD_STATE    = "FIELD_STATE"
FIELD_UPDATE   = "FIELD_UPDATE"
ACTION_SUCCESS = "ACTION_SUCCESS"
ACTION_ERROR   = "ACTION_ERROR"
PHASE_CHANGE   = "PHASE_CHANGE"
TIMER_TICK     = "TIMER_TICK"


def criar_mensagem(tipo: str, payload: dict | None = None) -> dict:
    return {"type": tipo, "payload": payload or {}}


def parse_mensagem(dados: dict) -> tuple[str, dict]:
    return dados.get("type", "DESCONHECIDO"), dados.get("payload", {})