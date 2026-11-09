import json
import os
from typing import List, Tuple
from modelos import PerfilProfissional, CertificadoOuCurso


class GerenciadorPerfil:
    """
    Serviço responsável por persistir, carregar e atualizar os dados
    do PerfilProfissional em um arquivo JSON local.
    """

    def __init__(self, caminho_arquivo: str = "dados/perfil_profissional.json"):
        self.caminho_arquivo = caminho_arquivo
        self._garantir_diretorio()

    def _garantir_diretorio(self) -> None:
        diretorio = os.path.dirname(self.caminho_arquivo)
        if diretorio:
            os.makedirs(diretorio, exist_ok=True)

    def _criar_perfil_inicial(self) -> PerfilProfissional:
        """
        Retorna um perfil base inicial caso ainda não exista um arquivo salvo no disco.
        """
        return PerfilProfissional(
            nome_completo="Alex Roberto Alves Caitete",
            cargo_desejado="Desenvolvedor Full Stack Júnior",
            competencias_tecnicas=[
                "Python",
                "FastAPI",
                "JavaScript",
                "React",
                "Node.js",
                "Git",
                "SQL"
            ],
            experiencias=[
                "Desenvolvimento de APIs RESTful utilizando Python, FastAPI e validação de dados com Pydantic.",
                "Integração de sistemas back-end com modelos de Inteligência Artificial (Google Gemini SDK).",
                "Construção de aplicações web modernas utilizando JavaScript, React e Node.js."
            ],
            cursos_e_certificados=[]
        )

    def obter_perfil(self) -> PerfilProfissional:
        """
        Carrega o perfil salvo em disco. Se não existir, cria e salva o perfil inicial.
        """
        if not os.path.exists(self.caminho_arquivo):
            perfil_inicial = self._criar_perfil_inicial()
            self.salvar_perfil(perfil_inicial)
            return perfil_inicial

        try:
            with open(self.caminho_arquivo, "r", encoding="utf-8") as arquivo_json:
                dados = json.load(arquivo_json)
            return PerfilProfissional.model_validate(dados)
        except Exception:
            perfil_inicial = self._criar_perfil_inicial()
            self.salvar_perfil(perfil_inicial)
            return perfil_inicial

    def salvar_perfil(self, perfil: PerfilProfissional) -> PerfilProfissional:
        """
        Salva o estado atual do PerfilProfissional no arquivo JSON.
        """
        self._garantir_diretorio()
        with open(self.caminho_arquivo, "w", encoding="utf-8") as arquivo_json:
            json.dump(perfil.model_dump(), arquivo_json, ensure_ascii=False, indent=4)
        return perfil

    def adicionar_certificado(
        self, novo_certificado: CertificadoOuCurso
    ) -> Tuple[PerfilProfissional, List[str]]:
        """
        Adiciona um novo certificado ao perfil e mescla automaticamente as novas
        tecnologias na lista de competências técnicas sem duplicar itens.
        """
        perfil = self.obter_perfil()

        # Verifica se o certificado já foi cadastrado (comparando título em minúsculas)
        titulos_existentes = [
            certificado.titulo.strip().lower()
            for certificado in perfil.cursos_e_certificados
        ]
        if novo_certificado.titulo.strip().lower() not in titulos_existentes:
            perfil.cursos_e_certificados.append(novo_certificado)

        # Adiciona apenas tecnologias que ainda não estão no perfil
        competencias_atuais_minusculas = {
            competencia.strip().lower() for competencia in perfil.competencias_tecnicas
        }
        novas_competencias: List[str] = []

        for tecnologia in novo_certificado.tecnologias_adquiridas:
            tecnologia_limpa = tecnologia.strip()
            if (
                tecnologia_limpa
                and tecnologia_limpa.lower() not in competencias_atuais_minusculas
            ):
                perfil.competencias_tecnicas.append(tecnologia_limpa)
                competencias_atuais_minusculas.add(tecnologia_limpa.lower())
                novas_competencias.append(tecnologia_limpa)

        self.salvar_perfil(perfil)
        return perfil, novas_competencias
