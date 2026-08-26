from sentence_transformers import SentenceTransformer
import open_clip
import torch
from PIL import Image
import numpy as np

# Load once at startup — never per-request
text_model = SentenceTransformer("all-mpnet-base-v2")

clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32", pretrained="openai"
)
clip_tokenizer = open_clip.get_tokenizer("ViT-B-32")
clip_model.eval()


def embed_text(text: str) -> np.ndarray:
    """MPNet embedding — used for text-to-text comparison. Best semantic signal for pure text."""
    return text_model.encode(text, normalize_embeddings=True)


def embed_text_clip(text: str) -> np.ndarray:
    """CLIP's own text encoder — lands in the SAME space as CLIP image embeddings.
    Used only when one side has a photo and the other doesn't."""
    with torch.no_grad():
        tokens = clip_tokenizer([text])
        features = clip_model.encode_text(tokens)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.squeeze(0).numpy()


def embed_image(image: Image.Image) -> np.ndarray:
    """CLIP image embedding."""
    with torch.no_grad():
        tensor = clip_preprocess(image).unsqueeze(0)
        features = clip_model.encode_image(tensor)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.squeeze(0).numpy()
