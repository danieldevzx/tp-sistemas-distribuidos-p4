
class Estrutura:
    def __init__(self, posicao, jogador_achou=-1, jogador_escondeu=-1):
        self.posicao = posicao
        self.jogador_achou = jogador_achou
        self.jogador_escondeu = jogador_escondeu

    def getJogadorEscondeu(self):
        return self.jogador_escondeu
    
    def getJogadorAchou(self):
        return self.jogador_achou
    
    def setJogadorEscondeu(self, jogador_escondeu): 
        self.jogador_escondeu = jogador_escondeu

    def setJogadorAchou(self, jogador_achou): 
        self.jogador_achou = jogador_achou

    
    


