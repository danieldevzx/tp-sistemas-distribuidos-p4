import socket
import threading
import json
import struct
from modelo.bd_base import inicializar_banco
from controller.usuario_controller import UsuarioController


class ServidorRede:
    def __init__(self, host='0.0.0.0', porta=5000):
        self.host = host
        self.porta = porta
        self.servidor = None
        self.usuario_controller = UsuarioController()
        # Guarda tuplas (socket, time_id) para poder filtrar broadcasts por time
        self._clientes: list[tuple[socket.socket, int]] = []
        self._lock_clientes = threading.Lock()

    # ------------------------------------------------------------------ #
    #  Gerência de clientes                                                #
    # ------------------------------------------------------------------ #

    def _registrar_cliente(self, sock, time_id: int):
        with self._lock_clientes:
            self._clientes.append((sock, time_id))

    def _remover_cliente(self, sock):
        with self._lock_clientes:
            self._clientes = [(s, t) for s, t in self._clientes if s is not sock]

    def _enviar_pacote(self, sock, mensagem: dict) -> bool:
        try:
            dados = json.dumps(mensagem).encode('utf-8')
            sock.sendall(struct.pack('>I', len(dados)) + dados)
            return True
        except Exception:
            return False

    def _broadcast(self, mensagem: dict):
        """Envia a mesma mensagem para todos os clientes."""
        with self._lock_clientes:
            mortos = []
            for sock, _ in self._clientes:
                if not self._enviar_pacote(sock, mensagem):
                    mortos.append(sock)
            for sock in mortos:
                self._clientes = [(s, t) for s, t in self._clientes if s is not sock]

    def _broadcast_field_update(self, linha: int, coluna: int, celula):
        """
        Envia FIELD_UPDATE com filtragem por time:
        - Time 1 (montagem):  vê jogador_escondeu e jogador_achou normalmente.
        - Time 2 (escavação): jogador_escondeu sempre chega como -1 (célula oculta).
        """
        with self._lock_clientes:
            mortos = []
            for sock, time_id in self._clientes:
                escondeu = celula.getJogadorEscondeu()
                achou    = celula.getJogadorAchou()

                # Time de escavação não sabe onde o time de montagem escondeu
                if time_id == 2:
                    escondeu = -1

                msg = {
                    "type": "FIELD_UPDATE",
                    "payload": {
                        "linha": linha,
                        "coluna": coluna,
                        "jogador_escondeu": escondeu,
                        "jogador_achou":    achou,
                    }
                }
                if not self._enviar_pacote(sock, msg):
                    mortos.append(sock)
            for sock in mortos:
                self._clientes = [(s, t) for s, t in self._clientes if s is not sock]

    # ------------------------------------------------------------------ #
    #  Inicialização                                                       #
    # ------------------------------------------------------------------ #

    def iniciar(self):
        inicializar_banco()
        self.usuario_controller.jogo.iniciar_timer(self._ao_tick, self._ao_fim_montagem)

        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.servidor.bind((self.host, self.porta))
        self.servidor.listen()
        print(f"[ESCUTANDO] Servidor rodando em {self.host}:{self.porta}")

        try:
            while True:
                sock, endereco = self.servidor.accept()
                t = threading.Thread(target=self.tratar_cliente, args=(sock, endereco))
                t.daemon = True
                t.start()
                print(f"[CONEXÕES ATIVAS] {threading.active_count() - 1}")
        except KeyboardInterrupt:
            print("\n[DESLIGANDO] Servidor parado.")
        finally:
            if self.servidor:
                self.servidor.close()

    # ------------------------------------------------------------------ #
    #  Callbacks do timer                                                  #
    # ------------------------------------------------------------------ #

    def _ao_tick(self, tempo_restante: int):
        self._broadcast({
            "type": "TIMER_TICK",
            "payload": {"tempo_restante": tempo_restante}
        })

    def _ao_fim_montagem(self):
        print("[JOGO] Fase de montagem encerrada — broadcast PHASE_CHANGE")
        self._broadcast({
            "type": "PHASE_CHANGE",
            "payload": {"fase": "escavacao", "tempo_restante": 0}
        })

    # ------------------------------------------------------------------ #
    #  Loop de cliente                                                     #
    # ------------------------------------------------------------------ #

    def tratar_cliente(self, sock, endereco):
        print(f"[NOVA CONEXÃO] {endereco} conectado.")
        time_id = -1
        try:
            while True:
                cabecalho = sock.recv(4)
                if not cabecalho:
                    break

                tamanho = struct.unpack('>I', cabecalho)[0]
                dados = b''
                while len(dados) < tamanho:
                    chunk = sock.recv(tamanho - len(dados))
                    if not chunk:
                        break
                    dados += chunk
                if not dados:
                    break

                requisicao = json.loads(dados.decode('utf-8'))
                tipo    = requisicao.get('type')
                payload = requisicao.get('payload')
                print(f"[REQUISIÇÃO] {tipo} de {endereco}")

                sucesso, tipo_resp, mensagem = self.processar_comando(tipo, payload)

                # Registra cliente com seu time_id após login
                if tipo == 'LOGIN' and sucesso:
                    # mensagem é a lista retornada por autenticar: [id, nome, ..., time_id]
                    time_id = mensagem[3]
                    self._registrar_cliente(sock, time_id)

                # Filtra FIELD_STATE para o time de escavação
                if tipo == 'GET_FIELD' and sucesso:
                    time_id_req = payload.get('time_id', time_id)
                    if time_id_req == 2:
                        mensagem = self._filtrar_campo_para_escavacao(mensagem)

                resposta   = {"success": sucesso, "type": tipo_resp, "payload": mensagem}
                dados_resp = json.dumps(resposta).encode('utf-8')
                sock.sendall(struct.pack('>I', len(dados_resp)) + dados_resp)

                # Broadcast filtrado por time após ADD_STRUCTURE
                if tipo == 'ADD_STRUCTURE' and sucesso:
                    linha  = payload.get("linha")
                    coluna = payload.get("coluna")
                    celula = self.usuario_controller.jogo.getCampo().getCampo()[linha][coluna]
                    self._broadcast_field_update(linha, coluna, celula)

        except Exception as e:
            print(f"[ERRO] {endereco}: {e}")
        finally:
            self._remover_cliente(sock)
            sock.close()
            print(f"[DESCONECTADO] {endereco} fechado.")

    def _filtrar_campo_para_escavacao(self, mensagem: dict) -> dict:
        """Remove jogador_escondeu do campo antes de enviar ao time de escavação."""
        campo_filtrado = []
        for linha in mensagem.get("campo", []):
            linha_filtrada = []
            for celula in linha:
                linha_filtrada.append({
                    "jogador_escondeu": -1,           # oculto para escavação
                    "jogador_achou":    celula["jogador_achou"],
                })
            campo_filtrado.append(linha_filtrada)
        return {**mensagem, "campo": campo_filtrado}

    def processar_comando(self, tipo, payload):
        if tipo == 'REGISTER':
            return self.usuario_controller.cadastrar(payload)
        elif tipo == 'LOGIN':
            return self.usuario_controller.autenticar(payload)
        elif tipo == 'ADD_STRUCTURE':
            return self.usuario_controller.adicionar_estrutura(payload)
        elif tipo == 'GET_FIELD':
            return self.usuario_controller.obter_campo()
        return False, "ACTION_ERROR", "Tipo de comando desconhecido"