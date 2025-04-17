from transformers import AutoTokenizer, AutoModel, pipeline
import torch

def load_legalbert_embedding_pipeline():
    """
    Laadt een Legal BERT pipeline voor Nederlandse en Engelse juridische teksten.
    Geeft embeddings terug voor semantische vergelijkingen.
    """
    model_name = "Gerwin/legal-bert-dutch-english"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    
    def embed(text):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
        # Neem gemiddelde over tokens (CLS-token is vaak minder stabiel)
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
        return embedding
    
    return embed
