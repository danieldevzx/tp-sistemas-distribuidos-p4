from modelo.usuario_modelo import UsuarioModelo
import random

class UsuarioController:
    """
    Controlador responsável por processar as requisições de negócio 
    relacionadas a usuários.
    """
    @staticmethod
    def cadastrar(dados_payload):
        usuario = dados_payload.get('username')
        senha = dados_payload.get('password')
        
        if not usuario or not senha:
            return False, "Usuário e senha são obrigatórios"
        
        return UsuarioModelo.inserir(usuario, senha, random.randint(1, 2))

    @staticmethod
    def autenticar(dados_payload):
        usuario = dados_payload.get('username')
        senha = dados_payload.get('password')
        
        if not usuario or not senha:
            return False, "Usuário e senha são obrigatórios"
            
        resultado = UsuarioModelo.buscar_por_credenciais(usuario, senha)
        
        if resultado:
            return True, "Login realizado com sucesso"
        else:
            return False, "Usuário ou senha inválidos"
