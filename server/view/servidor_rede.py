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

        # Guarda todos os sockets de clientes logados
        self._clientes: list[socket.socket] = []
        self._lock_clientes = threading.Lock()  # protege a lista

    def _registrar_cliente(self, socket_cliente):
        with self._lock_clientes:
            self._clientes.append(socket_cliente)

    def _remover_cliente(self, socket_cliente):
        with self._lock_clientes:
            self._clientes.remove(socket_cliente)

    def _broadcast(self, mensagem: dict):
        """Envia uma mensagem para TODOS os clientes conectados."""
        dados = json.dumps(mensagem).encode('utf-8')
        cabecalho = struct.pack('>I', len(dados))
        pacote = cabecalho + dados

        with self._lock_clientes:
            mortos = []
            for cliente in self._clientes:
                try:
                    cliente.sendall(pacote)
                except Exception:
                    mortos.append(cliente)
            for m in mortos:
                self._clientes.remove(m)

    def iniciar(self):
        inicializar_banco()
        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.servidor.bind((self.host, self.porta))
        self.servidor.listen()
        print(f"[ESCUTANDO] Servidor rodando em {self.host}:{self.porta}")

        try:
            while True:
                socket_cliente, endereco = self.servidor.accept()
                thread = threading.Thread(
                    target=self.tratar_cliente,
                    args=(socket_cliente, endereco)
                )
                thread.start()
                print(f"[CONEXÕES ATIVAS] {threading.active_count() - 1}")
        except KeyboardInterrupt:
            print("\n[DESLIGANDO] Servidor parado.")
        finally:
            if self.servidor:
                self.servidor.close()

    def tratar_cliente(self, socket_cliente, endereco):
        print(f"[NOVA CONEXÃO] {endereco} conectado.")
        autenticado = False
        try:
            while True:
                cabecalho = socket_cliente.recv(4)
                if not cabecalho:
                    break

                tamanho_mensagem = struct.unpack('>I', cabecalho)[0]
                dados = b''
                while len(dados) < tamanho_mensagem:
                    chunk = socket_cliente.recv(tamanho_mensagem - len(dados))
                    if not chunk:
                        break
                    dados += chunk

                if not dados:
                    break

                requisicao = json.loads(dados.decode('utf-8'))
                tipo = requisicao.get('type')
                payload = requisicao.get('payload')

                print(f"[REQUISIÇÃO] {tipo} de {endereco}")

                sucesso, tipo_resp, mensagem = self.processar_comando(tipo, payload)

                # Após login bem-sucedido, registra o socket para broadcasts
                if tipo == 'LOGIN' and sucesso and not autenticado:
                    self._registrar_cliente(socket_cliente)
                    autenticado = True

                resposta = {"success": sucesso, "type": tipo_resp, "payload": mensagem}
                dados_resposta = json.dumps(resposta).encode('utf-8')
                cabecalho_resposta = struct.pack('>I', len(dados_resposta))
                socket_cliente.sendall(cabecalho_resposta + dados_resposta)

                # Se foi ADD_STRUCTURE com sucesso → broadcast FIELD_UPDATE
                if tipo == 'ADD_STRUCTURE' and sucesso:
                    linha  = payload.get("linha")
                    coluna = payload.get("coluna")
                    # Busca o estado atualizado diretamente no modelo
                    celula = self.usuario_controller.jogo.getCampo().getCampo()[linha][coluna]
                    update = {
                        "type": "FIELD_UPDATE",
                        "payload": {
                            "linha": linha,
                            "coluna": coluna,
                            "jogador_escondeu": celula.getJogadorEscondeu(),
                            "jogador_achou":    celula.getJogadorAchou(),
                        }
                    }
                    self._broadcast(update)  # notifica TODOS (inclusive o autor)

        except Exception as e:
            print(f"[ERRO] {endereco}: {e}")
        finally:
            if autenticado:
                self._remover_cliente(socket_cliente)
            socket_cliente.close()
            print(f"[DESCONECTADO] {endereco} fechado.")

    def processar_comando(self, tipo, payload):
        if tipo == 'REGISTER':
            return self.usuario_controller.cadastrar(payload)
        elif tipo == 'LOGIN':
            return self.usuario_controller.autenticar(payload)
        elif tipo == 'ADD_STRUCTURE':
            return self.usuario_controller.adicionar_estrutura(payload)
        elif tipo == 'GET_FIELD':
            return self.usuario_controller.obter_campo()  # ← novo (ver abaixo)
        return False, "ACTION_ERROR", "Tipo de comando desconhecido"