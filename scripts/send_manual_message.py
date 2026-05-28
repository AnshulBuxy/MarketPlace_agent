import asyncio
import sys
import os
from pathlib import Path

# Add project root to path so we can import backend
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

try:
    from backend.config import get_settings
    from backend.services.whatsapp import send_twilio_whatsapp_message
except ImportError as e:
    print(f"Error: Could not import backend modules. Make sure you are running from the project root. {e}")
    sys.exit(1)

async def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/send_manual_message.py <phone_number> <message>")
        print("Example: python scripts/send_manual_message.py +9193... 'Hello from manual override!'")
        return

    to_number = sys.argv[1]
    message_body = " ".join(sys.argv[2:])
    if message_body == 'x':
        message_body = '''Name: Handcrafted Metal Boat Pen Holder 
    Category: Home Decor
    Materials: Metal, Brass, Wrought Iron
    Dimensions: approximately 15-20 cm in length'
    Description: An intricate handcrafted metal showpiece shaped like a traditional boat (Mayurpankhi) featuring figures of musicians and a mesh-style pen holder. Finished in a golden metallic tone with red and black decorative accents.
    
    Please bata dijiye agar sab details sahi hain ya kuch changes karne hain.'''
    
    settings = get_settings()
    
    print(f"Sending message to {to_number}...")
    try:
        result = await send_twilio_whatsapp_message(settings, to_number, message_body)
        print(f"✅ Success! Message SID: {result.message_sid}")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")

if __name__ == "__main__":
    asyncio.run(main())
