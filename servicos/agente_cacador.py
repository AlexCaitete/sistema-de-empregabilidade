import json
import os
from typing import List, Optional
from modelos import VagaEmprego, PerfilProfissional


class AgenteCacadorVagas:
    """
    Agente Caçador de Vagas:
    Responsável por armazenar, filtrar e ranquear vagas de emprego alinhadas
    ao perfil técnico e objetivos de carreira do usuário.
    """

    def __init__(self, caminho_arquivo: str = "dados/vagas_disponiveis.json"):
        self.caminho_arquivo = caminho_arquivo
        self._garantir_diretorio()
        self.vagas: List[VagaEmprego] = self._carregar_vagas()

    def _garantir_diretorio(self) -> None:
        diretorio = os.path.dirname(self.caminho_arquivo)
        if diretorio:
            os.makedirs(diretorio, exist_ok=True)

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
        if not os.path.exists(self.caminho_arquivo):
            vagas = self._vagas_iniciais()
            self._salvar_vagas(vagas)
            return vagas

        try:
            with open(self.caminho_arquivo, "r", encoding="utf-8") as arquivo_json:
                dados = json.load(arquivo_json)
            return [VagaEmprego.model_validate(item_vaga) for item_vaga in dados]
        except Exception:
            vagas = self._vagas_iniciais()
            self._salvar_vagas(vagas)
            return vagas

    def _salvar_vagas(self, vagas: List[VagaEmprego]) -> None:
        self._garantir_diretorio()
        with open(self.caminho_arquivo, "w", encoding="utf-8") as arquivo_json:
            json.dump(
                [vaga_item.model_dump() for vaga_item in vagas],
                arquivo_json,
                ensure_ascii=False,
                indent=4,
            )

    def listar_vagas(self) -> List[VagaEmprego]:
        """Retorna todas as vagas cadastradas."""
        self.vagas = self._carregar_vagas()
        return self.vagas

    def obter_vaga_por_id(self, id_vaga: str) -> Optional[VagaEmprego]:
        """Busca uma vaga específica pelo seu ID."""
        for vaga in self.listar_vagas():
            if vaga.id == id_vaga:
                return vaga
        return None

    def adicionar_vaga(self, nova_vaga: VagaEmprego) -> VagaEmprego:
        """Cadastra uma nova vaga no repositório local."""
        vagas = self.listar_vagas()
        if not nova_vaga.id:
            nova_vaga.id = f"vaga-{len(vagas) + 1:02d}"
        vagas.append(nova_vaga)
        self._salvar_vagas(vagas)
        self.vagas = vagas
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
        """
        Busca e ordena as vagas de acordo com palavras-chave (criterios)
        e/ou com as competências técnicas do PerfilProfissional do candidato.
        """
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
