import os
from pypdf import PdfReader
from fastapi import UploadFile, HTTPException

class DocumentParser:
    """
    Agente de Ingestão: Responsável por ler e extrair texto
    bruto de documentos PDF (certificados, diplomas, currículos).
    """

    @staticmethod
    def extrair_texto_de_pdf(file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            texto_completo = ""
            for pagina in reader.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
            return texto_completo.strip()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar o ficheiro PDF: {str(e)}"
            )

    @classmethod
    async def processar_upload(cls, arquivo: UploadFile) -> str:
        filename = arquivo.filename or ""

        if not filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Apenas arquivos PDF são suportados."
            )

        os.makedirs("temp_uploads", exist_ok=True)
        file_path = os.path.join("temp_uploads", filename)

        # Salva o arquivo localmente
        with open(file_path, "wb") as buffer:
            conteudo = await arquivo.read()
            buffer.write(conteudo)

        try:

            texto_extraido = cls.extrair_texto_de_pdf(file_path)
            return texto_extraido
        finally:

            if os.path.exists(file_path):
                os.remove(file_path)
