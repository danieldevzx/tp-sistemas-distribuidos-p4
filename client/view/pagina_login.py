from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from view.components.botao import BotaoCustomizado
from view.components.campo_texto import CampoTextoCustomizado

class PaginaLogin(QWidget):
    trocar_para_registro = pyqtSignal()
    requisitar_login = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(12)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        titulo_jogo = QLabel("CAMPO DE ESCAVAÇÃO")
        titulo_jogo.setStyleSheet("font-size: 20px; font-weight: bold; color: #ecf0f1;")
        
        subtitulo = QLabel("Campo de Escavação Cooperativo")
        subtitulo.setStyleSheet("font-size: 11px; color: #bdc3c7; font-style: italic;")
        
        sidebar_layout.addWidget(titulo_jogo)
        sidebar_layout.addWidget(subtitulo)
        
        regras_html = (
            "<html><body>"
            "<p style='color: #ecf0f1; font-weight: bold; font-size: 12px; margin-top: 5px;'>COMO JOGAR:</p>"
            "<hr style='border: 0; border-top: 1px solid #34495e; margin: 4px 0;'>"
            "<p style='color: #bdc3c7; font-size: 11px; line-height: 140%;'>"
            "<b>Equipes:</b> Ao logar, você recebe um time aleatório: <b>Montagem (1)</b> ou <b>Escavação (2)</b>."
            "</p>"
            "<p style='color: #bdc3c7; font-size: 11px; line-height: 140%;'>"
            "<b>Fase 1 - Montagem (Time 1):</b><br>"
            "Tem 60s para esconder até 10 estruturas (tesouros) clicando no campo."
            "</p>"
            "<p style='color: #bdc3c7; font-size: 11px; line-height: 140%;'>"
            "<b>Fase 2 - Escavação (Time 2):</b><br>"
            "Tem 20 tentativas para achar os tesouros. Células vazias revelam o número de tesouros vizinhos (0 a 8)."
            "</p>"
            "<p style='color: #bdc3c7; font-size: 11px; line-height: 140%;'>"
            "<b>Vitória:</b><br>"
            "• Time 2 vence ao achar todos os tesouros.<br>"
            "• Time 1 vence se o tempo ou as tentativas do Time 2 acabarem."
            "</p>"
            "</body></html>"
        )
        
        lbl_regras = QLabel()
        lbl_regras.setText(regras_html)
        lbl_regras.setTextFormat(Qt.TextFormat.RichText)
        lbl_regras.setWordWrap(True)
        lbl_regras.setStyleSheet("background-color: transparent;")
        sidebar_layout.addWidget(lbl_regras)
        
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(15)
        form_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.titulo = QLabel("Acessar Conta")
        self.titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        form_layout.addWidget(self.titulo)
        
        self.input_usuario = CampoTextoCustomizado("Usuário")
        form_layout.addWidget(self.input_usuario)
        
        self.input_senha = CampoTextoCustomizado("Senha", senha=True)
        form_layout.addWidget(self.input_senha)
        
        self.btn_login = BotaoCustomizado("Entrar")
        self.btn_login.clicked.connect(self.ao_clicar_login)
        form_layout.addWidget(self.btn_login)
        
        self.btn_ir_registro = BotaoCustomizado("Criar nova conta", cor_fundo="#34495e")
        self.btn_ir_registro.setFlat(True)
        self.btn_ir_registro.clicked.connect(self.trocar_para_registro.emit)
        form_layout.addWidget(self.btn_ir_registro)
        
        main_layout.addWidget(sidebar, stretch=4)
        main_layout.addWidget(form_widget, stretch=5)
        
        self.setLayout(main_layout)
        
    def ao_clicar_login(self):
        self.requisitar_login.emit(self.input_usuario.text(), self.input_senha.text())

