from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from PyQt6.QtCore import Qt
from view.pagina_login import PaginaLogin
from view.pagina_registro import PaginaRegistro
from view.pagina_home import PaginaHome

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projeto SD - Campo de Escavação")
        self.setFixedSize(700, 600)
        
        self.pilha = QStackedWidget()
        self.pagina_login = PaginaLogin()
        self.pagina_registro = PaginaRegistro()
        self.pagina_home = PaginaHome()
        
        self.pilha.addWidget(self.pagina_login)
        self.pilha.addWidget(self.pagina_registro)
        self.pilha.addWidget(self.pagina_home)
        
        self.setCentralWidget(self.pilha)
        
        self.pagina_login.trocar_para_registro.connect(lambda: self.mudar_pagina(1))
        self.pagina_registro.trocar_para_login.connect(lambda: self.mudar_pagina(0))
        
    def mudar_pagina(self, indice):
        self.pilha.setCurrentIndex(indice)
        
    def obter_indice_atual(self):
        return self.pilha.currentIndex()
            
    def definir_carregamento(self, carregando):
        self.setEnabled(not carregando)
        if carregando:
            self.setCursor(Qt.CursorShape.WaitCursor)
        else:
            self.unsetCursor()
