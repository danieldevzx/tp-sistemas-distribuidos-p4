import threading
from .campo import Campo

DURACAO_FASE_MONTAGEM = 60
DURACAO_FASE_ESCAVACAO = 60
MAX_ESTRUTURAS = 10
MAX_TENTATIVAS = 20


class Jogo:
    def __init__(self):
        self.campo = Campo()
        self.fase = "montagem"
        self.tempo_restante = DURACAO_FASE_MONTAGEM
        self.max_estruturas = MAX_ESTRUTURAS
        self.max_tentativas = MAX_TENTATIVAS
        self.tentativas_restantes = MAX_TENTATIVAS
        self.ganhador = None  # None: em andamento, 1: Time 1, 2: Time 2, 3: Empate
        self._lock_fase = threading.Lock()
        self._timer: threading.Timer | None = None
        self._callback_tick = None
        self._callback_fim_montagem = None
        self._callback_fim_jogo = None

    def iniciar_timer(self, callback_tick, callback_fim_montagem, callback_fim_jogo):
        self._callback_tick = callback_tick
        self._callback_fim_montagem = callback_fim_montagem
        self._callback_fim_jogo = callback_fim_jogo
        self._agendar_tick()

    def _agendar_tick(self):
        self._timer = threading.Timer(1.0, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self):
        with self._lock_fase:
            if self.fase == "finalizado":
                return
            self.tempo_restante -= 1
            tempo_atual = self.tempo_restante
            fase_atual = self.fase

        if self._callback_tick:
            threading.Thread(
                target=self._callback_tick,
                args=(tempo_atual,),
                daemon=True
            ).start()

        if tempo_atual <= 0:
            if fase_atual == "montagem":
                with self._lock_fase:
                    self.fase = "escavacao"
                    self.tempo_restante = DURACAO_FASE_ESCAVACAO
                if self._callback_fim_montagem:
                    threading.Thread(
                        target=self._callback_fim_montagem, daemon=True
                    ).start()
            elif fase_atual == "escavacao":
                with self._lock_fase:
                    self.fase = "finalizado"
                    escondidas = self.campo.contar_escondidos()
                    achadas = self.campo.contar_achados()
                    if escondidas > 0 and achadas == escondidas:
                        self.ganhador = 2
                    elif escondidas == 0:
                        self.ganhador = 3
                    else:
                        self.ganhador = 1
                if self._callback_fim_jogo:
                    threading.Thread(
                        target=self._callback_fim_jogo, daemon=True
                    ).start()
                return

        self._agendar_tick()

    def esta_em_montagem(self) -> bool:
        with self._lock_fase:
            return self.fase == "montagem"

    def get_info_fase(self) -> dict:
        with self._lock_fase:
            return {
                "fase": self.fase,
                "tempo_restante": self.tempo_restante,
                "tentativas_restantes": self.tentativas_restantes,
                "max_tentativas": self.max_tentativas,
                "max_estruturas": self.max_estruturas,
                "estruturas_escondidas": self.campo.contar_escondidos(),
                "estruturas_encontradas": self.campo.contar_achados(),
                "ganhador": self.ganhador
            }

    def getCampo(self):
        return self.campo

    def interacaoCampo(self, usuario: dict, linha: int, coluna: int):
        time_id = usuario.get("timeId")

        with self._lock_fase:
            fase_atual = self.fase
            if fase_atual == "finalizado":
                return False, "jogo_encerrado"

        if time_id == 2 and fase_atual == "montagem":
            return False, "aguarde"
        if time_id == 1 and fase_atual != "montagem":
            return False, "encerrada"

        if time_id == 2:
            with self._lock_fase:
                if self.tentativas_restantes <= 0:
                    return False, "sem_tentativas"

        # Validar limite de estruturas na montagem (apenas ao adicionar nova)
        celula = self.campo.getCampo()[linha][coluna]
        if time_id == 1:
            if celula.getJogadorEscondeu() == -1:  # Tentando adicionar
                if self.campo.contar_escondidos() >= self.max_estruturas:
                    return False, "limite_estruturas"

        ok, motivo = self.campo.interacaoCampo(usuario, linha, coluna)

        if ok and time_id == 2:
            with self._lock_fase:
                self.tentativas_restantes -= 1
                escondidas = self.campo.contar_escondidos()
                achadas = self.campo.contar_achados()
                
                if escondidas > 0 and achadas == escondidas:
                    self.fase = "finalizado"
                    self.ganhador = 2
                    if self._callback_fim_jogo:
                        threading.Thread(
                            target=self._callback_fim_jogo, daemon=True
                        ).start()
                elif self.tentativas_restantes <= 0:
                    self.fase = "finalizado"
                    self.ganhador = 1
                    if self._callback_fim_jogo:
                        threading.Thread(
                            target=self._callback_fim_jogo, daemon=True
                        ).start()

        return ok, motivo