import os
import threading
import Pyro5.api


class ProxyServidor:
    """Gerenciador dos proxies Pyro para o servidor."""

    def __init__(self):
        self._ns_host = os.environ.get("NS_HOST", "localhost")
        self._ns_port = int(os.environ.get("NS_PORT", "9090"))
        self._proxy_usuario = None
        self._proxy_jogo = None
        self._lock_chamada = threading.RLock()

    def conectar(self) -> bool:
        """Localiza os serviços no Name Server."""
        try:
            ns = Pyro5.api.locate_ns(host=self._ns_host, port=self._ns_port)
            uri_usuario = ns.lookup("servidor.usuario")
            uri_jogo = ns.lookup("servidor.jogo")
            self._proxy_usuario = Pyro5.api.Proxy(uri_usuario)
            self._proxy_jogo = Pyro5.api.Proxy(uri_jogo)
            print(f"[PROXY] Conectado via Name Server ({self._ns_host})")
            return True
        except Exception as e:
            print(f"[PROXY] Erro ao conectar: {e}")
            return False

    def desconectar(self):
        """Libera os proxies."""
        if self._proxy_usuario:
            self._proxy_usuario._pyroRelease()
            self._proxy_usuario = None
        if self._proxy_jogo:
            self._proxy_jogo._pyroRelease()
            self._proxy_jogo = None

    @property
    def usuario(self):
        return self._proxy_usuario

    @property
    def jogo(self):
        return self._proxy_jogo

    @property
    def esta_conectado(self) -> bool:
        return self._proxy_usuario is not None and self._proxy_jogo is not None

    def transferir_ownership(self):
        """Reivindica a posse dos proxies para a thread atual."""
        if self._proxy_usuario:
            self._proxy_usuario._pyroClaimOwnership()
        if self._proxy_jogo:
            self._proxy_jogo._pyroClaimOwnership()

    @property
    def lock_chamada(self):
        return self._lock_chamada
