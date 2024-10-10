#  transformers
from transformers import AutoTokenizer, AutoModelForCausalLM

#  tokenizer
tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2")

#  prompt )
prompt = "Purple is the best color because"

# prompt
input_ids = tokenizer.encode(prompt, return_tensors="pt")

#
output = model.generate(input_ids, max_length=15, num_return_sequences=1, pad_token_id=tokenizer.eos_token_id)

#
generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
print("Text Completion Response:\n" + generated_text + "\n")



#  prompt )2
prompt = "can i be data engineer what to learn  ?"

# prompt
input_ids = tokenizer.encode(prompt, return_tensors="pt")

#
output = model.generate(input_ids, max_length=15, num_return_sequences=1, pad_token_id=tokenizer.eos_token_id)

#
generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
print("Text Completion Response:\n" + generated_text + "\n")