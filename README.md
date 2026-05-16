# Projeto de Sistemas Distribuídos - Socket TCP com MVC

Este projeto implementa um sistema distribuído de autenticação (Cadastro e Login) utilizando Python, Sockets TCP e uma arquitetura robusta baseada no padrão **MVC (Model-View-Controller)**.

## 🏗️ Arquitetura do Sistema

O projeto foi totalmente refatorado para seguir o padrão MVC em ambas as pontas (Cliente e Servidor), garantindo separação de responsabilidades e facilidade de manutenção.

### Cliente (PyQt6)

- **Model (`client/model/`)**: Gerencia a conexão de rede (`ClienteRede`) e a tradução de mensagens. Não conhece a interface gráfica.
- **View (`client/view/`)**: Contém as páginas (`Login`, `Registro`, `Home`) e componentes visuais reaproveitáveis. É responsável apenas por exibir dados e capturar eventos.
- **Controller (`client/controller/`)**: O orquestrador. Recebe comandos da View, solicita dados ao Model e gerencia o **Worker** (Thread separada) para evitar que a interface trave durante requisições de rede.

### Servidor (Socket TCP + SQLite)

- **Model (`server/modelo/`)**: Lida com a persistência de dados (`bd_base.py`, `usuario_modelo.py`) e scripts SQL.
- **View (`server/view/`)**: No servidor, a "Visão" é a interface de rede (`servidor_rede.py`). Ela gerencia os Sockets e o protocolo de comunicação.
- **Controller (`server/controller/`)**: Processa as regras de negócio de autenticação e decide quais dados o modelo deve salvar ou buscar.

---

## 🚀 Como Executar (Docker)

> [!IMPORTANT]
> Antes de começar, certifique-se de que o **tutorial de instalação do Docker** foi concluído com sucesso.
> Você pode acessar o guia de instalação aqui: [Tutorial de Instalação Docker](https://drive.google.com/file/d/1Mc_HCTId83ddrbjUc3VXW0WqBjn3bYFa/view?usp=sharing)

Esta é a maneira recomendada, pois garante que todas as dependências do PyQt6 e do banco de dados estejam configuradas.

### 1. Permitir acesso ao Servidor X (Apenas Linux)

Como o cliente possui interface gráfica, você precisa autorizar o Docker a abrir janelas no seu monitor:

```bash
xhost +si:localuser:root
```

### 2. Iniciar o projeto

Para compilar e iniciar o servidor e um cliente:

```bash
docker-compose up --build
```

### 3. Executar múltiplas instâncias do Cliente

Para testar a concorrência do servidor com vários clientes simultâneos:

```bash
docker-compose up --scale client=3
```

_(Substitua `3` pelo número desejado de instâncias)_

### 4. Parando os containers

Para encerrar o projeto, você pode usar `Ctrl + C` no terminal onde o Docker está rodando. Se preferir, use:

```bash
docker-compose down
```

Caso os containers não fechem corretamente (comum em alguns ambientes com PyQt6), você pode forçar a parada utilizando:

```bash
sudo docker container stop template-sd-server-1 template-sd-db-init-1 template-sd-client-2 template-sd-client-N
```

*(Nota: Substitua `template-sd-client-N` pelos nomes/IDs reais dos containers caso tenha escalado para mais instâncias)*

---

## 🗄️ Visualizando o Banco de Dados (DBeaver)

Para visualizar e gerenciar os dados salvos no projeto (como a tabela de usuários), recomendamos o uso do **DBeaver**.

> [!TIP]
> Preparamos um guia passo a passo de como configurar e conectar o DBeaver ao banco de dados `sistema.db` deste projeto:
> [Guia de Uso do DBeaver](https://drive.google.com/file/d/1Z7i3VpFkK7frqA6rWSgvmAlDWp4Fm9uV/view?usp=sharing)

---

## 📡 Protocolo de Comunicação

A comunicação utiliza **Sockets TCP** com um protocolo de mensagem estruturado:

1.  **Cabeçalho (4 bytes)**: Um inteiro Big-endian representando o tamanho do corpo da mensagem.
2.  **Corpo (JSON)**: Dados da requisição ou resposta codificados em UTF-8.

**Exemplo de fluxo:**

- O Cliente envia o tamanho (4 bytes) + JSON de Login.
- O Servidor lê o tamanho, recebe o JSON, processa no Controller e devolve tamanho + JSON de Resposta.

> [!NOTE]
> Para entender mais sobre a implementação de Sockets em Python, veja a [Documentação Oficial de Sockets](https://docs.python.org/3/library/socket.html).

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.10** ([Documentação](https://docs.python.org/3.10/))
- **PyQt6** ([Documentação](https://www.riverbankcomputing.com/static/Docs/PyQt6/))
- **SQLite3** ([Documentação](https://www.sqlite.org/docs.html))
- **Docker & Docker Compose** ([Guia de Instalação](https://drive.google.com/file/d/1Mc_HCTId83ddrbjUc3VXW0WqBjn3bYFa/view?usp=sharing))
- **DBeaver** ([Guia de Uso](https://drive.google.com/file/d/1Z7i3VpFkK7frqA6rWSgvmAlDWp4Fm9uV/view?usp=sharing))
- **Socket & Threading** ([Documentação Sockets](https://docs.python.org/3/library/socket.html))
