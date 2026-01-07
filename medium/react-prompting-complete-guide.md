g# ReAct Prompting: How to Make AI Think AND Act Like a Human [2025]

*The secret technique that lets AI use Google, Wikipedia, and calculators while solving problems*

---

## The Problem with Regular AI

Have you ever asked ChatGPT a question and got a completely made-up answer? 

Like asking "Who won the NBA finals last year?" and getting confidently wrong information?

That's because regular AI can only use what's in its head. It can't Google things. It can't check facts. It just... guesses.

**ReAct fixes this.**

---

## What is ReAct Prompting?

ReAct stands for **Re**asoning + **Act**ing. It's a prompting technique from 2022 that teaches AI to:

1. **Think** about what it needs to do
2. **Act** by using tools (search, calculator, etc.)
3. **Observe** the results
4. **Think** again based on new information
5. **Repeat** until the answer is found

It's exactly how YOU solve problems:

```
YOU: "What's the capital of the country that won the 2022 World Cup?"

YOUR BRAIN:
  Think:  "I need to find who won the 2022 World Cup first"
  Action: *Googles "2022 World Cup winner"*
  See:    "Argentina won the 2022 World Cup"
  Think:  "Now I need to find Argentina's capital"
  Action: *Googles "capital of Argentina"*
  See:    "Buenos Aires"
  Think:  "Got it!"
  Answer: "Buenos Aires"
```

That's ReAct. Simple as that.

---

## How Does ReAct Work? (Visual Explanation)

Here's the ReAct loop:

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE ReAct LOOP                               │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────┐
                         │ QUESTION │
                         └────┬─────┘
                              │
                              ▼
                    ┌─────────────────┐
            ┌──────►│    THOUGHT      │
            │       │ "What do I need │
            │       │  to do next?"   │
            │       └────────┬────────┘
            │                │
            │                ▼
            │       ┌─────────────────┐
            │       │     ACTION      │
            │       │ Search[query]   │
            │       │ Calculate[math] │
            │       │ Lookup[topic]   │
            │       └────────┬────────┘
            │                │
            │                ▼
            │       ┌─────────────────┐
            │       │  OBSERVATION    │
            │       │ (Results from   │
            │       │  the action)    │
            │       └────────┬────────┘
            │                │
            │      ┌─────────┴─────────┐
            │      │                   │
            │      ▼                   ▼
            │  Need more          Got enough
            │  info?              info!
            │      │                   │
            └──────┘                   ▼
                              ┌─────────────────┐
                              │  FINAL ANSWER   │
                              └─────────────────┘
```

---

## Real Example: ReAct in Action

**Question:** "Aside from the Apple Remote, what other device can control the program Apple Remote was originally designed to interact with?"

### Without ReAct (Standard Prompting)

```
AI: "iPod"  ❌ WRONG
```

The AI just guessed. No reasoning, no checking.

### Without ReAct (Chain-of-Thought Only)

```
Thought: Let's think step by step. Apple Remote was originally 
         designed to interact with Apple TV. Apple TV can be 
         controlled by iPhone, iPad, and iPod Touch.

Answer: iPhone, iPad, iPod Touch  ❌ WRONG (Apple TV is wrong!)
```

The AI reasoned, but with wrong information from its memory.

### With ReAct ✅

```
Thought 1: I need to search Apple Remote and find what program 
           it was originally designed to interact with.

Action 1:  Search[Apple Remote]

Observation 1: The Apple Remote is a remote control introduced 
               in October 2005 by Apple... originally designed 
               to control the Front Row media center program...

Thought 2: Apple Remote was originally designed to control 
           Front Row. I need to search Front Row to find what 
           other device can control it.

Action 2:  Search[Front Row]

Observation 2: Could not find [Front Row]. 
               Similar: ['Front Row (Software)']

Thought 3: Front Row is not found. Let me search Front Row (Software).

Action 3:  Search[Front Row (Software)]

Observation 3: Front Row is a discontinued media center software 
               designed to be controlled by the Apple Remote or 
               the keyboard function keys...

Thought 4: Front Row can be controlled by Apple Remote OR 
           keyboard function keys. So the answer is keyboard 
           function keys.

Action 4:  Finish[Keyboard function keys]  ✅ CORRECT!
```

See the difference? ReAct:
- Searched for real information
- Corrected itself when search failed
- Found the actual answer

---

## Why ReAct Beats Chain-of-Thought

Here's a simple comparison:

```
┌─────────────────────────────────────────────────────────────────┐
│              CHAIN-OF-THOUGHT vs ReAct                          │
└─────────────────────────────────────────────────────────────────┘

