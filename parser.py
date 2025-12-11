from openai import OpenAI
import instructor
from schemas import Transaction

LLM_URL = "http://localhost:11434/v1"
LLM_API_KEY = "ollama"
LLM_MODEL = "llama3.1"
LLM_PROMPT = "Ты финансовый парсер. Твоя задача — извлекать детали транзакции из текста."

openai_client = OpenAI(
    base_url=LLM_URL,
    api_key=LLM_API_KEY,
)

# path to get JSON response
client = instructor.from_openai(openai_client, mode=instructor.Mode.JSON)

def parse_expense(user_input: str) -> Transaction:
    print(f"Processing with ollama: {user_input}...")

    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system", 
                "content": LLM_PROMPT
            },
            {
                "role": "user", 
                "content": user_input
            },
        ],
        response_model=Transaction,
    )

    return resp
