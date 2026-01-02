# Graph of Thoughts Prompting: The Ultimate Guide to AI Reasoning [2025]

*How ETH Zürich's breakthrough makes AI 62% smarter than Tree of Thoughts — with free Python code*

---

## What is Graph of Thoughts (GoT) Prompting?

Graph of Thoughts (GoT) is the most advanced prompt engineering technique available today. Developed by researchers at ETH Zürich and published in August 2023, GoT models AI reasoning as a **network of interconnected ideas** — not just a chain or a tree, but a full graph where thoughts can merge, split, loop back, and build on each other.

Think of it like this: Chain-of-Thought is a single road. Tree of Thoughts is a highway with exits. Graph of Thoughts is an entire city with roads going everywhere, connecting everything.

**Key result:** GoT improved sorting accuracy by **62% over Tree of Thoughts** while reducing costs by **31%**.

---

## The Evolution of AI Reasoning: From Chain to Graph

Let me show you how we got here:

```
THE EVOLUTION OF AI PROMPTING
═════════════════════════════════════════════════════════════════

2022: CHAIN OF THOUGHT (CoT)
┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
│Input│ → │Step1│ → │Step2│ → │Answer│
└─────┘   └─────┘   └─────┘   └─────┘

    ✓ Better than nothing
    ✗ Can't backtrack
    ✗ Single path only

─────────────────────────────────────────────────────────────────

2023: TREE OF THOUGHTS (ToT)
                    ┌─────┐
                    │Input│
                    └──┬──┘
           ┌──────────┼──────────┐
           ▼          ▼          ▼
        ┌─────┐   ┌─────┐   ┌─────┐
        │Path1│   │Path2│   │Path3│
        └──┬──┘   └──┬──┘   └─────┘
           │         │         ✗
           ▼         ▼      (pruned)
        ┌─────┐   ┌─────┐
        │ ... │   │ ... │
        └─────┘   └─────┘

    ✓ Multiple paths
    ✓ Can backtrack
    ✗ Paths never merge
    ✗ Can't combine insights

─────────────────────────────────────────────────────────────────

2023: GRAPH OF THOUGHTS (GoT)
                    ┌─────┐
                    │Input│
                    └──┬──┘
           ┌──────────┼──────────┐
           ▼          ▼          ▼
        ┌─────┐   ┌─────┐   ┌─────┐
        │ T1  │◄──│ T2  │──►│ T3  │
        └──┬──┘   └──┬──┘   └──┬──┘
           │    ╲    │    ╱    │
           │     ╲   │   ╱     │
           ▼      ╲  ▼  ╱      ▼
        ┌─────┐   ┌─────┐   ┌─────┐
        │ T4  │──►│MERGE│◄──│ T5  │
        └─────┘   └──┬──┘   └─────┘
                     │
              ┌──────┴──────┐
              ▼             ▼
           ┌─────┐      ┌─────┐
           │Refine│◄────│Score│
           └──┬──┘      └─────┘
              │    ↺ (feedback loop)
              ▼
           ┌──────┐
           │Answer│
           └──────┘

    ✓ Multiple paths
    ✓ Can backtrack  
    ✓ Paths CAN MERGE (aggregation)
    ✓ Feedback loops (refinement)
    ✓ Combine best insights
═════════════════════════════════════════════════════════════════
```

---

## How Does Graph of Thoughts Work?

GoT introduces four powerful operations that previous methods couldn't do:

### The Four Key Operations

