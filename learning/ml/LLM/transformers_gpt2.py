from transformers import pipeline, set_seed

# Initialize text generation pipeline with GPT-2 model
generator = pipeline('text-generation', model='gpt2')
# Ensure reproducibility for text generation
set_seed(42)

# Generate text based on a prompt
result = generator("Hello, I am a large language model,",
                   max_length=20,
                   num_return_sequences=1,
                   pad_token_id=generator.tokenizer.eos_token_id)

# Display the generated text
print("GPT-2 Response:\n" + result[0]['generated_text'] + "\n")