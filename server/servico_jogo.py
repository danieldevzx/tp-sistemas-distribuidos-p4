import threading
import Pyro5.api
from modelo.jogo import Jogo
from modelo.bd_base import inicializar_banco


@Pyro5.api.expose
class ServicoJogo:
    """Serviço remoto do jogo."""

    def __init__(self):
        inicializar_banco()
        self._jogo = Jogo()
        self._callbacks = []
        self._lock_callbacks = threading.Lock()
        self._jogo.iniciar_timer(self._ao_tick, self._ao_fim_montagem)

    # --- Métodos expostos ao cliente ---

    def registrar_callback(self, callback_uri: str, time_id: int):
        """Registra callback do cliente."""
        with self._lock_callbacks:
            self._callbacks.append((callback_uri, time_id))
        print(f"[JOGO] Callback registrado: {callback_uri} (time {time_id})")

    def remover_callback(self, callback_uri: str):
        """Remove callback do cliente."""
        with self._lock_callbacks:
            self._callbacks = [
                (uri, t) for uri, t in self._callbacks if uri != callback_uri
            ]
        print(f"[JOGO] Callback removido: {callback_uri}")

    def obter_campo(self, time_id: int):
        """Retorna o campo e estado atual da fase."""
        campo = self._jogo.getCampo().getCampo()
        info = self._jogo.get_info_fase()
        serializado = []
        for linha in campo:
            linha_dados = []
            for celula in linha:
                escondeu = celula.getJogadorEscondeu()
                achou = celula.getJogadorAchou()
                if time_id == 2 and achou == -1:
                    escondeu = -1
                linha_dados.append({
                    "jogador_escondeu": escondeu,
                    "jogador_achou": achou,
                })
            serializado.append(linha_dados)
        return {
            "campo": serializado,
            "fase": info["fase"],
            "tempo_restante": info["tempo_restante"],
        }

    def interacao_campo(self, usuario: dict, linha: int, coluna: int):
        """Processa interação do jogador com o campo."""
        resultado, motivo = self._jogo.interacaoCampo(usuario, linha, coluna)

        if not resultado:
            if motivo == "aguarde":
                return False, "Fase de montagem ainda não terminou — aguarde para escavar"
            if motivo == "encerrada":
                return False, "Fase de montagem encerrada — não é mais possível adicionar estruturas"
            return False, "Célula já ocupada"

        celula = self._jogo.getCampo().getCampo()[linha][coluna]
        self._broadcast_field_update(linha, coluna, celula)

        if motivo == "removed":
            return True, "Estrutura removida com sucesso"
        return True, "Estrutura adicionada com sucesso"

    def get_info_fase(self):
        """Retorna info da fase."""
        return self._jogo.get_info_fase()

    # --- Callbacks de timer ---

    def _ao_tick(self, tempo_restante: int):
        self._broadcast_tick(tempo_restante)

    def _ao_fim_montagem(self):
        print("[JOGO] Fase de montagem encerrada — broadcast PHASE_CHANGE")
        self._broadcast_phase_change("escavacao", 0)

    # --- Broadcasts via callbacks ---

    def _broadcast_tick(self, tempo_restante: int):
        self._executar_broadcast("on_tick", tempo_restante)

    def _broadcast_phase_change(self, fase: str, tempo: int):
        self._executar_broadcast("on_phase_change", fase, tempo)

    def _broadcast_field_update(self, linha: int, coluna: int, celula):
        """Envia atualização da célula filtrada por time."""
        with self._lock_callbacks:
            mortos = []
            for callback_uri, time_id in self._callbacks:
                try:
                    proxy = Pyro5.api.Proxy(callback_uri)
                    escondeu = celula.getJogadorEscondeu()
                    achou = celula.getJogadorAchou()
                    if time_id == 2 and achou == -1:
                        escondeu = -1
                    dados = {
                        "jogador_escondeu": escondeu,
                        "jogador_achou": achou,
                    }
                    proxy.on_field_update(linha, coluna, dados)
                except Exception as e:
                    print(f"[JOGO] Callback morto ({callback_uri}): {e}")
                    mortos.append(callback_uri)
            for uri in mortos:
                self._callbacks = [
                    (u, t) for u, t in self._callbacks if u != uri
                ]

    def _executar_broadcast(self, metodo: str, *args):
        """Executa chamada remota em todos os callbacks."""
        with self._lock_callbacks:
            mortos = []
            for callback_uri, _ in self._callbacks:
                try:
                    proxy = Pyro5.api.Proxy(callback_uri)
                    getattr(proxy, metodo)(*args)
                except Exception as e:
                    print(f"[JOGO] Callback morto ({callback_uri}): {e}")
                    mortos.append(callback_uri)
            for uri in mortos:
                self._callbacks = [
                    (u, t) for u, t in self._callbacks if u != uri
                ]