```
┌─────────────────────────────────────────────────────────────────┐
│                   GRAPH OF THOUGHTS OPERATIONS                  │
└─────────────────────────────────────────────────────────────────┘

1. GENERATION (Same as ToT)
   ─────────────────────────
   Create multiple thoughts from a single thought
   
   [Thought A] ──┬──► [Thought B]
                 ├──► [Thought C]  
                 └──► [Thought D]


2. AGGREGATION (NEW! GoT only)
   ────────────────────────────
   Combine multiple thoughts into one better thought
   
   [Thought A] ──┐
   [Thought B] ──┼──► [Combined Thought]
   [Thought C] ──┘
   
   Example: Merge 3 partial solutions into 1 complete solution


3. REFINEMENT (NEW! GoT only)
   ──────────────────────────
   Improve a thought using feedback loops
   
   [Thought] ◄─────────────────────┐
       │                           │
       ▼                           │
   [Evaluate] ─── "Not good" ──────┘
       │
       └─── "Good enough" ──► [Final Thought]


4. SCORING & PRUNING
   ──────────────────
   Rate thoughts and discard bad ones
   
   [Thought A] ──► Score: 0.9 ──► Keep ✓
   [Thought B] ──► Score: 0.3 ──► Prune ✗
   [Thought C] ──► Score: 0.7 ──► Keep ✓

└─────────────────────────────────────────────────────────────────┘
```

---

## Real Example: Sorting Numbers with Graph of Thoughts

Let's see GoT in action with a concrete example.

**Problem:** Sort this list: `[7, 2, 9, 1, 5, 3, 8, 4, 6, 0]`

### How Chain of Thought Does It (Fails Often)

```
Input: [7, 2, 9, 1, 5, 3, 8, 4, 6, 0]

CoT: "Let me sort step by step..."
     "First, find smallest: 0"
     "Then next: 1"
     "Then: 2..."
     [Often makes mistakes, can't verify]

Result: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] (if lucky)
        [0, 1, 2, 3, 5, 4, 6, 7, 8, 9] (common errors)
```

### How Graph of Thoughts Does It

```
┌─────────────────────────────────────────────────────────────────┐
│              GoT SORTING: DIVIDE AND CONQUER                    │
└─────────────────────────────────────────────────────────────────┘

Step 1: SPLIT into smaller chunks (Generation)
─────────────────────────────────────────────────

        [7, 2, 9, 1, 5, 3, 8, 4, 6, 0]
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    [7,2,9,1]   [5,3,8,4]    [6,0]


Step 2: SORT each chunk independently (Generation)
────────────────────────────────────────────────────

    [7,2,9,1]   [5,3,8,4]    [6,0]
        │           │           │
        ▼           ▼           ▼
    [1,2,7,9]   [3,4,5,8]    [0,6]


Step 3: MERGE sorted chunks (Aggregation) ← GoT EXCLUSIVE!
──────────────────────────────────────────────────────────

    [1,2,7,9] ──┐
                │
    [3,4,5,8] ──┼──► [0,1,2,3,4,5,6,7,8,9]
                │
    [0,6] ──────┘


Step 4: VERIFY result (Refinement) ← GoT EXCLUSIVE!
───────────────────────────────────────────────────

    [0,1,2,3,4,5,6,7,8,9]
              │
              ▼
    ┌─────────────────────┐
    │ "Is each number     │
    │  smaller than the   │◄────┐
    │  next one?"         │     │
    └──────────┬──────────┘     │
               │                │
        ┌──────┴──────┐         │
        ▼             ▼         │
     [YES] ✓       [NO] ✗ ──────┘
        │          (fix and retry)
        ▼
    FINAL: [0,1,2,3,4,5,6,7,8,9] ✓

└─────────────────────────────────────────────────────────────────┘
```

**Why this works better:**
- Smaller chunks = fewer mistakes
- Merging = combines correct partial solutions  
- Verification loop = catches and fixes errors

---

## Graph of Thoughts vs Tree of Thoughts: Key Differences

| Feature | Tree of Thoughts | Graph of Thoughts |
|---------|-----------------|-------------------|
| **Structure** | Hierarchical tree | Flexible network |
| **Paths merge?** | ❌ No, paths stay separate | ✅ Yes, can aggregate |
| **Feedback loops?** | ❌ No | ✅ Yes, can refine |
| **Best for** | Exploration problems | Complex synthesis |
| **Sorting accuracy** | Baseline | **+62% better** |
| **Cost** | Baseline | **-31% cheaper** |

