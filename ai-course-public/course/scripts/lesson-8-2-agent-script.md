# Lesson 8.2: Building Your First AI Agent
## Full Lesson Script (25-minute video)

---

## COLD OPEN (0:00 - 0:30)

[VISUAL: Screen showing a working AI agent doing research on the web]

**NARRATOR:**
"Watch this. I just asked an AI agent: 'What's the weather in Tokyo and convert it to Fahrenheit?' It didn't just give me an answer. It *thought* about what tools it needed, called a weather API, did the math, and gave me a complete response. And I'm going to show you exactly how to build this in the next 25 minutes."

[VISUAL: Code editor opens]

"By the end of this lesson, you'll have a working ReAct agent that can use any tool you give it. Let's go."

---

## HOOK (0:30 - 1:15)

**NARRATOR:**
"If you've ever wondered how AI agents actually work — not the hype, the real implementation — this is the lesson for you. We're going to build a ReAct agent from scratch. No LangChain, no CrewAI, no magic. Just 100 lines of Python that show you exactly what's happening under the hood.

This is the foundation. Once you understand this, every agent framework — LangChain, AutoGen, CrewAI, LangGraph — will make sense. Because they all use this same pattern.

Let's start with what an agent actually is."

---

## WHAT IS AN AGENT? (1:15 - 3:00)

[VISUAL: Animated diagram showing LLM ↔ Tools loop]

**NARRATOR:**
"An AI agent is a program that uses an LLM to decide what to do next, takes actions using tools, observes the results, and repeats until the task is done.

That's it. That's the whole concept.

The LLM is the brain. The tools are the hands. The loop is the workflow.

Here's the pattern — and I want you to memorize this:

**Think → Act → Observe → Think → Act → Observe → ...**

The agent thinks about what to do, takes an action using a tool, observes the result, then thinks again. It keeps going until it has enough information to answer the original question.

This pattern is called ReAct — Reasoning + Acting. It was a research paper from 2022 that changed everything. And we're going to implement it from scratch.

But first, let me show you what we'll build today."

---

## DEMO OF FINAL RESULT (3:00 - 4:00)

[VISUAL: Terminal showing agent in action]

**NARRATOR:**
"Here's our finished agent. I'm going to ask it: 'What's the weather in Tokyo right now?'

Watch what happens:

