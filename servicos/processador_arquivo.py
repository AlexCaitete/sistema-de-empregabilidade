import os
from typing import Optional
from pypdf import PdfReader
from fastapi import UploadFile, HTTPException
from modelos import PerfilProfissional, RespostaIngestaoCertificado
from servicos.gerenciador_perfil import GerenciadorPerfil
from servicos.agente_analista import AgenteAnalista


class ProcessadorDocumento:
    """
    Utilitário de leitura de documentos: responsável por ler e extrair
    texto bruto de arquivos PDF (certificados, diplomas, currículos).
    """

    @staticmethod
    def extrair_texto_de_pdf(caminho_arquivo: str) -> str:
        try:
            leitor_pdf = PdfReader(caminho_arquivo)
            texto_completo = ""
            for pagina in leitor_pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
            return texto_completo.strip()
        except Exception as erro:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar o ficheiro PDF: {str(erro)}"
            )

    @classmethod
    async def processar_upload(cls, arquivo: UploadFile) -> str:
        nome_original = arquivo.filename or ""
        nome_arquivo = os.path.basename(nome_original)

        if not nome_arquivo.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Apenas arquivos PDF são suportados."
            )

        os.makedirs("temp_uploads", exist_ok=True)
        caminho_arquivo = os.path.join("temp_uploads", nome_arquivo)

        conteudo = await arquivo.read()
        if not conteudo:
            raise HTTPException(
                status_code=400,
                detail="O arquivo enviado está vazio."
            )

        with open(caminho_arquivo, "wb") as arquivo_destino:
            arquivo_destino.write(conteudo)

        try:
            texto_extraido = cls.extrair_texto_de_pdf(caminho_arquivo)
            return texto_extraido
        finally:
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)


class AgenteIngestaoConhecimento:
    """
    Agente de Ingestão de Conhecimento:
    Coordena a leitura de PDFs de certificados ou currículos, extrai os conhecimentos
    via AgenteAnalista e atualiza automaticamente o PerfilProfissional no GerenciadorPerfil.
    """

    def __init__(
        self,
        gerenciador: Optional[GerenciadorPerfil] = None,
        analista: Optional[AgenteAnalista] = None,
    ):
        self.gerenciador = gerenciador or GerenciadorPerfil()
        self.analista = analista or AgenteAnalista()

    async def processar_documento(self, arquivo: UploadFile) -> str:
        """Extrai o texto bruto de um arquivo PDF enviado via upload."""
        texto = await ProcessadorDocumento.processar_upload(arquivo)
        if not texto:
            raise HTTPException(
                status_code=400,
                detail="O arquivo enviado parece estar vazio ou não contém texto legível."
            )
        return texto

    def atualizar_perfil(self, novo_perfil: PerfilProfissional) -> PerfilProfissional:
        """Persiste um PerfilProfissional completo no gerenciador."""
        return self.gerenciador.salvar_perfil(novo_perfil)

    async def ingerir_certificado(self, arquivo: UploadFile) -> RespostaIngestaoCertificado:
        """
        Processa o upload de um certificado PDF, extrai os dados estruturados com IA
        e adiciona as novas competências e o curso ao perfil do usuário.
        """
        texto_extraido = await self.processar_documento(arquivo)
        certificado = self.analista.extrair_certificado_de_texto(texto_extraido)
        perfil_atualizado, novas_competencias = self.gerenciador.adicionar_certificado(certificado)

        return RespostaIngestaoCertificado(
            mensagem="Certificado processado e perfil atualizado com sucesso!",
            certificado_extraido=certificado,
            novas_competencias_adicionadas=novas_competencias,
            perfil_atualizado=perfil_atualizado,
        )