### Visual Comparison

```
TREE OF THOUGHTS                    GRAPH OF THOUGHTS
(Paths never meet)                  (Paths can merge & loop)

       Input                              Input
         │                                  │
    ┌────┼────┐                      ┌──────┼──────┐
    ▼    ▼    ▼                      ▼      ▼      ▼
   [A]  [B]  [C]                    [A]◄──►[B]◄──►[C]
    │    │    │                      │  ╲   │   ╱  │
    ▼    ▼    ▼                      │   ╲  │  ╱   │
   [D]  [E]  [F]                     ▼    ╲ ▼ ╱    ▼
    │    │    │                     [D]───►[M]◄───[F]
    ▼    ▼    ▼                            │
   [G]  [H]  [I]                           ▼
    │         │                        [Refine]◄──┐
    ▼         ▼                            │      │
  Best?    Best?                           └──────┘
                                           │
                                           ▼
                                        [Answer]

Can't combine G+I!                  M = Merged best parts!
```

---

## Free Python Code: Graph of Thoughts with Ollama

Here's working code you can run today using **Ollama** (100% free, runs locally).

### Installation

```bash
# 1. Install Ollama from https://ollama.ai
# 2. Pull a model:
ollama pull mistral
# Or for better results:
ollama pull llama2:13b
```

### Complete Implementation

