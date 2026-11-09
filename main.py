import traceback
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from modelos import (
    PerfilProfissional,
    VagaEmprego,
    AnaliseCompatibilidade,
    CurriculoAdaptado,
    RespostaIngestaoCertificado,
)
from servicos.gerenciador_perfil import GerenciadorPerfil
from servicos.processador_arquivo import ProcessadorDocumento, AgenteIngestaoConhecimento
from servicos.agente_analista import AgenteAnalista
from servicos.agente_cacador import AgenteCacadorVagas
from servicos.agente_alfaiate import AgenteAlfaiateCurriculo

app = FastAPI(
    title="API de Empregabilidade e Agentes Inteligentes",
    description=(
        "Ecossistema multiagente para gestão de perfil profissional, ingestão de certificados "
        "em PDF com IA (Google Gemini), busca de vagas, análise de compatibilidade e adaptação de currículos."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gerenciador_perfil = GerenciadorPerfil()
analista = AgenteAnalista()
agente_ingestao = AgenteIngestaoConhecimento(
    gerenciador=gerenciador_perfil,
    analista=analista,
)
cacador_vagas = AgenteCacadorVagas()
alfaiate_curriculo = AgenteAlfaiateCurriculo()


@app.get("/", tags=["Status"])
async def verificar_status_api():
    return {
        "sistema": "Sistema Inteligente de Empregabilidade & Automação de Carreira",
        "versao": "2.0.0",
        "status": "online",
        "documentacao_interativa": "/docs",
    }


@app.get("/perfil", response_model=PerfilProfissional, tags=["1. Perfil & Ingestão"])
async def obter_perfil():
    return gerenciador_perfil.obter_perfil()


@app.put("/perfil", response_model=PerfilProfissional, tags=["1. Perfil & Ingestão"])
async def atualizar_perfil(perfil: PerfilProfissional):
    return gerenciador_perfil.salvar_perfil(perfil)


@app.post(
    "/perfil/analisar-documento",
    response_model=PerfilProfissional,
    tags=["1. Perfil & Ingestão"],
)
async def analisar_documento(arquivo: UploadFile = File(...)):
    try:
        texto_extraido = await ProcessadorDocumento.processar_upload(arquivo)

        if not texto_extraido:
            raise HTTPException(
                status_code=400,
                detail="O arquivo enviado parece estar vazio ou não pôde ser processado.",
            )

        perfil = analista.analisar_texto_para_perfil(texto_extraido)
        gerenciador_perfil.salvar_perfil(perfil)
        return perfil

    except HTTPException:
        raise
    except Exception as erro:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno na análise: {str(erro)}")


@app.post(
    "/perfil/upload-certificado",
    response_model=RespostaIngestaoCertificado,
    tags=["1. Perfil & Ingestão"],
)
async def enviar_certificado(arquivo: UploadFile = File(...)):
    try:
        return await agente_ingestao.ingerir_certificado(arquivo)
    except HTTPException:
        raise
    except Exception as erro:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar o certificado: {str(erro)}",
        )


@app.get("/vagas", response_model=List[VagaEmprego], tags=["2. Caçador de Vagas"])
async def listar_ou_buscar_vagas(
    criterios: Optional[str] = Query(
        default=None,
        description="Palavras-chave separadas por vírgula (ex: Python, FastAPI, Spring Boot)",
    )
):
    perfil_atual = gerenciador_perfil.obter_perfil()
    return cacador_vagas.buscar_vagas(criterios=criterios, perfil=perfil_atual)


@app.get(
    "/vagas/recomendadas",
    response_model=List[VagaEmprego],
    tags=["2. Caçador de Vagas"],
)
async def recomendar_vagas_para_perfil():
    perfil_atual = gerenciador_perfil.obter_perfil()
    return cacador_vagas.buscar_vagas(perfil=perfil_atual)


@app.post("/vagas", response_model=VagaEmprego, tags=["2. Caçador de Vagas"])
async def cadastrar_vaga(vaga: VagaEmprego):
    return cacador_vagas.adicionar_vaga(vaga)


@app.post(
    "/analise/compatibilidade",
    response_model=AnaliseCompatibilidade,
    tags=["3. Analista de Perfil"],
)
async def analisar_compatibilidade_vaga(vaga: VagaEmprego):
    try:
        perfil_atual = gerenciador_perfil.obter_perfil()
        return analista.analisar_compatibilidade(perfil_atual, vaga)
    except Exception as erro:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular compatibilidade: {str(erro)}",
        )


@app.post(
    "/analise/compatibilidade/{id_vaga}",
    response_model=AnaliseCompatibilidade,
    tags=["3. Analista de Perfil"],
)
async def analisar_compatibilidade_por_id(id_vaga: str):
    vaga = cacador_vagas.obter_vaga_por_id(id_vaga)
    if not vaga:
        raise HTTPException(status_code=404, detail=f"Vaga '{id_vaga}' não encontrada.")

    perfil_atual = gerenciador_perfil.obter_perfil()
    return analista.analisar_compatibilidade(perfil_atual, vaga)


@app.post(
    "/curriculo/adaptar",
    response_model=CurriculoAdaptado,
    tags=["4. Alfaiate de Currículo"],
)
async def adaptar_curriculo_para_vaga(vaga: VagaEmprego):
    try:
        perfil_atual = gerenciador_perfil.obter_perfil()
        return alfaiate_curriculo.adaptar_curriculo(perfil_atual, vaga)
    except Exception as erro:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao adaptar currículo: {str(erro)}",
        )


@app.post(
    "/curriculo/adaptar/{id_vaga}",
    response_model=CurriculoAdaptado,
    tags=["4. Alfaiate de Currículo"],
)
async def adaptar_curriculo_por_id(id_vaga: str):
    vaga = cacador_vagas.obter_vaga_por_id(id_vaga)
    if not vaga:
        raise HTTPException(status_code=404, detail=f"Vaga '{id_vaga}' não encontrada.")

    perfil_atual = gerenciador_perfil.obter_perfil()
    return alfaiate_curriculo.adaptar_curriculo(perfil_atual, vaga)
