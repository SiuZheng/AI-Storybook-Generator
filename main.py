import streamlit as st
from utils.llm_utils import generate_page_prompt,generate_story_prompt
from utils.image_utils import generate_image_nanobanana,generate_character_nanobanana,regenerate_image_nanobanana,regenerate_character_with_image_nanobanana
import uuid
import os
from PIL import Image
import zipfile
import io


if "character_version" not in st.session_state:
    st.session_state.character_version = 0
if "num_characters" not in st.session_state:
    st.session_state.num_characters = 0
if "character_data" not in st.session_state:
    st.session_state.character_data = []
if "generated_characters" not in st.session_state:
    st.session_state.generated_characters = []
def handle_file_upload(i,CHAR_DIR):
    uploaded_file = st.session_state.get(f"image_{i}")
    if uploaded_file is not None:
        save_path = os.path.join(CHAR_DIR, f"character_{i+1} {uuid.uuid4().hex}.jpg")
        image = Image.open(uploaded_file)
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(save_path)
        st.session_state.character_data[i]["image"] = save_path

def all_characters_valid(characters):
    for c in characters:
        if not c.get("name") or not c.get("traits") or not c.get("image"):
            return False
    return True

def update_character_name(i):
    name = st.session_state.get(f"name_{i}_{st.session_state.character_version}", "")
    st.session_state.character_data[i]["name"] = name

def update_character_traits(i):
    traits = st.session_state.get(f"traits_{i}_{st.session_state.character_version}", "")
    st.session_state.character_data[i]["traits"] = traits

CHAR_DIR = "characters"
os.makedirs(CHAR_DIR, exist_ok=True)
st.set_page_config(page_title="AI Storybook Page", layout="wide") # Changed to wide for better layout
st.title("📖 AI Storybook Generator")

if "character_version" not in st.session_state:
    st.session_state.character_version = 0
if "generated_story" not in st.session_state:
    st.session_state.generated_story = ""
if "story_data" not in st.session_state:
    st.session_state.story_data = None
if "img_paths" not in st.session_state:
    st.session_state.img_paths = []

