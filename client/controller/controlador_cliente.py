import os
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from model.cliente_rede import ClienteRede
from model.estado_jogo import EstadoJogo
from model import protocolo
from controller.worker import WorkerRequisicao, WorkerListener
from dataclasses import asdict


class ControladorCliente(QObject):
    sinal_login_erro = pyqtSignal(str)
    sinal_registro_sucesso = pyqtSignal(str)
    sinal_registro_erro = pyqtSignal(str)
    sinal_campo_atualizado = pyqtSignal(list)
    sinal_celula_atualizada = pyqtSignal(int, int, dict)

    def __init__(self, janela=None, parent=None):
        super().__init__(parent)
        self.janela = janela

        host = os.environ.get('SERVER_HOST', 'localhost')
        porta = int(os.environ.get('SERVER_PORT', 5000))
        self.rede = ClienteRede(host=host, porta=porta)
        self.estado = EstadoJogo()

        self._worker_requisicao: WorkerRequisicao | None = None
        self._worker_listener: WorkerListener | None = None

        self._conectar_sinais_view()

    def _conectar_sinais_view(self):
        if self.janela is None:
            return

        pagina_login = getattr(self.janela, 'pagina_login', None)
        if pagina_login and hasattr(pagina_login, 'requisitar_login'):
            pagina_login.requisitar_login.connect(self.processar_login)

        pagina_registro = getattr(self.janela, 'pagina_registro', None)
        if pagina_registro and hasattr(pagina_registro, 'requisitar_registro'):
            pagina_registro.requisitar_registro.connect(self.processar_registro)

        pagina_home = getattr(self.janela, 'pagina_home', None)
        if pagina_home:
            if hasattr(pagina_home, 'requisitar_criar_celula'):
                pagina_home.requisitar_criar_celula.connect(self.clicar_celula)
            self.sinal_campo_atualizado.connect(pagina_home.atualizar_campo_completo)
            self.sinal_celula_atualizada.connect(pagina_home.atualizar_celula)

    def processar_login(self, usuario: str, senha: str):
        if not usuario or not senha:
            QMessageBox.warning(self.janela, "Erro", "Por favor, preencha todos os campos")
            return
        self._definir_carregamento(True)
        self._iniciar_requisicao(protocolo.LOGIN, {"username": usuario, "password": senha})

    def processar_registro(self, usuario: str, senha: str):
        if not usuario or not senha:
            QMessageBox.warning(self.janela, "Erro", "Por favor, preencha todos os campos")
            return
        self._definir_carregamento(True)
        self._iniciar_requisicao(protocolo.REGISTER, {"username": usuario, "password": senha})

    def clicar_celula(self, linha: int, coluna: int):
        mensagem = protocolo.criar_mensagem(
            protocolo.INTERACT_FIELD,
            {"usuario": asdict(self.estado.jogador_local), "linha": linha, "coluna": coluna}
        )
        self.rede.enviar(mensagem)

    def solicitar_campo(self):
        time_id = self.estado.jogador_local.timeId if self.estado.jogador_local else -1
        mensagem = protocolo.criar_mensagem(protocolo.GET_FIELD, {"time_id": time_id})
        self.rede.enviar(mensagem)

    def _ao_receber_mensagem(self, dados: dict):
        tipo, payload = protocolo.parse_mensagem(dados)
        roteador = {
            protocolo.FIELD_STATE:    self._tratar_campo_completo,
            protocolo.FIELD_UPDATE:   self._tratar_campo_parcial,
            protocolo.ACTION_SUCCESS: self._tratar_acao_sucesso,
            protocolo.ACTION_ERROR:   self._tratar_acao_erro,
            protocolo.PHASE_CHANGE:   self._tratar_mudanca_fase,
            protocolo.TIMER_TICK:     self._tratar_tick_tempo,
        }
        handler = roteador.get(tipo)
        if handler:
            handler(payload)
        else:
            print(f"[CTRL] Tipo de mensagem desconhecido: {tipo}")

    def _tratar_login_sucesso(self, payload: dict):
        self._definir_carregamento(False)
        self.estado.definir_jogador(payload)
        self.estado.conectado = True

        if self.janela and hasattr(self.janela, 'mudar_pagina'):
            self.janela.mudar_pagina(2)
            pagina_home = getattr(self.janela, 'pagina_home', None)
            if pagina_home and hasattr(pagina_home, 'definir_info_jogador'):
                pagina_home.definir_info_jogador(
                    self.estado.jogador_local.nome,
                    self.estado.jogador_local.timeId
                )

        self.solicitar_campo()

    def _tratar_campo_completo(self, payload: dict):
        campo_dados = payload.get("campo", [])
        self.estado.fase = payload.get("fase", self.estado.fase)
        self.estado.tempo_restante = payload.get("tempo_restante", self.estado.tempo_restante)

        self.sinal_campo_atualizado.emit(campo_dados)

        pagina_home = getattr(self.janela, 'pagina_home', None)
        if pagina_home and hasattr(pagina_home, 'atualizar_fase'):
            pagina_home.atualizar_fase(self.estado.fase, self.estado.tempo_restante)

    def _tratar_campo_parcial(self, payload: dict):
        linha  = payload.get("linha", -1)
        coluna = payload.get("coluna", -1)
        self.sinal_celula_atualizada.emit(linha, coluna, payload)

    def _tratar_tick_tempo(self, payload: dict):
        tempo = payload.get("tempo_restante", 0)
        self.estado.tempo_restante = tempo
        pagina_home = getattr(self.janela, 'pagina_home', None)
        if pagina_home and hasattr(pagina_home, 'atualizar_tempo'):
            pagina_home.atualizar_tempo(tempo)

    def _tratar_mudanca_fase(self, payload: dict):
        fase  = payload.get("fase", "escavacao")
        tempo = payload.get("tempo_restante", 0)
        self.estado.fase = fase
        self.estado.tempo_restante = tempo
        pagina_home = getattr(self.janela, 'pagina_home', None)
        if pagina_home and hasattr(pagina_home, 'atualizar_fase'):
            pagina_home.atualizar_fase(fase, tempo)

    def _tratar_acao_sucesso(self, payload: dict):
        QMessageBox.information(self.janela, "Status", payload)

    def _tratar_acao_erro(self, payload: dict):
        QMessageBox.warning(self.janela, "Status", payload)

    def _ao_desconectar(self):
        self.estado.conectado = False
        print("[CTRL] Conexão perdida com o servidor.")
        if self.rede.reconectar():
            self.estado.conectado = True
            self._iniciar_listener()
            self.solicitar_campo()
        else:
            print("[CTRL] Não foi possível reconectar.")

    def desconectar(self):
        # Encerra a sessão
        if self._worker_listener:
            self._worker_listener.parar()
            self._worker_listener.wait(3000)
            self._worker_listener = None

        self.rede.fechar()
        self.estado.resetar()
        self.estado.conectado = False

    def _iniciar_requisicao(self, tipo: str, payload: dict):
        self._worker_requisicao = WorkerRequisicao(self.rede, tipo, payload)
        self._worker_requisicao.sinal_resultado.connect(
            lambda resp: self._ao_receber_resposta_oneshot(tipo, resp)
        )
        self._worker_requisicao.sinal_erro.connect(self._ao_erro_requisicao)
        self._worker_requisicao.start()

    def _ao_receber_resposta_oneshot(self, tipo_original: str, resposta: dict):
        _, payload = protocolo.parse_mensagem(resposta)

        self._definir_carregamento(False)

        if tipo_original == protocolo.LOGIN:
            if resposta["success"]:
                self._tratar_login_sucesso(payload)
                self._iniciar_listener()
            else:
                self.sinal_login_erro.emit(resposta.get("message", "Erro no login"))

        elif tipo_original == protocolo.REGISTER:
            if resposta["success"]:
                self.sinal_registro_sucesso.emit(resposta.get("message", "Registrado"))
                if self.janela and hasattr(self.janela, 'mudar_pagina'):
                    self.janela.mudar_pagina(0)
            else:
                self.sinal_registro_erro.emit(resposta.get("message", "Erro no registro"))
            self.rede.fechar()

    def _ao_erro_requisicao(self, mensagem: str):
        self._definir_carregamento(False)
        self.sinal_login_erro.emit(mensagem)

    def _iniciar_listener(self):
        if self._worker_listener and self._worker_listener.isRunning():
            return
        self._worker_listener = WorkerListener(self.rede)
        self._worker_listener.mensagem_recebida.connect(self._ao_receber_mensagem)
        self._worker_listener.desconectado.connect(self._ao_desconectar)
        self._worker_listener.start()
        print("[CTRL] Listener de mensagens iniciado.")

    def _definir_carregamento(self, carregando: bool):
        if self.janela and hasattr(self.janela, 'definir_carregamento'):
            self.janela.definir_carregamento(carregando)