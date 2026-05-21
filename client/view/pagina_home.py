from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class PaginaHome(QWidget):
    requisitar_criar_celula = pyqtSignal(int, int) 

    def __init__(self):
        super().__init__()
        
        layout = QGridLayout()
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.botoes = []

        for linha in range(3):
            linha_botoes = []
            for coluna in range(3):
                btn = QPushButton()
                btn.setFixedSize(100, 100)
                
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #34495e;
                        border-radius: 8px;
                    }
                    QPushButton:hover {
                        background-color: #415b76;
                    }
                """)
                
                btn.clicked.connect(lambda checked, l=linha, c=coluna: self.ao_clicar_quadrado(l, c))
                
                layout.addWidget(btn, linha, coluna)
                linha_botoes.append(btn)
                
            self.botoes.append(linha_botoes)

        self.setLayout(layout)

    def ao_clicar_quadrado(self, linha, coluna):
        self.requisitar_criar_celula.emit(linha, coluna)