[Types: What's the weather in Tokyo?]

[Agent output:]
- Thought: I need to use the get_weather tool with city=Tokyo
- Action: get_weather({"city": "Tokyo"})
- Observation: 22°C, partly cloudy
- Thought: I have the answer. Let me format it nicely.
- Final Answer: The current weather in Tokyo is 22°C with partly cloudy skies.

That's a ReAct agent. The LLM decided which tool to use, what arguments to pass, and when it had enough information to stop.

Now let's build it. I'll show you every line."

---

## SETUP (4:00 - 5:30)

[VISUAL: VS Code, creating new file `agent.py`]

**NARRATOR:**
"First, let's set up our project. You'll need:
- Python 3.10 or higher
- An OpenAI API key (we'll use GPT-4o-mini for cost)
- The `openai` Python package

Let me create a new directory and install dependencies:

```bash
mkdir my-first-agent
cd my-first-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install openai python-dotenv
```

Now I'll create our main file:

[Creates agent.py]

The first thing we need is a way to define tools. Tools are just functions the agent can call. Let me show you the simplest possible tool definition."

---

## TOOL DEFINITION (5:30 - 8:00)

[VISUAL: Code editor, typing tool definitions]

**NARRATOR:**
"Here's how we define a tool. We're going to use a pattern called 'JSON schema tool definitions' — it's what the OpenAI API expects.

```python
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# Tool 1: Get current weather
def get_weather(city: str) -> str:
    '''Get current weather for a city'''
    # In production, use a real weather API
    # For demo, return mock data
    weather_data = {
        "Tokyo": "22°C, partly cloudy",
        "London": "15°C, rainy",
        "New York": "18°C, sunny",
        "Singapore": "30°C, humid",
    }
    return weather_data.get(city, f"Weather data not available for {city}")

# Tool 2: Calculate math
def calculate(expression: str) -> str:
    '''Calculate a math expression. Example: 2 + 2 * 3'''
    try:
        result = eval(expression)  # Don't use eval in production!
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# Tool definitions in OpenAI format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city. Use this when the user asks about weather conditions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city, e.g. 'Tokyo', 'London'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate a math expression. Use this for any math calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A valid math expression, e.g. '2 + 2 * 3'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]
```

Notice three things:

1. **The `description` field is critical.** The LLM uses this to decide when to use the tool. Be specific. 'Use this when the user asks about weather' is much better than 'Gets weather.'

2. **The `parameters` schema** tells the LLM what arguments to pass. Be clear about types and what's required.

3. **The function name** is what the LLM will call. Use clear, action-oriented names.

Now let's build the actual agent loop."

---

## THE AGENT LOOP (8:00 - 14:00)

[VISUAL: Code editor, typing the main agent logic]

**NARRATOR:**
"This is the heart of the agent. The loop that makes the magic happen.

```python
# Map tool names to actual functions
AVAILABLE_FUNCTIONS = {
    "get_weather": get_weather,
    "calculate": calculate,
}

def run_agent(user_query: str, max_iterations: int = 5) -> str:
    '''Run a ReAct agent with tool use'''
    
    messages = [
        {"role": "system", "content": '''You are a helpful AI assistant with access to tools.

When you need to use a tool, respond with a function call.
When you have enough information to answer the user, provide a final answer.

Think step by step about what the user needs and which tools can help.'''},
        {"role": "user", "content": user_query}
    ]
    
    print(f"\n{'='*60}")
    print(f"User: {user_query}")
    print(f"{'='*60}\n")
    
    for iteration in range(max_iterations):
        print(f"--- Iteration {iteration + 1} ---")
        
        # Step 1: Ask LLM what to do
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"  # Let LLM decide
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)
        
        # Step 2: Check if LLM wants to use a tool
        tool_calls = response_message.tool_calls
        
        if not tool_calls:
            # No tool use — final answer
            final_answer = response_message.content
            print(f"\n✓ Final Answer: {final_answer}\n")
            return final_answer
        
        # Step 3: Execute each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"🔧 Calling: {function_name}({function_args})")
            
            # Call the actual function
            function_to_call = AVAILABLE_FUNCTIONS[function_name]
            function_response = function_to_call(**function_args)
            
            print(f"📊 Result: {function_response}\n")
            
            # Add the tool response to messages
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })
    
    return "Max iterations reached. Could not complete the task."
```

Let me walk you through this:

1. **We start with the user's query** in the messages array.
2. **We call the LLM** with our tools available. The LLM decides if it needs to use a tool or can answer directly.
3. **If the LLM wants to use a tool**, we execute it and add the result back to the messages.
4. **We loop** — the LLM sees the tool result and decides what to do next.
5. **When the LLM doesn't call any tool**, that's our final answer.

That's the entire ReAct loop. Simple, right?

Now let's test it."

---

## TESTING THE AGENT (14:00 - 18:00)

[VISUAL: Terminal running the agent]

**NARRATOR:**
"Let's test this with a few queries.

**Test 1: Simple tool use**

```python
run_agent("What's the weather in Tokyo?")
```

[Output:]
```
============================================================
User: What's the weather in Tokyo?
============================================================

--- Iteration 1 ---
🔧 Calling: get_weather({'city': 'Tokyo'})
📊 Result: 22°C, partly cloudy

--- Iteration 2 ---

✓ Final Answer: The current weather in Tokyo is 22°C with partly cloudy skies.
```

The agent used the tool, got the result, and gave a natural language answer. Perfect.

**Test 2: Multi-step reasoning**

```python
run_agent("What's the weather in Singapore, and what's 22 + 30?")
```

[Output:]
```
--- Iteration 1 ---
🔧 Calling: get_weather({'city': 'Singapore'})
📊 Result: 30°C, humid

--- Iteration 2 ---
🔧 Calling: calculate({'expression': '22 + 30'})
📊 Result: 52

--- Iteration 3 ---

✓ Final Answer: The weather in Singapore is 30°C and humid. 
Also, 22 + 30 equals 52.
```

The agent used *two different tools* in sequence. It understood the question had two parts.

**Test 3: When no tool is needed**

```python
run_agent("Say hello in Japanese")
```

[Output:]
```
--- Iteration 1 ---

✓ Final Answer: Konnichiwa! (こんにちは)
```

The agent didn't use any tool because it could answer directly.

**Test 4: Edge case**

```python
run_agent("What's the weather in Mars?")
```

[Output:]
```
--- Iteration 1 ---
🔧 Calling: get_weather({'city': 'Mars'})
📊 Result: Weather data not available for Mars

--- Iteration 2 ---

✓ Final Answer: I don't have weather data available for Mars, 
as it's not a city with weather measurements in my database.
```

The agent gracefully handled the case when the tool didn't have the answer.

Pretty cool, right? This is a real, working AI agent. And it's only 100 lines of code."

---

## IMPROVING THE AGENT (18:00 - 21:00)

[VISUAL: Code editor, adding improvements]

**NARRATOR:**
"Now let's make this production-ready. Three improvements:

**1. Better error handling:**

```python
def run_agent(user_query: str, max_iterations: int = 5) -> str:
    # ... (same as before) ...
    
    for tool_call in tool_calls:
        try:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name not in AVAILABLE_FUNCTIONS:
                function_response = f"Error: Unknown function '{function_name}'"
            else:
                function_to_call = AVAILABLE_FUNCTIONS[function_name]
                function_response = function_to_call(**function_args)
                
        except Exception as e:
            function_response = f"Error executing {function_name}: {str(e)}"
        
        messages.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": function_response,
        })
```

**2. Add logging:**

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use logger.info() throughout the agent loop
```

**3. Token tracking:**

```python
total_tokens = 0

for iteration in range(max_iterations):
    response = client.chat.completions.create(...)
    total_tokens += response.usage.total_tokens
    print(f"Tokens used: {response.usage.total_tokens}")

print(f"\nTotal tokens: {total_tokens}")
print(f"Estimated cost: ${total_tokens * 0.00015 / 1000:.4f}")
```

**4. Add conversation memory:**

```python
class Agent:
    def __init__(self):
        self.conversation_history = []
    
    def chat(self, user_message: str) -> str:
        # Add to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Run agent with full history
        # ...
        
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
```

These are the patterns you'll use in every production agent. Take a screenshot of this code — you'll reference it later."

---

## COMMON PITFALLS (21:00 - 23:00)

[VISUAL: Bullet points on screen]

**NARRATOR:**
"Before we wrap up, let me save you hours of debugging. Here are the top 5 mistakes people make with agents:

**1. Vague tool descriptions**
❌ Bad: 'Gets weather'
✅ Good: 'Get the current weather for a city. Use this when the user asks about weather conditions, temperature, or if it's raining/sunny.'

The LLM uses the description to decide when to use the tool. Be specific.

**2. Not handling tool errors**
If a tool fails, the agent will see the error in the observation and might get stuck in a loop. Always return a clear error message.

**3. No max iterations**
Without `max_iterations`, an agent can loop forever. Always set a limit (5-10 is usually enough).

**4. Too many tools**
Don't give an agent 50 tools. It gets confused. Group related tools. Use multi-agent systems for complex tasks.

**5. No observability**
In production, you need to see what the agent is thinking and doing. Add logging. Use LangSmith or Helicone."

---

## HOMEWORK (23:00 - 24:00)

[VISUAL: Code editor showing starter code]

**NARRATOR:**
"Your homework is to extend this agent. Pick ONE of these:

**Option 1: Add a web search tool**
Use the Tavily API or SerpAPI to let your agent search the web.

**Option 2: Add a file reader tool**
Let your agent read and summarize PDF files.

**Option 3: Add a database query tool**
Connect to a SQLite database and let your agent answer questions about the data.

**Option 4: Build a research agent**
Combine web search + summarization to do multi-source research.

The starter code is in the GitHub repo. Link in the description.

Post your solutions in the Discord #showcase channel. I'll do code reviews on the best ones."

---

## WRAP-UP (24:00 - 25:00)

[VISUAL: Course logo + next lesson preview]

**NARRATOR:**
"That's Lesson 8.2. You now understand:
- What AI agents actually are
- The ReAct pattern
- How to build an agent from scratch
- How to give agents tools
- Common pitfalls to avoid

In the next lesson — **8.3: OpenAI Assistants API** — we'll look at how to use OpenAI's hosted agent framework. It's higher-level, easier to use, and handles a lot of the complexity we just dealt with manually.

If you enjoyed this, hit like, subscribe, and share with a friend who wants to learn AI engineering.

See you in the next one. 🚀"

[END SCREEN: Subscribe + next lesson]

---

## SLIDES / VISUAL AIDS

**Slide 1: Title**
- "Building Your First AI Agent"
- ReAct pattern diagram
- Course logo

**Slide 2: What is an Agent?**
- Think → Act → Observe loop diagram
- LLM = brain, Tools = hands

**Slide 3: Tools Format**
- JSON schema example
- Highlight: name, description, parameters

**Slide 4: The Loop**
- Pseudo-code for the ReAct loop
- Numbered steps

**Slide 5: Common Pitfalls**
- Top 5 mistakes list
- Icons for each

**Slide 6: Homework**
- 4 options
- GitHub link
- Discord link

**Slide 7: Next Lesson**
- OpenAI Assistants API preview
- "Coming up next"

---

## RESOURCES MENTIONED

- **Code:** https://github.com/aiforbiz/ai-engineer-course/tree/main/lesson-8-2
- **OpenAI Function Calling docs:** https://platform.openai.com/docs/guides/function-calling
- **ReAct paper:** https://arxiv.org/abs/2210.03629
- **LangChain agents:** https://python.langchain.com/docs/modules/agents/

---

## CHAPTERS (for YouTube)

```
0:00 - Cold open: agent in action
0:30 - What is an AI agent?
3:00 - Demo: what we're building
4:00 - Setup and dependencies
5:30 - Defining tools (JSON schema)
8:00 - The ReAct agent loop
14:00 - Testing with 4 real queries
18:00 - Production improvements
21:00 - Top 5 mistakes to avoid
23:00 - Homework & next lesson
```

---

**Duration:** 25 minutes
**Difficulty:** Intermediate
**Prerequisites:** Python, basic OpenAI API usage
**Next lesson:** 8.3 - OpenAI Assistants API
