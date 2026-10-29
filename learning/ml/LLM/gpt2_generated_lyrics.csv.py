import pandas as pd

# Create sample data
data = {
    "ID": [1, 2, 3, 4, 5],
    "Prompt": [
        "The sun is shining so bright",
        "Lonely nights and empty dreams",
        "Dancing under the moonlight",
        "Chasing the echoes of time",
        "Lost in a world of wonder"
    ],
    "Generated_Lyrics": [
        "The sun is shining so bright, spreading warmth through the sky. The birds sing in delight, as the day passes by.",
        "Lonely nights and empty dreams, drifting through silent streams. Stars fade, leaving me to chase lost beams.",
        "Dancing under the moonlight, shadows sway in the night. Hearts beat to the rhythm, lost in a moment of pure delight.",
        "Chasing the echoes of time, through mountains we climb. Memories drift away, like leaves in the autumn wind's rhyme.",
        "Lost in a world of wonder, where dreams and reality blend. Colors burst like thunder, as new adventures transcend."
    ]
}

# Convert to DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv('gpt2_generated_lyrics.csv', index=False)

print("Sample CSV file 'gpt2_generated_lyrics.csv' created successfully!")