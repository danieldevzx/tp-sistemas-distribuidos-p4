import threading
from .campo import Campo

DURACAO_FASE_MONTAGEM = 60  # segundos


class Jogo:
    def __init__(self):
        self.campo = Campo()
        self.fase = "montagem"
        self.tempo_restante = DURACAO_FASE_MONTAGEM
        self._lock_fase = threading.Lock()
        self._timer: threading.Timer | None = None
        self._callback_tick = None          # chamado a cada segundo com o tempo restante
        self._callback_fim_montagem = None  # chamado quando o tempo chega a 0

    # ------------------------------------------------------------------ #
    #  Fase                                                                #
    # ------------------------------------------------------------------ #

    def iniciar_timer(self, callback_tick, callback_fim_montagem):
        self._callback_tick = callback_tick
        self._callback_fim_montagem = callback_fim_montagem
        self._agendar_tick()

    def _agendar_tick(self):
        self._timer = threading.Timer(1.0, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self):
        with self._lock_fase:
            if self.fase != "montagem":
                return
            self.tempo_restante -= 1
            tempo_atual = self.tempo_restante

        # Avisa o servidor do novo tempo (broadcast para clientes)
        if self._callback_tick:
            threading.Thread(
                target=self._callback_tick,
                args=(tempo_atual,),
                daemon=True
            ).start()

        if tempo_atual <= 0:
            with self._lock_fase:
                self.fase = "escavacao"
            if self._callback_fim_montagem:
                threading.Thread(
                    target=self._callback_fim_montagem, daemon=True
                ).start()
            return

        self._agendar_tick()

    def esta_em_montagem(self) -> bool:
        with self._lock_fase:
            return self.fase == "montagem"

    def get_info_fase(self) -> dict:
        with self._lock_fase:
            return {"fase": self.fase, "tempo_restante": self.tempo_restante}

    # ------------------------------------------------------------------ #
    #  Campo                                                               #
    # ------------------------------------------------------------------ #

    def getCampo(self):
        return self.campo

    def interacaoCampo(self, usuario: dict, linha: int, coluna: int):
        time_id = usuario.get("timeId")

        with self._lock_fase:
            fase_atual = self.fase

        if time_id == 2 and fase_atual == "montagem":
            return False, "aguarde"
        if time_id == 1 and fase_atual != "montagem":
            return False, "encerrada"

        ok = self.campo.interacaoCampo(usuario, linha, coluna)
        return ok, None