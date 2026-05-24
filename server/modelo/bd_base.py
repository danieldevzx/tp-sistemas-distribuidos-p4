import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'sistema.db'))
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'scripts', 'esquema.sql')

def obter_conexao():
    return sqlite3.connect(DB_PATH)

def inicializar_banco():
    """
    Lê o arquivo SQL "esquema.sql" e executa no banco de dados para 
    garantir que a estrutura esteja atualizada.
    """
    if not os.path.exists(SCHEMA_PATH):
        print(f"[ERRO] Arquivo de esquema não encontrado em: {SCHEMA_PATH}")
        return

    try:
        with open(SCHEMA_PATH, 'r') as f:
            script_sql = f.read()

        conexao = obter_conexao()
        cursor = conexao.cursor()
        cursor.executescript(script_sql)
        
        conexao.commit()
        conexao.close()
        print("[SUCESSO] Estrutura do banco de dados verificada/atualizada.")
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar banco: {e}")