```python
"""
Graph of Thoughts Implementation with Ollama (FREE)
Based on ETH Zürich's GoT paper (2023)
"""

import requests
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
import re


@dataclass
class Thought:
    """A single thought node in the graph."""
    id: str
    content: str
    score: float = 0.0
    parent_ids: List[str] = None
    
    def __post_init__(self):
        if self.parent_ids is None:
            self.parent_ids = []


class GraphOfThoughts:
    """
    Graph of Thoughts implementation.
    Supports: Generation, Aggregation, Refinement, Scoring
    """
    
    def __init__(self, model: str = "mistral"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"
        self.thoughts: Dict[str, Thought] = {}
        self.thought_counter = 0
    
    def _ask(self, prompt: str) -> str:
        """Send prompt to Ollama."""
        response = requests.post(
            self.url,
            json={"model": self.model, "prompt": prompt, "stream": False}
        )
        return response.json()["response"]
    
    def _new_id(self) -> str:
        """Generate unique thought ID."""
        self.thought_counter += 1
        return f"T{self.thought_counter}"
    
    # =========================================
    # OPERATION 1: GENERATE
    # =========================================
    def generate(self, parent: Thought, num_thoughts: int = 3) -> List[Thought]:
        """
        Generate multiple new thoughts from a parent thought.
        This is the branching operation.
        """
        prompt = f"""
Given this current state: {parent.content}

Generate {num_thoughts} different ways to proceed or improve this.
Be specific and actionable.

Format your response as:
Option 1: [your idea]
Option 2: [your idea]
Option 3: [your idea]
"""
        response = self._ask(prompt)
        
        new_thoughts = []
        for line in response.split('\n'):
            if 'Option' in line and ':' in line:
                content = line.split(':', 1)[-1].strip()
                if content:
                    thought = Thought(
                        id=self._new_id(),
                        content=content,
                        parent_ids=[parent.id]
                    )
                    self.thoughts[thought.id] = thought
                    new_thoughts.append(thought)
        
        return new_thoughts[:num_thoughts]
    
    # =========================================
    # OPERATION 2: AGGREGATE (GoT Exclusive!)
    # =========================================
    def aggregate(self, thoughts: List[Thought]) -> Thought:
        """
        Combine multiple thoughts into one better thought.
        This is what makes GoT special - merging paths!
        """
        thoughts_text = "\n".join([f"- {t.content}" for t in thoughts])
        
        prompt = f"""
I have these different ideas/solutions:

{thoughts_text}

Combine the BEST parts of each into ONE superior solution.
Take what works from each and synthesize them together.

Combined solution:
"""
        response = self._ask(prompt)
        
        aggregated = Thought(
            id=self._new_id(),
            content=response.strip(),
            parent_ids=[t.id for t in thoughts]
        )
        self.thoughts[aggregated.id] = aggregated
        
        print(f"  [AGGREGATE] Combined {len(thoughts)} thoughts → {aggregated.id}")
        return aggregated
    
    # =========================================
    # OPERATION 3: REFINE (GoT Exclusive!)
    # =========================================
    def refine(self, thought: Thought, max_iterations: int = 3) -> Thought:
        """
        Improve a thought through feedback loops.
        This is the self-correction mechanism.
        """
        current = thought
        
        for i in range(max_iterations):
            # Evaluate current thought
            eval_prompt = f"""
Evaluate this solution critically:
{current.content}

What are its weaknesses or errors? Be specific.
If it's perfect, say "PERFECT".

Evaluation:
"""
            evaluation = self._ask(eval_prompt)
            
            if "PERFECT" in evaluation.upper() or "no error" in evaluation.lower():
                print(f"  [REFINE] Iteration {i+1}: Perfect! Stopping.")
                break
            
            # Improve based on feedback
            improve_prompt = f"""
Original solution:
{current.content}

Problems found:
{evaluation}

Create an IMPROVED version that fixes these problems:
"""
            improved = self._ask(improve_prompt)
            
            refined = Thought(
                id=self._new_id(),
                content=improved.strip(),
                parent_ids=[current.id]
            )
            self.thoughts[refined.id] = refined
            current = refined
            
            print(f"  [REFINE] Iteration {i+1}: Improved → {refined.id}")
        
        return current
    
    # =========================================
    # OPERATION 4: SCORE
    # =========================================
    def score(self, thought: Thought, criteria: str = "") -> float:
        """
        Score a thought's quality (0.0 to 1.0).
        """
        prompt = f"""
Rate this solution on a scale of 0 to 10:
{thought.content}

{f"Criteria: {criteria}" if criteria else ""}

Give ONLY a number from 0 to 10.
"""
        response = self._ask(prompt)
        
        # Extract number
        numbers = re.findall(r'\d+\.?\d*', response)
        if numbers:
            score = float(numbers[0]) / 10.0
            thought.score = min(1.0, max(0.0, score))
        else:
            thought.score = 0.5
        
        return thought.score
    
    # =========================================
    # MAIN SOLVING METHOD
    # =========================================
    def solve(self, problem: str, use_aggregation: bool = True, 
              use_refinement: bool = True) -> Thought:
        """
        Solve a problem using full Graph of Thoughts.
        
        Pipeline:
        1. Generate initial thoughts
        2. Score and keep best
        3. Generate more from best
        4. Aggregate all good thoughts (GoT!)
        5. Refine the aggregated result (GoT!)
        """
        print(f"\n{'='*60}")
        print("GRAPH OF THOUGHTS SOLVER")
        print(f"{'='*60}")
        print(f"\nProblem: {problem}\n")
        
        # Create root thought
        root = Thought(id=self._new_id(), content=problem)
        self.thoughts[root.id] = root
        
        # Step 1: Generate initial thoughts
        print("Step 1: Generating initial approaches...")
        initial_thoughts = self.generate(root, num_thoughts=3)
        for t in initial_thoughts:
            print(f"  [{t.id}] {t.content[:60]}...")
        
        # Step 2: Score initial thoughts
        print("\nStep 2: Scoring approaches...")
        for t in initial_thoughts:
            score = self.score(t)
            print(f"  [{t.id}] Score: {score:.2f}")
        
        # Keep thoughts with score > 0.5
        good_thoughts = [t for t in initial_thoughts if t.score > 0.5]
        if not good_thoughts:
            good_thoughts = sorted(initial_thoughts, key=lambda x: x.score, reverse=True)[:2]
        
        print(f"\n  Keeping {len(good_thoughts)} promising thoughts")
        
        # Step 3: Generate more thoughts from good ones
        print("\nStep 3: Expanding promising thoughts...")
        all_candidates = list(good_thoughts)
        for t in good_thoughts[:2]:
            expansions = self.generate(t, num_thoughts=2)
            for exp in expansions:
                self.score(exp)
                if exp.score > 0.4:
                    all_candidates.append(exp)
                    print(f"  [{exp.id}] from [{t.id}]: {exp.content[:50]}... (Score: {exp.score:.2f})")
        
        # Step 4: AGGREGATE (GoT exclusive!)
        if use_aggregation and len(all_candidates) > 1:
            print("\nStep 4: AGGREGATING thoughts (GoT feature!)...")
            # Take top candidates
            top_candidates = sorted(all_candidates, key=lambda x: x.score, reverse=True)[:3]
            aggregated = self.aggregate(top_candidates)
            self.score(aggregated)
            print(f"  Aggregated thought score: {aggregated.score:.2f}")
        else:
            aggregated = max(all_candidates, key=lambda x: x.score)
        
        # Step 5: REFINE (GoT exclusive!)
        if use_refinement:
            print("\nStep 5: REFINING with feedback loop (GoT feature!)...")
            final = self.refine(aggregated, max_iterations=2)
        else:
            final = aggregated
        
        # Final scoring
        self.score(final, criteria="completeness, correctness, clarity")
        
        print(f"\n{'='*60}")
        print("FINAL ANSWER")
        print(f"{'='*60}")
        print(f"\n{final.content}")
        print(f"\nFinal Score: {final.score:.2f}")
        print(f"Total thoughts explored: {len(self.thoughts)}")
        
        return final


# =========================================
# SORTING EXAMPLE (from the paper)
# =========================================

class GoTSorter(GraphOfThoughts):
    """
    Specialized GoT for sorting - matches the paper's approach.
    """
    
    def sort_list(self, numbers: List[int]) -> List[int]:
        """Sort using GoT's divide-aggregate-refine approach."""
        
        print(f"\n{'='*60}")
        print("GoT SORTING")
        print(f"{'='*60}")
        print(f"Input: {numbers}\n")
        
        # Step 1: Split into chunks
        chunk_size = max(4, len(numbers) // 3)
        chunks = [numbers[i:i+chunk_size] for i in range(0, len(numbers), chunk_size)]
        print(f"Step 1: Split into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {chunk}")
        
        # Step 2: Sort each chunk
        print("\nStep 2: Sort each chunk")
        sorted_chunks = []
        for i, chunk in enumerate(chunks):
            prompt = f"Sort these numbers from smallest to largest: {chunk}\nReturn ONLY the sorted list in format [a, b, c, ...]"
            response = self._ask(prompt)
            
            # Parse the response
            match = re.search(r'\[[\d,\s]+\]', response)
            if match:
                sorted_chunk = eval(match.group())
            else:
                sorted_chunk = sorted(chunk)  # Fallback
            
            sorted_chunks.append(sorted_chunk)
            print(f"  Chunk {i+1}: {chunk} → {sorted_chunk}")
        
        # Step 3: AGGREGATE - merge sorted chunks
        print("\nStep 3: AGGREGATE sorted chunks")
        merge_prompt = f"""
Merge these sorted lists into one fully sorted list:
{sorted_chunks}

The final list should contain ALL numbers sorted from smallest to largest.
Return ONLY the merged sorted list in format [a, b, c, ...]
"""
        merge_response = self._ask(merge_prompt)
        
        match = re.search(r'\[[\d,\s]+\]', merge_response)
        if match:
            merged = eval(match.group())
        else:
            # Fallback: manual merge
            merged = sorted([n for chunk in sorted_chunks for n in chunk])
        
        print(f"  Merged: {merged}")
        
        # Step 4: REFINE - verify and fix
        print("\nStep 4: REFINE with verification")
        verify_prompt = f"""
Verify this sorted list is correct: {merged}

Check:
1. Is every number smaller than or equal to the next?
2. Are all original numbers present?

If there are errors, provide the CORRECTED sorted list.
If correct, respond with "CORRECT" followed by the list.
"""
        verify_response = self._ask(verify_prompt)
        
        if "CORRECT" in verify_response.upper():
            final = merged
            print("  Verification: PASSED ✓")
        else:
            match = re.search(r'\[[\d,\s]+\]', verify_response)
            if match:
                final = eval(match.group())
                print(f"  Verification: Fixed to {final}")
            else:
                final = merged
        
        print(f"\n{'='*60}")
        print(f"RESULT: {final}")
        print(f"{'='*60}")
        
        return final


# =========================================
# USAGE EXAMPLES
# =========================================

if __name__ == "__main__":
    
    # Example 1: General problem solving
    print("\n" + "="*70)
    print("EXAMPLE 1: General Problem Solving")
    print("="*70)
    
    got = GraphOfThoughts(model="mistral")
    
    problem = """
    A farmer has 17 sheep. All but 9 die. 
    How many sheep does the farmer have left?
    """
    
    result = got.solve(problem)
    
    # Example 2: Sorting (paper benchmark)
    print("\n" + "="*70)
    print("EXAMPLE 2: Sorting (Paper Benchmark)")
    print("="*70)
    
    sorter = GoTSorter(model="mistral")
    numbers = [7, 2, 9, 1, 5, 3, 8, 4, 6, 0]
    sorted_result = sorter.sort_list(numbers)
    
    # Verify
    expected = sorted(numbers)
    print(f"\nExpected: {expected}")
    print(f"Got:      {sorted_result}")
    print(f"Correct:  {'✓' if sorted_result == expected else '✗'}")
```

