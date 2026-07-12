import asyncio

from gigachat import GigaChat
from config import GIGACHAT_API_KEY


def analyze_reviews(reviews):
    """Отправляет отзывы в GigaChat и получает анализ (плюсы, минусы, рекомендация)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        with GigaChat(credentials=GIGACHAT_API_KEY, verify_ssl_certs=False) as client:
            response = client.chat(
                "Проанализируй отзывы о товаре и ответь СТРОГО в этом формате:\n\n"
                "ПЛЮСЫ:\n"
                "- пункт 1\n"
                "- пункт 2\n\n"
                "МИНУСЫ:\n"
                "- пункт 1\n"
                "- пункт 2\n\n"
                "РЕКОМЕНДАЦИЯ:\n"
                "Одно-два коротких предложения.\n\n"
                "Правила:\n"
                "- Максимум 5 пунктов в каждом списке\n"
                "- Только главные мысли, без повторов\n"
                "- Без заголовков Markdown (#, ##)\n"
                "- Без длинных объяснений\n\n"
                "Отзывы:\n\n" + reviews
            )
            return response.choices[0].message.content
    finally:
        loop.close()
