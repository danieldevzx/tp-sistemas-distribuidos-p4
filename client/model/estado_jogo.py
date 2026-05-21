from dataclasses import dataclass, field

TAMANHO_CAMPO = 20


TIPO_OCULTO = "oculto"
TIPO_VAZIO = "vazio"
TIPO_TESOURO = "tesouro"
TIPO_BOMBA = "bomba"
TIPO_ESTRUTURA = "estrutura"


TIME_MONTAGEM = "montagem"
TIME_ESCAVACAO = "escavacao"


# Dataclasses
@dataclass
class Jogador:
    # Jogador local
    id: str = ""
    nome: str = ""
    time: str = ""
    pontuacao: int = 0


@dataclass
class Celula:
    # Célula individual do campo
    linha: int = 0
    coluna: int = 0
    tipo: str = TIPO_OCULTO
    dono: str | None = None


@dataclass
class EstadoJogo:
    # Estado da partida
    jogador_local: Jogador | None = None
    campo: list = field(default_factory=list)
    tempo_restante: int = 0
    tentativas_restantes: int = 0
    cooldown_ativo: bool = False
    conectado: bool = False
    fase: str = ""

    def __post_init__(self):
        # Inicia campo vazio
        if not self.campo:
            self.campo = self._criar_campo_vazio()

    # Métodos públicos
    def inicializar_campo(self, dados_servidor: list) -> None:
        # Preenche campo inicial
        for i, linha in enumerate(dados_servidor):
            for j, celula_dados in enumerate(linha):
                if i < TAMANHO_CAMPO and j < TAMANHO_CAMPO:
                    self.campo[i][j] = Celula(
                        linha=i,
                        coluna=j,
                        tipo=celula_dados.get("tipo", TIPO_OCULTO),
                        dono=celula_dados.get("dono")
                    )

    def atualizar_celula(self, linha: int, coluna: int, dados: dict) -> None:
        # Atualiza célula do campo
        if 0 <= linha < TAMANHO_CAMPO and 0 <= coluna < TAMANHO_CAMPO:
            celula = self.campo[linha][coluna]
            celula.tipo = dados.get("tipo", celula.tipo)
            celula.dono = dados.get("dono", celula.dono)

    def definir_jogador(self, dados: dict) -> None:
        # Define jogador local
        self.jogador_local = Jogador(
            id=dados.get("id", ""),
            nome=dados.get("nome", ""),
            time=dados.get("time", ""),
            pontuacao=dados.get("pontuacao", 0)
        )

    def resetar(self) -> None:
        # Reseta estado
        self.jogador_local = None
        self.campo = self._criar_campo_vazio()
        self.tempo_restante = 0
        self.tentativas_restantes = 0
        self.cooldown_ativo = False
        self.fase = ""

    # Métodos privados
    def _criar_campo_vazio(self) -> list:
        # Cria matriz vazia
        return [
            [Celula(linha=i, coluna=j) for j in range(TAMANHO_CAMPO)]
            for i in range(TAMANHO_CAMPO)
        ]
