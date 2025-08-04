import asyncio
import json
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from telegram import Message, PhotoSize
from telegram.ext import ContextTypes
from openai import OpenAI
from config import BOT_TOKEN, OPENROUTER_API_KEY, MODEL
from tools import TOOL_MAPPING
from tools_def import tools
from models import save_message_orm, get_conversation_messages_orm
import threading
from health import start_health_server

# OpenAI via OpenRouter
openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# System prompt
with open("prompt.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Utility: get image URL from Telegram file_id
async def get_telegram_file_url(context: ContextTypes.DEFAULT_TYPE, file_id: str) -> str:
    try:
        file = await context.bot.get_file(file_id)
        return f"{file.file_path}"
    except Exception as e:
        return f"Error fetching file: {e}"

# Main processing logic for LLM + tool
async def process_llm(update: Update, context: ContextTypes.DEFAULT_TYPE, user_content):
    chat_id = str(update.effective_chat.id)

    # Load conversation history
    conversation_history = await get_conversation_messages_orm(chat_id)

    # Format messages
    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history:
        if msg.role == "system":
            continue

        formatted = {"role": msg.role, "content": msg.content}

        if msg.role == "tool" and msg.tool_call_id:
            formatted["tool_call_id"] = msg.tool_call_id

        if msg.role == "assistant" and msg.name and msg.tool_call_id:
            formatted["tool_calls"] = [
                {
                    "id": msg.tool_call_id,
                    "function": {
                        "name": msg.name,
                        "arguments": msg.content,
                    },
                    "type": "function",
                }
            ]
            formatted["content"] = None

        messages.append(formatted)

    # Add new user content
    messages.append({"role": "user", "content": user_content})
    await save_message_orm(chat_id, "user", user_content)

    # First LLM call
    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
    )
    assistant_msg = response.choices[0].message

    # If tool call triggered
    if hasattr(assistant_msg, "tool_calls") and assistant_msg.tool_calls:
        print(assistant_msg.tool_calls)
        tool_call = assistant_msg.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        await save_message_orm(
            chat_id,
            role="assistant",
            content=tool_call.function.arguments,
            name=tool_call.function.name,
            tool_call_id=tool_call.id
        )

        try:
            # Call tool function
            if tool_name == "generate_ai_image":
                tool_args["update"] = update
            tool_result = await TOOL_MAPPING[tool_name](**tool_args)
            tool_content = json.dumps(tool_result)

        except Exception as e:
            # Gracefully handle tool failure
            print(f"Tool call error for {tool_name}: {e}")
            tool_content = json.dumps({"error": f"Something went wrong while executing {tool_name}"})

        # Append assistant & tool result to context
        messages.append(assistant_msg)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_name,
            "content": tool_content,
        })
        await save_message_orm(chat_id, "tool", tool_content, name=tool_name, tool_call_id=tool_call.id)

        # Final LLM call with tool result
        final_response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
        )
        final_text = final_response.choices[0].message.content
        await save_message_orm(chat_id, "assistant", final_text)
        await update.message.reply_text(final_text)

    else:
        reply = assistant_msg.content or "I didn't understand that."
        await save_message_orm(chat_id, "assistant", reply)
        await update.message.reply_text(reply)

# Text message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    await process_llm(update, context, user_input)

# Image upload handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    message: Message = update.message
    if not message or not message.photo:
        await message.reply_text("No Image received.")
        return

    # Get only the highest resolution photo per message
    best_photo: PhotoSize = max(message.photo, key=lambda p: p.file_size)
    image_url: str = await get_telegram_file_url(context, best_photo.file_id)
    print(image_url)
    user_content = f"User uploaded the following image: {image_url}"
    await process_llm(update, context, user_content)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot is running...")
    print(f"Using model: {MODEL}")
    threading.Thread(target=start_health_server, daemon=True).start()
    print("Health server started on port 8080")
    app.run_polling()
    
