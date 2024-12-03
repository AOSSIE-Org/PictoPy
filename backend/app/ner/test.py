import numpy as np
import onnxruntime
from transformers import AutoTokenizer, AutoConfig

# Run the ner_onnx.py to create the onnx model in the models folder
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