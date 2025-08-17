import random
import pandas as pd
from datetime import date, timedelta

# ---- Data pools ----
GENRES = [
    {"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"},
    {"id": 16, "name": "Animation"}, {"id": 35, "name": "Comedy"},
    {"id": 80, "name": "Crime"}, {"id": 18, "name": "Drama"},
    {"id": 14, "name": "Fantasy"}, {"id": 36, "name": "History"},
    {"id": 27, "name": "Horror"}, {"id": 10402, "name": "Music"},
    {"id": 9648, "name": "Mystery"}, {"id": 10749, "name": "Romance"},
    {"id": 878, "name": "Science Fiction"}, {"id": 53, "name": "Thriller"},
    {"id": 10751, "name": "Family"}
]

ADJ = ["Silent","Dark","Golden","Hidden","Broken","Secret","Wild","Lost",
       "Crimson","Eternal","Fading","Neon","Iron","Silver","Emerald","Quantum"]
NOUN = ["Shadow","Promise","Empire","Echo","Code","Dream","City","River","Path",
        "Fire","Legacy","Kingdom","Mirror","Storm","Truth","Game","Voyage"]
ROLES = ["thief","soldier","detective","musician","scientist","teacher","pilot",
         "runner","wanderer","doctor","guardian","hacker","prince","princess"]
GOALS = ["save a city","find a lost friend","protect a secret",
         "reunite a family","escape the past","solve a mystery",
         "win freedom","change the future","survive the night",
         "stop a conspiracy","restore peace"]

LANGS = ["en","es","fr","de","it","ja","ko","hi"]

# ---- Helpers ----
def rand_date(start=date(1960,1,1), end=date(2022,12,31)):
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()

def pick_genres():
    k = random.randint(1, 2)
    chosen = random.sample(GENRES, k)
    return "[" + ", ".join(
        "{'id': " + str(g['id']) + ", 'name': '" + g['name'] + "'}" for g in chosen
    ) + "]"

def make_title(i):
    pattern = random.choice([
        "The {adj} {noun}", "{adj} {noun}", "{noun} of {noun2}"
    ])
    return pattern.format(adj=random.choice(ADJ),
                          noun=random.choice(NOUN),
                          noun2=random.choice(NOUN)) + f" {i}"

def make_overview():
    return f"A {random.choice(ROLES)} sets out to {random.choice(GOALS)}, facing challenges along the way."

# ---- Generator ----
def generate_movies(n=1000, path="../../data/movies_metadata.csv"):
    rows = []
    for i in range(1, n+1):
        rows.append({
            "id": i,
            "title": make_title(i),
            "vote_count": random.randint(200, 15000),
            "vote_average": round(random.uniform(5.0, 9.3), 1),
            "genres": pick_genres(),
            "overview": make_overview(),
            "release_date": rand_date(),
            "original_language": random.choice(LANGS)
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    print(f"✅ Generated {n} movies → {path}")

# ---- Run ----
if __name__ == "__main__":
    generate_movies()
