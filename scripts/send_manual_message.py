import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

try:
    from backend.config import get_settings
    from backend.services.whatsapp import send_meta_whatsapp_message
except ImportError as e:
    print(f"Error: Could not import backend modules. Make sure you're running from the project root. {e}")
    sys.exit(1)


async def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/send_manual_message.py <phone_number> <message>")
        print("Example: python scripts/send_manual_message.py 919300000000 'Hello!'")
        return

    to_number = sys.argv[1]
    message_body = " ".join(sys.argv[2:])

    if message_body == "x":
        message_body = (
            "Name: Handcrafted Metal Boat Pen Holder\n"
            "Category: Home Decor\n"
            "Materials: Metal, Brass, Wrought Iron\n"
            "Dimensions: approximately 15-20 cm in length\n"
            "Description: An intricate handcrafted metal showpiece shaped like a traditional boat "
            "(Mayurpankhi) featuring figures of musicians and a mesh-style pen holder. "
            "Finished in a golden metallic tone with red and black decorative accents.\n\n"
            "Please bata dijiye agar sab details sahi hain ya kuch changes karne hain."
        )

    settings = get_settings()
    print(f"Sending message to {to_number}...")
    try:
        result = await send_meta_whatsapp_message(settings, to=to_number, text=message_body)
        print(f"✅ Success! Message ID: {result.message_id}")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")


if __name__ == "__main__":
    asyncio.run(main())
