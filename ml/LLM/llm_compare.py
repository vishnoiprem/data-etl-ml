from transformers import pipeline
from rouge import Rouge

# Define the German proverb and the correct translation
german_proverb = "Anfangen ist leicht, beharren eine Kunst"
correct_translation = "To begin is easy, to persist is an art."

# Initialize the translation pipeline
pipe = pipeline("text2text-generation", model="bigscience/mt0-small")

# Define the translation prompt
prompt = "Translate to English: Anfangen ist leicht, beharren eine Kunst."

# Generate the translation using the pipeline
generated_translation = pipe(prompt, max_length=50)[0]['generated_text']
print(f"Generated Translation: {generated_translation}")

# Initialize ROUGE for evaluation
rouge = Rouge()

# Calculate ROUGE scores between the generated translation and the correct translation
scores = rouge.get_scores(generated_translation, correct_translation, avg=True)

# Display the ROUGE scores
print("\nROUGE Scores:")
for metric, values in scores.items():
    print(f"{metric}: Precision = {values['p']:.2f}, Recall = {values['r']:.2f}, F1-Score = {values['f']:.2f}")