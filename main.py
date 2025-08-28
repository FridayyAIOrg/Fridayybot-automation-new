import asyncio
import json
import logging
from typing import Any, Dict, List
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
from health import create_health_app
from aiohttp import web
import nest_asyncio
nest_asyncio.apply()  # Patch the event loop to allow reentry

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
async def process_llm(update: Update, user_content: str):
    """
    Processes a user message, handling single or multi-turn tool calls in a loop
    before providing a final response.
    """
    chat_id = str(update.effective_chat.id)

    # 1. Load and format conversation history
    conversation_history = await get_conversation_messages_orm(chat_id)
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history:
        if msg.role == "system":
            continue
        
        formatted = {"role": msg.role, "content": msg.content}
        if msg.role == "tool" and msg.tool_call_id:
            formatted["tool_call_id"] = msg.tool_call_id
        
        if msg.role == "assistant" and msg.name and msg.tool_call_id:
            formatted["tool_calls"] = [{
                "id": msg.tool_call_id,
                "function": {"name": msg.name, "arguments": msg.content},
                "type": "function",
            }]
            formatted["content"] = None
        
        messages.append(formatted)

    # 2. Add new user message
    messages.append({"role": "user", "content": user_content})
    await save_message_orm(chat_id, "user", user_content)

    # 3. Start the conversation loop
    while True:
        # Make the API call
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        assistant_msg = response.choices[0].message

        # If there are no tool calls, this is the final response
        if not assistant_msg.tool_calls:
            # Use the response content directly, not from messages array
            final_text = assistant_msg.content or "Done."
            
            # Clean any potential reasoning artifacts
            final_text = clean_response_content(final_text)
            
            # Save and send the final response
            await save_message_orm(chat_id, "assistant", final_text)
            await update.message.reply_text(final_text)
            return  # Exit the function

        # --- If there ARE tool calls, process them ---
        # First, append the assistant's request to call tools to the message history
        messages.append({
            "role": "assistant",
            "content": assistant_msg.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                } for tool_call in assistant_msg.tool_calls
            ]
        })

        # Process each tool call requested in this turn
        for tool_call in assistant_msg.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # Save the assistant's request to call a tool
            await save_message_orm(
                chat_id,
                role="assistant",
                content=tool_call.function.arguments,
                name=tool_name,
                tool_call_id=tool_call.id
            )

            print(f"Executing tool: {tool_name} with args: {tool_args}")
            try:
                # Special handling for tools that need extra context
                if tool_name == "generate_ai_image":
                    tool_args["update"] = update
                
                # Call the corresponding tool function
                tool_result = await TOOL_MAPPING[tool_name](**tool_args)
                tool_content = json.dumps(tool_result)

            except Exception as e:
                # Gracefully handle tool failure
                print(f"Tool call error for {tool_name}: {e}")
                tool_content = json.dumps({"error": f"Something went wrong while executing {tool_name}: {e}"})

            # Append the tool's result to the message history for the next iteration
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": tool_content,
            })
            await save_message_orm(chat_id, "tool", tool_content, name=tool_name, tool_call_id=tool_call.id)


def clean_response_content(content: str) -> str:
    """Remove any internal reasoning or system artifacts from response"""
    if not content:
        return "Done."
    
    # Remove common reasoning patterns that might leak through
    lines = content.split('\n')
    cleaned_lines = []
    skip_next = False
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines at the start
        if not cleaned_lines and not line:
            continue
            
        # Skip lines that look like internal reasoning
        reasoning_indicators = [
            'Looking at', 'The issue', 'The problem', 'Solution', 'Here are',
            'This appears to be', 'It seems', 'The bot', 'Any way we can',
            'Code:', 'Let\'s', 'So respond:', 'Use the exact phrase:',
            'To be safe', 'Best to', 'Perhaps we', 'So current',
            'But system expects', 'But now', 'However earlier'
        ]
        
        if any(line.startswith(indicator) for indicator in reasoning_indicators):
            continue
            
        if 'reasoning' in line.lower() or 'artifact' in line.lower():
            continue
            
        cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines).strip()
    return result if result else "Done."

# Text message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    await process_llm(update, user_input)

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
    await process_llm(update, user_content)

async def run_health_server():
    app = create_health_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=8080)
    await site.start()
    print("✅ Health server running on port 8080")

async def setup_and_start():
    await run_health_server()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("🤖 Bot is running...")
    print(f"🧠 Using model: {MODEL}")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(setup_and_start())
