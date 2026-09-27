import os
import sys
import base64
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from dotenv import load_dotenv

# Carregar variáveis de ambiente (.env local ou na raiz)
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent

if (current_dir / ".env").exists():
    load_dotenv(dotenv_path=current_dir / ".env")
elif (parent_dir / ".env").exists():
    load_dotenv(dotenv_path=parent_dir / ".env")
else:
    load_dotenv()

# Suporte a imports diretos e como pacote backend
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from services.remover import remove_background, SUPPORTED_MODELS
    from services.gemini_service import analyze_and_suggest_backgrounds
except ImportError:
    from backend.services.remover import remove_background, SUPPORTED_MODELS
    from backend.services.gemini_service import analyze_and_suggest_backgrounds

app = FastAPI(
    title="Luminocut API",
    description="API de remoção de fundo com IA e assistência estética via Gemini",
    version="1.0.0"
)

# Habilitar CORS para o frontend Next.js (Local e Produção)
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
configured_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

# Lista de origens explicitamente confiáveis
known_origins = [
    "https://luminocut.phdev.top",
    "http://luminocut.phdev.top",
    "https://luminocut.phdev.com",
    "http://luminocut.phdev.com",
    "https://luminocut-api.phdev.top",
    "http://luminocut-api.phdev.top",
    "https://luminocut-api.phdev.com",
    "http://luminocut-api.phdev.com",
    "https://services-luminocut-backend.khdya3.easypanel.host",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
all_allowed_origins = list(set(configured_origins + known_origins))

# Starlette CORSMiddleware: Quando allow_credentials=True, wildcard "*" só funciona via regex
if "*" in configured_origins or cors_origins_raw == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=all_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

@app.get("/")
def root():
    return {
        "service": "Luminocut API",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "Luminocut API",
        "has_gemini": bool(os.getenv("GEMINI_API_KEY")),
        "models": list(SUPPORTED_MODELS.keys())
    }

@app.get("/api/models")
def get_available_models():
    return {
        "models": [
            {"id": model_id, "name": name, "is_default": model_id == "isnet-anime"}
            for model_id, name in SUPPORTED_MODELS.items()
        ]
    }

@app.post("/api/remove-bg")
async def remove_bg_endpoint(
    file: UploadFile = File(...),
    model: str = Form("isnet-anime"),
    alpha_matting: bool = Form(False),
    af_threshold: int = Form(240),
    ab_threshold: int = Form(10),
    a_erode: int = Form(10),
    only_mask: bool = Form(False),
    return_base64: bool = Form(True)
):
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Arquivo de imagem vazio.")

        output_bytes, metrics = remove_background(
            image_bytes=image_bytes,
            model_name=model,
            alpha_matting=alpha_matting,
            af_threshold=af_threshold,
            ab_threshold=ab_threshold,
            a_erode=a_erode,
            only_mask=only_mask
        )

        if return_base64:
            b64_str = base64.b64encode(output_bytes).decode("utf-8")
            data_url = f"data:image/png;base64,{b64_str}"
            return JSONResponse({
                "success": True,
                "data_url": data_url,
                "metrics": metrics
            })
        else:
            return Response(
                content=output_bytes,
                media_type="image/png",
                headers={
                    "X-Execution-Time-Ms": str(metrics["execution_time_ms"]),
                    "X-Model-Used": metrics["model_used"]
                }
            )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}")

@app.post("/api/gemini/suggest-backgrounds")
async def suggest_backgrounds_endpoint(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Arquivo de imagem vazio.")

        mime_type = file.content_type or "image/png"
        result = analyze_and_suggest_backgrounds(image_bytes, mime_type=mime_type)
        return JSONResponse(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise Gemini: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
