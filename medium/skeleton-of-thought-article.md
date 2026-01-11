# Skeleton-of-Thought Prompting: How to Make AI Respond 2x Faster [2025]

*The secret technique that outlines first, then fills in details — all at once*

---

## Why Is ChatGPT So Slow Sometimes?

Have you ever asked ChatGPT a question and watched it type... word... by... word... for what felt like forever?

I have. Especially when asking complex questions that need multiple points.

Here's the problem: **Normal AI generates answers sequentially.** Point 1, then Point 2, then Point 3. One after another. Like writing an essay from start to finish without an outline.

But what if AI could work like a team of writers? One person writes the outline, then multiple people fill in different sections *at the same time*?

That's exactly what **Skeleton-of-Thought (SoT)** does.

---

## What is Skeleton-of-Thought?

Let me make this simple:

```
SKELETON-OF-THOUGHT = Outline first + Fill in details in parallel
```

Think of it like building a house:

| Traditional Approach | Skeleton-of-Thought |
|---------------------|---------------------|
| Build room 1 completely | Draw the blueprint first |
| Then build room 2 | Then build ALL rooms at the same time |
| Then build room 3 | Much faster! |
| Slow and sequential | Fast and parallel |

---

## How Does It Work?

SoT has two phases:

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: SKELETON                        │
│                    (Create the outline)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  Question: "What are effective        │
        │  strategies for conflict resolution?" │
        └───────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────┐
                │     SKELETON:     │
                │  1. Active listen │
                │  2. Identify root │
                │  3. Find middle   │
                │  4. Set boundaries│
                │  5. Follow up     │
                └───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 2: EXPAND                          │
│              (Fill in ALL points at once)                   │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  Point 1  │   │  Point 2  │   │  Point 3  │
    │ (expand)  │   │ (expand)  │   │ (expand)  │
    └───────────┘   └───────────┘   └───────────┘
            │               │               │
            └───────────────┼───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ FINAL ANSWER  │
                    │  (combined)   │
                    └───────────────┘
```

---

## Normal AI vs. Skeleton-of-Thought

Here's the difference visually:

### Normal Decoding (Sequential = Slow)

```
Question: "What are conflict resolution strategies?"

AI thinks: "Let me answer point by point..."

1. Active listening involves fully concentrating on...
   [wait for completion]
   
2. Identify issues. Look into the root causes of...
   [wait for completion]
   
3. Compromise. Look for a middle ground...
   [wait for completion]

Total time: 30 seconds ⏱️
```

### Skeleton-of-Thought (Parallel = Fast)

```
Question: "What are conflict resolution strategies?"

STEP 1 - AI creates skeleton:
  1. Active listening
  2. Identify issues  
  3. Compromise

STEP 2 - AI expands ALL points simultaneously:
  [Point 1 expanding...] + [Point 2 expanding...] + [Point 3 expanding...]
  
STEP 3 - Combine results

Total time: 15 seconds ⏱️ (2x faster!)
```

---

## The Two Prompts You Need

SoT uses two specific prompts. Let me show you exactly what they are.

### Prompt 1: The Skeleton Generator

```
You're an organizer responsible for only giving the skeleton 
(not the full content) for answering the question. 

Provide the skeleton in a list of points (numbered 1., 2., 3., etc.) 
to answer the question. 

Instead of writing a full sentence, each skeleton point should be 
very short with only 3 to 5 words. 

Generally, the skeleton should have 3 to 10 points.

Question: {YOUR_QUESTION}

Skeleton:
```

### Prompt 2: The Point Expander

```
You're responsible for continuing the writing of one and only one 
point in the overall answer to the following question.

Question: {YOUR_QUESTION}

The skeleton of the answer is:
{SKELETON}

Continue and only continue the writing of point {POINT_NUMBER}. 
Write it very shortly in 1 to 2 sentences and do not continue 
with other points!
```

---

## Real Example: Step by Step

Let me walk you through a complete example.

### Question:
> "What are the benefits of remote work?"

### Step 1: Generate the Skeleton

**Prompt:**
```
You're an organizer responsible for only giving the skeleton 
(not the full content) for answering the question.