---

## Simple Prompt Templates for Graph of Thoughts

You don't need code to use GoT concepts. Here are prompts you can copy:

### Template 1: The Network Method

```
I need to solve this problem: [YOUR PROBLEM]

Use the Graph of Thoughts approach:

PHASE 1 - GENERATE: Create 3 different approaches to this problem.

PHASE 2 - DEVELOP: For each approach, take 2 more steps.

PHASE 3 - AGGREGATE: Now look at ALL the partial solutions above.
What are the BEST ideas from each? Combine them into ONE superior solution.

PHASE 4 - REFINE: Look at your combined solution critically.
What could go wrong? Fix any issues.

Final Answer:
```

### Template 2: The Merge-and-Verify Method

```
Problem: [YOUR PROBLEM]

Step 1: Think of 3 completely different ways to solve this.
   Approach A:
   Approach B:
   Approach C:

Step 2: What's the BEST part of each approach?
   Best of A:
   Best of B:
   Best of C:

Step 3: Combine these best parts into one solution.
   Combined:

Step 4: Check your combined solution for errors. Fix any you find.
   Final verified answer:
```

### Template 3: The Division Method (for sorting/organizing tasks)

```
Task: [YOUR SORTING/ORGANIZING TASK]

1. SPLIT: Break this into 3 smaller pieces.
   Piece 1:
   Piece 2:
   Piece 3:

2. SOLVE: Handle each piece separately.
   Solution 1:
   Solution 2:
   Solution 3:

3. MERGE: Combine all solutions into one complete answer.
   Merged result:

4. VERIFY: Double-check the merged result is correct.
   Verified answer:
```

