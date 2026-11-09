import os
import sqlite3


class GerenciadorBancoDados:
    def __init__(self, caminho_banco: str = "dados/empregabilidade.db"):
        self.caminho_banco = caminho_banco
        self._garantir_diretorio()
        self._inicializar_tabelas()

    def _garantir_diretorio(self) -> None:
        diretorio = os.path.dirname(self.caminho_banco)
        if diretorio:
            os.makedirs(diretorio, exist_ok=True)

    def obter_conexao(self) -> sqlite3.Connection:
        conexao = sqlite3.connect(self.caminho_banco)
        conexao.row_factory = sqlite3.Row
        return conexao

    def _inicializar_tabelas(self) -> None:
        with self.obter_conexao() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS perfil_profissional (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    nome_completo TEXT NOT NULL,
                    cargo_desejado TEXT NOT NULL,
                    competencias_json TEXT NOT NULL,
                    experiencias_json TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS certificados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL UNIQUE,
                    instituicao TEXT NOT NULL,
                    tecnologias_json TEXT NOT NULL,
                    data_conclusao TEXT
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vagas_emprego (
                    id TEXT PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    empresa TEXT NOT NULL,
                    requisitos_json TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    localizacao TEXT,
                    nivel TEXT
                )
                """
            )

            conexao.commit()
