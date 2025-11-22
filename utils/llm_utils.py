from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List
from utils.model_story import Storybook, Story

STORYBOOK_SCHEMA = Storybook.model_json_schema()
STORY_SCHEMA =Story.model_json_schema()
def generate_page_prompt(title, genre, tone, art_style,pages,age,characters,story):
    """Generate a short story page and image prompt."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    story=story
    structured_llm = llm.with_structured_output(
        schema=STORYBOOK_SCHEMA, method="json_schema"
    )
    character_text = ""
    if characters:
        character_text = "Main Characters:\n"
        for char in characters:
            character_text += f"- Name: {char['name']}\n  Traits: {char['traits']}\n"
        character_text += (
            "\nUse ONLY these characters in the story. "
            "Ensure they appear consistently across all pages.\n"
        )
        include_character_in_prompt = (
            "- If characters appear in the scene, include them clearly in the image prompt, "
            "with specific attention to their pose, facial expression, and position.\n"
        )
    prompt = f"""
    Generate image prompt for illustrated storybook titled "{title}".
    With story:{story}
    Genre: {genre}. Tone: {tone}. Age:{age}
    
    {character_text if characters else ''}

    Each page prompt should contain:
    - The story text (length appropriate for the audience's age; short and simple for younger readers).
    - Details of the environment.
    - Colour and shape for items to ensure consistency.
    - A matching image prompt describing the scene using this art style: {art_style}.
    {include_character_in_prompt if characters else ''}
    - Make Sure the prompt is very detailed 5-6 sentences.
    Generate exactly {pages} pages.

    Return the result in JSON format:
    {{
      "book_name": "...",
      "pages": [
        {{
          "text": "story text here",
          "image_prompt": "image description here"
        }}
      ]
    }}

    Example:
    {{
    "book_name":"a lost banana",
    "pages":[
      {{
        "text":"Once upon a time...",
        "image_prompt":"A watercolor painting of a banana in a forest."
      }}
    ]
    }}
    """

    response = structured_llm.invoke(prompt)
    try:

        return response
    except Exception:
        return  {
            "book_name":"a lost banana",
            "pages":[
                {
                    "text":"Once upon a time...",
                    "image_prompt":"A watercolor painting of a banana in a forest."
                },
            ]
        }
    
def generate_story_prompt(title, genre, tone, art_style,page,age):
    """
    Generate a natural-language prompt for the LLM to create a story.

    Args:
        title (str): The title of the story.
        genre (str): The genre of the story (e.g., Fantasy, Adventure).
        tone (str): The tone/mood of the story (e.g., Heartwarming, Whimsical).
        art_style (str): Art style for illustrations (e.g., Watercolor, Cartoonish).
        num_pages (int): Number of pages / story length.
        characters (list of dict, optional): List of character dicts with 'name' and 'traits'.
        audience (str, optional): Target audience or reading level.

    Returns:
        str: A formatted string prompt suitable for sending to an LLM.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    structured_llm = llm.with_structured_output(
        schema=STORY_SCHEMA, method="json_schema"
    )
    prompt = f"""
    Write a {page}-page {genre} story titled '{title}'
    with a {tone.lower() if tone else 'neutral'} tone
    for {age if age else 'children'}.
    If age is very small, the story should be very short and easy.
    Illustrate the story in {art_style if art_style else 'default style'}.
    Write the full story in a complete narrative with a proper ending and natural flow. 
    Ensure the story is exactly for {page} pages.

    Additionally, suggest 1-5 main characters of the story.(Only include nenecessary characters that appeared in the story and ensure the least characters is in the story, maximum of 5 characters allowed)
    The trait of the characters should be very detailed, in terms of clothing, the background, looking, characteristic.
    Return the result in JSON format:
    {{
      "story": "...",
      "character": [
        {{
          "name": "character name",
          "trait": "character's trait and characteristic"
        }}
      ]
    }}

    Example:
    {{
    "story":"Once upon a time...",
    "character":[
      {{
        "name":"Jane Doe",
        "trait":"A lion, brave, black color, tall"
      }}
    ]
    }}
    """

    response = structured_llm.invoke(prompt)
    try:
        return response
    except Exception:
        return  {
            "story":"Once upon a time...",
            "character":[
                {
                    "name":"Jane Doe",
                    "trait":"A lion, brave, black color, tall"
                },
            ]
        }