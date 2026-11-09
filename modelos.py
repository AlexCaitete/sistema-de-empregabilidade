from pydantic import BaseModel, Field
from typing import List, Optional


class CertificadoOuCurso(BaseModel):
    titulo: str = Field(..., description="Título do curso ou certificado concluído")
    instituicao: str = Field(..., description="Nome da instituição emissora")
    tecnologias_adquiridas: List[str] = Field(
        default_factory=list,
        description="Lista de tecnologias, ferramentas ou competências abordadas no curso"
    )
    data_conclusao: Optional[str] = Field(
        default=None,
        description="Data de conclusão ou emissão do certificado"
    )


class PerfilProfissional(BaseModel):
    nome_completo: str = Field(..., description="Nome completo do profissional")
    cargo_desejado: str = Field(..., description="Cargo ou objetivo profissional desejado")
    competencias_tecnicas: List[str] = Field(
        default_factory=list,
        description="Lista de habilidades e tecnologias que o profissional domina"
    )
    experiencias: List[str] = Field(
        default_factory=list,
        description="Histórico de experiências profissionais ou projetos relevantes"
    )
    cursos_e_certificados: List[CertificadoOuCurso] = Field(
        default_factory=list,
        description="Lista de cursos e certificados concluídos"
    )


class VagaEmprego(BaseModel):
    id: Optional[str] = Field(default=None, description="Identificador único da vaga")
    titulo: str = Field(..., description="Título do cargo da vaga")
    empresa: str = Field(..., description="Nome da empresa contratante")
    requisitos: List[str] = Field(
        default_factory=list,
        description="Lista de tecnologias e requisitos pedidos na vaga"
    )
    descricao: str = Field(..., description="Descrição detalhada das atividades e responsabilidades")
    localizacao: Optional[str] = Field(default="Remoto", description="Localidade ou modelo de trabalho")
    nivel: Optional[str] = Field(default="Júnior", description="Nível de senioridade da vaga")


class AnaliseCompatibilidade(BaseModel):
    vaga_titulo: str = Field(..., description="Título da vaga analisada")
    empresa: str = Field(..., description="Empresa da vaga analisada")
    percentual_compatibilidade: int = Field(
        ...,
        ge=0,
        le=100,
        description="Grau de compatibilidade entre o perfil e a vaga (0 a 100)"
    )
    competencias_em_comum: List[str] = Field(
        default_factory=list,
        description="Competências exigidas na vaga que o candidato já possui"
    )
    competencias_faltantes: List[str] = Field(
        default_factory=list,
        description="Requisitos da vaga que ainda não constam no perfil do candidato"
    )
    pontos_fortes: List[str] = Field(
        default_factory=list,
        description="Destaques do perfil do candidato para esta vaga"
    )
    recomendacoes_estudo: List[str] = Field(
        default_factory=list,
        description="Sugestões práticas de estudo para cobrir os requisitos faltantes"
    )
    parecer_geral: str = Field(..., description="Resumo analítico sobre a aderência do candidato à vaga")


class CurriculoAdaptado(BaseModel):
    perfil_base: PerfilProfissional = Field(..., description="Perfil original utilizado como base")
    vaga_alvo: VagaEmprego = Field(..., description="Vaga para a qual o currículo foi adaptado")
    resumo_profissional_otimizado: str = Field(
        ...,
        description="Resumo profissional focado nas palavras-chave e objetivos da vaga"
    )
    competencias_destacadas: List[str] = Field(
        default_factory=list,
        description="Competências do perfil priorizadas para esta vaga"
    )
    experiencias_adaptadas: List[str] = Field(
        default_factory=list,
        description="Experiências descritas dando ênfase aos requisitos da vaga"
    )
    conteudo_otimizado: str = Field(
        ...,
        description="Currículo completo formatado em Markdown pronto para exportação"
    )


class RespostaIngestaoCertificado(BaseModel):
    mensagem: str
    certificado_extraido: CertificadoOuCurso
    novas_competencias_adicionadas: List[str]
    perfil_atualizado: PerfilProfissional
