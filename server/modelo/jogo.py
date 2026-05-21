from .campo import Campo

class Jogo:
    def __init__(self):
        self.campo = Campo()
    
    def getCampo(self):
        return self.campo
    
    def interacaoCampo(self, usuario, posicao):
        return self.campo.interacaoCampo(usuario, posicao)
    