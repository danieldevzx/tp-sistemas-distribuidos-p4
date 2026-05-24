from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

TAMANHO_CAMPO = 20

# Cores
COR_VAZIA      = "#d0d3d4"   # cinza claro — célula livre
COR_ESCONDEU   = "#e74c3c"   # vermelho    — jogador_escondeu != -1
COR_ACHOU      = "#2ecc71"   # verde       — jogador_achou != -1
COR_AMBOS      = "#8e44ad"   # roxo        — os dois preenchidos


class CelulaWidget(QPushButton):
    """Um quadrado clicável do campo."""
    clicada = pyqtSignal(int, int)

    def __init__(self, linha: int, coluna: int):
        super().__init__()
        self.linha = linha
        self.coluna = coluna
        self._jogador_escondeu = -1
        self._jogador_achou = -1

        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._aplicar_estilo(COR_VAZIA)
        self.clicked.connect(lambda: self.clicada.emit(self.linha, self.coluna))

    # --- API pública ---

    def atualizar(self, jogador_escondeu: int, jogador_achou: int):
        """Atualiza o estado visual da célula."""
        self._jogador_escondeu = jogador_escondeu
        self._jogador_achou = jogador_achou

        if jogador_escondeu != -1 and jogador_achou != -1:
            cor = COR_AMBOS
        elif jogador_escondeu != -1:
            cor = COR_ESCONDEU
        elif jogador_achou != -1:
            cor = COR_ACHOU
        else:
            cor = COR_VAZIA

        self._aplicar_estilo(cor)

    # --- Privado ---

    def _aplicar_estilo(self, cor: str):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {cor};
                border: 1px solid rgba(0,0,0,0.15);
                border-radius: 2px;
            }}
            QPushButton:hover {{
                border: 2px solid #2c3e50;
            }}
            QPushButton:pressed {{
                opacity: 0.7;
            }}
        """)


class PaginaHome(QWidget):
    # Sinal emitido ao clicar numa célula → controlador processa
    requisitar_criar_celula = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self._celulas: list[list[CelulaWidget]] = []
        self._construir_ui()

    # ------------------------------------------------------------------ #
    #  Construção da UI                                                    #
    # ------------------------------------------------------------------ #

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(12, 12, 12, 12)
        raiz.setSpacing(10)

        # Cabeçalho com info do jogador
        raiz.addWidget(self._criar_cabecalho())

        # Legenda de cores
        raiz.addWidget(self._criar_legenda())

        # Grade do campo
        raiz.addWidget(self._criar_grade(), stretch=1)

    def _criar_cabecalho(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_jogador = QLabel("Jogador: —")
        self.lbl_jogador.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")

        self.lbl_time = QLabel("Time: —")
        self.lbl_time.setStyleSheet("font-size: 13px; color: #7f8c8d;")

        layout.addWidget(self.lbl_jogador)
        layout.addStretch()
        layout.addWidget(self.lbl_time)
        return container

    def _criar_legenda(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        for cor, texto in [
            (COR_VAZIA,    "Livre"),
            (COR_ESCONDEU, "Escondido"),
            (COR_ACHOU,    "Encontrado"),
            (COR_AMBOS,    "Ambos"),
        ]:
            quadrado = QFrame()
            quadrado.setFixedSize(14, 14)
            quadrado.setStyleSheet(
                f"background-color: {cor}; border: 1px solid rgba(0,0,0,0.2); border-radius: 2px;"
            )
            lbl = QLabel(texto)
            lbl.setStyleSheet("font-size: 11px; color: #555;")

            sub = QHBoxLayout()
            sub.setSpacing(4)
            sub.setContentsMargins(0, 0, 0, 0)
            sub.addWidget(quadrado)
            sub.addWidget(lbl)

            wrapper = QWidget()
            wrapper.setLayout(sub)
            layout.addWidget(wrapper)

        layout.addStretch()
        return container

    def _criar_grade(self) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(2)
        grid.setContentsMargins(0, 0, 0, 0)

        for linha in range(TAMANHO_CAMPO):
            linha_celulas = []
            for coluna in range(TAMANHO_CAMPO):
                celula = CelulaWidget(linha, coluna)
                celula.clicada.connect(self.requisitar_criar_celula)
                grid.addWidget(celula, linha, coluna)
                linha_celulas.append(celula)
            self._celulas.append(linha_celulas)

        return container

    # ------------------------------------------------------------------ #
    #  API chamada pelo controlador                                        #
    # ------------------------------------------------------------------ #

    def atualizar_campo_completo(self, dados: list):
        """
        Recebe a matriz 20×20 do servidor e pinta todas as células.
        Cada elemento: {"jogador_escondeu": int, "jogador_achou": int}
        """
        for i, linha in enumerate(dados):
            for j, celula_dados in enumerate(linha):
                if i < TAMANHO_CAMPO and j < TAMANHO_CAMPO:
                    self._celulas[i][j].atualizar(
                        celula_dados.get("jogador_escondeu", -1),
                        celula_dados.get("jogador_achou", -1),
                    )

    def atualizar_celula(self, linha: int, coluna: int, dados: dict):
        """
        Atualiza uma única célula (chamado no FIELD_UPDATE do broadcast).
        """
        if 0 <= linha < TAMANHO_CAMPO and 0 <= coluna < TAMANHO_CAMPO:
            self._celulas[linha][coluna].atualizar(
                dados.get("jogador_escondeu", -1),
                dados.get("jogador_achou", -1),
            )

    def definir_info_jogador(self, nome: str, time_id: int):
        """Atualiza o cabeçalho com dados do jogador logado."""
        self.lbl_jogador.setText(f"Jogador: {nome}")
        nome_time = "Montagem" if time_id == 1 else "Escavação"
        self.lbl_time.setText(f"Time: {nome_time}")