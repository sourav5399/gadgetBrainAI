import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
MODEL = ("gpt-5-nano", "gpt-4.1-mini")

api_key = os.getenv('OPENAI_API_KEY')

system_prompt = """
You are a gadget expert.

You must ALWAYS return valid JSON only (no markdown, no extra text).

Return exactly one of these shapes:

1) Need more info:
{
  "status": "need_more_info",
  "question": "single clear follow-up question"
}

2) Final recommendation:
{
  "status": "final_recommendation",
  "recommendation": "detailed recommendation text in plain string"
}

Rules:
- Ask follow-up if budget, location/currency, usage pattern, or category is unclear. (all of these are important to make a good recommendation)
- If user gives mixed categories, ask to choose one category first. Mix categories are not allowed. Mixed categories means user cannot compare products from different categories. 
Like phone and laptops cannot be compared. simlarly you cannot compare a laptop with an AC. Prompt the user to choose one category first.
- When enough info is available, return final_recommendation.
"""

def create_client(base_url=None, api_key_override=None):
    """Create an OpenAI-compatible client."""
    resolved_api_key = api_key_override or api_key
    return OpenAI(api_key=resolved_api_key)


def normalize_products(raw_products):
    """Convert comma-separated products into a cleaned list."""
    return [p.strip() for p in raw_products.split(",") if p.strip()]


def build_initial_user_message(products):
    """Create the first user message from selected products."""
    products_text = ", ".join(products)
    return (
        f"These are the products I'm considering: {products_text}. "
        "Help me choose the best one."
    )


def build_messages(initial_user_message):
    """Create initial conversation with system prompt and first user turn."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": initial_user_message},
    ]


def get_json_reply(client, messages, model=MODEL):
    """Get assistant reply and parse expected JSON schema."""
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    raw = response.choices[0].message.content.strip()
    # Try strict JSON parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: force model to fix format
        fix_messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "Return the previous answer as valid JSON only, matching required schema."}
        ]
        fixed = client.chat.completions.create(
            model=model,
            messages=fix_messages,
            temperature=0
        ).choices[0].message.content.strip()
        return json.loads(fixed)

def main():
    # Initial products input
    client = create_client()
    print("Compare Agent: Hello! I'm here to help you choose the best product.\n What products are you considering?\n Enter the products separated by commas.")
    raw_products = input("You: ")
    products = normalize_products(raw_products)
    first_user_message = build_initial_user_message(products)
    messages = build_messages(first_user_message)

    while True:
        data = get_json_reply(client, messages)

        status = data.get("status")

        if status == "need_more_info":
            question = data.get("question", "Please provide more details.")
            print(f"\nCompare Agent: {question}")
            user_reply = input("You: ")

            # Keep conversation history
            messages.append({"role": "assistant", "content": json.dumps(data)})
            messages.append({"role": "user", "content": user_reply})

        elif status == "final_recommendation":
            recommendation = data.get("recommendation", "No recommendation provided.")
            print("\nCompare Agent Recommendation:\n")
            print(recommendation)
            break

        else:
            # Safety fallback if schema is wrong
            print("\nCompare Agent returned unexpected format. Asking again...")
            messages.append({"role": "assistant", "content": json.dumps(data)})
            messages.append({
                "role": "user",
                "content": "Your JSON format was invalid. Return one of the two required schemas exactly."
            })

if __name__ == "__main__":
    main()