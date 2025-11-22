from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List


class Page(BaseModel):
    text: str = Field(description="The text of the page")
    image_prompt: str = Field(description="The image prompt for LLM")


class Storybook(BaseModel):
    book_name: str = Field(description="Name of the storybook")
    pages: List[Page] = Field(description="List of pages in the storybook")

    model_config = {
        "arbitrary_types_allowed": True  # <- allows List[Page] to be accepted
    }


class Character(BaseModel):
    name: str = Field(description="Name of the character")
    trait: str = Field(description="Trait of the character")


class Story(BaseModel):
    story: str = Field(description="The story of the book")
    character: List[Character] = Field(description="List of characters")

    model_config = {
        "arbitrary_types_allowed": True
    }


# Optional: rebuild models to resolve forward references
Storybook.model_rebuild()
Story.model_rebuild()