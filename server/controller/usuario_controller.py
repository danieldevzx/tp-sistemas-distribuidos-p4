from modelo.usuario_modelo import UsuarioModelo
import random
from modelo.jogo import Jogo

class UsuarioController:
    """
    Controlador responsável por processar as requisições de negócio 
    relacionadas a usuários.
    """
    def __init__(self):
        self.jogo = Jogo()


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
            return True, { "mensagem": "Login realizado com sucesso", "usuario": resultado }
        else:
            return False, "Usuário ou senha inválidos"
    
    @staticmethod
    def interagir_campo(dados_payload):
        usuario = dados_payload.get('usuario')
        posicao = dados_payload.get('posicao')
        if usuario[3] == 1:
            
        else:


        return True, "CAPETA"
