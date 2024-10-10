from rouge import Rouge
import pandas as pd

# Import the lyrics dataset, which only contains the generated lyrics
lyrics_df = pd.read_csv('gpt2_generated_lyrics.csv')

# Instantiate the Rouge class
rouge = Rouge()

# Print examples of generated lyrics to understand what was produced
print("Generated:\n" + lyrics_df['Generated_Lyrics'][0] + "\n")

# Since there is no 'Expected_Lyrics', we cannot compute ROUGE scores.
# Instead, we can focus on other analyses or generate evaluation metrics based on criteria that are available.

# Uncomment below if 'Expected_Lyrics' column exists
# scores = rouge.get_scores(lyrics_df['Generated_Lyrics'],
#                           lyrics_df['Expected_Lyrics'], avg=True)

# If you want to add dummy comparisons, you can use the generated lyrics as both generated and expected
# scores = rouge.get_scores(lyrics_df['Generated_Lyrics'], lyrics_df['Generated_Lyrics'], avg=True)

# Uncomment to print ROUGE scores if computed
# print("{:<10} {:<15} {:<15} {:<15}".format('', 'Recall', 'Precision', 'F-1 Score'))
# print("{:<10} {:<15} {:<15} {:<15}".format('ROUGE-1',
#                                            round(scores['rouge-1']['r'], 4),
#                                            round(scores['rouge-1']['p'], 4),
#                                            round(scores['rouge-1']['f'], 4)))

# print("{:<10} {:<15} {:<15} {:<15}".format('ROUGE-L',
#                                            round(scores['rouge-l']['r'], 4),
#                                            round(scores['rouge-l']['p'], 4),
#                                            round(scores['rouge-l']['f'], 4)))