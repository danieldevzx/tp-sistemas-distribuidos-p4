import threading
import Pyro5.api
import Pyro5.server
from PyQt6.QtCore import QObject, pyqtSignal


class SinaisCallback(QObject):
    """Sinais Qt para repasse de eventos remotos."""
    sinal_tick = pyqtSignal(int)
    sinal_field_update = pyqtSignal(int, int, dict)
    sinal_phase_change = pyqtSignal(str, int)


@Pyro5.api.expose
class CallbackCliente:
    """Objeto remoto de callback do cliente."""

    def __init__(self, sinais: SinaisCallback):
        self._sinais = sinais

    def on_tick(self, tempo_restante: int):
        self._sinais.sinal_tick.emit(tempo_restante)

    def on_field_update(self, linha: int, coluna: int, dados: dict):
        self._sinais.sinal_field_update.emit(linha, coluna, dados)

    def on_phase_change(self, fase: str, tempo: int):
        self._sinais.sinal_phase_change.emit(fase, tempo)


class DaemonCallback:
    """Daemon Pyro local para escuta de callbacks."""

    def __init__(self, sinais: SinaisCallback):
        self._sinais = sinais
        self._daemon = None
        self._uri = None
        self._thread = None

    def iniciar(self, host: str = "0.0.0.0", nathost: str | None = None) -> str:
        """Inicia o daemon local."""
        if nathost:
            self._daemon = Pyro5.server.Daemon(host=host, nathost=nathost)
        else:
            self._daemon = Pyro5.server.Daemon(host=host)
        callback = CallbackCliente(self._sinais)
        self._uri = self._daemon.register(callback)

        self._thread = threading.Thread(
            target=self._daemon.requestLoop, daemon=True
        )
        self._thread.start()
        print(f"[CALLBACK] Daemon do cliente iniciado: {self._uri}")
        return str(self._uri)

    def parar(self):
        """Para o daemon local."""
        if self._daemon:
            self._daemon.shutdown()
            self._daemon = None
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        print("[CALLBACK] Daemon do cliente encerrado.")

    @property
    def uri(self) -> str | None:
        return str(self._uri) if self._uri else None
