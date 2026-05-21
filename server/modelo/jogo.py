from .campo import Campo

class Jogo:
    def __init__(self):
        self.campo = Campo()
    
    def getCampo(self):
        return self.campo
    
    def interacaoCampo(self, usuario: list, linha: int, coluna: int):
        return self.campo.interacaoCampo(usuario, linha, coluna)
    