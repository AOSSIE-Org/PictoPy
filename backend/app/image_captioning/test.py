# to perform ner on the query and the caption to find similar keys in ner-query dictionary and the ner-caption dictionary


from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

model_name = "dslim/bert-base-NER"  
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)


ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, grouped_entities=True)
query = "Elon Musk was seen in Austin, Texas, during a SpaceX event."
caption = "Show me pictures of Elon Musk in Texas."
query_entities = ner_pipeline(query)
caption_entities = ner_pipeline(caption)


query_extracted = {entity['word']: entity['entity_group'] for entity in query_entities}
caption_extracted = {entity['word']: entity['entity_group'] for entity in caption_entities}

print("Query Entities:", query_extracted)
print("Caption Entities:", caption_extracted)

def merge_entities(query_extracted, caption_extracted):
    merged = {}
    skip = False
    keys = list(caption_extracted.keys())

    for i, key in enumerate(keys):
        if skip:
            skip = False
            continue

        if i < len(keys) - 1:

            combined_entity = " ".join([key, keys[i + 1]])

            if combined_entity in query_extracted and combined_entity not in merged:
                merged[combined_entity] = query_extracted[combined_entity]
                skip = True  
            else:
                merged[key] = caption_extracted[key]
        else:
            merged[key] = caption_extracted[key]

    return merged        

merged_caption = merge_entities(query_extracted, caption_extracted)
merged_query = merge_entities(caption_extracted, query_extracted)
common_entities = set(merged_query.keys()) & set(merged_caption.keys())

print("Common Entities:", common_entities)
print("length:", len(common_entities))