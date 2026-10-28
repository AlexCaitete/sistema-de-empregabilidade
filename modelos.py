from pydantic import BaseModel, Field
from typing import List, Optional

class CertificadoOuCurso(BaseModel):
    titulo: str
    instituicao: str
    tecnologias_adquiridas: List[str]
    data_conclusao: Optional[str] = None

class PerfilProfissional(BaseModel):  # <-- Aqui: BaseModel com B maiúsculo
    nome_completo: str
    cargo_desejado: str
    competencias_tecnicas: List[str]
    experiencias: List[str]
    cursos_e_certificados: List[CertificadoOuCurso]