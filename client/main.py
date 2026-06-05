import sys
from PyQt6.QtWidgets import QApplication
from view.janela_principal import JanelaPrincipal
from controller.controlador_cliente import ControladorCliente


def principal():
    app = QApplication(sys.argv)

    janela = JanelaPrincipal()

    controlador = ControladorCliente(janela)

    app.aboutToQuit.connect(controlador.desconectar)

    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    principal()
