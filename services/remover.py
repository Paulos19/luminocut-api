import io
import time
import gc
from typing import Dict, Any, Tuple
from PIL import Image
import rembg

# Modelos suportados de alta performance e consumo de RAM contido (<400MB)
SUPPORTED_MODELS = {
    "isnet-anime": "ISNet Anime & Arte (Perfeito para ilustrações, capuzes, roupas claras e traços 2D/3D)",
    "u2net_human_seg": "U2Net Human Seg (Alta precisão para retratos, pessoas, cabelos finos e fotos reais)",
    "isnet-general-use": "ISNet Geral (Alta precisão para objetos, e-commerce e produtos)",
    "u2net": "U2Net Padrão (Segmentação fotográfica clássica)",
    "silueta": "Silueta (Leve e ultra-rápido para testes instantâneos)"
}

# Alias para evitar OOM crash no container Docker com 1GB/2GB de RAM:
# birefnet-general tem ~1GB de pesos ONNX e aloca >3.5GB de RAM, gerando SIGKILL imediato.
# Mapeamos birefnet-general automaticamente para u2net_human_seg (176MB)
MODEL_ALIASES = {
    "birefnet-general": "u2net_human_seg",
    "birefnet-general-lite": "u2net_human_seg",
    "birefnet": "u2net_human_seg",
}

# Cache de sessão único: mantém apenas 1 modelo na RAM por vez para economizar memória
_SESSIONS: Dict[str, Any] = {}
MAX_CACHED_SESSIONS = 1
MAX_INFERENCE_DIM = 2048  # Dimensão máxima segura para inferência em CPU (evita pico de RAM em fotos 4K/8K)

def get_session(model_name: str = "isnet-anime") -> Any:
    """Retorna uma sessão do modelo rembg em cache ou inicializa uma nova, limpando sessões anteriores."""
    actual_model = MODEL_ALIASES.get(model_name, model_name)
    if actual_model not in SUPPORTED_MODELS:
        actual_model = "isnet-anime"
    
    if actual_model not in _SESSIONS:
        if len(_SESSIONS) >= MAX_CACHED_SESSIONS:
            print(f"[REMOVER] Descarregando modelos antigos {list(_SESSIONS.keys())} da RAM...")
            _SESSIONS.clear()
            gc.collect()
            
        print(f"[REMOVER] Carregando modelo ONNX: {actual_model}...")
        _SESSIONS[actual_model] = rembg.new_session(actual_model)
        print(f"[REMOVER] Modelo {actual_model} carregado com sucesso!")
        
    return _SESSIONS[actual_model]

def remove_background(
    image_bytes: bytes,
    model_name: str = "isnet-anime",
    alpha_matting: bool = False,
    af_threshold: int = 240,
    ab_threshold: int = 10,
    a_erode: int = 10,
    only_mask: bool = False
) -> Tuple[bytes, dict]:
    """
    Remove o fundo da imagem fornecida em bytes com proteção de memória OOM e restauração full-res.
    """
    start_time = time.perf_counter()
    actual_model = MODEL_ALIASES.get(model_name, model_name)
    
    session = get_session(actual_model)
    
    # 1. Carregar imagem original e checar dimensões
    with Image.open(io.BytesIO(image_bytes)) as img_obj:
        orig_img = img_obj.convert("RGBA")
        orig_w, orig_h = orig_img.size
        
    needs_downscale = max(orig_w, orig_h) > MAX_INFERENCE_DIM
    if needs_downscale:
        scale = MAX_INFERENCE_DIM / max(orig_w, orig_h)
        target_w = max(1, int(orig_w * scale))
        target_h = max(1, int(orig_h * scale))
        resized_img = orig_img.resize((target_w, target_h), Image.Resampling.BILINEAR)
        buf = io.BytesIO()
        resized_img.save(buf, format="PNG")
        inference_bytes = buf.getvalue()
    else:
        inference_bytes = image_bytes
        
    try:
        # Processamento pelo rembg
        processed_bytes = rembg.remove(
            inference_bytes,
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=af_threshold,
            alpha_matting_background_threshold=ab_threshold,
            alpha_matting_erode_size=a_erode,
            only_mask=only_mask
        )
        
        # Se foi redimensionado, restaurar resolução nativa aplicando a máscara sobre o original
        if needs_downscale:
            with Image.open(io.BytesIO(processed_bytes)) as proc_img:
                if only_mask:
                    mask = proc_img.convert("L").resize((orig_w, orig_h), Image.Resampling.LANCZOS)
                    out_buf = io.BytesIO()
                    mask.save(out_buf, format="PNG")
                    output_bytes = out_buf.getvalue()
                else:
                    proc_rgba = proc_img.convert("RGBA")
                    alpha_mask = proc_rgba.split()[3].resize((orig_w, orig_h), Image.Resampling.LANCZOS)
                    final_img = orig_img.copy()
                    final_img.putalpha(alpha_mask)
                    out_buf = io.BytesIO()
                    final_img.save(out_buf, format="PNG", optimize=True)
                    output_bytes = out_buf.getvalue()
        else:
            output_bytes = processed_bytes
            
    finally:
        # Forçar coleta de lixo após inferência para evitar acumulação de tensores
        gc.collect()

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    metrics = {
        "execution_time_ms": elapsed_ms,
        "width": orig_w,
        "height": orig_h,
        "model_used": actual_model,
        "requested_model": model_name,
        "alpha_matting": alpha_matting
    }
    
    return output_bytes, metrics
