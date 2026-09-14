import os
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEFAULT_MODEL = "gpt-4o-mini"  # swap for whichever model you're using


def generate_post(topic, tone="informative and engaging"):
    """
    Generate a full blog post draft from a topic.
    Returns a dict with 'title' and 'body', or raises AIServiceError on failure.
    """
    prompt = (
        f"Write a blog post about the following topic: {topic}\n\n"
        f"Tone: {tone}\n\n"
        "Respond in exactly this format:\n"
        "TITLE: <a compelling title>\n"
        "EXCERPT: <A short intro about the topic/title>\n"
        "BODY:\n<the full post body, well-structured with paragraphs>"
    )

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a skilled blog writer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1200,
        )
    except OpenAIError as e:
        raise AIServiceError(f"Failed to generate post: {e}") from e

    text = response.choices[0].message.content
    return _parse_generated_post(text)


def edit_post_content(existing_body, instruction):
    """
    Revise existing post content based on a free-text instruction.
    Returns the revised body as a string, or raises AIServiceError on failure.
    """
    prompt = (
        f"Here is a blog post draft:\n\n{existing_body}\n\n"
        f"Please revise it according to this instruction: {instruction}\n\n"
        "Return only the revised post body, with no extra commentary."
    )

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a skilled editor improving blog post drafts."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1200,
        )
    except OpenAIError as e:
        raise AIServiceError(f"Failed to edit post: {e}") from e

    return response.choices[0].message.content.strip()


def _parse_generated_post(text):
    """
    Splits the model's 'TITLE: ...\nEXCERPT: ...\nBODY:\n...' response
    into separate fields. Falls back gracefully if the model doesn't
    follow the format exactly.
    """
    title, excerpt, body = "", "", text.strip()

    if "TITLE:" in text and "EXCERPT:" in text and "BODY:" in text:
        try:
            title_part, rest = text.split("EXCERPT:", 1)
            excerpt_part, body_part = rest.split("BODY:", 1)

            title = title_part.replace("TITLE:", "").strip()
            excerpt = excerpt_part.strip()
            body = body_part.strip()
        except ValueError:
            pass  # fall back to using the raw text as body

    return {"title": title, "excerpt": excerpt, "body": body}


class AIServiceError(Exception):
    """Raised when the AI service fails to generate or edit content."""
    pass