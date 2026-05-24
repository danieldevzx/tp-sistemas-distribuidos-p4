import socket
import json
import struct
import threading
import time


class ClienteRede:
    def __init__(self, host: str = 'localhost', porta: int = 5000):
        self.host = host
        self.porta = porta
        self.socket: socket.socket | None = None
        self._lock_envio = threading.Lock()
        self._max_tentativas_reconexao = 3

    def conectar(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.porta))
            self.socket.settimeout(None)
            return True
        except Exception as e:
            print(f"[REDE] Erro de conexão: {e}")
            self.socket = None
            return False

    def reconectar(self) -> bool:
        self.fechar()
        for tentativa in range(self._max_tentativas_reconexao):
            espera = 2 ** tentativa
            print(f"[REDE] Tentativa {tentativa + 1}/{self._max_tentativas_reconexao} em {espera}s...")
            time.sleep(espera)
            if self.conectar():
                print("[REDE] Reconectado!")
                return True
        return False

    def fechar(self) -> None:
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

    @property
    def esta_conectado(self) -> bool:
        return self.socket is not None

    def enviar(self, mensagem: dict) -> bool:
        if not self.socket:
            return False
        with self._lock_envio:
            try:
                dados = json.dumps(mensagem, ensure_ascii=False).encode('utf-8')
                cabecalho = struct.pack('>I', len(dados))
                self.socket.sendall(cabecalho + dados)
                return True
            except Exception as e:
                print(f"[REDE] Erro ao enviar: {e}")
                return False

    def receber_linha(self) -> dict | None:
        if not self.socket:
            return None
        try:
            cabecalho = self._receber_exato(4)
            if not cabecalho:
                return None
            tamanho = struct.unpack('>I', cabecalho)[0]

            corpo = self._receber_exato(tamanho)
            if not corpo:
                return None

            return json.loads(corpo.decode('utf-8'))
        except (ConnectionResetError, BrokenPipeError, OSError):
            return None
        except json.JSONDecodeError as e:
            print(f"[REDE] JSON inválido: {e}")
            return None

    def _receber_exato(self, n: int) -> bytes | None:
        """Garante que lê exatamente n bytes."""
        dados = b''
        while len(dados) < n:
            chunk = self.socket.recv(n - len(dados))
            if not chunk:
                return None
            dados += chunk
        return dados

    def enviar_e_receber(self, mensagem: dict) -> dict | None:
        if self.enviar(mensagem):
            return self.receber_linha()
        return None