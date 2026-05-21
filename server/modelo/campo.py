from .estrutura import Estrutura

class Campo:
    def __init__(self):
        self.campo = [[Estrutura(posicao=(linha, coluna)) for coluna in range(20)] for linha in range(20)]
    
    def getCampo(self):
        return self.campo

    def interacaoCampo(self, usuario, posicao):
        linha, coluna = posicao
        celula = self.campo[linha][coluna]

        if usuario.timeId == 1:
            if celula.getJogadorEscondeu() != -1:
                return False
            celula.setJogadorEscondeu(usuario.id)
        else:
            if celula.getJogadorAchou != -1:
                return False
            celula.setJogadorAchou(usuario.id)

        return True

        