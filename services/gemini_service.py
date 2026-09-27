import os
import json
import base64
from typing import Optional, Dict, Any
from google import genai
from google.genai import types

def get_gemini_client() -> Optional[genai.Client]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[GEMINI] Erro ao instanciar cliente Gemini: {e}")
        return None

def analyze_and_suggest_backgrounds(image_bytes: bytes, mime_type: str = "image/png") -> Dict[str, Any]:
    """
    Analisa a imagem e sugere ideias de fundos, paletas de cores harmoniosas e tags com Gemini.
    """
    client = get_gemini_client()
    if not client:
        return {
            "error": "GEMINI_API_KEY não configurada no .env",
            "subject": "Objeto ou Pessoa",
            "palettes": ["#0f172a", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#ffffff"],
            "ideas": [
                {"title": "Estúdio Minimalista", "description": "Fundo limpo com gradiente suave e iluminação suave de estúdio.", "color": "#f8fafc"},
                {"title": "Escritório Moderno", "description": "Ambiente corporativo contemporâneo com desfoque de profundidade.", "color": "#1e293b"},
                {"title": "Luz Dourada / Sunset", "description": "Iluminação quente e acolhedora com tons dourados e alaranjados.", "color": "#fbbf24"},
                {"title": "Dark Neon / Cyberpunk", "description": "Tons escuros com detalhes em azul e roxo fluorescente.", "color": "#090d16"}
            ]
        }

    try:
        prompt = """
Você é um diretor de arte e fotógrafo de estúdio de classe mundial.
Analise este sujeito da foto (cujo fundo será removido) e responda ESTRITAMENTE em formato JSON no seguinte formato:
{
  "subject": "Descrição curta do sujeito (ex: 'Relógio esportivo preto' ou 'Mulher em traje executivo')",
  "category": "produto | retrato | veiculo | animal | outro",
  "recommended_palettes": ["#hex1", "#hex2", "#hex3", "#hex4", "#hex5", "#hex6"],
  "ideas": [
    {
      "title": "Nome do Cenário (ex: Estúdio Comercial Clean)",
      "description": "Explicação curta do motivo pelo qual combina com o sujeito",
      "style": "minimalist | studio | luxury | outdoor | neon",
      "color": "#hex_principal_ou_fundo"
    },
    {
      "title": "Nome do Cenário 2",
      "description": "Explicação curta",
      "style": "minimalist | studio | luxury | outdoor | neon",
      "color": "#hex"
    },
    {
      "title": "Nome do Cenário 3",
      "description": "Explicação curta",
      "style": "minimalist | studio | luxury | outdoor | neon",
      "color": "#hex"
    },
    {
      "title": "Nome do Cenário 4",
      "description": "Explicação curta",
      "style": "minimalist | studio | luxury | outdoor | neon",
      "color": "#hex"
    }
  ]
}
Responda APENAS o JSON válido, sem crases de markdown e sem texto antes ou depois.
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                prompt
            ]
        )
        
        raw_text = response.text.strip()
        # Limpar caso tenha retornado com bloco markdown ```json ... ```
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        data = json.loads(raw_text)
        return data

    except Exception as e:
        print(f"[GEMINI] Erro na análise: {e}")
        return {
            "error": str(e),
            "subject": "Sujeito detectado",
            "recommended_palettes": ["#ffffff", "#000000", "#3b82f6", "#10b981", "#8b5cf6", "#f59e0b"],
            "ideas": [
                {"title": "Estúdio Fotográfico", "description": "Fundo neutro com iluminação suave", "color": "#f1f5f9"},
                {"title": "Gradiente Noturno", "description": "Contraste moderno e elegante", "color": "#0f172a"},
                {"title": "Vibrante Pop", "description": "Destaque e energia comercial", "color": "#3b82f6"}
            ]
        }
