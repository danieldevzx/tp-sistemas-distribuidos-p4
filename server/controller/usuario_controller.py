from modelo.usuario_modelo import UsuarioModelo
import random
from modelo.jogo import Jogo


class UsuarioController:
    def __init__(self):
        self.jogo = Jogo()

    @staticmethod
    def cadastrar(dados_payload):
        usuario = dados_payload.get('username')
        senha = dados_payload.get('password')
        if not usuario or not senha:
            return False, "ACTION_ERROR", "Usuário e senha são obrigatórios"
        return True, "ACTION_SUCCESS", UsuarioModelo.inserir(usuario, senha, random.randint(1, 2))

    @staticmethod
    def autenticar(dados_payload):
        usuario = dados_payload.get('username')
        senha = dados_payload.get('password')
        if not usuario or not senha:
            return False, "ACTION_ERROR", "Usuário e senha são obrigatórios"
        resultado = UsuarioModelo.buscar_por_credenciais(usuario, senha)
        if resultado:
            return True, "ACTION_SUCCESS", resultado
        return False, "ACTION_ERROR", "Usuário ou senha inválidos"

    def adicionar_estrutura(self, dados_payload):
        usuario = dados_payload.get('usuario')
        linha   = dados_payload.get('linha')
        coluna  = dados_payload.get('coluna')

        resultado, motivo = self.jogo.interacaoCampo(usuario, linha, coluna)

        if not resultado:
            if motivo == "aguarde":
                return False, "ACTION_ERROR", "Fase de montagem ainda não terminou — aguarde para escavar"
            if motivo == "encerrada":
                return False, "ACTION_ERROR", "Fase de montagem encerrada — não é mais possível adicionar estruturas"
            return False, "ACTION_ERROR", "Célula já ocupada"

        if motivo == "removed":
            return True, "ACTION_SUCCESS", "Estrutura removida com sucesso"

        return True, "ACTION_SUCCESS", "Estrutura adicionada com sucesso"

    def obter_campo(self):
        campo = self.jogo.getCampo().getCampo()
        info  = self.jogo.get_info_fase()
        serializado = []
        for linha in campo:
            linha_dados = []
            for celula in linha:
                linha_dados.append({
                    "jogador_escondeu": celula.getJogadorEscondeu(),
                    "jogador_achou":    celula.getJogadorAchou(),
                })
            serializado.append(linha_dados)
        # Inclui fase e tempo no FIELD_STATE para o cliente sincronizar
        return True, "FIELD_STATE", {
            "campo": serializado,
            "fase": info["fase"],
            "tempo_restante": info["tempo_restante"],
        }