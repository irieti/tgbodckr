from telethon import TelegramClient, events
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = str(os.getenv("API_HASH", ""))
target_group_ids_str = os.getenv("TARGET_GROUP_IDS", "")
target_group_ids = (
    list(map(int, target_group_ids_str.split(","))) if target_group_ids_str else []
)

source_ids_str = os.getenv("SOURCE_IDS", "")
source_ids = list(map(int, source_ids_str.split(","))) if source_ids_str else []

keywords_str = os.getenv("KEYWORDS", "")
keywords = keywords_str.split(",") if keywords_str else []

# Initialize the Telegram client
client = TelegramClient("userbot_session", API_ID, API_HASH)
message_queue = asyncio.Queue()


# Process and forward messages without delay or looping
async def process_message():
    while True:
        source_id, message = await message_queue.get()
        message_id = message.id

        # Get the name of the source group/channel
        try:
            source_entity = await client.get_entity(source_id)
            source_name = source_entity.title
        except Exception as e:
            print(f"Failed to get source name for ID {source_id}: {e}")
            source_name = "Unknown Source"

        # Forward the message along with the source name
        for group_id in target_group_ids:
            try:
                # Send the source name as a separate message
                await client.send_message(
                    group_id, f"Message from the group: {source_name}"
                )

                # Forward the original message
                await client.forward_messages(group_id, message)
                print(
                    f"Message ID:{message_id} from '{source_name}' forwarded to group with ID {group_id}"
                )
            except Exception as e:
                print(
                    f"Error forwarding message to group with ID {group_id} from '{source_name}': {e}"
                )

        message_queue.task_done()


# Adds a new message to the queue
async def add_message_to_queue(source_id, message):
    await message_queue.put((source_id, message))


# Event handler for new messages
@client.on(events.NewMessage(chats=source_ids))
async def handler(event):
    message = event.message
    message_text = message.message.lower()
    source_id = event.chat_id
    print(f"New message detected in source with ID {source_id}")

    # Check if message contains any of the keywords
    if any(keyword.lower() in message_text for keyword in keywords):
        print("Message contains keyword, adding to queue.")
        await add_message_to_queue(source_id, message)
    else:
        print("Message does not contain specified keywords. Skipping.")


# Function to generate a file with group IDs
async def get_group_ids():
    dialogs = await client.get_dialogs()
    with open("group_ids.txt", "w", encoding="utf-8") as file:
        for dialog in dialogs:
            if dialog.is_group or dialog.is_channel:
                file.write(f"Name: {dialog.name}, ID: {dialog.id}\n")
    print("Group IDs have been saved to group_ids.txt")


# Main function to start the client and manage tasks
async def main():
    await client.start()
    print("Client Created")

    # Generate the group IDs file
    await get_group_ids()

    # Start the message processing task
    asyncio.create_task(process_message())

    # Run the client until disconnected
    await client.run_until_disconnected()


# Run the main function within the client
if __name__ == "__main__":
    asyncio.run(main())
