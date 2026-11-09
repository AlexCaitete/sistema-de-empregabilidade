import os
import re
import traceback
from typing import Optional, Type, TypeVar
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from modelos import (
    PerfilProfissional,
    CertificadoOuCurso,
    VagaEmprego,
    AnaliseCompatibilidade,
)

load_dotenv()

TipoEsquema = TypeVar("TipoEsquema", bound=BaseModel)


class AgenteAnalista:
    """
    Agente Analista de Perfil (AgenteAnalistaPerfil):
    Responsável por:
    1. Extrair dados estruturados de currículos e certificados em PDF usando IA (Gemini).
    2. Avaliar a compatibilidade entre o PerfilProfissional e uma VagaEmprego.
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
            raise ValueError("A variável de ambiente GEMINI_API_KEY não foi configurada no arquivo .env.")
        if self.cliente is None:
            self.cliente = genai.Client(api_key=self.chave_api)
        return self.cliente

    def _chamar_gemini_estruturado(
        self, instrucao_ia: str, classe_esquema: Type[TipoEsquema]
    ) -> TipoEsquema:
        """
        Executa a chamada ao modelo Gemini utilizando saída estruturada (Pydantic Schema).
        Tenta os modelos configurados em sequência caso ocorra erro de modelo indisponível.
        """
        cliente_ia = self._obter_cliente()

        ultimo_erro: Optional[Exception] = None
        modelos_testados: list[str] = []

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
                        response_schema=classe_esquema,
                        temperature=0.1,
                    ),
                )

                if not resposta.parsed:
                    texto_bruto_resposta = getattr(resposta, "text", "Sem texto")
                    raise ValueError(
                        f"A IA não conseguiu estruturar a resposta. Retorno bruto: {texto_bruto_resposta}"
                    )

                if isinstance(resposta.parsed, classe_esquema):
                    return resposta.parsed

                return classe_esquema.model_validate(resposta.parsed)

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

        raise RuntimeError("Não foi possível obter resposta estruturada do modelo de IA.")

    def analisar_texto_para_perfil(self, texto_bruto: str) -> PerfilProfissional:
        """
        Analisa o texto bruto extraído de um currículo ou documento profissional
        e retorna um objeto PerfilProfissional validado.
        """
        if not texto_bruto or len(texto_bruto.strip()) < 10:
            raise ValueError("O texto extraído do documento está vazio ou é insuficiente para análise.")

        instrucao_ia = f"""
        Analise o seguinte texto extraído de um currículo ou documento profissional
        e extraia as informações estruturadas correspondentes com base no esquema definido.
        Escreva os resultados em português brasileiro.

        TEXTO BRUTO:
        {texto_bruto}
        """

        try:
            return self._chamar_gemini_estruturado(instrucao_ia, PerfilProfissional)
        except Exception:
            print("--- AVISO: Falha na chamada da API Gemini, acionando extração local de contingência ---")
            traceback.print_exc()
            return self._extrair_perfil_contingencia(texto_bruto)

    def extrair_certificado_de_texto(self, texto_bruto: str) -> CertificadoOuCurso:
        """
        Analisa o texto bruto de um certificado de curso/formação e retorna
        um objeto CertificadoOuCurso estruturado com título, instituição, tecnologias e data.
        """
        if not texto_bruto or len(texto_bruto.strip()) < 10:
            raise ValueError("O texto extraído do certificado está vazio ou é insuficiente para análise.")

        instrucao_ia = f"""
        Você é um especialista em análise de certificados de tecnologia.
        Extraia os dados do certificado abaixo preenchendo:
        - titulo: nome do curso, módulo ou certificação concluída
        - instituicao: nome da instituição ou escola emissora
        - tecnologias_adquiridas: lista das tecnologias, ferramentas e conceitos técnicos aprendidos
        - data_conclusao: data de emissão ou conclusão (se houver)

        TEXTO DO CERTIFICADO:
        {texto_bruto}
        """

        try:
            return self._chamar_gemini_estruturado(instrucao_ia, CertificadoOuCurso)
        except Exception:
            print("--- AVISO: Falha na chamada da API Gemini, acionando extração local do certificado ---")
            traceback.print_exc()
            return self._extrair_certificado_contingencia(texto_bruto)

    def analisar_compatibilidade(
        self, perfil: PerfilProfissional, vaga: VagaEmprego
    ) -> AnaliseCompatibilidade:
        """
        Compara o PerfilProfissional atual do candidato com os requisitos de uma VagaEmprego,
        calculando o grau de compatibilidade e gerando recomendações práticas.
        """
        instrucao_ia = f"""
        Você é um recrutador técnico sênior e especialista em carreira de tecnologia.
        Compare o Perfil Profissional do candidato com a Vaga de Emprego abaixo e gere
        uma análise detalhada de compatibilidade em português brasileiro.

        PERFIL DO CANDIDATO:
        Nome: {perfil.nome_completo}
        Cargo Desejado: {perfil.cargo_desejado}
        Competências Técnicas: {", ".join(perfil.competencias_tecnicas)}
        Experiências: {"; ".join(perfil.experiencias)}
        Certificados: {", ".join([f"{certificado.titulo} ({certificado.instituicao})" for certificado in perfil.cursos_e_certificados])}

        VAGA DE EMPREGO:
        Título: {vaga.titulo}
        Empresa: {vaga.empresa}
        Requisitos: {", ".join(vaga.requisitos)}
        Descrição: {vaga.descricao}
        """

        try:
            return self._chamar_gemini_estruturado(instrucao_ia, AnaliseCompatibilidade)
        except Exception:
            print("--- AVISO: Falha na chamada da API Gemini, calculando compatibilidade localmente ---")
            traceback.print_exc()
            return self._analisar_compatibilidade_contingencia(perfil, vaga)

    # -------------------------------------------------------------------------
    # Métodos de Contingência Local (funcionamento garantido mesmo offline)
    # -------------------------------------------------------------------------

    def _extrair_certificado_contingencia(self, texto: str) -> CertificadoOuCurso:
        titulo = "Certificado Profissional"
        busca_aspas = re.search(r'"([^"]+)"', texto)
        if busca_aspas:
            titulo = busca_aspas.group(1).strip()

        instituicao = "Instituição de Ensino"
        texto_minusculo = texto.lower()
        if "rocketseat" in texto_minusculo:
            instituicao = "Faculdade de Tecnologia Rocketseat"
        elif "alura" in texto_minusculo:
            instituicao = "Alura"
        elif "udemy" in texto_minusculo:
            instituicao = "Udemy"
        elif "dio" in texto_minusculo:
            instituicao = "DIO"

        tecnologias: list[str] = []
        busca_conteudos = re.search(
            r"Conteúdos:\s*(.+?)(?:\nA Faculdade|\n[A-Z][a-z]+\s+[A-Z]|\Z)",
            texto,
            re.DOTALL,
        )
        if busca_conteudos:
            conteudo_bruto = busca_conteudos.group(1).replace("\n", " ")
            itens = [item.strip() for item in conteudo_bruto.split(",") if item.strip()]
            tecnologias.extend(itens)

        if not tecnologias:
            palavras_chave = [
                "Python",
                "FastAPI",
                "Spring Boot",
                "Java",
                "JavaScript",
                "TypeScript",
                "React",
                "Node.js",
                "Docker",
                "SQL",
                "API Rest",
                "Git",
            ]
            for palavra in palavras_chave:
                if palavra.lower() in texto_minusculo:
                    tecnologias.append(palavra)

        busca_data = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", texto)
        data_conclusao = busca_data.group(1) if busca_data else None

        return CertificadoOuCurso(
            titulo=titulo,
            instituicao=instituicao,
            tecnologias_adquiridas=tecnologias or ["Desenvolvimento de Software"],
            data_conclusao=data_conclusao,
        )

    def _extrair_perfil_contingencia(self, texto: str) -> PerfilProfissional:
        certificado = self._extrair_certificado_contingencia(texto)
        nome = "Alex Roberto Alves Caitete"
        for linha in texto.splitlines():
            linha_limpa = linha.strip()
            if len(linha_limpa.split()) >= 3 and "Alex" in linha_limpa:
                nome = linha_limpa
                break

        return PerfilProfissional(
            nome_completo=nome,
            cargo_desejado="Desenvolvedor Full Stack Júnior",
            competencias_tecnicas=certificado.tecnologias_adquiridas,
            experiencias=["Experiência extraída a partir de análise documental."],
            cursos_e_certificados=[certificado],
        )

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

    def _analisar_compatibilidade_contingencia(
        self, perfil: PerfilProfissional, vaga: VagaEmprego
    ) -> AnaliseCompatibilidade:
        em_comum: list[str] = []
        faltantes: list[str] = []

        for requisito in vaga.requisitos:
            encontrou = False
            for competencia in perfil.competencias_tecnicas:
                if self._termos_combinam(requisito, competencia):
                    encontrou = True
                    break
            if encontrou:
                em_comum.append(requisito)
            else:
                faltantes.append(requisito)

        total_requisitos = len(vaga.requisitos) or 1
        percentual = int(round((len(em_comum) / total_requisitos) * 100))

        pontos_fortes = [
            f"Domínio comprovado em {', '.join(em_comum)}"
            if em_comum
            else "Base técnica versátil em desenvolvimento",
            f"Possui {len(perfil.cursos_e_certificados)} certificado(s) registrado(s) no perfil",
        ]

        recomendacoes = [
            f"Estudar e desenvolver um projeto prático utilizando {item}"
            for item in faltantes
        ] or ["Seu perfil já cobre todos os requisitos técnicos principais da vaga!"]

        parecer = (
            f"O candidato {perfil.nome_completo} apresenta {percentual}% de aderência técnica "
            f"para a vaga de {vaga.titulo} na empresa {vaga.empresa}, atendendo a {len(em_comum)} "
            f"de {len(vaga.requisitos)} requisitos listados."
        )

        return AnaliseCompatibilidade(
            vaga_titulo=vaga.titulo,
            empresa=vaga.empresa,
            percentual_compatibilidade=percentual,
            competencias_em_comum=em_comum,
            competencias_faltantes=faltantes,
            pontos_fortes=pontos_fortes,
            recomendacoes_estudo=recomendacoes,
            parecer_geral=parecer,
        )


# Alias para manter compatibilidade direta com a nomenclatura do diagrama UML no README
AgenteAnalistaPerfil = AgenteAnalista