---

## Research Results: Graph of Thoughts Performance

From the ETH Zürich paper (2023):

### Sorting Task (32 numbers)

| Method | Error Rate | Cost Savings |
|--------|-----------|--------------|
| Chain of Thought | High | Baseline |
| Tree of Thoughts | Medium | Baseline |
| **Graph of Thoughts** | **62% lower** | **31% cheaper** |

### Why GoT Wins

```
SORTING 32 NUMBERS: WHY GoT BEATS ToT
─────────────────────────────────────────────

Tree of Thoughts:
• Sorts entire list in one attempt
• Multiple attempts = multiple FULL sorts
• Errors compound across the list
• No way to combine partial successes

Graph of Thoughts:
• Splits into small chunks (8 numbers each)
• Each chunk sorted independently (low error)
• AGGREGATES sorted chunks (merge sort style)
• REFINES to catch any remaining errors
• Errors stay isolated, don't compound

Result: 62% fewer errors, 31% less compute
```

---

## When Should You Use Graph of Thoughts?

### ✅ Best Use Cases for GoT

- **Complex synthesis** — Combining multiple sources/ideas
- **Sorting and organizing** — Any divide-and-conquer problem
- **Code generation** — Generate parts, merge, then refine
- **Essay writing** — Multiple drafts merged into best version
- **Decision making** — Evaluate options, combine best aspects
- **Data analysis** — Break down, analyze parts, synthesize

