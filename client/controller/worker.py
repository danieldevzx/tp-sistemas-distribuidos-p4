# Threads de background para comunicação com o servidor

from PyQt6.QtCore import QThread, pyqtSignal
from model.cliente_rede import ClienteRede
from model.protocolo import criar_mensagem


class WorkerRequisicao(QThread):
    # Worker para operações request/response simples
    sinal_resultado = pyqtSignal(dict)
    sinal_erro = pyqtSignal(str)

    def __init__(self, cliente: ClienteRede, tipo_requisicao: str, payload: dict):
        super().__init__()
        self.cliente = cliente
        self.tipo_requisicao = tipo_requisicao
        self.payload = payload

    def run(self):
        try:

            if not self.cliente.esta_conectado:
                if not self.cliente.conectar():
                    self.sinal_erro.emit("Não foi possível conectar ao servidor")
                    return


            mensagem = criar_mensagem(self.tipo_requisicao, self.payload)
            resposta = self.cliente.enviar_e_receber(mensagem)

            if resposta is None:
                self.sinal_erro.emit("Servidor não respondeu ou conexão perdida")
                return

            self.sinal_resultado.emit(resposta)

        except Exception as e:
            self.sinal_erro.emit(f"Erro inesperado: {e}")
        finally:
            self.deleteLater()


class WorkerListener(QThread):
    # Worker persistente que escuta mensagens do servidor em loop
    mensagem_recebida = pyqtSignal(dict)
    desconectado = pyqtSignal()

    def __init__(self, cliente: ClienteRede):
        super().__init__()
        self.cliente = cliente
        self._rodando = True

    def run(self):
        # Loop principal
        while self._rodando:
            mensagem = self.cliente.receber_linha()

            if mensagem is None:

                if self._rodando:
                    self.desconectado.emit()
                break

            self.mensagem_recebida.emit(mensagem)

    def parar(self):
        # Encerra o worker
        self._rodando = False

        self.cliente.fechar()
