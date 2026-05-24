LOGIN = "LOGIN"
REGISTER = "REGISTER"
GET_FIELD = "GET_FIELD"
ADD_STRUCTURE = "ADD_STRUCTURE"
REMOVE_STRUCTURE = "REMOVE_STRUCTURE"
PING = "PING"


LOGIN_SUCCESS = "LOGIN_SUCCESS"
LOGIN_ERROR = "LOGIN_ERROR"
FIELD_STATE = "FIELD_STATE"
FIELD_UPDATE = "FIELD_UPDATE"
ACTION_SUCCESS = "ACTION_SUCCESS"
ACTION_ERROR = "ACTION_ERROR"
GAME_OVER = "GAME_OVER"
PLAYER_INFO = "PLAYER_INFO"
PHASE_CHANGE = "PHASE_CHANGE"
TIMER_TICK   = "TIMER_TICK"


def criar_mensagem(tipo: str, payload: dict | None = None) -> dict:
    # Cria mensagem padronizada
    return {
        "type": tipo,
        "payload": payload or {}
    }


def parse_mensagem(dados: dict) -> tuple[str, dict]:
    # Extrai tipo e payload da mensagem
    tipo = dados.get("type", "DESCONHECIDO")
    payload = dados.get("payload", {})
    return tipo, payload