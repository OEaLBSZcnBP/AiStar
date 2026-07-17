import asyncio
import urllib.parse
import aiohttp
import random
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL_NAMES = {
    "gpt": "🧠 ChatGPT",
    "deepseek": "🐳 DeepSeek",
    "gemini": "💎 Gemini",
    "grok": "⚡ Grok",
    "claude": "🧩 Claude"
}

user_models = {}


async def ask_groq(text: str, model: str) -> str:
    if not GROQ_API_KEY:
        return None

    model_map = {
        "gpt": "llama-3.3-70b-versatile",
        "deepseek": "llama-3.3-70b-versatile",
        "grok": "llama-3.3-70b-versatile",
        "claude": "llama-3.3-70b-versatile",
        "gemini": "llama-3.1-8b-instant"
    }

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_map.get(model, model_map["gpt"]),
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 2000
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if "choices" in result:
                        return result["choices"][0]["message"]["content"]
                return None
    except Exception:
        return None
        

async def ask_together(text: str, model: str) -> str:
    if not TOGETHER_API_KEY:
        return None

    model_map = {
        "gpt": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "deepseek": "deepseek-ai/DeepSeek-V3",
        "grok": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "claude": "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "gemini": "google/gemma-2-9b-it"
    }

    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_map.get(model, model_map["gpt"]),
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 2000
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=45) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if "choices" in result:
                        return result["choices"][0]["message"]["content"]
                return None
    except Exception:
        return None


async def ask_gemini(text: str, model: str) -> str:
    if not GEMINI_API_KEY:
        return None

    model_name = "gemini-2.0-flash-exp"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {"maxOutputTokens": 2000}
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if "candidates" in result:
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                return None
    except Exception:
        return None


async def ask_openrouter(text: str, model: str) -> str:
    if not OPENROUTER_API_KEY:
        return None

    model_map = {
        "gpt": "openai/gpt-oss-20b:free",
        "deepseek": "qwen/qwen-2.5-coder-32b-instruct:free",
        "grok": "meta-llama/llama-3.3-70b-instruct:free",
        "claude": "nvidia/llama-3.1-nemotron-70b-instruct:free",
        "gemini": "google/gemma-2-9b-it:free"
    }

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me",
        "X-Title": "Telegram AI Bot"
    }
    data = {
        "model": model_map.get(model, model_map["gpt"]),
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 2000
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=45) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if "choices" in result:
                        return result["choices"][0]["message"]["content"]
                return None
    except Exception:
        return None


async def ask_pollinations(text: str, model: str) -> str:
    model_map = {
        "gpt": "openai",
        "deepseek": "deepseek",
        "gemini": "gemini",
        "grok": "openai-fast",
        "claude": "claude"
    }

    m = model_map.get(model, "openai")
    encoded = urllib.parse.quote(text)
    url = f"https://text.pollinations.ai/{encoded}?model={m}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=45) as resp:
                if resp.status == 200:
                    return (await resp.text()).strip()
                return None
    except Exception:
        return None


async def ask_ai(user_id: int, text: str) -> tuple:
    if not text or not text.strip():
        return ("❌", "Пустой запрос")

    model_key = user_models.get(user_id)
    if not model_key:
        model_key = random.choice(list(MODEL_NAMES.keys()))

    display_name = MODEL_NAMES.get(model_key, "ИИ")

    services = [
        ("Groq", lambda: ask_groq(text, model_key)),
        ("Together", lambda: ask_together(text, model_key)),
        ("Gemini", lambda: ask_gemini(text, model_key)),
        ("OpenRouter", lambda: ask_openrouter(text, model_key)),
        ("Pollinations", lambda: ask_pollinations(text, model_key)),
    ]

    for service_name, ask_func in services:
        try:
            result = await ask_func()
            if result and len(result.strip()) > 0:
                return (f"{display_name} [{service_name}]", result)
        except Exception:
            continue

    return ("❌", "Все сервисы временно недоступны. Попробуй позже.")


bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
router = Router()
dp.include_router(router)


@router.message(Command("start"))
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Выбрать модель", callback_data="models")],
        [InlineKeyboardButton(text="🎨 Картинка", callback_data="image"),
         InlineKeyboardButton(text="🎬 Видео", callback_data="video")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])

    await message.answer(
        "Приветствую! Я бот с искусственным интеллектом, просто задай мне вопрос и я отвечу.\n\n"
        "💡 Бот сам подбирает лучшую доступную модель",
        reply_markup=kb
    )


@router.callback_query(F.data == "models")
@router.message(Command("model"))
async def choose_model(event: Message | CallbackQuery):
    if isinstance(event, CallbackQuery):
        target = event.message
        await event.answer()
    else:
        target = event

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 ChatGPT", callback_data="set_gpt")],
        [InlineKeyboardButton(text="🐳 DeepSeek", callback_data="set_deepseek")],
        [InlineKeyboardButton(text="💎 Gemini", callback_data="set_gemini")],
        [InlineKeyboardButton(text="⚡ Grok", callback_data="set_grok")],
        [InlineKeyboardButton(text="🧩 Claude", callback_data="set_claude")],
        [InlineKeyboardButton(text="🎲 Случайная", callback_data="set_random")]
    ])
    await target.answer("🤖 <b>Выбери модель ИИ:</b>", reply_markup=kb)


