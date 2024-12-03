from transformers import AutoModelForTokenClassification
import torch

# Pre-trained model name
model_name = "dslim/bert-base-NER"
model_path = r'C:\Users\sanid\Downloads\gsoc_@pictopy\PictoPy\backend\app\models\bert-base-NER.onnx'

# Load the pre-trained model for token classification
model = AutoModelForTokenClassification.from_pretrained(model_name)

# Generate dummy inputs for the model with input_ids in the valid range
vocab_size = model.config.vocab_size  # 30522 for BERT-based models

# Ensure input_ids are within the model's vocab size range
inputs = {
    'input_ids': torch.randint(0, vocab_size, [1, 32], dtype=torch.long),  # Adjust range to model vocab size
    'attention_mask': torch.ones([1, 32], dtype=torch.long),
}

# Define symbolic names for dynamic axes
symbolic_names = {0: 'batch_size', 1: 'max_seq_len'}

# Export the model to ONNX format
torch.onnx.export(
    model,  # Model to export
    (inputs['input_ids'], inputs['attention_mask']),  # Model inputs
    model_path,  # Save path
    opset_version=14,  # ONNX opset version
    do_constant_folding=True,  # Optimization flag
    input_names=['input_ids', 'attention_mask'],  # Input names
    output_names=['logits'],  # Output names
    dynamic_axes={  # Define dynamic axes for variable input sizes
        'input_ids': symbolic_names,
        'attention_mask': symbolic_names,
        'logits': symbolic_names
    }
)

print(f"Model exported to {model_path}")