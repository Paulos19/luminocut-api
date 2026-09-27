# Luminocut API - Backend (FastAPI + ONNX Runtime)

Microsserviço de inteligência artificial de alta performance para recorte de fundo de imagens e direção de arte assistida com Google Gemini.

## 🚀 Modelos Suportados
- **`isnet-anime`** (Padrão): Otimizado para ilustrações, capuzes brancos e traços 2D/3D sem apagar roupas.
- **`birefnet-general`**: Ultra HD 4K para fotos reais, retratos e cabelos finos.
- **`isnet-general-use`**: E-commerce, objetos e produtos.
- **`u2net`**: Segmentação clássica de fotos.
- **`silueta`**: Execução instantânea e ultraleve.

## 📦 Deploy no Easypanel
1. Crie um novo serviço no Easypanel a partir deste repositório GitHub.
2. Selecione o tipo de build: **Dockerfile**.
3. Adicione as variáveis de ambiente:
   - `GEMINI_API_KEY`: Sua chave de API do Google Gemini.
   - `CORS_ORIGINS`: `*` ou a URL do seu frontend (ex: `https://luminocut.seudominio.com`).
   - `PORT`: `8000`.
4. Porta da aplicação no Easypanel: `8000`.
5. (Opcional) Volume persistente para cache de modelos ONNX:
   - Destino no container: `/root/.u2net`