@router.callback_query(F.data.startswith("set_"))
async def set_model(callback: CallbackQuery):
    data = callback.data.split("_", 1)[1]
    if data == "random":
        user_models.pop(callback.from_user.id, None)
        await callback.answer("🎲 Случайный выбор!")
        await callback.message.edit_text("🎲 Модель рандомится")
    else:
        user_models[callback.from_user.id] = data
        name = MODEL_NAMES.get(data, data)
        await callback.answer(f"✅ {name}")
        await callback.message.edit_text(f"✅ Выбрана: <b>{name}</b>")


@router.callback_query(F.data == "help")
@router.message(Command("help"))
async def cmd_help(event: Message | CallbackQuery):
    help_text = (
        "📖 <b>Команды:</b>\n\n"
        "🚀 <b>/start</b> — Главное меню\n"
        "🤖 <b>/model</b> — Выбрать модель ИИ\n"
        "🎨 <b>/image [текст]</b> — Картинка\n"
        "🎬 <b>/video [текст]</b> — Видео\n"
        "🔄 <b>/reset</b> — Сбросить модель\n"
        "❓ <b>/help</b> — Помощь\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 <b>Доступные модели:</b>\n\n"
        "• 🧠 <b>ChatGPT</b> — универсальная\n"
        "• 🐳 <b>DeepSeek</b> — код + текст\n"
        "• 💎 <b>Gemini</b> — быстрая, Google\n"
        "• ⚡ <b>Grok</b> — X.AI\n"
        "• 🧩 <b>Claude</b> — длинные тексты\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Как пользоваться:</b>\n\n"
        "1️⃣ Нажми /start и выбери модель\n"
        "2️⃣ Напиши любой вопрос — получишь ответ\n"
        "3️⃣ Для картинки: <code>/image описание</code>\n"
        "4️⃣ Для видео: <code>/video описание</code>\n\n"
        "🎁 Картинки и видео — бесплатно!"
    )
    if isinstance(event, CallbackQuery):
        await event.answer()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_start")]
        ])
        await event.message.answer(help_text, reply_markup=kb)
    else:
        await event.answer(help_text)


@router.callback_query(F.data == "back_start")
async def back_to_start(callback: CallbackQuery):
    await callback.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Выбрать модель", callback_data="models")],
        [InlineKeyboardButton(text="🎨 Картинка", callback_data="image"),
         InlineKeyboardButton(text="🎬 Видео", callback_data="video")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])
    await callback.message.answer(
        "Приветствую! Я бот с искусственным интеллектом, просто задай мне вопрос и я отвечу.",
        reply_markup=kb
    )


@router.callback_query(F.data == "image")
async def image_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🎨 <b>Картинка</b>\n\n<code>/image кот в скафандре</code>")


@router.callback_query(F.data == "video")
async def video_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🎬 <b>Видео</b>\n\n<code>/video волны океана</code>\n⏱ 3 сек")


@router.message(Command("reset"))
async def reset_context(message: Message):
    user_models.pop(message.from_user.id, None)
    await message.answer("🔄 Модель сброшена!")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message):
    msg = await message.answer("🤔 <i>Думаю...</i>")
    model_name, response = await ask_ai(message.from_user.id, message.text)
    await msg.edit_text(f"🤖 <b>{model_name}:</b>\n\n{response}")


@router.message(Command("image"))
async def gen_image(message: Message):
    prompt = message.text.replace("/image", "").strip()
    if not prompt:
        await message.answer("❌ Напиши описание:\n<code>/image кот в скафандре</code>")
        return

    msg = await message.answer("🎨 <i>Рисую...</i>")
    try:
        encoded = urllib.parse.quote(prompt)
        img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux"
        await message.answer_photo(
            photo=img_url,
            caption=f"🎨 <b>{prompt}</b>\n\n⚙️ Flux\n🔗 <a href=\"{img_url}\">Открыть</a>"
        )
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")


@router.message(Command("video"))
async def gen_video(message: Message):
    prompt = message.text.replace("/video", "").strip()
    if not prompt:
        await message.answer("❌ Напиши описание:\n<code>/video волны океана</code>")
        return

    msg = await message.answer("🎬 <i>Генерирую видео...</i>\n⏳ 1-3 мин")
    try:
        encoded = urllib.parse.quote(prompt)
        video_url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&model=animate-diff&duration=3"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(video_url, timeout=aiohttp.ClientTimeout(total=180)) as resp:
                    if resp.status != 200:
                        await msg.edit_text(f"❌ HTTP {resp.status}")
                        return
                    video_data = await resp.read()
                    if len(video_data) < 1000:
                        await msg.edit_text("❌ Видео пустое")
                        return

                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                        tmp.write(video_data)
                        tmp_path = tmp.name
                    try:
                        await message.answer_video(
                            video=open(tmp_path, "rb"),
                            caption=f"🎬 <b>{prompt}</b>\n\n⚙️ Animate-Diff"
                        )
                        await msg.delete()
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass
            except asyncio.TimeoutError:
                await msg.edit_text("❌ Таймаут")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")


@router.message(F.photo)
async def edit_image(message: Message):
    caption = message.caption or ""
    if not caption:
        await message.answer("❌ Отправь фото с подписью")
        return
    msg = await message.answer("✏️ <i>Генерирую...</i>")
    try:
        full_prompt = f"{caption}, high quality, detailed"
        encoded = urllib.parse.quote(full_prompt)
        img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux"
        await message.answer_photo(photo=img_url, caption=f"✏️ <b>{caption}</b>")
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")


async def main():
    print("Бот запущен!")
    print("Модели: ChatGPT, DeepSeek, Gemini, Grok, Claude")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
