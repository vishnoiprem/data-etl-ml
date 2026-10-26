"""
AI Prompt Generator - Lead magnet for the AI course
Takes a business problem and returns ready-to-use AI prompts.
Run: python prompt_generator.py
"""
import json
from pathlib import Path
from datetime import datetime


# A small library of prompt templates — extend as you grow
PROMPT_LIBRARY = {
    "customer_service": [
        {
            "title": "Customer Email Auto-Reply",
            "prompt": """You are a friendly customer service rep for {business_type}.
A customer just emailed: "{customer_question}"
Write a helpful, concise reply (under 150 words) that:
1. Acknowledges their question
2. Provides a clear answer
3. Offers further help
Use a warm, professional tone.""",
            "example_input": {"business_type": "an online clothing store", "customer_question": "Where's my order #12345?"}
        },
        {
            "title": "Refund Request Response",
            "prompt": """A customer requested a refund for {product}.
Write a reply that:
1. Empathizes with their experience
2. Explains the refund process (3-5 business days)
3. Offers a 20% discount on next order
4. Keeps the door open for feedback
Tone: understanding, not defensive. Under 120 words.""",
        },
        {
            "title": "FAQ Generator",
            "prompt": """Generate 20 frequently asked questions for a {business_type}.
For each FAQ, provide:
- Question
- Short answer (2-3 sentences)
Group by category: Orders, Products, Returns, Account, Shipping.
Make them sound like real customer questions.""",
        },
    ],
    "marketing": [
        {
            "title": "30-Day Content Calendar",
            "prompt": """Create a 30-day social media content calendar for {business_type}.
For each day provide:
- Day number
- Platform (rotate: LinkedIn, Instagram, TikTok, Facebook)
- Post topic
- Hook (first line that stops the scroll)
- 2-3 sentence caption
- Relevant hashtags (3-5)
Mix educational, behind-the-scenes, testimonials, and promotional posts.""",
        },
        {
            "title": "LinkedIn Post from Idea",
            "prompt": """Write a LinkedIn post about {topic}.
Structure:
- Hook (1 line, contrarian or surprising)
- Story or insight (3-5 short lines)
- 3 actionable takeaways (bullets)
- CTA question to drive comments
Tone: conversational, first-person, under 200 words.""",
        },
        {
            "title": "Email Subject Lines (10 variants)",
            "prompt": """Write 10 email subject lines for: {campaign_goal}
Constraints:
- Under 50 characters
- Create curiosity OR urgency OR personalization
- A/B test friendly (vary approach)
- No spam words (FREE, ACT NOW, $$$)
For each, predict open rate potential (high/med/low).""",
        },
    ],
    "operations": [
        {
            "title": "Process Documentation",
            "prompt": """Document the following business process: {process_description}
Output a step-by-step SOP:
1. Goal of the process
2. Who is responsible for each step
3. Step-by-step instructions (numbered)
4. Tools needed
5. Common errors and fixes
6. Estimated time per execution
Format as a clear checklist.""",
        },
        {
            "title": "Meeting Agenda",
            "prompt": """Create a meeting agenda for a {meeting_type} meeting.
Context: {context}
Include:
- Meeting goal (1 sentence)
- Pre-read items
- Agenda items with time allocations (60 min total)
- Discussion questions
- Action item template at end
- Who should attend""",
        },
    ],
    "strategy": [
        {
            "title": "Competitor Analysis",
            "prompt": """Analyze {competitor_name} as a competitor to my {your_business}.
Research and report on:
1. Their positioning and unique value prop
2. Pricing strategy
3. Content marketing approach
4. Strengths (3-5 points)
5. Weaknesses / gaps I can exploit (3-5 points)
6. 3 tactical moves I can make this month""",
        },
        {
            "title": "90-Day Plan",
            "prompt": """Create a 90-day plan to {goal}.
Break it into 3 monthly phases:
- Month 1: Foundation (what to set up)
- Month 2: Growth (what to scale)
- Month 3: Optimization (what to refine)
For each month, give:
- 3 main objectives
- Weekly milestones
- Key metrics to track
- Common pitfalls to avoid""",
        },
    ],
}


