from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

def load_ner_pipeline():
    model_name = "uvacreate/bert-base-dutch-legal"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    return pipeline("ner", model=model, tokenizer=tokenizer, grouped_entities=True)
