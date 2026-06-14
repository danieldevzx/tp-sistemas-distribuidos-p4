from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

TAMANHO_CAMPO = 10

COR_VAZIA    = "#d0d3d4"
COR_ESCONDEU = "#e74c3c"
COR_ACHOU    = "#2ecc71"
COR_AMBOS    = "#8e44ad"


class CelulaWidget(QPushButton):
    clicada = pyqtSignal(int, int)

    def __init__(self, linha: int, coluna: int):
        super().__init__()
        self.linha  = linha
        self.coluna = coluna
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._aplicar_estilo(COR_VAZIA)
        self.clicked.connect(lambda: self.clicada.emit(self.linha, self.coluna))

    def atualizar(self, jogador_escondeu: int, jogador_achou: int, vizinhos: int = -1):
        cor = COR_VAZIA
        texto = ""
        cor_texto = "black"
        if jogador_escondeu != -1 and jogador_achou != -1:
            cor = COR_AMBOS
        elif jogador_escondeu != -1:
            cor = COR_ESCONDEU
        elif jogador_achou != -1:
            cor = "#eaeded"
            if vizinhos >= 0:
                texto = str(vizinhos) if vizinhos > 0 else ""
                self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                cor_texto = "#2e4053"
                if vizinhos == 1: cor_texto = "#2980b9"
                elif vizinhos == 2: cor_texto = "#27ae60"
                elif vizinhos == 3: cor_texto = "#c0392b"
                elif vizinhos >= 4: cor_texto = "#8e44ad"
        
        self.setText(texto)
        self._aplicar_estilo(cor, cor_texto)

    def _aplicar_estilo(self, cor: str, cor_texto: str = "black"):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {cor};
                color: {cor_texto};
                border: 1px solid rgba(0,0,0,0.15);
                border-radius: 2px;
            }}
            QPushButton:hover {{ border: 2px solid #2c3e50; }}
        """)


class PaginaHome(QWidget):
    requisitar_criar_celula = pyqtSignal(int, int)
    requisitar_reiniciar = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._celulas: list[list[CelulaWidget]] = []
        self._fase = "montagem"
        self._time_id = -1
        self._construir_ui()

    def _construir_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(12, 12, 12, 12)
        raiz.setSpacing(8)
        raiz.addWidget(self._criar_cabecalho())
        raiz.addWidget(self._criar_banner_fase())
        raiz.addWidget(self._criar_legenda())
        raiz.addWidget(self._criar_grade(), stretch=1)

    def _criar_cabecalho(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_jogador = QLabel("Jogador: —")
        self.lbl_jogador.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #2c3e50;")

        self.lbl_contadores = QLabel("")
        self.lbl_contadores.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #34495e;")

        self.btn_reiniciar = QPushButton("Reiniciar")
        self.btn_reiniciar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_reiniciar.setEnabled(False)
        self.btn_reiniciar.clicked.connect(self.requisitar_reiniciar.emit)

        self.lbl_time = QLabel("Time: —")
        self.lbl_time.setStyleSheet("font-size: 13px; color: #7f8c8d;")

        layout.addWidget(self.lbl_jogador)
        layout.addStretch()
        layout.addWidget(self.lbl_contadores)
        layout.addStretch()
        layout.addWidget(self.btn_reiniciar)
        layout.addStretch()
        layout.addWidget(self.lbl_time)
        return container

    def _criar_banner_fase(self) -> QWidget:
        """Faixa colorida que mostra a fase atual e o contador."""
        self.banner = QFrame()
        self.banner.setFixedHeight(36)
        layout = QHBoxLayout(self.banner)
        layout.setContentsMargins(12, 0, 12, 0)

        self.lbl_fase = QLabel("⏳ Fase de Montagem")
        self.lbl_fase.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: white;")

        self.lbl_tempo = QLabel("60s")
        self.lbl_tempo.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: white;")

        layout.addWidget(self.lbl_fase)
        layout.addStretch()
        layout.addWidget(self.lbl_tempo)

        self._atualizar_banner("montagem", 60)
        return self.banner

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
            q = QFrame()
            q.setFixedSize(14, 14)
            q.setStyleSheet(
                f"background-color:{cor}; border:1px solid rgba(0,0,0,.2); border-radius:2px;")
            lbl = QLabel(texto)
            lbl.setStyleSheet("font-size:11px; color:#555;")
            sub = QHBoxLayout()
            sub.setSpacing(4)
            sub.setContentsMargins(0, 0, 0, 0)
            sub.addWidget(q)
            sub.addWidget(lbl)
            w = QWidget()
            w.setLayout(sub)
            layout.addWidget(w)
        layout.addStretch()
        return container

    def _criar_grade(self) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(2)
        grid.setContentsMargins(0, 0, 0, 0)
        for linha in range(TAMANHO_CAMPO):
            row = []
            for coluna in range(TAMANHO_CAMPO):
                c = CelulaWidget(linha, coluna)
                c.clicada.connect(self.requisitar_criar_celula)
                grid.addWidget(c, linha, coluna)
                row.append(c)
            self._celulas.append(row)
        return container

    def _atualizar_banner(self, fase: str, tempo: int):
        self._fase = fase
        if fase == "montagem":
            self.banner.setStyleSheet(
                "background-color: #e67e22; border-radius: 4px;")
            self.lbl_fase.setText("Fase de Montagem")
            self.lbl_tempo.setText(f"{tempo}s")
            self.lbl_tempo.setVisible(True)
            self.btn_reiniciar.setEnabled(False)
        elif fase == "escavacao":
            self.banner.setStyleSheet(
                "background-color: #27ae60; border-radius: 4px;")
            self.lbl_fase.setText("Fase de Escavação")
            self.lbl_tempo.setText(f"{tempo}s")
            self.lbl_tempo.setVisible(True)
            self.btn_reiniciar.setEnabled(False)
        else:
            self.banner.setStyleSheet(
                "background-color: #7f8c8d; border-radius: 4px;")
            self.lbl_fase.setText("Jogo Finalizado")
            self.lbl_tempo.setVisible(False)
            self.btn_reiniciar.setEnabled(True)
        self._atualizar_interatividade()

    def _atualizar_interatividade(self):
        """
        Time 1 (montagem)  → clicável só durante montagem.
        Time 2 (escavação) → clicável só durante escavação.
        """
        if self._time_id == 1:
            habilitado = (self._fase == "montagem")
        elif self._time_id == 2:
            habilitado = (self._fase == "escavacao")
        else:
            habilitado = False

        for linha in self._celulas:
            for celula in linha:
                celula.setEnabled(habilitado)

    def definir_info_jogador(self, nome: str, time_id: int):
        self._time_id = time_id
        self.lbl_jogador.setText(f"Jogador: {nome}")
        nome_time = "Montagem" if time_id == 1 else "Escavação"
        self.lbl_time.setText(f"Time: {nome_time}")
        self._atualizar_interatividade()

    def atualizar_fase(self, fase: str, tempo_restante: int):
        """Chamado pelo controlador ao receber PHASE_CHANGE ou FIELD_STATE."""
        self._atualizar_banner(fase, tempo_restante)

    def atualizar_tempo(self, tempo_restante: int):
        """Atualiza só o contador sem mudar a fase."""
        if self._fase in ("montagem", "escavacao"):
            self.lbl_tempo.setText(f"{tempo_restante}s")

    def atualizar_campo_completo(self, dados: list):
        for i, linha in enumerate(dados):
            for j, cd in enumerate(linha):
                if i < TAMANHO_CAMPO and j < TAMANHO_CAMPO:
                    self._celulas[i][j].atualizar(
                        cd.get("jogador_escondeu", -1),
                        cd.get("jogador_achou",    -1),
                        cd.get("vizinhos",         -1),
                    )

    def atualizar_celula(self, linha: int, coluna: int, dados: dict):
        if 0 <= linha < TAMANHO_CAMPO and 0 <= coluna < TAMANHO_CAMPO:
            self._celulas[linha][coluna].atualizar(
                dados.get("jogador_escondeu", -1),
                dados.get("jogador_achou",    -1),
                dados.get("vizinhos",         -1),
            )

    def atualizar_contadores(self, tentativas_restantes: int, max_tentativas: int, max_estruturas: int, estruturas_escondidas: int, estruturas_encontradas: int, ganhador: int | None):
        if self._fase == "montagem":
            self.lbl_contadores.setText(f"Estruturas: {estruturas_escondidas} / {max_estruturas}")
        elif self._fase == "escavacao":
            self.lbl_contadores.setText(f"Tentativas: {tentativas_restantes} / {max_tentativas} | Achados: {estruturas_encontradas} / {estruturas_escondidas}")
        elif self._fase == "finalizado":
            vencedor_txt = "Empate"
            if ganhador == 1:
                vencedor_txt = "Time 1 Venceu"
            elif ganhador == 2:
                vencedor_txt = "Time 2 Venceu"
            self.lbl_contadores.setText(f"Fim de Jogo! Vencedor: {vencedor_txt}")