### ❌ When NOT to Use GoT

- **Simple factual questions** — "What's 2+2?"
- **When ToT is enough** — If you just need exploration
- **Speed-critical tasks** — GoT has more overhead
- **Simple classification** — Binary yes/no questions

---

## Graph of Thoughts: Pros and Cons

### Advantages

| Benefit | Explanation |
|---------|-------------|
| **Better accuracy** | 62% improvement on sorting |
| **Cost efficient** | 31% cheaper than alternatives |
| **Combines insights** | Merges best of multiple paths |
| **Self-correcting** | Feedback loops fix errors |
| **Flexible** | Adapts to problem structure |

### Disadvantages

| Drawback | Explanation |
|----------|-------------|
| **Complex to implement** | More moving parts than CoT/ToT |
| **Harder to debug** | Graph structure can be confusing |
| **Overkill for simple tasks** | Unnecessary overhead |
| **Requires good prompts** | Aggregation quality depends on prompts |

---

## Quick Comparison: All Prompting Methods

```
┌─────────────────┬──────────────┬──────────────┬──────────────┐
│    Method       │  Structure   │  Key Feature │  Best For    │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│                 │              │              │              │
│ Chain of        │   Linear     │  Step-by-    │  Simple      │
│ Thought         │   A→B→C      │  step        │  reasoning   │
│                 │              │              │              │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│                 │              │              │              │
│ Tree of         │   Branching  │  Multiple    │  Exploration │
│ Thoughts        │   tree       │  paths       │  problems    │
│                 │              │              │              │
├─────────────────┼──────────────┼──────────────┼──────────────┤
│                 │              │              │              │
│ Graph of        │   Network    │  Merge +     │  Complex     │
│ Thoughts        │   graph      │  Refine      │  synthesis   │
│                 │              │              │              │
└─────────────────┴──────────────┴──────────────┴──────────────┘
```

---

## Key Takeaways: Graph of Thoughts Prompting

1. **GoT is the most advanced prompting technique** — It goes beyond chains and trees to full graphs

2. **Two exclusive features: Aggregation + Refinement** — Merge paths and use feedback loops

3. **62% better, 31% cheaper** — On sorting tasks vs Tree of Thoughts

4. **Best for synthesis problems** — When you need to combine multiple ideas

5. **Use the templates above** — You don't need code to get started

---

## References

- Besta et al. (2024) "[Graph of Thoughts: Solving Elaborate Problems with Large Language Models](https://arxiv.org/abs/2308.09687)" — ETH Zürich, AAAI 2024
- Official GitHub: [github.com/spcl/graph-of-thoughts](https://github.com/spcl/graph-of-thoughts)
- Yao et al. (2023) "Tree of Thoughts" — Princeton/DeepMind

---

*Found this useful? Follow for more AI tutorials.*

*Questions? Drop them in the comments!*

---

**Tags:** #GraphOfThoughts #PromptEngineering #AI #LLM #MachineLearning #ChatGPT #Ollama #FreeAI #ETHZurich
