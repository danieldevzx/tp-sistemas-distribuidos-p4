import os
import socket
import time
import Pyro5.api
import Pyro5.server
from servico_usuario import ServicoUsuario
from servico_jogo import ServicoJogo


def _eh_nathost_valido(valor: str | None) -> bool:
    if not valor:
        return False
    return valor not in {"server", "localhost", "0.0.0.0", "127.0.0.1", "::1"}


def resolver_nathost() -> str | None:
    """Resolve um host utilizável para a URI Pyro publicada no Name Server."""
    for valor in (os.environ.get("HOST_IP"), os.environ.get("SERVER_NATHOST")):
        if _eh_nathost_valido(valor):
            return valor

    try:
        host = socket.gethostbyname(socket.gethostname())
        if _eh_nathost_valido(host):
            return host
    except Exception:
        pass

    try:
        host = socket.gethostname()
        if _eh_nathost_valido(host):
            return host
    except Exception:
        pass

    return None


def aguardar_nameserver(host: str, port: int, tentativas: int = 10, intervalo: int = 2):
    """Aguarda a disponibilidade do Name Server."""
    for i in range(tentativas):
        try:
            ns = Pyro5.api.locate_ns(host=host, port=port)
            print(f"[MAIN] Name Server encontrado em {host}:{port}")
            return ns
        except Exception:
            print(f"[MAIN] Aguardando Name Server ({i + 1}/{tentativas})...")
            time.sleep(intervalo)
    raise RuntimeError(f"Name Server não encontrado em {host}:{port} após {tentativas} tentativas")


def principal():
    """Inicializa o servidor e registra os serviços no Name Server."""
    ns_host = os.environ.get("NS_HOST", "localhost")
    ns_port = int(os.environ.get("NS_PORT", "9090"))
    server_host = os.environ.get("SERVER_HOST", "0.0.0.0")
    server_port = int(os.environ.get("SERVER_PORT", "9091"))
    server_nathost = resolver_nathost()

    ns = aguardar_nameserver(ns_host, ns_port)

    daemon = Pyro5.server.Daemon(host=server_host, port=server_port, nathost=server_nathost)
    print(f"[MAIN] Registrando URIs Pyro com nathost={server_nathost or 'auto'}")

    servico_usuario = ServicoUsuario()
    uri_usuario = daemon.register(servico_usuario)
    ns.register("servidor.usuario", uri_usuario)
    print(f"[MAIN] ServicoUsuario registrado: {uri_usuario}")

    servico_jogo = ServicoJogo()
    uri_jogo = daemon.register(servico_jogo)
    ns.register("servidor.jogo", uri_jogo)
    print(f"[MAIN] ServicoJogo registrado: {uri_jogo}")

    print(f"[MAIN] Servidor Pyro5 pronto. Aguardando requisições...")
    daemon.requestLoop()


if __name__ == "__main__":
    principal()
