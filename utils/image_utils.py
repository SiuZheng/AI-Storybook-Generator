from google import genai
from google.genai import types
import uuid
import os
import time
from PIL import Image
from google.genai.types import (
    HarmCategory,
    HarmBlockThreshold,
    SafetySetting,
    FinishReason
)
safety_settings = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.OFF,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.OFF,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.OFF,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.OFF,
    ),
]

def generate_image_nanobanana(image_prompts,characters=None,ratio="1.1"):
    """
    image_prompts: list of text prompts for each page
    ratio: image aspect ratio
    characters: optional list of dicts with keys: 'name', 'traits', 'image' (local file or uploaded)
    """
    output_dir = "images"
    os.makedirs(output_dir, exist_ok=True)
    CHAR_DIR = "characters"
    os.makedirs(CHAR_DIR, exist_ok=True)

    client = genai.Client()
    inline_requests = []
    characters_uriandmime=[]
    error = []
    for char in characters:
        char_image = char.get("image")
        char_file = client.files.upload(file=char_image)
        characters_uriandmime.append({"uri":char_file.uri,"mime_type":char_file.mime_type})

    for prompt in image_prompts:
            contents_list = []

            if characters:
                desc_text = "Character descriptions to maintain consistency:\n"
                
                for i,char in enumerate(characters):
                    char_image = char.get("image")
                    
                    if char.get("name") or char.get("traits"):
                        desc_text += f"Character: {char.get('name', '')}\nTraits: {char.get('traits', '')}\n\n"     

                    contents_list.append({
                            "file_data": {"file_uri": characters_uriandmime[i]["uri"], "mime_type": characters_uriandmime[i]["mime_type"]}
                        })
                if desc_text.strip():
                    prompt = f"Image Prompt :{prompt}"
                    prompt +=f" \n{desc_text}"
            prompt+= "No wording in the image. "       
            contents_list.append({"text": prompt})
            inline_requests.append({
                "contents": [
                    {
                        "parts": contents_list,
                        "role": "user"
                    }
                ],
                "config": types.GenerateContentConfig(
                    image_config=types.ImageConfig(aspect_ratio=ratio),
                    safety_settings= safety_settings
                )
            })
    inline_batch_job = client.batches.create(
    model="models/gemini-2.5-flash-image",
    src=inline_requests,
    config={
        'display_name': "inlined-requests-job-1",
    },
    )
    job_name = inline_batch_job.name
    print(f"Polling status for job: {job_name}")
    while True:
        batch_job_inline = client.batches.get(name=job_name)
        if batch_job_inline.state.name in ('JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED', 'JOB_STATE_EXPIRED'):
            break
        print(f"Job not finished. Current state: {batch_job_inline.state.name}. Waiting 30 seconds...")
        time.sleep(30)
    print(f"Job finished with state: {batch_job_inline.state.name}")
    if batch_job_inline.state.name == 'JOB_STATE_SUCCEEDED':
        img_path=[]
    for i, inline_response in enumerate(batch_job_inline.dest.inlined_responses, start=1):
        print(f"\n--- Response {i} ---")
        unique_filename = f"output_{i} {uuid.uuid4().hex}.png"
        output_path = os.path.join("images", unique_filename)
        if inline_response.response:
            if getattr(inline_response.response, "prompt_feedback", None) is not None:
                if inline_response.response.prompt_feedback.block_reason is not None:
                    print("Response blocked:", inline_response.response.prompt_feedback.block_reason)
                    img_path.append("")
                    error.append(inline_response.response.prompt_feedback.block_reason)
            elif (inline_response.response.candidates[0].finish_reason==FinishReason.STOP):
                for part in inline_response.response.candidates[0].content.parts:
                    if part.text is not None:
                        print(part.text)
                    elif part.inline_data is not None:
                        image = part.as_image()
                        image.save(output_path)
                        img_path.append(output_path)
                error.append("")
            else:
                img_path.append("")
                error.append(inline_response.response.candidates[0].finish_reason)
    return img_path,error

def generate_character_nanobanana(characters,genre,tone,art_style,i,ratio):
    CHAR_DIR = "characters"
    os.makedirs(CHAR_DIR, exist_ok=True)
    client = genai.Client()
    prompt = (
        "Generate A character based on the details below, ensure the quality of the character. (Dont include any words)" \
        "Do not include additional character in the picture unless stated."
        f"A {art_style} illustration of the character.\n"
        f"Genre: {genre}. Tone: {tone}.\n"
        f"Character details: {characters}\n"
    )

    response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio=ratio,
                ),
                safety_settings= safety_settings
            )
        )
    
    save_path = None
    error=""
    if getattr(response, "prompt_feedback", None) is not None:
        if response.prompt_feedback.block_reason is not None:
            error = response.prompt_feedback.block_reason
            return save_path,error
    if response.parts:
        for part in response.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                save_path = os.path.join(CHAR_DIR, f"character_{i+1} {uuid.uuid4().hex}.jpg")
                image = part.as_image()
                image.save(save_path)
    else:
        error= "the model did not return any picture."
    return save_path,error

