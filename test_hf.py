import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv(".env")
token = os.environ.get("HUGGINGFACE_API_TOKEN")

if not token:
    print("No token found")
    exit(1)

print("Initializing InferenceClient with provider fal-ai...")
client = InferenceClient(
    provider="fal-ai",
    api_key=token
)

print("Client initialized. Testing basic API call...")
# We will just verify it can authenticate and load the model, 
# although we need an image to do image-to-image.
# Let's hit the text-to-image to see if the routing works for FLUX.2-dev
try:
    image = client.text_to_image(
        "A cute cat",
        model="black-forest-labs/FLUX.2-dev"
    )
    print("Success! Generated image size:", image.size)
    image.save("test_cat.png")
except Exception as e:
    print("Error during inference:")
    print(e)
