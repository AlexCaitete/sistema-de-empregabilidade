import os
import traceback
from dotenv import load_dotenv
from google import genai
from google.genai import types
from modelos import PerfilProfissional

load_dotenv()

class AgenteAnalista:
    """
    Agente Analista: Responsável por processar o texto bruto de documentos
    e extrair dados estruturados utilizando Inteligência Artificial (Gemini).
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("A variável de ambiente GEMINI_API_KEY não foi encontrada.")
        self.client = genai.Client(api_key=api_key)

    def analisar_texto_para_perfil(self, texto_bruto: str) -> PerfilProfissional:
        if not texto_bruto or len(texto_bruto.strip()) < 10:
            raise ValueError("O texto extraído do documento está vazio ou é insuficiente para análise.")

        prompt = f"""
        Analisa o seguinte texto extraído de um currículo ou documento profissional
        e extrai as informações estruturadas correspondentes com base no schema definido:

        TEXTO BRUTO:
        {texto_bruto}
        """

        try:
            # Utilizando o modelo exigido pela API e types.GenerateContentConfig para tipagem correta
            response = self.client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PerfilProfissional,
                    temperature=0.1,
                ),
            )

            if not response.parsed:
                raise ValueError(f"A IA não conseguiu estruturar o documento. Resposta bruta: {getattr(response, 'text', 'Sem texto')}")

            if isinstance(response.parsed, PerfilProfissional):
                return response.parsed

            return PerfilProfissional.model_validate(response.parsed)

        except Exception as e:
            print("--- ERRO CRÍTICO NO AGENTE ANALISTA ---")
            traceback.print_exc()
            raise e
