# Worker de background para chamadas RMI Pyro5

from PyQt6.QtCore import QThread, pyqtSignal


class WorkerRMI(QThread):
    """Worker para chamadas RMI em background."""
    sinal_resultado = pyqtSignal(object)
    sinal_erro = pyqtSignal(str)

    def __init__(self, proxy, funcao, *args):
        super().__init__()
        self._proxy = proxy
        self._funcao = funcao
        self._args = args

    def run(self):
        try:
            self._proxy.transferir_ownership()
            resultado = self._funcao(*self._args)
            self.sinal_resultado.emit(resultado)
        except Exception as e:
            self.sinal_erro.emit(f"Erro na requisição: {e}")
        finally:
            self.deleteLater()
