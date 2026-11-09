import os
import traceback
from typing import List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from modelos import PerfilProfissional, VagaEmprego, CurriculoAdaptado

load_dotenv()


class _EsquemaGeracaoAlfaiate(BaseModel):
    resumo_profissional_otimizado: str
    competencias_destacadas: List[str]
    experiencias_adaptadas: List[str]
    conteudo_otimizado: str


class AgenteAlfaiateCurriculo:
    """
    Agente Alfaiate de Currículo:
    Adapta e reescreve o currículo do candidato especificamente para os
    requisitos e palavras-chave de uma vaga de emprego desejada, aplicando
    as regras de otimização para sistemas ATS (Gupy, Greenhouse, Workday, LinkedIn).
    """

    MODELOS_DISPONIVEIS = [
        os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]

    def __init__(self):
        self.chave_api = os.getenv("GEMINI_API_KEY")
        self.cliente: Optional[genai.Client] = None

    def _obter_cliente(self) -> genai.Client:
        if not self.chave_api:
            raise ValueError("Chave GEMINI_API_KEY não configurada.")
        if self.cliente is None:
            self.cliente = genai.Client(api_key=self.chave_api)
        return self.cliente

    def adaptar_curriculo(
        self, perfil: PerfilProfissional, vaga: VagaEmprego
    ) -> CurriculoAdaptado:
        """
        Gera um CurriculoAdaptado personalizado para a vaga alvo a partir do PerfilProfissional,
        otimizado para leitura automatizada por robôs de recrutamento (ATS).
        """
        instrucao_ia = f"""
        Você é um especialista sênior em Recrutamento Técnico e algoritmos de triagem ATS
        (Applicant Tracking Systems como Gupy, Greenhouse, Workday e LinkedIn).

        Sua tarefa é adaptar e reescrever o currículo do candidato especificamente para a VAGA ALVO,
        maximizando a pontuação de compatibilidade (match score) no ATS sem inventar experiências falsas.

        DIRETRIZES OBRIGATÓRIAS DE OTIMIZAÇÃO ATS:
        1. Correspondência Exata de Palavras-Chave (Keyword Matching): Identifique os requisitos da vaga
           que o candidato domina e utilize exatamente a mesma grafia da vaga no Resumo Profissional,
           na lista de Competências Destacadas e na descrição das Experiências.
        2. Verbos de Ação e Método de Impacto: Reescreva cada experiência iniciando com verbos de ação
           fortes (ex: Desenvolveu, Implementou, Arquitetou, Integrou), conectando a atividade realizada
           às tecnologias exigidas na descrição da vaga.
        3. Formatação Limpa para Leitura de Robôs (Campo 'conteudo_otimizado'):
           - Gere o currículo completo em Markdown de coluna única.
           - NÃO utilize emojis, tabelas, colunas ou caracteres gráficos especiais nos títulos das seções,
             pois eles prejudicam os parsers de ATS.
           - Utilize exatamente os títulos de seção padronizados para ATS:
             # [Nome Completo]
             **[Título exato da Vaga Alvo]**
             ## RESUMO PROFISSIONAL
             ## COMPETÊNCIAS TÉCNICAS
             ## EXPERIÊNCIA PROFISSIONAL
             ## CURSOS E CERTIFICAÇÕES
        4. Priorização por Relevância: Ordene as competências e os certificados colocando primeiro
           aqueles que têm relação direta com os requisitos da vaga alvo.

        PERFIL BASE DO CANDIDATO:
        Nome: {perfil.nome_completo}
        Cargo Atual/Desejado: {perfil.cargo_desejado}
        Competências Técnicas: {", ".join(perfil.competencias_tecnicas)}
        Experiências: {" | ".join(perfil.experiencias)}
        Cursos e Certificados: {", ".join([f"{certificado.titulo} - {certificado.instituicao} (Tecnologias: {', '.join(certificado.tecnologias_adquiridas)})" for certificado in perfil.cursos_e_certificados])}

        VAGA ALVO:
        Cargo da Vaga: {vaga.titulo}
        Empresa: {vaga.empresa}
        Nível: {vaga.nivel or "Júnior"}
        Localização: {vaga.localizacao or "Remoto"}
        Requisitos Obrigatórios e Desejáveis: {", ".join(vaga.requisitos)}
        Descrição da Vaga: {vaga.descricao}
        """

        try:
            resultado_ia = self._chamar_gemini(instrucao_ia)
            return CurriculoAdaptado(
                perfil_base=perfil,
                vaga_alvo=vaga,
                resumo_profissional_otimizado=resultado_ia.resumo_profissional_otimizado,
                competencias_destacadas=resultado_ia.competencias_destacadas,
                experiencias_adaptadas=resultado_ia.experiencias_adaptadas,
                conteudo_otimizado=resultado_ia.conteudo_otimizado,
            )
        except Exception:
            print("--- AVISO: Falha na chamada da API Gemini no Agente Alfaiate, gerando currículo ATS localmente ---")
            traceback.print_exc()
            return self._adaptar_curriculo_contingencia(perfil, vaga)

    def _chamar_gemini(self, instrucao_ia: str) -> _EsquemaGeracaoAlfaiate:
        cliente_ia = self._obter_cliente()

        ultimo_erro: Optional[Exception] = None
        modelos_testados: List[str] = []

        for modelo in self.MODELOS_DISPONIVEIS:
            if not modelo or modelo in modelos_testados:
                continue
            modelos_testados.append(modelo)

            try:
                resposta = cliente_ia.models.generate_content(
                    model=modelo,
                    contents=instrucao_ia,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=_EsquemaGeracaoAlfaiate,
                        temperature=0.2,
                    ),
                )
                if not resposta.parsed:
                    raise ValueError("Resposta vazia do modelo.")
                if isinstance(resposta.parsed, _EsquemaGeracaoAlfaiate):
                    return resposta.parsed
                return _EsquemaGeracaoAlfaiate.model_validate(resposta.parsed)
            except Exception as erro:
                ultimo_erro = erro
                mensagem_erro = str(erro).lower()
                termos_criticos = [
                    "connect",
                    "network",
                    "timeout",
                    "getaddrinfo",
                    "api_key_invalid",
                    "permission_denied",
                ]
                if any(termo_erro in mensagem_erro for termo_erro in termos_criticos):
                    break
                continue

        if ultimo_erro is not None:
            raise ultimo_erro

        raise RuntimeError("Não foi possível adaptar o currículo pelo modelo de IA.")

    @staticmethod
    def _termos_combinam(termo_a: str, termo_b: str) -> bool:
        a = termo_a.strip().lower()
        b = termo_b.strip().lower()
        if a == b:
            return True
        # Evita falso positivo clássico entre "java" e "javascript"
        if {a, b} == {"java", "javascript"}:
            return False
        palavras_a = set(a.replace("/", " ").replace("-", " ").split())
        palavras_b = set(b.replace("/", " ").replace("-", " ").split())
        if a in palavras_b or b in palavras_a:
            return True
        return False

    def _adaptar_curriculo_contingencia(
        self, perfil: PerfilProfissional, vaga: VagaEmprego
    ) -> CurriculoAdaptado:
        """
        Gera localmente um currículo estruturado seguindo as regras de ATS
        (correspondência de palavras-chave, seções padronizadas sem emojis e priorização).
        """
        destacadas: List[str] = []
        outras: List[str] = []

        for competencia in perfil.competencias_tecnicas:
            encontrou_correspondencia = False
            for req_original in vaga.requisitos:
                if self._termos_combinam(req_original, competencia):
                    if competencia not in destacadas:
                        destacadas.append(competencia)
                    encontrou_correspondencia = True
                    break
            if not encontrou_correspondencia and competencia not in outras:
                outras.append(competencia)

        competencias_ordenadas = destacadas + outras
        principais_termos = destacadas[:6] if destacadas else competencias_ordenadas[:6]

        resumo = (
            f"Atuação focada como {vaga.titulo}, com experiência prática no desenvolvimento de soluções "
            f"utilizando {', '.join(principais_termos)}. "
            f"Perfil direcionado para as demandas da {vaga.empresa}, combinando domínio técnico em "
            f"{', '.join(vaga.requisitos[:4])} com boas práticas de arquitetura, qualidade de código e entrega contínua."
        )

        experiencias_adaptadas = [
            f"{experiencia.rstrip('.')} — aplicando competências alinhadas a {', '.join(principais_termos[:3])}."
            for experiencia in perfil.experiencias
        ]

        secao_certificados = ""
        if perfil.cursos_e_certificados:
            linhas_certificados = [
                f"- {certificado.titulo} | Instituição: {certificado.instituicao} "
                f"| Competências: {', '.join(certificado.tecnologias_adquiridas)}"
                + (f" | Conclusão: {certificado.data_conclusao}" if certificado.data_conclusao else "")
                for certificado in perfil.cursos_e_certificados
            ]
            secao_certificados = (
                "\n## CURSOS E CERTIFICAÇÕES\n" + "\n".join(linhas_certificados) + "\n"
            )

        curriculo_markdown = (
            f"# {perfil.nome_completo}\n"
            f"**Cargo Alvo: {vaga.titulo} | {vaga.empresa} ({vaga.localizacao or 'Remoto'})**\n\n"
            f"## RESUMO PROFISSIONAL\n"
            f"{resumo}\n\n"
            f"## COMPETÊNCIAS TÉCNICAS\n"
            + "\n".join([f"- {competencia}" for competencia in competencias_ordenadas])
            + "\n\n## EXPERIÊNCIA PROFISSIONAL\n"
            + "\n".join([f"- {experiencia}" for experiencia in experiencias_adaptadas])
            + "\n"
            + secao_certificados
        )

        return CurriculoAdaptado(
            perfil_base=perfil,
            vaga_alvo=vaga,
            resumo_profissional_otimizado=resumo,
            competencias_destacadas=destacadas if destacadas else competencias_ordenadas[:6],
            experiencias_adaptadas=experiencias_adaptadas,
            conteudo_otimizado=curriculo_markdown,
        )
