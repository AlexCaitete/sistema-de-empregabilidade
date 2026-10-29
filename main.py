from fastapi import FastAPI, UploadFile, File, HTTPException
from parser import DocumentParser
from modelos import PerfilProfissional, CertificadoOuCurso
from servicos.agente_analista import AgenteAnalista

app = FastAPI(
    title="API de Empregabilidade e Agentes Inteligentes",
    version="1.3.0",
)
analista = AgenteAnalista()

@app.post("/perfil/analisar-documento", response_model=PerfilProfissional)
async def analisar_documento(file: UploadFile = File(...)):
    try:
        texto_extraido = await DocumentParser.processar_upload(file)

        if not texto_extraido:
            raise HTTPException(status_code=400, detail="O arquivo enviado parece estar vazio ou não pôde ser processado.")

        perfil = analista.analisar_texto_para_perfil(texto_extraido)
        return perfil

    except Exception as e:
        import traceback
        traceback.print_exc()  # Imprime o erro exato na consola do Uvicorn
        raise HTTPException(status_code=500, detail=f"Erro interno na análise: {str(e)}")

@app.post("/perfil/upload-certificado")
async def upload_certificado(file: UploadFile = File(...)):
    texto_extraido = await DocumentParser.processar_upload(file)
    return {
        "mensagem": "Documento processado com sucesso!",
        "nome_arquivo": file.filename,
        "tamanho_texto_extraido": len(texto_extraido),
        "amostra_conteudo": texto_extraido[:300] + "..."
    }
