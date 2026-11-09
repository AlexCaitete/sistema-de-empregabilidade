import json
from typing import List, Tuple
from modelos import PerfilProfissional, CertificadoOuCurso
from servicos.banco_dados import GerenciadorBancoDados


class GerenciadorPerfil:
    def __init__(self, caminho_banco: str = "dados/empregabilidade.db"):
        self.banco = GerenciadorBancoDados(caminho_banco=caminho_banco)

    def _criar_perfil_inicial(self) -> PerfilProfissional:
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
                "SQL",
            ],
            experiencias=[
                "Desenvolvimento de APIs RESTful utilizando Python, FastAPI e validação de dados com Pydantic.",
                "Integração de sistemas back-end com modelos de Inteligência Artificial (Google Gemini SDK).",
                "Construção de aplicações web modernas utilizando JavaScript, React e Node.js.",
            ],
            cursos_e_certificados=[],
        )

    def obter_perfil(self) -> PerfilProfissional:
        with self.banco.obter_conexao() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                "SELECT nome_completo, cargo_desejado, competencias_json, experiencias_json "
                "FROM perfil_profissional WHERE id = 1"
            )
            linha_perfil = cursor.fetchone()

            if not linha_perfil:
                perfil_inicial = self._criar_perfil_inicial()
                self.salvar_perfil(perfil_inicial)
                return perfil_inicial

            cursor.execute(
                "SELECT titulo, instituicao, tecnologias_json, data_conclusao "
                "FROM certificados ORDER BY id ASC"
            )
            linhas_certificados = cursor.fetchall()

            lista_certificados: List[CertificadoOuCurso] = []
            for linha_cert in linhas_certificados:
                lista_certificados.append(
                    CertificadoOuCurso(
                        titulo=linha_cert["titulo"],
                        instituicao=linha_cert["instituicao"],
                        tecnologias_adquiridas=json.loads(linha_cert["tecnologias_json"]),
                        data_conclusao=linha_cert["data_conclusao"],
                    )
                )

            return PerfilProfissional(
                nome_completo=linha_perfil["nome_completo"],
                cargo_desejado=linha_perfil["cargo_desejado"],
                competencias_tecnicas=json.loads(linha_perfil["competencias_json"]),
                experiencias=json.loads(linha_perfil["experiencias_json"]),
                cursos_e_certificados=lista_certificados,
            )

    def salvar_perfil(self, perfil: PerfilProfissional) -> PerfilProfissional:
        with self.banco.obter_conexao() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT INTO perfil_profissional (id, nome_completo, cargo_desejado, competencias_json, experiencias_json)
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    nome_completo = excluded.nome_completo,
                    cargo_desejado = excluded.cargo_desejado,
                    competencias_json = excluded.competencias_json,
                    experiencias_json = excluded.experiencias_json
                """,
                (
                    perfil.nome_completo,
                    perfil.cargo_desejado,
                    json.dumps(perfil.competencias_tecnicas, ensure_ascii=False),
                    json.dumps(perfil.experiencias, ensure_ascii=False),
                ),
            )

            for certificado in perfil.cursos_e_certificados:
                cursor.execute(
                    """
                    INSERT INTO certificados (titulo, instituicao, tecnologias_json, data_conclusao)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(titulo) DO UPDATE SET
                        instituicao = excluded.instituicao,
                        tecnologias_json = excluded.tecnologias_json,
                        data_conclusao = excluded.data_conclusao
                    """,
                    (
                        certificado.titulo.strip(),
                        certificado.instituicao,
                        json.dumps(certificado.tecnologias_adquiridas, ensure_ascii=False),
                        certificado.data_conclusao,
                    ),
                )

            conexao.commit()

        return perfil

    def adicionar_certificado(
        self, novo_certificado: CertificadoOuCurso
    ) -> Tuple[PerfilProfissional, List[str]]:
        perfil = self.obter_perfil()

        titulos_existentes = [
            certificado.titulo.strip().lower()
            for certificado in perfil.cursos_e_certificados
        ]
        if novo_certificado.titulo.strip().lower() not in titulos_existentes:
            perfil.cursos_e_certificados.append(novo_certificado)

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