Provide the skeleton in a list of points (numbered 1., 2., 3., etc.)
Each point should be very short with only 3 to 5 words.
The skeleton should have 3 to 10 points.

Question: What are the benefits of remote work?

Skeleton:
```

**AI Response:**
```
1. Flexible work schedule
2. No commute time
3. Better work-life balance
4. Cost savings
5. Increased productivity
6. Wider talent pool
```

### Step 2: Expand Each Point (In Parallel!)

Now we send 6 separate requests — one for each point — *at the same time*.

**For Point 1:**
```
You're responsible for continuing the writing of one point.

Question: What are the benefits of remote work?

The skeleton of the answer is:
1. Flexible work schedule
2. No commute time
3. Better work-life balance
4. Cost savings
5. Increased productivity
6. Wider talent pool

Continue and only continue point 1. Write it in 1-2 sentences.
```

**AI Response for Point 1:**
```
1. Flexible work schedule: Remote work allows employees to set their 
   own hours, enabling them to work when they're most productive and 
   accommodate personal responsibilities.
```

**All 6 points expand simultaneously...**

### Step 3: Combine Results

```
What are the benefits of remote work?

1. Flexible work schedule: Remote work allows employees to set their 
   own hours, enabling them to work when they're most productive.

2. No commute time: Eliminating daily commutes saves hours each week 
   and reduces stress and transportation costs.

3. Better work-life balance: Working from home makes it easier to 
   manage family responsibilities alongside professional duties.

4. Cost savings: Both employees and employers save money on office 
   space, commuting, and work attire.

5. Increased productivity: Many workers report fewer distractions 
   and higher output when working from home.

6. Wider talent pool: Companies can hire the best talent regardless 
   of geographic location.
```

**Done! And it was 2x faster because all points expanded at once.**

---

## Python Code: Implement SoT Yourself

Here's working code you can use right now:

```python
"""
Skeleton-of-Thought Implementation
Works with OpenAI API or any compatible LLM
"""

import asyncio
from openai import OpenAI

client = OpenAI()  # Uses OPENAI_API_KEY from environment

def generate_skeleton(question: str) -> list[str]:
    """
    Phase 1: Generate the skeleton outline
    Returns a list of short points (3-5 words each)
    """
    
    skeleton_prompt = f"""You're an organizer responsible for only giving the skeleton 
(not the full content) for answering the question.

Provide the skeleton in a list of points (numbered 1., 2., 3., etc.) to answer the question.
Instead of writing a full sentence, each skeleton point should be very short with only 3 to 5 words.
Generally, the skeleton should have 3 to 10 points.

Question: {question}

Skeleton:"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": skeleton_prompt}],
        temperature=0.7
    )
    
    # Parse the skeleton into a list
    skeleton_text = response.choices[0].message.content
    points = []
    
    for line in skeleton_text.strip().split('\n'):
        line = line.strip()
        if line and line[0].isdigit():
            # Remove the number prefix (e.g., "1. ")
            point = line.split('.', 1)[1].strip() if '.' in line else line
            points.append(point)
    
    return points


async def expand_point_async(question: str, skeleton: list[str], point_index: int) -> str:
    """
    Phase 2: Expand a single point (async for parallel execution)
    """
    
    skeleton_text = '\n'.join([f"{i+1}. {p}" for i, p in enumerate(skeleton)])
    
    expand_prompt = f"""You're responsible for continuing the writing of one and only one point 
in the overall answer to the following question.

Question: {question}

The skeleton of the answer is:
{skeleton_text}

