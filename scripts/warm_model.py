"""
Pre-warm and download fastembed ONNX model at build time.
Prevents cold-start network downloads at runtime on Render.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastembed import TextEmbedding
from app.config import EMBEDDING_MODEL, MODEL_CACHE_DIR

def warm_model():
    print(f"[Build] Downloading and caching {EMBEDDING_MODEL} to {MODEL_CACHE_DIR}...")
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
    
    # Initialize TextEmbedding with target cache directory and single thread
    model = TextEmbedding(
        model_name=EMBEDDING_MODEL,
        cache_dir=MODEL_CACHE_DIR,
        threads=1
    )
    
    # Run dummy embedding to ensure ONNX model and tokenizer are fully downloaded and cached
    test_emb = list(model.embed(["Athenaeum Library Policy Assistant warmup query"]))
    print(f"[Build] Model pre-warm successful. Embedded test shape: {test_emb[0].shape}")

if __name__ == "__main__":
    warm_model()
