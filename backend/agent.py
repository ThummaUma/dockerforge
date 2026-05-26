import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def clean_dockerfile(content):
    if not content:
        return "FROM python:3.9-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"python\", \"app.py\"]"
    content = content.strip()
    if "```dockerfile" in content:
        content = content.split("```dockerfile")[1]
        content = content.split("```")[0]
    elif "```" in content:
        content = content.split("```")[1]
        if "```" in content:
            content = content.split("```")[0]
    return content.strip()

def generate_dockerfile(file_summary):
    try:
        msg = """Generate a simple working Dockerfile for this Python repository.

STRICT RULES:
- Start directly with FROM, no markdown, no backticks
- Use python:3.9-slim as base image
- If requirements.txt has psycopg2 or psycopg2-binary, add this line before pip install:
  RUN apt-get update && apt-get install -y libpq-dev gcc
- If requirements.txt has any C dependencies add libpq-dev gcc
- Keep it simple and working

Repository files:
""" + file_summary[:3000]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[
                {
                    "role": "system",
                    "content": "You are a Docker expert. Respond with ONLY raw Dockerfile content. No markdown. No backticks. No explanations. Start directly with FROM. For Python projects with psycopg2, always install libpq-dev and gcc first."
                },
                {
                    "role": "user",
                    "content": msg
                }
            ]
        )
        result = response.choices[0].message.content
        return clean_dockerfile(result)
    except Exception as e:
        return "FROM python:3.9-slim\nWORKDIR /app\nRUN apt-get update && apt-get install -y libpq-dev gcc\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"python\", \"app.py\"]"

def fix_dockerfile(dockerfile, error):
    try:
        msg = """Fix this Dockerfile error.

STRICT RULES:
- Return ONLY fixed Dockerfile starting with FROM
- No markdown, no backticks, no explanations
- If error mentions pg_config or psycopg2, add:
  RUN apt-get update && apt-get install -y libpq-dev gcc
- If error mentions missing libraries, install them with apt-get

Current Dockerfile:
""" + dockerfile + """

Error:
""" + error[:500]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[
                {
                    "role": "system",
                    "content": "You are a Docker expert. Respond with ONLY raw Dockerfile content. No markdown. No backticks. Start directly with FROM."
                },
                {
                    "role": "user",
                    "content": msg
                }
            ]
        )
        result = response.choices[0].message.content
        return clean_dockerfile(result)
    except Exception as e:
        return dockerfile