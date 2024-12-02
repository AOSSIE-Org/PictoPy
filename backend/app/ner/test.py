from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline, AutoConfig
import onnxruntime
from difflib import SequenceMatcher
import numpy as np

# to perform ner on the query and the caption to find similar keys in ner-query dictionary and the ner-caption dictionary
# without onnx
def simple_ner():
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

# to perform ner using the onnx model and to do comparision based on the onnx model
# to run the function complex_ner first run the ner_onnx.py file to create the onnx model

def complex_ner():
    model_path = r'C:\Users\sanid\Downloads\gsoc_@pictopy\PictoPy\backend\app\models\bert-base-NER.onnx'
    session = onnxruntime.InferenceSession(model_path)

    tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
    config = AutoConfig.from_pretrained("dslim/bert-base-NER")
    id2label = config.id2label


    def prepare_inputs(text, tokenizer, max_seq_length=32):
        encoding = tokenizer.encode_plus(
            text,
            max_length=max_seq_length,
            truncation=True,
            padding="max_length",
            return_tensors="np"
        )
        return {
            "input_ids": encoding["input_ids"].astype(np.int64),
            "attention_mask": encoding["attention_mask"].astype(np.int64),
        }


    def combine_subwords(tokens, labels):
        combined_tokens = []
        combined_labels = []
        current_word = ""
        current_label = None

        for token, label in zip(tokens, labels):
            if token.startswith("##"):
                current_word += token[2:]
            else:
                if current_word:
                    combined_tokens.append(current_word)
                    combined_labels.append(current_label)
                current_word = token
                current_label = label

        if current_word:
            combined_tokens.append(current_word)
            combined_labels.append(current_label)

        return combined_tokens, combined_labels


    def perform_ner(text, session, tokenizer, id2label):
        inputs = prepare_inputs(text, tokenizer)
        
        outputs = session.run(
            None,
            {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
            },
        )

        logits = outputs[0]
        predictions = np.argmax(logits, axis=-1)

        tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])

        filtered_tokens = []
        filtered_labels = []

        for token, pred in zip(tokens, predictions[0]):
            label = id2label[pred]
            if token not in ["[PAD]", "[CLS]", "[SEP]"]:
                filtered_tokens.append(token)
                filtered_labels.append(label)

        combined_tokens, combined_labels = combine_subwords(filtered_tokens, filtered_labels)
        return list(zip(combined_tokens, combined_labels))


    def compare_ner_results(text1, text2, session, tokenizer, id2label):
        ner_result1 = perform_ner(text1, session, tokenizer, id2label)
        ner_result2 = perform_ner(text2, session, tokenizer, id2label)

        ner_dict1 = {token: label for token, label in ner_result1 if label != 'O'}
        ner_dict2 = {token: label for token, label in ner_result2 if label != 'O'}

        print("Original NER Results:")
        for token, label in ner_result1:
            print(f"{token:15} -> {label}")
        print(ner_dict1)

        print("Comparison NER Results:")
        for token, label in ner_result2:
            print(f"{token:15} -> {label}")
        print(ner_dict2)

        common_entities = set(ner_dict1.keys()) & set(ner_dict2.keys())
        print("\nCommon Entities:", common_entities)

    text1 = "Shalin is from New York and employed at Tesla."
    text2 = "Shalin and Robert work at Tesla."

    compare_ner_results(text1, text2, session, tokenizer, id2label)



complex_ner()    