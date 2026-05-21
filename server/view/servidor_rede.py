import socket
import threading
import json
import struct
from modelo.bd_base import inicializar_banco
from controller.usuario_controller import UsuarioController

class ServidorRede:
    """
    Camada de Visão (Interface) do Servidor.
    Responsável por gerenciar conexões TCP, threads e o protocolo de comunicação.
    """
    
    def __init__(self, host='0.0.0.0', porta=5000):
        self.host = host
        self.porta = porta
        self.servidor = None
        self.usuario_controller = UsuarioController()

    # --- INICIALIZAÇÃO E LOOP PRINCIPAL ---

    def iniciar(self):
        """Prepara o socket e fica escutando novas conexões."""
        inicializar_banco()
        
        # Cria o socket TCP/IP
        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Permite reutilizar a porta imediatamente após fechar o servidor
        self.servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.servidor.bind((self.host, self.porta))
        self.servidor.listen()
        
        print(f"[ESCUTANDO] Servidor MVC rodando em {self.host}:{self.porta}")
        
        try:
            while True:
                # Aceita uma nova conexão
                socket_cliente, endereco = self.servidor.accept()
                
                # Cria uma thread separada para cada cliente (Multi-threading)
                # Isso permite que vários clientes usem o sistema ao mesmo tempo
                thread = threading.Thread(target=self.tratar_cliente, args=(socket_cliente, endereco))
                thread.start()
                
                print(f"[CONEXÕES ATIVAS] {threading.active_count() - 1}")
        except KeyboardInterrupt:
            print("\n[DESLIGANDO] Servidor parado pelo usuário.")
        finally:
            if self.servidor:
                self.servidor.close()

    # --- TRATAMENTO DE PROTOCOLO E MENSAGENS ---

    def tratar_cliente(self, socket_cliente, endereco):
        """Gerencia a comunicação com um cliente específico."""
        print(f"[NOVA CONEXÃO] {endereco} conectado.")
        try:
            while True:
                # 1. LER O CABEÇALHO (Protocolo de Tamanho Fixo)
                # Recebemos os primeiros 4 bytes que contêm o tamanho do resto da mensagem
                cabecalho = socket_cliente.recv(4)
                if not cabecalho:
                    break
                
                # Desempacota os 4 bytes para um número inteiro (Big-endian)
                tamanho_mensagem = struct.unpack('>I', cabecalho)[0]
                
                # 2. LER O CORPO DA MENSAGEM (Tamanho Variável)
                # Garante que lemos todos os bytes prometidos pelo cabeçalho
                dados = b''
                while len(dados) < tamanho_mensagem:
                    chunk = socket_cliente.recv(tamanho_mensagem - len(dados))
                    if not chunk:
                        break
                    dados += chunk
                
                if not dados:
                    break
                    
                # 3. PROCESSAR A REQUISIÇÃO
                # Decodifica o JSON e extrai o tipo de operação e os dados
                requisicao = json.loads(dados.decode('utf-8'))
                tipo = requisicao.get('type')
                payload = requisicao.get('payload')
                
                print(f"[REQUISIÇÃO] {tipo} de {endereco}")
                
                # 4. DELEGAR PARA O CONTROLLER (Lógica de Negócio)
                sucesso, tipo, mensagem = self.processar_comando(tipo, payload)
                
                # 5. ENVIAR RESPOSTA
                # Prepara o JSON de resposta
                resposta = {"success": sucesso, "type": tipo, "payload": mensagem}
                dados_resposta = json.dumps(resposta).encode('utf-8')
                
                # Empacota o tamanho da resposta no cabeçalho de 4 bytes
                cabecalho_resposta = struct.pack('>I', len(dados_resposta))
                
                # Envia [Cabeçalho + Corpo]
                socket_cliente.sendall(cabecalho_resposta + dados_resposta)
                
        except Exception as e:
            print(f"[ERRO] {endereco}: {e}")
        finally:
            socket_cliente.close()
            print(f"[DESCONECTADO] {endereco} fechado.")

    def processar_comando(self, tipo, payload):
        """
        Roteia a requisição para o controlador correto.
        Retorna uma tupla (sucesso, mensagem).
        """
        if tipo == 'REGISTER':
            return self.usuario_controller.cadastrar(payload)
        elif tipo == 'LOGIN':
            return self.usuario_controller.autenticar(payload)
        elif tipo == 'ADD_STRUCTURE':
            return self.usuario_controller.adicionar_estrutura(payload)
        return False, "Tipo de comando desconhecido"