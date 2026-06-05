import os
import socket
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
from model.proxy_servidor import ProxyServidor
from model.callback_cliente import SinaisCallback, DaemonCallback
from model.estado_jogo import EstadoJogo
from controller.worker import WorkerRMI
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

        self.proxy = ProxyServidor()
        self.estado = EstadoJogo()

        # Callback Pyro para broadcasts
        self._sinais_callback = SinaisCallback()
        self._daemon_callback = DaemonCallback(self._sinais_callback)

        self._worker: WorkerRMI | None = None

        self._conectar_sinais_view()
        self._conectar_sinais_callback()

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

    def _conectar_sinais_callback(self):
        """Conecta sinais do callback aos handlers da UI."""
        self._sinais_callback.sinal_tick.connect(self._tratar_tick_tempo)
        self._sinais_callback.sinal_field_update.connect(self._tratar_campo_parcial)
        self._sinais_callback.sinal_phase_change.connect(self._tratar_mudanca_fase)

    # --- Ações do usuário ---

    def processar_login(self, usuario: str, senha: str):
        if not usuario or not senha:
            QMessageBox.warning(self.janela, "Erro", "Por favor, preencha todos os campos")
            return
        self._definir_carregamento(True)

        if not self.proxy.esta_conectado:
            if not self.proxy.conectar():
                self._definir_carregamento(False)
                QMessageBox.warning(self.janela, "Erro", "Não foi possível conectar ao servidor")
                return

        self._iniciar_requisicao(
            self.proxy.usuario.autenticar, usuario, senha,
            callback_sucesso=self._ao_login_sucesso,
        )

    def processar_registro(self, usuario: str, senha: str):
        if not usuario or not senha:
            QMessageBox.warning(self.janela, "Erro", "Por favor, preencha todos os campos")
            return
        self._definir_carregamento(True)

        if not self.proxy.esta_conectado:
            if not self.proxy.conectar():
                self._definir_carregamento(False)
                QMessageBox.warning(self.janela, "Erro", "Não foi possível conectar ao servidor")
                return

        self._iniciar_requisicao(
            self.proxy.usuario.cadastrar, usuario, senha,
            callback_sucesso=self._ao_registro_sucesso,
        )

    def clicar_celula(self, linha: int, coluna: int):
        usuario_dict = asdict(self.estado.jogador_local)
        self._iniciar_requisicao(
            self.proxy.jogo.interacao_campo, usuario_dict, linha, coluna,
            callback_sucesso=self._ao_interacao_sucesso,
        )

    def solicitar_campo(self):
        time_id = self.estado.jogador_local.timeId if self.estado.jogador_local else -1
        self._iniciar_requisicao(
            self.proxy.jogo.obter_campo, time_id,
            callback_sucesso=self._ao_campo_recebido,
        )

    # --- Handlers de resposta ---

    def _ao_login_sucesso(self, resultado):
        self._definir_carregamento(False)
        sucesso, dados = resultado

        if not sucesso:
            QMessageBox.warning(self.janela, "Erro", str(dados))
            return

        self.estado.definir_jogador(dados)
        self.estado.conectado = True

        # Iniciar callback do cliente (com IP real)
        callback_host = os.environ.get("CALLBACK_HOST", "0.0.0.0")
        callback_nathost = socket.gethostbyname(socket.gethostname())
        callback_uri = self._daemon_callback.iniciar(
            host=callback_host, nathost=callback_nathost
        )

        # Registrar callback e reivindicar ownership do proxy
        self.proxy.transferir_ownership()
        self.proxy.jogo.registrar_callback(callback_uri, self.estado.jogador_local.timeId)

        if self.janela and hasattr(self.janela, 'mudar_pagina'):
            self.janela.mudar_pagina(2)
            pagina_home = getattr(self.janela, 'pagina_home', None)
            if pagina_home and hasattr(pagina_home, 'definir_info_jogador'):
                pagina_home.definir_info_jogador(
                    self.estado.jogador_local.nome,
                    self.estado.jogador_local.timeId
                )

        self.solicitar_campo()

    def _ao_registro_sucesso(self, resultado):
        self._definir_carregamento(False)
        sucesso, dados = resultado

        if sucesso:
            QMessageBox.information(self.janela, "Sucesso", str(dados))
            if self.janela and hasattr(self.janela, 'mudar_pagina'):
                self.janela.mudar_pagina(0)
        else:
            QMessageBox.warning(self.janela, "Erro", str(dados))

        self.proxy.transferir_ownership()
        self.proxy.desconectar()

    def _ao_campo_recebido(self, resultado):
        campo_dados = resultado.get("campo", [])
        self.estado.fase = resultado.get("fase", self.estado.fase)
        self.estado.tempo_restante = resultado.get("tempo_restante", self.estado.tempo_restante)

        self.sinal_campo_atualizado.emit(campo_dados)

        pagina_home = getattr(self.janela, 'pagina_home', None)
        if pagina_home and hasattr(pagina_home, 'atualizar_fase'):
            pagina_home.atualizar_fase(self.estado.fase, self.estado.tempo_restante)

    def _ao_interacao_sucesso(self, resultado):
        sucesso, mensagem = resultado
        if not sucesso:
            QMessageBox.warning(self.janela, "Erro", mensagem)

    # --- Handlers de callback (broadcasts do servidor) ---

    def _tratar_tick_tempo(self, tempo_restante: int):
        self.estado.tempo_restante = tempo_restante
        pagina_home = getattr(self.janela, 'pagina_home', None)
        if pagina_home and hasattr(pagina_home, 'atualizar_tempo'):
            pagina_home.atualizar_tempo(tempo_restante)

    def _tratar_campo_parcial(self, linha: int, coluna: int, dados: dict):
        self.sinal_celula_atualizada.emit(linha, coluna, dados)

    def _tratar_mudanca_fase(self, fase: str, tempo: int):
        self.estado.fase = fase
        self.estado.tempo_restante = tempo
        pagina_home = getattr(self.janela, 'pagina_home', None)
        if pagina_home and hasattr(pagina_home, 'atualizar_fase'):
            pagina_home.atualizar_fase(fase, tempo)

    # --- Lifecycle ---

    def desconectar(self):
        """Encerra sessão do cliente."""
        self.proxy.transferir_ownership()
        callback_uri = self._daemon_callback.uri
        if callback_uri and self.proxy.esta_conectado:
            try:
                self.proxy.jogo.remover_callback(callback_uri)
            except Exception:
                pass

        self._daemon_callback.parar()
        self.proxy.desconectar()
        self.estado.resetar()

    # --- Utilitários ---

    def _iniciar_requisicao(self, funcao, *args, callback_sucesso=None):
        """Executa chamada RMI em background."""
        self._worker = WorkerRMI(self.proxy, funcao, *args)
        if callback_sucesso:
            self._worker.sinal_resultado.connect(callback_sucesso)
        self._worker.sinal_erro.connect(self._ao_erro_requisicao)
        self._worker.start()

    def _ao_erro_requisicao(self, mensagem: str):
        self._definir_carregamento(False)
        QMessageBox.warning(self.janela, "Erro", mensagem)

    def _definir_carregamento(self, carregando: bool):
        if self.janela and hasattr(self.janela, 'definir_carregamento'):
            self.janela.definir_carregamento(carregando)