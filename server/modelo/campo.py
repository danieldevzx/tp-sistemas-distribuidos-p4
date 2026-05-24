import threading
from .estrutura import Estrutura

class Campo:
    def __init__(self):
        self.campo = [
            [Estrutura(posicao=(linha, coluna)) for coluna in range(20)]
            for linha in range(20)
        ]
        self._locks = [
            [threading.Semaphore(1) for _ in range(20)]
            for _ in range(20)
        ]

    def getCampo(self):
        return self.campo

    def interacaoCampo(self, usuario: dict, linha: int, coluna: int):
        sem = self._locks[linha][coluna]
        sem.acquire()
        try:
            celula = self.campo[linha][coluna]

            if usuario['timeId'] == 1:
                # Se já foi este jogador que escondeu, remove (toggle)
                if celula.getJogadorEscondeu() == usuario['id']:
                    celula.setJogadorEscondeu(-1)
                    return True, "removed"
                # Célula ocupada por outro jogador
                if celula.getJogadorEscondeu() != -1:
                    return False, "ocupada"
                celula.setJogadorEscondeu(usuario['id'])
                return True, "added"
            else:
                if celula.getJogadorAchou() != -1:
                    return False, "ocupada"
                celula.setJogadorAchou(usuario['id'])
                return True, "added"
        finally:
            sem.release()