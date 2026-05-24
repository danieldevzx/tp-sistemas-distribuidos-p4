from dataclasses import dataclass


@dataclass
class Jogador:
    id: int = -1
    nome: str = ""
    timeId: int = -1

@dataclass
class EstadoJogo:
    jogador_local: Jogador | None = None
    conectado: bool = False
    fase: str = ""
    tempo_restante: int = 0

    def definir_jogador(self, dados: list) -> None:
        self.jogador_local = Jogador(
            id=dados[0],
            nome=dados[1],
            timeId=dados[3]
        )

    def resetar(self) -> None:
        self.jogador_local = None
        self.conectado = False
        self.fase = ""
        self.tempo_restante = 0