import socket
import json
import threading
import time


class ClienteRede:
    # Cliente TCP que comunica com o servidor usando JSON

    def __init__(self, host: str = 'localhost', porta: int = 5000):
        self.host = host
        self.porta = porta
        self.socket: socket.socket | None = None
        self._buffer = b''
        self._lock_envio = threading.Lock()
        self._max_tentativas_reconexao = 3


    def conectar(self) -> bool:
        # Conecta ao servidor
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.porta))

            self.socket.settimeout(None)
            self._buffer = b''
            return True
        except Exception as e:
            print(f"[REDE] Erro de conexão: {e}")
            self.socket = None
            return False

    def reconectar(self) -> bool:
        # Tenta reconectar ao servidor com backoff exponencial
        self.fechar()
        for tentativa in range(self._max_tentativas_reconexao):
            espera = 2 ** tentativa
            print(f"[REDE] Tentativa de reconexão {tentativa + 1}/{self._max_tentativas_reconexao} em {espera}s...")
            time.sleep(espera)
            if self.conectar():
                print("[REDE] Reconectado com sucesso!")
                return True
        print("[REDE] Falha ao reconectar após todas as tentativas.")
        return False

    def fechar(self) -> None:
        # Fecha o socket de forma segura
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.socket.close()
            except OSError:
                pass
            self.socket = None
        self._buffer = b''

    @property
    def esta_conectado(self) -> bool:
        # Verifica se está conectado
        return self.socket is not None


    def enviar(self, mensagem: dict) -> bool:
        # Envia mensagem JSON
        if not self.socket:
            return False

        with self._lock_envio:
            try:
                dados = json.dumps(mensagem, ensure_ascii=False).encode('utf-8') + b'\n'
                self.socket.sendall(dados)
                return True
            except Exception as e:
                print(f"[REDE] Erro ao enviar: {e}")
                return False


    def receber_linha(self) -> dict | None:
        # Lê do socket até encontrar \\n
        if not self.socket:
            return None

        try:
            while b'\n' not in self._buffer:
                dados = self.socket.recv(4096)
                if not dados:

                    return None
                self._buffer += dados


            linha, self._buffer = self._buffer.split(b'\n', 1)
            return json.loads(linha.decode('utf-8'))

        except (ConnectionResetError, BrokenPipeError, OSError):
            return None
        except json.JSONDecodeError as e:
            print(f"[REDE] JSON inválido recebido: {e}")
            return None


    def enviar_e_receber(self, mensagem: dict) -> dict | None:
        # Envia e aguarda a resposta (bloqueante)
        if self.enviar(mensagem):
            return self.receber_linha()
        return None