CHAIN-OF-THOUGHT (Reasoning Only):
──────────────────────────────────

  Question ──► Think ──► Think ──► Think ──► Answer
                │         │         │
                └─────────┴─────────┘
                Uses ONLY what's in AI's head
                (Can hallucinate facts!)


ReAct (Reasoning + Acting):
───────────────────────────

  Question ──► Think ──► ACT ──► See ──► Think ──► ACT ──► Answer
                          │              │          │
                          ▼              │          ▼
                      [Google]           │      [Calculator]
                      [Wikipedia]        │      [Database]
                      [Tools]            │      [APIs]
                          │              │          │
                          └──────────────┴──────────┘
                          Uses REAL external information!
```

| Feature | Chain-of-Thought | ReAct |
|---------|-----------------|-------|
| Uses external tools |  No |  Yes  |
| Can check facts     |  No |  Yes |
| Self-corrects       |  Rarely |  Yes |
| Transparent reasoning |  Yes |  Yes |
| Best for facts      |  Can hallucinate |  Verifies info |

---

## The 3 ReAct Actions You Need to Know

ReAct uses simple action commands:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ReAct ACTION TYPES                           │
└─────────────────────────────────────────────────────────────────┘

1. SEARCH[query]
   ─────────────
   Search for information on a topic
   
   Example: Search[Python programming language]
   Returns: Wikipedia article about Python


2. LOOKUP[keyword]
   ────────────────
   Find specific info within the current page
   
   Example: Lookup[release date]
   Returns: The sentence containing "release date"


3. FINISH[answer]
   ───────────────
   Provide the final answer and stop
   
   Example: Finish[The answer is 42]
```

---

## Copy-Paste ReAct Prompt Templates

### Template 1: Basic ReAct Format

```
Answer the following question by thinking step by step and 
using Search and Lookup actions when needed.

Question: [YOUR QUESTION]

Use this format:
Thought: [Your reasoning about what to do next]
Action: Search[query] or Lookup[keyword] or Finish[answer]
Observation: [What you learned from the action]
... (repeat Thought/Action/Observation as needed)

Begin!

Question: [YOUR QUESTION]
Thought:
```

### Template 2: ReAct with Calculator

```
You have access to these tools:
- Search[query]: Search Wikipedia for information
- Calculate[expression]: Do math calculations
- Finish[answer]: Give final answer

Answer step by step using Thought, Action, Observation format.

Question: [YOUR QUESTION]

Thought 1:
```

### Template 3: Simple ReAct (Easy to Remember)

```
Solve this step by step. For each step:
1. THINK: What do I need to find out?
2. ACT: Search for it or calculate it
3. SEE: What did I learn?
4. Repeat until you have the answer

Question: [YOUR QUESTION]

Step 1:
THINK:
```

---

## Free Python Code: ReAct with Ollama

Here's working code using **Ollama** (100% free, runs locally):

### Installation

```bash
# 1. Install Ollama from https://ollama.ai
# 2. Pull a model:
ollama pull mistral
```

### Complete ReAct Implementation