def get_categories():
    """Return all available categories"""
    return list(PROMPT_LIBRARY.keys())


def get_prompts_in_category(category):
    """Return all prompts in a category"""
    return [p["title"] for p in PROMPT_LIBRARY.get(category, [])]


def generate_prompt(category, prompt_title, variables=None):
    """
    Build a ready-to-use prompt. Substitutes user variables.
    Returns dict with title, prompt, and example.
    """
    prompts = PROMPT_LIBRARY.get(category, [])
    for p in prompts:
        if p["title"] == prompt_title:
            final = p["prompt"]
            if variables:
                try:
                    final = final.format(**variables)
                except KeyError as e:
                    return {
                        "error": f"Missing variable: {e}",
                        "required": [v for v in ["business_type", "customer_question", "topic", "campaign_goal", "process_description", "meeting_type", "context", "competitor_name", "your_business", "goal", "product"] if "{" + v + "}" in p["prompt"]]
                    }
            return {
                "title": p["title"],
                "category": category,
                "prompt": final,
                "example_input": p.get("example_input"),
                "instructions": "Copy this prompt and paste it into ChatGPT, Claude, or any AI tool."
            }
    return {"error": f"Prompt '{prompt_title}' not found in category '{category}'"}


def save_prompt(prompt_data, email=None):
    """Save to local JSON file (in production, save to database)"""
    log_file = Path("prompt_log.jsonl")
    entry = {
        "timestamp": datetime.now().isoformat(),
        "email": email or "anonymous",
        **prompt_data
    }
    with log_file.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return log_file


def interactive():
    """Interactive CLI mode"""
    print("=" * 60)
    print(" AI PROMPT GENERATOR ".center(60, "="))
    print("=" * 60)
    print("Get ready-to-use AI prompts for your business.\n")

    while True:
        print("\nCategories:")
        for i, cat in enumerate(get_categories(), 1):
            print(f"  {i}. {cat.replace('_', ' ').title()}")
        print("  q. Quit")

        choice = input("\nChoose a category (number): ").strip()
        if choice.lower() == "q":
            print("Thanks for using AI Prompt Generator!")
            break

        try:
            cat = get_categories()[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid choice. Try again.")
            continue

        print(f"\nPrompts in {cat.replace('_', ' ').title()}:")
        prompts = get_prompts_in_category(cat)
        for i, p in enumerate(prompts, 1):
            print(f"  {i}. {p}")

        p_choice = input("\nChoose a prompt (number): ").strip()
        try:
            title = prompts[int(p_choice) - 1]
        except (ValueError, IndexError):
            print("Invalid choice. Try again.")
            continue

        # Detect variables in the prompt
        template = next(p for p in PROMPT_LIBRARY[cat] if p["title"] == title)
        import re
        variables = re.findall(r"\{(\w+)\}", template["prompt"])
        values = {}
        for v in variables:
            val = input(f"  Enter {v}: ").strip()
            values[v] = val

        result = generate_prompt(cat, title, values)
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
            print(f"   Required: {result.get('required', [])}")
        else:
            print("\n" + "=" * 60)
            print(f" {result['title']} ".center(60, "-"))
            print("=" * 60)
            print(result["prompt"])
            print("=" * 60)
            print(f"\n{result['instructions']}\n")

            # Save to log
            email = input("Your email (to save this, optional): ").strip()
            log_file = save_prompt(result, email)
            print(f"✅ Saved to {log_file}")

            # Offer to copy to clipboard
            try:
                import pyperclip
                pyperclip.copy(result["prompt"])
                print("📋 Copied to clipboard!")
            except ImportError:
                pass


# Quick API for use in other tools
def list_all():
    """List all prompts in a tree"""
    print(json.dumps({cat: get_prompts_in_category(cat) for cat in get_categories()}, indent=2))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_all()
    else:
        interactive()
