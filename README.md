# Jogo de Escavação Distribuído - Pyro5 RMI com MVC

Este projeto implementa um sistema distribuído de jogo de escavação competitivo utilizando Python, **Pyro5 (Remote Method Invocation)** e uma arquitetura robusta baseada no padrão **MVC (Model-View-Controller)**.

---

## 🎮 Como Jogar (Regras do Jogo)

O sistema conta com um fluxo competitivo inspirado no clássico **Campo Minado**:

1. **Equipes Dinâmicas:** Ao realizar login, os jogadores são automaticamente e aleatoriamente distribuídos entre o **Time 1 (Montagem)** e o **Time 2 (Escavação)**, garantindo balanceamento (1 e 2, 1 e 2...).
2. **Fase 1 - Montagem:** O Time 1 tem 60 segundos para esconder até **10 tesouros** no tabuleiro. O Time 2 apenas assiste.
3. **Fase 2 - Escavação:** O Time 2 tem **20 tentativas** para encontrar todos os tesouros escondidos. Ao escavar uma célula vazia, ela revela o **número de tesouros adjacentes (0 a 8)**.
4. **Condições de Vitória e Reinício:**
   - O Time 2 vence se achar todos os tesouros antes de acabarem suas tentativas.
   - O Time 1 vence caso as tentativas acabem ou o tempo do Time 2 se esgote.
   - Ao fim da partida, um botão **Reiniciar** é habilitado no cabeçalho. Ao ser clicado, limpa o tabuleiro e re-sorteia os times de todos os conectados, promovendo grande rejogabilidade!

---

## 🏗️ Arquitetura do Sistema

O projeto utiliza uma arquitetura baseada em RMI (Invocação de Método Remoto) para comunicação de rede, garantindo que o cliente e o servidor se comuniquem por meio de objetos distribuídos em vez de sockets de baixo nível.

### Cliente (PyQt6)

- **Model (`client/model/`)**:
  - `ProxyServidor`: Gerencia a conexão com o Name Server e encapsula os proxies remotos do servidor.
  - `CallbackCliente`: Objeto local exposto via Daemon Pyro que escuta os broadcasts do servidor.
  - `EstadoJogo`: Controla o estado local do campo e a fase atual.
- **View (`client/view/`)**: Páginas da interface gráfica (`Login`, `Registro`, `Home`). Apenas capturam interações de tela e renderizam atualizações de estado.
- **Controller (`client/controller/`)**:
  - `ControladorCliente`: Orquestra as requisições e processa os eventos recebidos do servidor.
  - `WorkerRMI`: Thread secundária (`QThread`) para executar as chamadas RMI em background, evitando travar a interface visual. Gerencia dinamicamente a posse (`ownership`) do proxy Pyro5.

### Servidor (Pyro5 Daemon + SQLite)

- **Model (`server/modelo/`)**: Gerencia a persistência com SQLite (`usuario_modelo.py`) e as regras lógicas de estado do tabuleiro e do timer (`jogo.py`).
- **View (`server/main.py`)**: Ponto de entrada que inicializa o Daemon Pyro e registra os serviços no Name Server.
- **Controller (`server/servico_usuario.py` & `server/servico_jogo.py`)**:
  - Expostos remotamente via `@Pyro5.api.expose`.
  - Processam requisições de autenticação e de interação com o tabuleiro.
  - O `ServicoJogo` gerencia o envio de eventos (timer, fase, cliques) em tempo real via callbacks cadastrados pelos clientes ativos.

---

## 🚀 Como Executar (Docker)

> [!IMPORTANT]
> Antes de começar, certifique-se de que o **tutorial de instalação do Docker** foi concluído com sucesso.
> Você pode acessar o guia de instalação aqui: [Tutorial de Instalação Docker](https://drive.google.com/file/d/1Mc_HCTId83ddrbjUc3VXW0WqBjn3bYFa/view?usp=sharing)

Esta é a maneira recomendada, pois garante que todas as dependências do Pyro5, PyQt6 e do banco de dados estejam configuradas.

### 1. Permitir acesso ao Servidor X (Apenas Linux)

Como o cliente possui interface gráfica, você precisa autorizar o Docker a abrir janelas no seu monitor:

```bash
xhost +si:localuser:root
```

### 2. Iniciar o projeto

Para construir e iniciar o Name Server, o Servidor de aplicação e um Cliente:

```bash
docker-compose up --build
```

### 3. Executar múltiplas instâncias do Cliente

Para testar a concorrência e o tempo real (callbacks) com múltiplos jogadores:

Abra um novo terminal no host e execute instâncias adicionais do cliente usando:

```bash
docker-compose run client
```

*Cada cliente executado desta forma abrirá uma nova janela Qt e criará automaticamente seu próprio daemon de callback em seu respectivo IP na rede interna do Docker.*

### 4. Parando os containers

Para encerrar o projeto, você pode usar `Ctrl + C` no terminal principal do compose. Se preferir, use:

```bash
docker-compose down
```

---

## 🗄️ Visualizando o Banco de Dados (DBeaver)

Para visualizar e gerenciar a tabela de usuários persistidos pelo SQLite, recomendamos o uso do **DBeaver**.

> [!TIP]
> Preparamos um guia passo a passo de como configurar e conectar o DBeaver ao banco de dados `sistema.db` deste projeto:
> [Guia de Uso do DBeaver](https://drive.google.com/file/d/1Z7i3VpFkK7frqA6rWSgvmAlDWp4Fm9uV/view?usp=sharing)

---

## 📡 Comunicação e Protocolo (RMI)

A comunicação utiliza a biblioteca **Pyro5** com a seguinte distribuição:

1. **Name Server (Porta 9090)**: Centraliza a tabela de nomes e suas URIs Pyro.
2. **Serviços Remotos**:
   - `servidor.usuario`: Gerencia cadastro e login.
   - `servidor.jogo`: Gerencia o tabuleiro, o timer e a lista de callbacks registrados.
3. **Callbacks (Notificações)**:
   - Cada cliente abre uma escuta dinâmica e se cadastra no servidor.
   - O servidor realiza chamadas remotas unidirecionais para notificar mudanças de ticks de tempo, interações com células e transições de fase.

Para mais detalhes sobre as decisões e conceitos de arquitetura dessa migração, leia o guia em [MIGRACAO_PYRO5.md](MIGRACAO_PYRO5.md).

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.10** ([Documentação](https://docs.python.org/3.10/))
- **Pyro5** ([Documentação](https://pyro5.readthedocs.io/))
- **PyQt6** ([Documentação](https://www.riverbankcomputing.com/static/Docs/PyQt6/))
- **SQLite3** ([Documentação](https://www.sqlite.org/docs.html))
- **Docker & Docker Compose** ([Guia de Instalação](https://drive.google.com/file/d/1Mc_HCTId83ddrbjUc3VXW0WqBjn3bYFa/view?usp=sharing))
- **DBeaver** ([Guia de Uso](https://drive.google.com/file/d/1Z7i3VpFkK7frqA6rWSgvmAlDWp4Fm9uV/view?usp=sharing))