```python
"""
ReAct Prompting Implementation with Ollama (FREE)
Combines Reasoning + Acting for better AI answers
"""

import requests
import re


class ReActAgent:
    """
    A simple ReAct agent that can search and reason.
    Uses Ollama for the LLM (free, local).
    """
    
    def __init__(self, model: str = "mistral"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"
        self.max_steps = 7
        self.knowledge_base = {}  # Simple cache
    
    def ask_llm(self, prompt: str) -> str:
        """Send prompt to Ollama."""
        response = requests.post(
            self.url,
            json={"model": self.model, "prompt": prompt, "stream": False}
        )
        return response.json()["response"]
    
    def search(self, query: str) -> str:
        """
        Simulate a search action.
        In production, connect to real APIs (Wikipedia, Google, etc.)
        """
        # For demo, use the LLM as a knowledge source
        # In real use: call Wikipedia API, Google Search API, etc.
        prompt = f"Provide a brief, factual summary about: {query}"
        result = self.ask_llm(prompt)
        return result[:500]  # Limit length
    
    def calculate(self, expression: str) -> str:
        """Do math calculations safely."""
        try:
            # Only allow safe math operations
            allowed = set('0123456789+-*/.() ')
            if all(c in allowed for c in expression):
                result = eval(expression)
                return f"Result: {result}"
            else:
                return "Error: Invalid expression"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def parse_action(self, text: str) -> tuple:
        """Extract action type and input from response."""
        # Look for Action: pattern
        action_match = re.search(r'Action:?\s*(\w+)\[([^\]]+)\]', text, re.IGNORECASE)
        if action_match:
            action_type = action_match.group(1).lower()
            action_input = action_match.group(2)
            return action_type, action_input
        return None, None
    
    def execute_action(self, action_type: str, action_input: str) -> str:
        """Execute the specified action."""
        if action_type == "search":
            return self.search(action_input)
        elif action_type == "calculate":
            return self.calculate(action_input)
        elif action_type == "lookup":
            return self.search(action_input)  # Simplified
        elif action_type == "finish":
            return f"FINAL ANSWER: {action_input}"
        else:
            return f"Unknown action: {action_type}"
    
    def solve(self, question: str) -> str:
        """
        Main ReAct loop: Think → Act → Observe → Repeat
        """
        print(f"\n{'='*60}")
        print("ReAct AGENT")
        print(f"{'='*60}")
        print(f"\nQuestion: {question}\n")
        
        # Build the initial prompt with ReAct instructions
        prompt = f"""You are a helpful assistant that answers questions by 
thinking step by step and using actions to find information.

Available actions:
- Search[query]: Search for information about a topic
- Calculate[math]: Do a math calculation
- Finish[answer]: Give your final answer

Always use this format:
Thought: [your reasoning]
Action: [action type][input]

Question: {question}

Thought 1:"""
        
        trajectory = ""
        
        for step in range(1, self.max_steps + 1):
            print(f"\n--- Step {step} ---")
            
            # Get LLM response
            full_prompt = prompt + trajectory
            response = self.ask_llm(full_prompt)
            
            # Extract thought
            thought_match = re.search(r'(.*?)(?=Action:|$)', response, re.DOTALL)
            thought = thought_match.group(1).strip() if thought_match else response
            print(f"Thought: {thought[:200]}...")
            
            # Parse action
            action_type, action_input = self.parse_action(response)
            
            if action_type is None:
                # No action found, try to extract answer
                print("No action found, extracting answer...")
                break
            
            print(f"Action: {action_type}[{action_input}]")
            
            # Check if finished
            if action_type == "finish":
                print(f"\n{'='*60}")
                print("FINAL ANSWER")
                print(f"{'='*60}")
                print(f"\n{action_input}")
                return action_input
            
            # Execute action
            observation = self.execute_action(action_type, action_input)
            print(f"Observation: {observation[:200]}...")
            
            # Add to trajectory
            trajectory += f"""
{thought}
Action: {action_type.capitalize()}[{action_input}]
Observation: {observation}

Thought {step + 1}:"""
        
        # If we ran out of steps, ask for final answer
        final_prompt = prompt + trajectory + "\nBased on all the above, give your final answer using Finish[answer]:"
        final_response = self.ask_llm(final_prompt)
        
        _, final_answer = self.parse_action(final_response)
        if final_answer:
            print(f"\n{'='*60}")
            print("FINAL ANSWER")
            print(f"{'='*60}")
            print(f"\n{final_answer}")
            return final_answer
        
        return final_response


# Example usage
if __name__ == "__main__":
    agent = ReActAgent(model="mistral")
    
    # Test questions
    questions = [
        "What is the capital of the country that hosted the 2024 Olympics?",
        "If I have 15 apples and give away 40% of them, how many do I have left?",
        "Who invented the telephone and in what year?"
    ]
    
    for q in questions:
        result = agent.solve(q)
        print("\n" + "="*60 + "\n")
```

---

## ReAct with LangChain (Even Easier!)

LangChain has built-in ReAct support. Here's how to use it:

```python
"""
ReAct with LangChain - The Easy Way
Requires: pip install langchain openai google-search-results
"""

from langchain.llms import OpenAI
from langchain.agents import load_tools, initialize_agent
import os

# Set up API keys
os.environ["OPENAI_API_KEY"] = "your-key-here"
os.environ["SERPER_API_KEY"] = "your-serper-key"  # For Google search

# Initialize LLM
llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0)

# Load tools
tools = load_tools(["google-serper", "llm-math"], llm=llm)

# Create ReAct agent
agent = initialize_agent(
    tools, 
    llm, 
    agent="zero-shot-react-description",
    verbose=True  # Shows the thinking process!
)

# Ask a question
result = agent.run(
    "Who is the current CEO of Tesla and what is their age squared?"
)

print(result)
```

**Output:**
```
> Entering new AgentExecutor chain...
I need to find who is the CEO of Tesla, then their age, then square it.

Action: Search
Action Input: "Tesla CEO"
Observation: Elon Musk is the CEO of Tesla.

Thought: Now I need to find Elon Musk's age.
Action: Search
Action Input: "Elon Musk age"
Observation: 53 years old

Thought: Now I need to calculate 53 squared.
Action: Calculator
Action Input: 53**2
Observation: 2809

Thought: I now know the final answer.
Final Answer: Elon Musk is the CEO of Tesla and his age (53) squared is 2809.

> Finished chain.
```

