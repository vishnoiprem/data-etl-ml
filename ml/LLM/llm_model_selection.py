from transformers import pipeline, set_seed

# Initialize text generation pipeline with GPT-2 model
generator = pipeline('text-generation', model='gpt2')
# Ensure reproducibility for text generation
set_seed(1)

# Generate text based on a prompt for text completion
result = generator("Purple is the best color because", max_length=15, num_return_sequences=1, pad_token_id=generator.tokenizer.eos_token_id)
# Display the generated text
print("Text Completion Response:\n" + result[0]['generated_text'] + "\n")

# Ensure reproducibility for text generation
set_seed(1)

# Generate text based on a prompt for instruction following
test_result = generator("Write a poem about gravity", max_length=19, num_return_sequences=1, pad_token_id=generator.tokenizer.eos_token_id)
# Display the generated text
print("Instruction Following Response:\n" + test_result[0]['generated_text'])