# --------------------------
#     SIDEBAR: CONFIGURATION
# --------------------------
with st.sidebar:
    api_key = st.text_input("Enter your API Key:", type="password")
    if api_key:
        st.session_state["GOOGLE_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key  # Set temporarily for current session
        st.success("API Key successfully loaded for this session!")

    st.header("🛠 Story Configuration")

    # --- Story inputs ---
    with st.expander("📌 Story Information", expanded=True):
        title = st.text_input("Story Title", placeholder="The Lost Puppy")

        genre_options = [
            "Children", "Fantasy", "Adventure", "Sci-Fi",
            "Mystery", "Fairy Tale", "Historical", "Comedy",
            "Animal Story", "Friendship", "Magical Realism",
            "Superhero", "Mythology", "Educational", "Slice of Life"
        ]
        genre_select = st.selectbox("Genre", genre_options, index=0)
        genre_custom = st.text_input("Custom Genre (optional)")

        genre = genre_custom if genre_custom else genre_select
        age = st.text_input("Target Age / Reading Level", placeholder="5-7")

    with st.expander("🎭 Tone & Writing Style", expanded=False):
        tone_options = [
            "Heartwarming", "Whimsical", "Exciting", "Calm and Peaceful",
            "Mysterious", "Inspirational", "Funny and Playful", "Adventurous",
            "Dreamy and Magical", "Dramatic", "Hopeful", "Serious",
            "Suspenseful", "Uplifting", "Melancholic (Gentle Sadness)"
        ]
        tone_select = st.selectbox("Tone", tone_options, index=0)
        tone_custom = st.text_input("Custom Tone (optional)")

        tone = tone_custom if tone_custom else tone_select
        art_style = st.text_input("Art Style", "Watercolor illustration, soft colors")

    with st.expander("🖼 Page Settings", expanded=False):
        ratio = st.selectbox(
            "Image Aspect Ratio",
            ["1:1", "16:9", "9:16", "4:3", "3:4"],
            index=0
        )
        num_pages = st.number_input(
            "Number of Pages", 
            min_value=1, 
            max_value=100, 
            value=10,  # default
            step=1
        )

# --------------------------
#     MAIN AREA: TABS
# --------------------------
tab1, tab2 = st.tabs(["✍️ Create Story", "📖 Read Storybook"])

with tab1:
    st.header("1. Generate Story Text")
    if st.button("✨ Generate Story", key="generate_story_button"):
        with st.spinner("Generating story..."):
            try:
                storybook = generate_story_prompt(title, genre, tone, art_style, num_pages, age)
                st.session_state.generated_story = storybook.get("story", "")
                st.session_state.generated_characters = storybook.get("character", [])[:5]  # max 5 characters
                st.session_state.character_data = []
                for char in st.session_state.generated_characters:
                    st.session_state.character_data.append({
                        "name": char.get("name", ""),
                        "traits": char.get("trait", ""),
                        "image": None
                    })

                st.session_state.num_characters = len(st.session_state.generated_characters)
                st.session_state.character_version += 1
            except Exception as e:
                st.error(f"Story generation failed: {e}")
                st.session_state.generated_story = ""
                st.session_state.generated_characters = []

    # Display / Edit Generated Story
    st.subheader("📝 Generated Story (Editable)")
    st.text_area(
        "Edit the story here:",
        key="generated_story",  # binds to session_state directly
        height=300
    )

    st.divider()
    st.header("2. Character Setup")
    
    # Number of characters (optional)
    num_characters = st.number_input("Number of Main Characters (optional)", min_value=0, max_value=5, value=st.session_state.get("num_characters", 0), step=1)

    for i in range(num_characters):
        existing = st.session_state.character_data[i] if i < len(st.session_state.character_data) else {}
        with st.expander(f"Character {i+1}", expanded=False):
            # Pre-fill from session state if exists
            while len(st.session_state.character_data) <= i:
                st.session_state.character_data.append({"name": "", "traits": "", "image": None})
            
            char_name = st.text_input(f"Character {i+1} Name", value=existing.get("name", ""), key=f"name_{i}_{st.session_state.character_version}",on_change=update_character_name,args=[i])
            char_traits = st.text_area(f"Character {i+1} Traits / Description", value=existing.get("traits", ""), key=f"traits_{i}_{st.session_state.character_version}",on_change=update_character_traits,args=[i])
            char_image_upload = st.file_uploader(f"Upload Character {i+1} Image (optional)", type=["png","jpg"], key=f"image_{i}",on_change=handle_file_upload,args=[i,CHAR_DIR])
            # Button to generate image via Nanobanana  
            if st.button(f"Generate Character {i+1} Image via Nanobanana", key=f"generate_{i}"):
                if not char_name and not char_traits:
                    st.warning("Please enter a name or traits to generate the character image.")
                else:
                    with st.spinner(f"Generating image for Character {i+1}..."):
                        char_image_path = generate_character_nanobanana([f"{char_name}, {char_traits}"], genre,tone,art_style,i,ratio=ratio)
                        st.session_state.character_data[i]["image"] = char_image_path

            # Button to regenerate character with original image
            if st.button(f"🔄 Re-generate Character {i+1} with Original Image", key=f"regen_char_{i}"):
                if not st.session_state.character_data[i]["image"]:
                    st.warning("Ensure to have a picture")
                else:
                    with st.spinner(f"Regenerating image for Character {i+1} using original image..."):
                        new_char_path = regenerate_character_with_image_nanobanana(
                            character_description=f"{char_name}, {char_traits}",
                            original_image_path=st.session_state.character_data[i]["image"],
                            genre=genre,
                            tone=tone,
                            art_style=art_style,
                            ratio=ratio
                        )
                        if new_char_path:
                            st.session_state.character_data[i]["image"] = new_char_path
                            st.session_state.character_version += 1
                            st.rerun()
                        else:
                            st.error("Failed to regenerate character image.")
            if st.session_state.character_data[i]["image"]:
                st.image(st.session_state.character_data[i]["image"], caption=f"{char_name if char_name else 'Generated Character'} Image", width=300)

    # Button to clear all characters
    if st.button("Clear All Characters"):
        st.session_state.character_data = []
        st.session_state.generated_characters = []
        st.session_state.num_characters = 0
        st.session_state.character_version += 1

    st.divider()
    st.header("3. Generate Illustrations")
    generate = st.button("✨ Generate Images")

    if generate:
        if not title:
            st.warning("Please enter a story title.")
            st.stop()

        if not st.session_state.generated_story:
            st.warning("Please ensure the story is generated")
            st.stop()

        if st.session_state.character_data:
            st.session_state.character_data = st.session_state.character_data[:num_characters]
            if not all_characters_valid(st.session_state.character_data):
                print(st.session_state.character_data)
                st.warning("Please complete ALL character fields (name, traits, and image).")
                st.stop()

        # Generate story text
        with st.spinner("🧠 Generating image prompt..."):
            st.session_state.story_data = generate_page_prompt(
                            title, 
                            genre, 
                            tone, 
                            art_style, 
                            num_pages,
                            age,
                            st.session_state.character_data,
                            st.session_state.generated_story
                        )

        # Generate images
        with st.spinner("🎨 Generating illustrations..."):
            image_prompts = [page["image_prompt"] for page in st.session_state.story_data["page"]]
            st.session_state.img_paths = generate_image_nanobanana(image_prompts, characters=st.session_state.character_data,ratio=ratio)
        
        st.success("Images generated! Switch to the 'Read Storybook' tab to view them.")
        st.session_state.character_version += 1

with tab2:
    if st.session_state.story_data and st.session_state.img_paths:
        st.header("📥 Download")
        download_option = st.radio("Choose download:", ["All", "Story Images", "Character Images"], horizontal=True)
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            if download_option in ["All", "Story Images"]:
                for i, path in enumerate(st.session_state.img_paths):
                    if os.path.exists(path):
                        ext = os.path.splitext(path)[1]
                        zf.write(path, arcname=f"story_images/{i+1}{ext}")
            
            if download_option in ["All", "Character Images"]:
                for i, char in enumerate(st.session_state.character_data):
                    path = char.get("image")
                    if path and os.path.exists(path):
                        ext = os.path.splitext(path)[1]
                        zf.write(path, arcname=f"characters/{i+1}{ext}")
        
        st.download_button(
            label="Download ZIP",
            data=zip_buffer.getvalue(),
            file_name="storybook_assets.zip",
            mime="application/zip"
        )
        st.divider()

        st.header("📚 Story Output")

        # Ensure we have enough image paths (handle potential mismatches if generation failed partially)
        # In a real app, you'd want more robust error handling here.
        
        for i, page in enumerate(st.session_state.story_data["page"], start=1):
            st.subheader(f"Page {i}")

            # Create two columns: left for image, right for text
            col1, col2 = st.columns([1, 1])  # equal width, adjust ratio if needed

            # Left column: image
            with col1:
                if i-1 < len(st.session_state.img_paths):
                    st.image(st.session_state.img_paths[i-1], caption=f"Page {i} Illustration", width=400)
                else:
                    st.warning("Image not available.")

            # Right column: text
            with col2:
                st.write(page["text"])
                
                # Editable Image Prompt
                new_prompt = st.text_area(f"Image Prompt for Page {i}", value=page['image_prompt'], key=f"prompt_{i}_{st.session_state.character_version}")
                
                # Update prompt in session state if changed
                if new_prompt != page['image_prompt']:
                    st.session_state.story_data["page"][i-1]["image_prompt"] = new_prompt
                
                # Re-generate Button
                if st.button(f"🔄 Re-generate Image {i}", key=f"regen_{i}"):
                    with st.spinner(f"Regenerating image for Page {i}..."):
                        
                        new_img_path = regenerate_image_nanobanana(
                            new_prompt, 
                            characters=st.session_state.character_data, 
                            ratio=ratio
                        )
                        if new_img_path:
                            # Update the image path in session state
                            if i-1 < len(st.session_state.img_paths):
                                st.session_state.img_paths[i-1] = new_img_path
                            else:
                                # If for some reason the list was shorter, append (though index logic should hold)
                                st.session_state.img_paths.append(new_img_path)
                            st.rerun()
                        else:
                            st.error("Failed to regenerate image.")

                # Re-generate with Original Image Button
                if st.button(f"🔄 Re-generate with Original Image {i}", key=f"regen_img_{i}"):
                    with st.spinner(f"Regenerating image for Page {i} using original image..."):
                        from utils.image_utils import regenerate_image_with_image_nanobanana
                        
                        current_img_path = st.session_state.img_paths[i-1]
                        new_img_path = regenerate_image_with_image_nanobanana(
                            new_prompt, 
                            original_image_path=current_img_path,
                            characters=st.session_state.character_data, 
                            ratio=ratio
                        )
                        if new_img_path:
                            # Update the image path in session state
                            if i-1 < len(st.session_state.img_paths):
                                st.session_state.img_paths[i-1] = new_img_path
                            else:
                                st.session_state.img_paths.append(new_img_path)
                            st.rerun()
                        else:
                            st.error("Failed to regenerate image.")
    else:
        st.info("Go to the 'Create Story' tab to generate your storybook first!")
