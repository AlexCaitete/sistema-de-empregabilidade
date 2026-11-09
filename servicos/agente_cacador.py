import json
from typing import List, Optional
from modelos import VagaEmprego, PerfilProfissional
from servicos.banco_dados import GerenciadorBancoDados


class AgenteCacadorVagas:
    def __init__(self, caminho_banco: str = "dados/empregabilidade.db"):
        self.banco = GerenciadorBancoDados(caminho_banco=caminho_banco)
        self.vagas: List[VagaEmprego] = self._carregar_vagas()

    def _vagas_iniciais(self) -> List[VagaEmprego]:
        return [
            VagaEmprego(
                id="vaga-01",
                titulo="Desenvolvedor Back-end Python Júnior",
                empresa="TechNova Solutions",
                requisitos=["Python", "FastAPI", "Pydantic", "API Rest", "SQL", "Git", "Docker"],
                descricao=(
                    "Atuar no desenvolvimento e manutenção de microsserviços e APIs RESTful em Python "
                    "com FastAPI, integração com bancos de dados relacionais e consumo de APIs de IA."
                ),
                localizacao="Remoto",
                nivel="Júnior",
            ),
            VagaEmprego(
                id="vaga-02",
                titulo="Desenvolvedor Full Stack Júnior (React / Node / Python)",
                empresa="InovaWeb Digital",
                requisitos=["JavaScript", "React", "Node.js", "Python", "API Rest", "Git", "TypeScript"],
                descricao=(
                    "Desenvolvimento de aplicações web completas, construindo interfaces reativas em React "
                    "e integrando com serviços back-end em Node.js e Python."
                ),
                localizacao="Híbrido - São Paulo, SP",
                nivel="Júnior",
            ),
            VagaEmprego(
                id="vaga-03",
                titulo="Desenvolvedor Back-end Java / Spring Boot Júnior",
                empresa="FinBank Sistemas",
                requisitos=[
                    "Java",
                    "Spring Boot",
                    "API Rest",
                    "Controller",
                    "Annotations",
                    "IoC DI",
                    "SQL",
                    "Git",
                ],
                descricao=(
                    "Desenvolvimento de APIs financeiras utilizando ecossistema Spring Boot, injeção de "
                    "dependências (IoC/DI), criação de controllers REST e boas práticas de engenharia de software."
                ),
                localizacao="Remoto",
                nivel="Júnior",
            ),
            VagaEmprego(
                id="vaga-04",
                titulo="Engenheiro de Software Júnior - IA & Automação",
                empresa="NeuralWorks Brasil",
                requisitos=["Python", "FastAPI", "LLMs", "API Rest", "JSON", "Git"],
                descricao=(
                    "Construção de agentes inteligentes e pipelines de extração de dados estruturados "
                    "utilizando Python, FastAPI e SDKs de modelos generativos (Gemini/OpenAI)."
                ),
                localizacao="Remoto",
                nivel="Júnior",
            ),
        ]

    def _carregar_vagas(self) -> List[VagaEmprego]:
        with self.banco.obter_conexao() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                "SELECT id, titulo, empresa, requisitos_json, descricao, localizacao, nivel "
                "FROM vagas_emprego ORDER BY id ASC"
            )
            linhas = cursor.fetchall()

            if not linhas:
                vagas_padrao = self._vagas_iniciais()
                for vaga in vagas_padrao:
                    self._inserir_vaga_no_banco(vaga)
                return vagas_padrao

            vagas_carregadas: List[VagaEmprego] = []
            for linha in linhas:
                vagas_carregadas.append(
                    VagaEmprego(
                        id=linha["id"],
                        titulo=linha["titulo"],
                        empresa=linha["empresa"],
                        requisitos=json.loads(linha["requisitos_json"]),
                        descricao=linha["descricao"],
                        localizacao=linha["localizacao"],
                        nivel=linha["nivel"],
                    )
                )
            return vagas_carregadas

    def _inserir_vaga_no_banco(self, vaga: VagaEmprego) -> None:
        with self.banco.obter_conexao() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                """
                INSERT INTO vagas_emprego (id, titulo, empresa, requisitos_json, descricao, localizacao, nivel)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    titulo = excluded.titulo,
                    empresa = excluded.empresa,
                    requisitos_json = excluded.requisitos_json,
                    descricao = excluded.descricao,
                    localizacao = excluded.localizacao,
                    nivel = excluded.nivel
                """,
                (
                    vaga.id,
                    vaga.titulo,
                    vaga.empresa,
                    json.dumps(vaga.requisitos, ensure_ascii=False),
                    vaga.descricao,
                    vaga.localizacao,
                    vaga.nivel,
                ),
            )
            conexao.commit()

    def listar_vagas(self) -> List[VagaEmprego]:
        self.vagas = self._carregar_vagas()
        return self.vagas

    def obter_vaga_por_id(self, id_vaga: str) -> Optional[VagaEmprego]:
        for vaga in self.listar_vagas():
            if vaga.id == id_vaga:
                return vaga
        return None

    def adicionar_vaga(self, nova_vaga: VagaEmprego) -> VagaEmprego:
        vagas = self.listar_vagas()
        if not nova_vaga.id:
            nova_vaga.id = f"vaga-{len(vagas) + 1:02d}"
        self._inserir_vaga_no_banco(nova_vaga)
        self.vagas = self._carregar_vagas()
        return nova_vaga

    @staticmethod
    def _termos_combinam(termo_a: str, termo_b: str) -> bool:
        a = termo_a.strip().lower()
        b = termo_b.strip().lower()
        if a == b:
            return True
        if {a, b} == {"java", "javascript"}:
            return False
        palavras_a = set(a.replace("/", " ").replace("-", " ").split())
        palavras_b = set(b.replace("/", " ").replace("-", " ").split())
        return a in palavras_b or b in palavras_a

    def buscar_vagas(
        self,
        criterios: Optional[str] = None,
        perfil: Optional[PerfilProfissional] = None,
    ) -> List[VagaEmprego]:
        vagas = self.listar_vagas()

        if criterios:
            termos = [termo.strip().lower() for termo in criterios.split(",") if termo.strip()]
            vagas_filtradas: List[VagaEmprego] = []
            for vaga in vagas:
                texto_vaga = (
                    f"{vaga.titulo} {vaga.empresa} {vaga.descricao} {' '.join(vaga.requisitos)}"
                ).lower()
                if any(termo in texto_vaga for termo in termos):
                    vagas_filtradas.append(vaga)
            vagas = vagas_filtradas

        if perfil:
            def calcular_pontuacao(vaga: VagaEmprego) -> int:
                pontos = 0
                for requisito in vaga.requisitos:
                    if any(
                        self._termos_combinam(requisito, competencia)
                        for competencia in perfil.competencias_tecnicas
                    ):
                        pontos += 1
                return pontos

            vagas = sorted(vagas, key=calcular_pontuacao, reverse=True)

        return vagas
