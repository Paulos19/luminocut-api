import io
import time
from typing import Dict, Any, Tuple
from PIL import Image
import rembg

# Cache de sessões de modelos para evitar recarregar da memória
_SESSIONS: Dict[str, Any] = {}

SUPPORTED_MODELS = {
    "isnet-anime": "ISNet Anime & Arte (Perfeito para ilustrações, capuzes, roupas claras e traços 2D/3D)",
    "birefnet-general": "BiRefNet General (Ultra HD 4K, cabelos finos e máxima resolução para fotos reais)",
    "isnet-general-use": "ISNet Geral (Alta precisão para objetos, e-commerce e produtos)",
    "u2net": "U2Net Padrão (Segmentação fotográfica clássica e rápida)",
    "silueta": "Silueta (Leve e ultra-rápido para testes instantâneos)"
}

def get_session(model_name: str = "isnet-anime") -> Any:
    """Retorna uma sessão do modelo rembg em cache ou inicializa uma nova."""
    if model_name not in SUPPORTED_MODELS:
        model_name = "isnet-anime"
    
    if model_name not in _SESSIONS:
        print(f"[REMOVER] Carregando modelo ONNX: {model_name}...")
        _SESSIONS[model_name] = rembg.new_session(model_name)
        print(f"[REMOVER] Modelo {model_name} carregado com sucesso!")
        
    return _SESSIONS[model_name]

def remove_background(
    image_bytes: bytes,
    model_name: str = "isnet-anime",
    alpha_matting: bool = False,
    af_threshold: int = 240,
    ab_threshold: int = 10,
    a_erode: int = 10,
    only_mask: bool = False
) -> tuple[bytes, dict]:
    """
    Remove o fundo da imagem fornecida em bytes.
    Retorna os bytes da imagem PNG resultante e métricas de execução.
    """
    start_time = time.perf_counter()
    
    session = get_session(model_name)
    
    # Processamento pelo rembg
    output_bytes = rembg.remove(
        image_bytes,
        session=session,
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=af_threshold,
        alpha_matting_background_threshold=ab_threshold,
        alpha_matting_erode_size=a_erode,
        only_mask=only_mask
    )
    
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    # Obter dimensões originais e finais
    with Image.open(io.BytesIO(image_bytes)) as original:
        width, height = original.size
        
    metrics = {
        "execution_time_ms": elapsed_ms,
        "width": width,
        "height": height,
        "model_used": model_name,
        "alpha_matting": alpha_matting
    }
    
    return output_bytes, metrics
