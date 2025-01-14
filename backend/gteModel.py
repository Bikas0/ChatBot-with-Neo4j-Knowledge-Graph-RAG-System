import os
from sentence_transformers import SentenceTransformer
def embedding_model_download(folder):
    # Save the SentenceTransformer model locally
    os.makedirs(folder, exist_ok=True)
    # Load the SentenceTransformer model
    sentence_model_name = "thenlper/gte-large"
    sentence_model = SentenceTransformer(sentence_model_name)
    sentence_model.save(folder)
    print(f"SentenceTransformer model saved to {folder}")

embedding_model_download("GeneralTextEmbeddingModel")