---

## When Should You Use ReAct Prompting?

### ✅ Best Use Cases for ReAct

| Use Case | Why ReAct Helps |
|----------|-----------------|
| **Fact-checking** | Can verify against real sources |
| **Current events** | Can search for latest info |
| **Multi-step research** | Can gather info from multiple sources |
| **Math + facts combined** | Can search AND calculate |
| **Complex questions** | Can break down and verify each part |

### ❌ When NOT to Use ReAct

- **Simple questions** — "What is 2+2?" (no need to search)
- **Creative writing** — No facts to verify
- **Opinion questions** — "What's the best color?"
- **When speed matters** — ReAct is slower due to multiple steps

---

## ReAct vs Other Prompting Methods

```
┌─────────────────────────────────────────────────────────────────┐
│           PROMPTING METHODS COMPARISON                          │
└─────────────────────────────────────────────────────────────────┘

METHOD              │ REASONING │ ACTIONS │ EXTERNAL INFO │ BEST FOR
────────────────────┼───────────┼─────────┼───────────────┼──────────
Standard            │    ❌     │   ❌    │      ❌       │ Simple Q&A
                    │           │         │               │
Chain-of-Thought    │    ✅     │   ❌    │      ❌       │ Math, Logic
                    │           │         │               │
ReAct               │    ✅     │   ✅    │      ✅       │ Research,
                    │           │         │               │ Fact-checking
                    │           │         │               │
Tree of Thoughts    │    ✅     │   ❌    │      ❌       │ Complex
                    │           │         │               │ puzzles
                    │           │         │               │
ReAct + CoT         │    ✅     │   ✅    │      ✅       │ BEST OVERALL
(Combined)          │           │         │               │ for accuracy
```

---

## Research Results: How Well Does ReAct Work?

From the original paper (Yao et al., 2022):

### HotpotQA (Question Answering)

| Method | Success Rate |
|--------|-------------|
| Standard | 28.7% |
| Chain-of-Thought | 29.4% |
| Act-only | 25.0% |
| **ReAct** | **34.2%** |
| **ReAct + CoT** | **35.1%** |

### FEVER (Fact Verification)

| Method | Accuracy |
|--------|----------|
| Standard | 57.1% |
| Chain-of-Thought | 56.3% |
| Act-only | 58.9% |
| **ReAct** | **60.9%** |

### ALFWorld (Decision Making Game)

| Method | Success Rate |
|--------|-------------|
| Act-only | 45% |
| **ReAct** | **71%** |

---

## Common ReAct Mistakes to Avoid

### ❌ Mistake 1: Infinite Loops

```
Thought: I need to search for X
Action: Search[X]
Observation: [some info]
Thought: I need more info, let me search X again
Action: Search[X]  ← SAME SEARCH!
```

**Fix:** Add a step limit and track previous searches.

### ❌ Mistake 2: Ignoring Observations

```
Thought: The capital of France is London
Action: Search[capital of France]
Observation: Paris is the capital of France
Thought: So the answer is London  ← IGNORED THE OBSERVATION!
```

**Fix:** Always base next thought on the observation.

### ❌ Mistake 3: Too Many Actions

```
Thought: Let me search everything...
Action: Search[topic A]
Action: Search[topic B]
Action: Search[topic C]  ← One action at a time!
```

**Fix:** One Thought → One Action → One Observation per step.

---

## Key Takeaways: ReAct Prompting

1. **ReAct = Reasoning + Acting** — The AI thinks AND uses tools

2. **Solves hallucination** — Can verify facts with real searches

3. **Simple loop:** Think → Act → Observe → Repeat

4. **Three actions:** Search, Calculate, Finish

5. **Best combined with CoT** — ReAct + Chain-of-Thought = best accuracy

6. **Use for research tasks** — Fact-checking, current events, multi-step questions

---

## Try It Yourself: ReAct Challenge

Copy this prompt into ChatGPT or Claude:

```
You are a ReAct agent. Answer questions by thinking step by step 
and using Search actions to find information.

Format:
Thought: [your reasoning]
Action: Search[query] or Finish[answer]
Observation: [I'll tell you what the search found]

Question: What is the population of the capital city of Japan?

Thought 1:
```

Then pretend to be the "Observation" by giving search results!

---

## References

- Yao et al. (2022) "[ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)"
- LangChain Documentation: [ReAct Agents](https://docs.langchain.com)
- Prompt Engineering Guide: [ReAct Prompting](https://www.promptingguide.ai)

---

*Found this helpful? Follow for more AI tutorials!*

*Questions? Drop them in the comments!*

---

**Tags:** #ReAct #PromptEngineering #AI #LLM #ChatGPT #LangChain #MachineLearning #AIAgents
