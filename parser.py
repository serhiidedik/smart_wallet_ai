import base64
from openai import OpenAI
import instructor
from schemas import Transaction

LLM_URL = "http://localhost:11434/v1"
LLM_API_KEY = "ollama"
LLM_TEXT_MODEL = "llama3.1"
LLM_VISION_MODEL = "llava"

# Llama 3.1 handles Russian instructions well
LLM_TEXT_PROMPT = "Ты финансовый парсер. Твоя задача — извлекать детали транзакции из текста."

# Llava follows structure better with English instructions
LLM_VISION_PROMPT = (
    "Analyze this receipt image. Extract total amount, merchant name, and category. "
    "Return the result ONLY as a JSON object matching the schema."
)

openai_client = OpenAI(
    base_url=LLM_URL,
    api_key=LLM_API_KEY,
)

# Patch client. MD_JSON mode handles markdown code blocks common in LLM responses
client = instructor.from_openai(openai_client, mode=instructor.Mode.MD_JSON)

def parse_expense(user_input: str) -> Transaction:
    print(f"Processing text with {LLM_TEXT_MODEL}: {user_input}...")

    resp = client.chat.completions.create(
        model=LLM_TEXT_MODEL,
        messages=[
            {"role": "system", "content": LLM_TEXT_PROMPT},
            {"role": "user", "content": user_input},
        ],
        response_model=Transaction,
    )

    return resp

# Helper: convert image to base64 string
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Parse image using vision model
def parse_receipt_image(image_path: str) -> Transaction:
    print(f"👀 Scanning: {image_path}...")
    base64_image = encode_image(image_path)

    return client.chat.completions.create(
        model=LLM_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": LLM_VISION_PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
        response_model=Transaction,
        max_retries=3, # Give it a few tries if validation fails
    )