def regenerate_image_nanobanana(prompt, characters=None, ratio="1:1"):
    """
    Regenerates a single image based on the prompt and characters.
    """

    output_dir = "images"
    os.makedirs(output_dir, exist_ok=True)
    
    client = genai.Client()
    parts = []
    error = ""
    if characters:
        desc_text = "Character descriptions to maintain consistency:\n"
        for char in characters:
            if char.get("name") or char.get("traits"):
                desc_text += f"Character: {char.get('name', '')}\nTraits: {char.get('traits', '')}\n\n"
            char_image = char.get("image")
            if char_image:
                char_file = client.files.upload(file=char_image)
                parts.append(types.Part(
                    file_data=types.FileData(
                        file_uri=char_file.uri,
                        mime_type=char_file.mime_type
                    )
                ))
        
        if desc_text.strip():
            prompt = f"User Prompt :{prompt}"
            prompt +=f" \n{desc_text}"

    prompt += "No wording in the image. "
    parts.append(types.Part(text=prompt))

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=parts,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio=ratio),
            safety_settings= safety_settings
        )
    )
    save_path = None
    
    if getattr(response, "prompt_feedback", None) is not None:
        if response.prompt_feedback.block_reason is not None:
            print("Response blocked:", response.prompt_feedback.block_reason)
            error=response.prompt_feedback.block_reason
            return save_path,error
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                unique_filename = f"output_{uuid.uuid4().hex}.png"
                save_path = os.path.join(output_dir, unique_filename)
                image = part.as_image()
                image.save(save_path)
                break # Only save the first image found
    else:
        error= "the model did not return any picture."
    return save_path,error

def regenerate_image_with_image_nanobanana(prompt, original_image_path, characters=None, ratio="1:1"):
    """
    Regenerates an image using an existing image as input (Image-to-Image).
    """
    output_dir = "images"
    os.makedirs(output_dir, exist_ok=True)
    
    client = genai.Client()
    parts = []
    error=""
    if original_image_path and os.path.exists(original_image_path):
        original_file = client.files.upload(file=original_image_path)
        parts.append(types.Part(
            file_data=types.FileData(
                file_uri=original_file.uri,
                mime_type=original_file.mime_type
            )
        ))
        parts.append(types.Part(text="Edit the picture based on this picture"))
    
    if characters:
        desc_text = "Character descriptions to maintain consistency:\n"
        for char in characters:
            if char.get("name") or char.get("traits"):
                desc_text += f"Character: {char.get('name', '')}\nTraits: {char.get('traits', '')}\n\n"
            
            char_image = char.get("image")
            if char_image:
                char_file = client.files.upload(file=char_image)
                parts.append(types.Part(
                    file_data=types.FileData(
                        file_uri=char_file.uri,
                        mime_type=char_file.mime_type
                    )
                ))
        
        if desc_text.strip():
            prompt = f"User Prompt :{prompt}"
            prompt +=f" \n{desc_text}"

    prompt += "No wording in the image. "
    parts.append(types.Part(text=prompt))
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=parts,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio=ratio),
            safety_settings= safety_settings
        )
    )

    save_path = None
    if getattr(response, "prompt_feedback", None) is not None:
        if response.prompt_feedback.block_reason is not None:
            print("Response blocked:", response.prompt_feedback.block_reason)
            error = response.prompt_feedback.block_reason
            return save_path,error
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                unique_filename = f"output_{uuid.uuid4().hex}.png"
                save_path = os.path.join(output_dir, unique_filename)
                image = part.as_image()
                image.save(save_path)
                break # Only save the first image found
    else:
        error= "the model did not return any picture."
    return save_path,error

def regenerate_character_with_image_nanobanana(character_description, original_image_path, genre, tone, art_style, ratio="1:1"):
    """
    Regenerates a character image using an existing image as input (Image-to-Image).
    """
    output_dir = "characters"
    os.makedirs(output_dir, exist_ok=True)
    client = genai.Client()

    prompt = f"""
    You are a professional character designer for a {genre} storybook.
    The tone of the story is {tone}.
    The art style is {art_style}.

    Please redesign the character based on the provided image and the following description:
    {character_description}

    Ensure the character design is consistent with the art style and tone.
    Ensure there is no extra character unless stated.
    """

    parts = []
    error=""
    try:
        if os.path.exists(original_image_path):
            image = Image.open(original_image_path)
            parts.append(image)
            parts.append(types.Part(text="Edit the character based on this picture"))
        else:
            print(f"Error: Original image not found at {original_image_path}")
            return None
    except Exception as e:
        print(f"Error loading original image: {e}")
        return None

    parts.append(types.Part(text=prompt))

    response = client.models.generate_content(
        model="models/gemini-2.5-flash-image",
        contents=parts,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio=ratio),
            safety_settings= safety_settings
        )
    )

    save_path = None
    if getattr(response, "prompt_feedback", None) is not None:
        if response.prompt_feedback.block_reason is not None:
            print("Response blocked:", response.prompt_feedback.block_reason)
            error = response.prompt_feedback.block_reason
            return save_path,error
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                unique_filename = f"character_regen_{uuid.uuid4().hex}.png"
                save_path = os.path.join(output_dir, unique_filename)
                image = part.as_image()
                image.save(save_path)
                break 
    else:
        error= "the model did not return any picture."
    return save_path,error