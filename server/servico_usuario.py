import Pyro5.api
import random
from modelo.usuario_modelo import UsuarioModelo


@Pyro5.api.expose
class ServicoUsuario:
    """Serviço remoto de autenticação."""

    def cadastrar(self, usuario: str, senha: str):
        if not usuario or not senha:
            return False, "Usuário e senha são obrigatórios"
        resultado = UsuarioModelo.inserir(usuario, senha, random.randint(1, 2))
        return True, resultado

    def autenticar(self, usuario: str, senha: str):
        if not usuario or not senha:
            return False, "Usuário e senha são obrigatórios"
        resultado = UsuarioModelo.buscar_por_credenciais(usuario, senha)
        if resultado:
            return True, list(resultado)
        return False, "Usuário ou senha inválidos"