Continue and only continue the writing of point {point_index + 1}. 
Write it very shortly in 1 to 2 sentences and do not continue with other points!"""

    # Using sync client in async context (for simplicity)
    # In production, use async OpenAI client
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": expand_prompt}],
        temperature=0.7
    )
    
    return response.choices[0].message.content


async def expand_all_points_parallel(question: str, skeleton: list[str]) -> list[str]:
    """
    Expand ALL points in parallel for speed
    """
    tasks = [
        expand_point_async(question, skeleton, i) 
        for i in range(len(skeleton))
    ]
    
    # Run all expansions simultaneously!
    expanded_points = await asyncio.gather(*tasks)
    return expanded_points


def skeleton_of_thought(question: str) -> str:
    """
    Main function: Complete SoT pipeline
    """
    print(f"Question: {question}\n")
    
    # Phase 1: Generate skeleton
    print("🦴 Phase 1: Generating skeleton...")
    skeleton = generate_skeleton(question)
    print(f"Skeleton: {skeleton}\n")
    
    # Phase 2: Expand all points in parallel
    print("📝 Phase 2: Expanding all points in parallel...")
    expanded = asyncio.run(expand_all_points_parallel(question, skeleton))
    
    # Combine results
    print("\n✅ Final Answer:\n")
    final_answer = ""
    for i, point in enumerate(expanded):
        final_answer += f"{point}\n\n"
        print(f"{point}\n")
    
    return final_answer


# Try it!
if __name__ == "__main__":
    question = "What are the most effective strategies for conflict resolution in the workplace?"
    result = skeleton_of_thought(question)
```

---

## Simpler Version: Using Ollama (100% Free)

Don't want to pay for OpenAI? Here's a version using Ollama:

```python
"""
Skeleton-of-Thought with Ollama (Free & Local)
"""

import requests
import concurrent.futures

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"  # or llama2, codellama, etc.


def ask_ollama(prompt: str) -> str:
    """Send a prompt to Ollama and get response"""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]


def generate_skeleton(question: str) -> list[str]:
    """Phase 1: Create the outline"""
    
    prompt = f"""You're an organizer. Give ONLY a skeleton outline for answering this question.
    
Rules:
- List 3-7 points numbered 1., 2., 3., etc.
- Each point should be 3-5 words ONLY
- Don't write full sentences

Question: {question}

Skeleton:"""
    
    response = ask_ollama(prompt)
    
    # Parse points
    points = []
    for line in response.strip().split('\n'):
        line = line.strip()
        if line and line[0].isdigit():
            point = line.split('.', 1)[1].strip() if '.' in line else line
            if point:
                points.append(point)
    
    return points[:7]  # Max 7 points


def expand_single_point(args: tuple) -> str:
    """Expand one point (for parallel execution)"""
    question, skeleton, index = args
    
    skeleton_text = '\n'.join([f"{i+1}. {p}" for i, p in enumerate(skeleton)])
    
    prompt = f"""Expand ONLY point {index + 1} for this question.

Question: {question}

Skeleton:
{skeleton_text}

Write 1-2 sentences for point {index + 1} ONLY. Don't write other points."""
    
    return ask_ollama(prompt)


def skeleton_of_thought(question: str) -> str:
    """Main SoT function with parallel expansion"""
    
    print(f"❓ Question: {question}\n")
    
    # Phase 1: Skeleton
    print("🦴 Generating skeleton...")
    skeleton = generate_skeleton(question)
    print("Skeleton:")
    for i, point in enumerate(skeleton):
        print(f"  {i+1}. {point}")
    print()
    
    # Phase 2: Parallel expansion
    print("⚡ Expanding all points in parallel...")
    
    # Prepare arguments for parallel execution
    args_list = [(question, skeleton, i) for i in range(len(skeleton))]
    
    # Use ThreadPoolExecutor for parallel API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(skeleton)) as executor:
        expanded_points = list(executor.map(expand_single_point, args_list))
    
    # Combine results
    print("\n✅ FINAL ANSWER:\n")
    print("-" * 50)
    
    final_answer = ""
    for i, expanded in enumerate(expanded_points):
        clean_text = expanded.strip()
        final_answer += f"{i+1}. {clean_text}\n\n"
        print(f"{i+1}. {clean_text}\n")
    
    return final_answer


# Example usage
if __name__ == "__main__":
    # Install Ollama first: https://ollama.ai
    # Then run: ollama pull mistral
    
    questions = [
        "What are the benefits of meditation?",
        "How can I improve my public speaking skills?",
        "What are the key principles of good software design?"
    ]
    
    for q in questions:
        print("=" * 60)
        skeleton_of_thought(q)
        print()
