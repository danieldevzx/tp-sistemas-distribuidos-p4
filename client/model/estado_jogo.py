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
    tentativas_restantes: int = 0
    max_tentativas: int = 0
    max_estruturas: int = 0
    estruturas_escondidas: int = 0
    estruturas_encontradas: int = 0
    ganhador: int | None = None

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
        self.tentativas_restantes = 0
        self.max_tentativas = 0
        self.max_estruturas = 0
        self.estruturas_escondidas = 0
        self.estruturas_encontradas = 0
        self.ganhador = None