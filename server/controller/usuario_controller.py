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
            return False, "ACTION_ERROR", "Usuário e senha são obrigatórios"
        time = random.randint(1, 2)
        return True, "ACTION_SUCCESS", UsuarioModelo.inserir(usuario, senha, 1)

    @staticmethod
    def autenticar(dados_payload):
        usuario = dados_payload.get('username')
        senha = dados_payload.get('password')
        
        if not usuario or not senha:
            return False, "Usuário e senha são obrigatórios"
            
        resultado = UsuarioModelo.buscar_por_credenciais(usuario, senha)

        if resultado:
            return True,"ACTION_SUCCESS", resultado
        else:
            return False, "ACTION_ERROR", "Usuário ou senha inválidos"
    
    def adicionar_estrutura(self, dados_payload):
        usuario = dados_payload.get('usuario')
        linha = dados_payload.get('linha')
        coluna = dados_payload.get('coluna')
        resultado = self.jogo.interacaoCampo(usuario, linha, coluna)
        print("CHOU AQUTII")
        if resultado:
            return True, "ACTION_SUCCESS", "Estrutura adicionada com sucesso"
        return False, "ACTION_ERROR", "Não foi adicionada"
    
    def obter_campo(self):
        campo = self.jogo.getCampo().getCampo()  # matriz 20×20 de Estrutura
        serializado = []
        for linha in campo:
            linha_dados = []
            for celula in linha:
                linha_dados.append({
                    "jogador_escondeu": celula.getJogadorEscondeu(),
                    "jogador_achou":    celula.getJogadorAchou(),
                })
            serializado.append(linha_dados)

        return True, "FIELD_STATE", {"campo": serializado}