```

---

## When Should You Use SoT?

### ✅ Perfect For:

- **Long-form answers** with multiple points
- **List-based questions** ("What are the benefits of...", "How can I...")
- **Educational content** with clear sections
- **Speed-critical applications** where response time matters
- **High-volume requests** where parallel processing saves money

### ❌ Not Great For:

- **Simple questions** with short answers
- **Creative writing** that needs to flow naturally
- **Math problems** that need step-by-step reasoning
- **Conversations** that require context continuity
- **Pay-per-token APIs** (the skeleton adds overhead)

---

## SoT vs. Other Prompting Methods

| Method | Speed | Quality | Best For |
|--------|-------|---------|----------|
| Standard | Slow | Good | Simple questions |
| Chain-of-Thought | Slow | Better | Math, logic |
| Skeleton-of-Thought | **Fast** | Good | Multi-point answers |
| Tree of Thoughts | Very Slow | Best | Complex puzzles |

---

## The Downsides (Be Honest)

Nothing is perfect. Here are the cons:

### 1. Less Coherent Answers

Since each point is expanded independently, they might not connect smoothly.

```
❌ Problem:
Point 2 might repeat something from Point 1
Point 3 might contradict Point 2
The answer feels "choppy"
```

**Fix:** Add a final "polish" step to smooth transitions.

### 2. Higher Token Count

The skeleton adds extra tokens, which can cost more on pay-per-word APIs.

```
Normal: 1 request
SoT: 1 skeleton request + N expansion requests

More requests = More tokens = Higher cost
```

**Fix:** Use SoT only when speed matters more than cost.

### 3. Variable Speed Gains

Not all questions benefit equally. Simple questions might actually be slower with SoT.

```
"What is 2+2?" → SoT is overkill
"List 10 benefits of exercise" → SoT shines
```

**Fix:** Use SoT selectively for multi-point questions.

---

## Copy-Paste Templates

### Template 1: Skeleton Generator

```
You're an organizer. Provide ONLY a skeleton outline for this question.

Rules:
- Number points 1., 2., 3., etc.
- Keep each point to 3-5 words
- Include 3-10 points total
- No full sentences

Question: [YOUR QUESTION]

Skeleton:
```

### Template 2: Point Expander

```
Expand ONLY point [NUMBER] of this answer.

Question: [YOUR QUESTION]

Skeleton:
[PASTE SKELETON HERE]

Write 1-2 sentences for point [NUMBER] only.
Do not write other points.
```

### Template 3: Combined (For Simple Use)

```
Answer this question using the Skeleton-of-Thought method:

Step 1: First, create a skeleton outline with 3-7 short points (3-5 words each)
Step 2: Then, expand each point into 1-2 sentences

Question: [YOUR QUESTION]

Skeleton:
[AI fills this]

Expanded Answer:
[AI fills this]
```

---

## Key Takeaways

1. **SoT = Outline first, expand in parallel**
   - Creates a skeleton with short points
   - Expands all points simultaneously
   - 2x faster for multi-point answers

2. **Two-phase process**
   - Phase 1: Generate skeleton (3-5 words per point)
   - Phase 2: Expand each point (1-2 sentences each)

3. **Best for list-based questions**
   - "What are the benefits of..."
   - "How can I improve..."
   - "List the reasons for..."

4. **Trade-offs exist**
   - Faster but potentially less coherent
   - More requests but parallel execution
   - Not for simple questions

5. **Easy to implement**
   - Just two prompts
   - Works with any LLM
   - Parallel execution is key

---

## Try It Right Now

Here's a quick test you can do in ChatGPT:

```
You're an organizer. Create a skeleton outline for this question 
with 5 short points (3-5 words each):

"What are the most important soft skills for career success?"

Skeleton:
```

Then take that skeleton and expand each point separately. Notice how the structure helps organize the answer!

---

## References

- Ning et al. (2023) "Skeleton-of-Thought: Large Language Models Can Do Parallel Decoding"
- Analytics Vidhya Advanced Prompt Engineering Course

---

*Thanks for reading! If this technique saves you time, drop a comment below.*

*Questions? I read every one.*

---

**Tags:** #PromptEngineering #AI #ChatGPT #LLM #SkeletonOfThought #Productivity
