import os
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from model.cliente_rede import ClienteRede
from model.estado_jogo import EstadoJogo
from model import protocolo
from controller.worker import WorkerRequisicao, WorkerListener


class ControladorCliente(QObject):
    # Controlador central


    sinal_login_sucesso = pyqtSignal(dict)
    sinal_login_erro = pyqtSignal(str)
    sinal_registro_sucesso = pyqtSignal(str)
    sinal_registro_erro = pyqtSignal(str)
    sinal_campo_atualizado = pyqtSignal(list)
    sinal_celula_atualizada = pyqtSignal(int, int, dict)
    sinal_acao_sucesso = pyqtSignal(str)
    sinal_acao_erro = pyqtSignal(str)
    sinal_fim_de_jogo = pyqtSignal(dict)
    sinal_jogador_info = pyqtSignal(dict)
    sinal_desconectado = pyqtSignal()
    sinal_conectado = pyqtSignal()
    sinal_cooldown_inicio = pyqtSignal(int)
    sinal_cooldown_fim = pyqtSignal()
    sinal_tempo_atualizado = pyqtSignal(int)

    COOLDOWN_ESCAVACAO = 30

    def __init__(self, janela=None, parent=None):
        # Inicializa o controlador
        super().__init__(parent)
        self.janela = janela


        host = os.environ.get('SERVER_HOST', 'localhost')
        porta = int(os.environ.get('SERVER_PORT', 5000))
        self.rede = ClienteRede(host=host, porta=porta)
        self.estado = EstadoJogo()


        self._worker_requisicao: WorkerRequisicao | None = None
        self._worker_listener: WorkerListener | None = None


        self._timer_cooldown = QTimer(self)
        self._timer_cooldown.setSingleShot(True)
        self._timer_cooldown.timeout.connect(self._ao_encerrar_cooldown)


        self._conectar_sinais_view()


    def _conectar_sinais_view(self):
        # Conecta sinais da View
        if self.janela is None:
            return


        pagina_login = getattr(self.janela, 'pagina_login', None)
        if pagina_login and hasattr(pagina_login, 'requisitar_login'):
            pagina_login.requisitar_login.connect(self.processar_login)


        pagina_registro = getattr(self.janela, 'pagina_registro', None)
        if pagina_registro and hasattr(pagina_registro, 'requisitar_registro'):
            pagina_registro.requisitar_registro.connect(self.processar_registro)


    def processar_login(self, usuario: str, senha: str):
        # Processa login
        if not usuario or not senha:
            self.sinal_login_erro.emit("Por favor, preencha todos os campos")
            return

        self._definir_carregamento(True)
        payload = {"username": usuario, "password": senha}
        self._iniciar_requisicao(protocolo.LOGIN, payload)

    def processar_registro(self, usuario: str, senha: str):
        # Processa registro
        if not usuario or not senha:
            self.sinal_registro_erro.emit("Por favor, preencha todos os campos")
            return

        self._definir_carregamento(True)
        payload = {"username": usuario, "password": senha}
        self._iniciar_requisicao(protocolo.REGISTER, payload)


    def clicar_celula(self, linha: int, coluna: int):
        # Processa clique no campo
        if self.estado.cooldown_ativo:
            self.sinal_acao_erro.emit("Aguarde o cooldown terminar")
            return

        mensagem = protocolo.criar_mensagem(
            protocolo.ADD_STRUCTURE,
            {"linha": linha, "coluna": coluna}
        )
        self.rede.enviar(mensagem)

    def remover_estrutura(self, linha: int, coluna: int):
        # Remove estrutura
        mensagem = protocolo.criar_mensagem(
            protocolo.REMOVE_STRUCTURE,
            {"linha": linha, "coluna": coluna}
        )
        self.rede.enviar(mensagem)

    def solicitar_campo(self):
        # Solicita campo
        mensagem = protocolo.criar_mensagem(protocolo.GET_FIELD)
        self.rede.enviar(mensagem)

    def enviar_ping(self):
        # Envia ping
        mensagem = protocolo.criar_mensagem(protocolo.PING)
        self.rede.enviar(mensagem)


    def _ao_receber_mensagem(self, dados: dict):
        # Roteador de mensagens do servidor
        tipo, payload = protocolo.parse_mensagem(dados)

        roteador = {
            protocolo.LOGIN_SUCCESS:  self._tratar_login_sucesso,
            protocolo.LOGIN_ERROR:    self._tratar_login_erro,
            protocolo.FIELD_STATE:    self._tratar_campo_completo,
            protocolo.FIELD_UPDATE:   self._tratar_campo_parcial,
            protocolo.ACTION_SUCCESS: self._tratar_acao_sucesso,
            protocolo.ACTION_ERROR:   self._tratar_acao_erro,
            protocolo.GAME_OVER:      self._tratar_fim_de_jogo,
            protocolo.PLAYER_INFO:    self._tratar_jogador_info,
        }

        handler = roteador.get(tipo)
        if handler:
            handler(payload)
        else:
            print(f"[CTRL] Tipo de mensagem desconhecido: {tipo}")

    def _tratar_login_sucesso(self, payload: dict):
        # Login sucesso
        self._definir_carregamento(False)
        self.estado.definir_jogador(payload)
        self.estado.conectado = True
        self.sinal_login_sucesso.emit(payload)
        self.sinal_conectado.emit()


        if self.janela and hasattr(self.janela, 'mudar_pagina'):
            self.janela.mudar_pagina(2)


        self.solicitar_campo()

    def _tratar_login_erro(self, payload: dict):
        # Login erro
        self._definir_carregamento(False)
        mensagem = payload.get("message", payload.get("mensagem", "Erro no login"))
        self.sinal_login_erro.emit(mensagem)

    def _tratar_campo_completo(self, payload: dict):
        # Campo recebido
        campo_dados = payload.get("campo", [])
        self.estado.inicializar_campo(campo_dados)


        self.estado.tempo_restante = payload.get("tempo_restante", self.estado.tempo_restante)
        self.estado.tentativas_restantes = payload.get("tentativas_restantes", self.estado.tentativas_restantes)
        self.estado.fase = payload.get("fase", self.estado.fase)

        self.sinal_campo_atualizado.emit(campo_dados)
        if self.estado.tempo_restante > 0:
            self.sinal_tempo_atualizado.emit(self.estado.tempo_restante)

    def _tratar_campo_parcial(self, payload: dict):
        # Atualiza célula
        linha = payload.get("linha", -1)
        coluna = payload.get("coluna", -1)
        self.estado.atualizar_celula(linha, coluna, payload)
        self.sinal_celula_atualizada.emit(linha, coluna, payload)

    def _tratar_acao_sucesso(self, payload: dict):
        # Ação sucesso
        mensagem = payload.get("message", payload.get("mensagem", "Ação realizada"))
        self.sinal_acao_sucesso.emit(mensagem)

        self._iniciar_cooldown()

    def _tratar_acao_erro(self, payload: dict):
        # Ação erro
        mensagem = payload.get("message", payload.get("mensagem", "Ação inválida"))
        self.sinal_acao_erro.emit(mensagem)

    def _tratar_fim_de_jogo(self, payload: dict):
        # Fim de jogo
        self.sinal_fim_de_jogo.emit(payload)

    def _tratar_jogador_info(self, payload: dict):
        # Atualiza jogador
        self.estado.definir_jogador(payload)
        self.sinal_jogador_info.emit(payload)


    def _ao_desconectar(self):
        # Tratamento de desconexão
        self.estado.conectado = False
        self.sinal_desconectado.emit()
        print("[CTRL] Conexão perdida com o servidor.")


        if self.rede.reconectar():
            self.estado.conectado = True
            self.sinal_conectado.emit()
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


    def _iniciar_cooldown(self):
        # Inicia cooldown
        self.estado.cooldown_ativo = True
        self._timer_cooldown.start(self.COOLDOWN_ESCAVACAO * 1000)
        self.sinal_cooldown_inicio.emit(self.COOLDOWN_ESCAVACAO)

    def _ao_encerrar_cooldown(self):
        # Fim cooldown
        self.estado.cooldown_ativo = False
        self.sinal_cooldown_fim.emit()


    def _iniciar_requisicao(self, tipo: str, payload: dict):
        # Dispara worker one-shot
        self._worker_requisicao = WorkerRequisicao(self.rede, tipo, payload)
        self._worker_requisicao.sinal_resultado.connect(
            lambda resp: self._ao_receber_resposta_oneshot(tipo, resp)
        )
        self._worker_requisicao.sinal_erro.connect(self._ao_erro_requisicao)
        self._worker_requisicao.start()

    def _ao_receber_resposta_oneshot(self, tipo_original: str, resposta: dict):
        # Processa resposta one-shot
        tipo_resposta, payload = protocolo.parse_mensagem(resposta)


        if "success" in resposta:
            if tipo_original == protocolo.LOGIN:
                if resposta["success"]:
                    self._definir_carregamento(False)
                    self.estado.conectado = True
                    self.estado.definir_jogador(resposta.get("payload", {"nome": ""}))
                    self.sinal_login_sucesso.emit(resposta.get("payload", {}))
                    self.sinal_conectado.emit()
                    if self.janela and hasattr(self.janela, 'mudar_pagina'):
                        self.janela.mudar_pagina(2)

                    self._iniciar_listener()
                else:
                    self._definir_carregamento(False)
                    self.sinal_login_erro.emit(resposta.get("message", "Erro no login"))
            elif tipo_original == protocolo.REGISTER:
                self._definir_carregamento(False)
                if resposta["success"]:
                    self.sinal_registro_sucesso.emit(resposta.get("message", "Registrado"))
                    if self.janela and hasattr(self.janela, 'mudar_pagina'):
                        self.janela.mudar_pagina(0)
                else:
                    self.sinal_registro_erro.emit(resposta.get("message", "Erro no registro"))

            if tipo_original == protocolo.REGISTER:
                self.rede.fechar()
            return


        self._ao_receber_mensagem(resposta)


        if tipo_resposta == protocolo.LOGIN_SUCCESS:
            self._iniciar_listener()

    def _ao_erro_requisicao(self, mensagem: str):
        # Erro de requisição
        self._definir_carregamento(False)
        self.sinal_login_erro.emit(mensagem)

    def _iniciar_listener(self):
        # Inicia worker listener
        if self._worker_listener and self._worker_listener.isRunning():
            return

        self._worker_listener = WorkerListener(self.rede)
        self._worker_listener.mensagem_recebida.connect(self._ao_receber_mensagem)
        self._worker_listener.desconectado.connect(self._ao_desconectar)
        self._worker_listener.start()
        print("[CTRL] Listener de mensagens iniciado.")


    def _definir_carregamento(self, carregando: bool):
        # Atualiza carregamento
        if self.janela and hasattr(self.janela, 'definir_carregamento'):
            self.janela.definir_carregamento(carregando)
