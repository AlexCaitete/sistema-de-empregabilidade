from fastapi import FastAPI, UploadFile, File, HTTPException
import os
from modelos import PerfilProfissional, CertificadoOuCurso

app = FastAPI(
    title="API de Empregabilidade e Agentes Inteligentes",
    version="1.0.0",
)

# Perfil para simulação 
perfil_usuario = PerfilProfissional(
    nome_completo="Alex Roberto Alves Caitete",
    cargo_desejado="Desenvolvedor Full Stack",
    competencias_tecnicas=["Python", "JavaScript", "React", "Node.js"],
    experiencias=[
        "Desenvolvedor Full Stack na Empresa XYZ (2020 - Presente)",
        "Estagiário de Desenvolvimento Web na Empresa ABC (2018 - 2020)"
    ],
    cursos_e_certificados=[]
)

DIRETORIO_UPLOADS = "uploads"
os.makedirs(DIRETORIO_UPLOADS, exist_ok=True)

@app.post("/perfil/upload-certificado", response_model=PerfilProfissional)
async def fazer_upload_certificado(
    titulo_curso: str,
    instituicao: str,
    arquivo: UploadFile = File(...)
):
    """
    Recebe um arquivo de certificado (PDF ou imagem), salva no disco 
    e atualiza automaticamente o perfil profissional do usuário.
    """
    try:
        caminho_arquivo = os.path.join(DIRETORIO_UPLOADS, arquivo.filename)

        content = await arquivo.read()
        with open(caminho_arquivo, "wb") as f:
            f.write(content)

        novas_tecnologias = ["Arquitetura orientada a eventos", "Microsserviços", "Docker", "Kubernetes"]

        novo_certificado = CertificadoOuCurso(
            titulo=titulo_curso,
            instituicao=instituicao,
            tecnologias_adquiridas=novas_tecnologias,
            data_conclusao="2026-10"
        )

        perfil_usuario.cursos_e_certificados.append(novo_certificado)
        for tech in novas_tecnologias:
            if tech not in perfil_usuario.competencias_tecnicas:
                perfil_usuario.competencias_tecnicas.append(tech)

        return perfil_usuario

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar o arquivo: {str(e)}")

@app.get("/perfil", response_model=PerfilProfissional)
async def obter_perfil():
    """Retorna o perfil profissional atualizado."""
    return perfil_usuario