import asyncio
import re

from gigachat import GigaChat
from config import GIGACHAT_API_KEY

PROBLEM_KEYWORDS = {
    "работа": ["работает", "работал", "работали", "функционирует",
               "включается", "включил", "включила"],
    "сломал": ["сломался", "сломалась", "сломали", "поломка",
               "поломался", "вышел из строя", "не работает",
               "не включается"],
    "батарея": ["батарейка", "аккумулятор", "зарядка", "заряд",
                "разряд", "разряжается", "садится", "держит заряд"],
    "bluetooth": ["bluetooth", "блютуз", "подключени", "сопряжени",
                  "пара", "связь"],
    "запах": ["запах", "воняет", "пахнет", "аромат",
              "химический запах"],
    "люфт": ["люфт", "люфтит", "шатается", "играет",
             "неплотно", "болтается"],
    "трещин": ["трещин", "треснул", "треска", "разломал", "скол"],
    "шум": ["шум", "шумит", "визжит", "свистит",
            "стучит", "гудит", "жужжит"],
    "запуск": ["запуск", "загрузк", "включение", "старт", "boot"],
    "драйвер": ["драйвер", "драйвера", "драйверов",
                "установк драйвер", "обновлени драйвер"],
    "наушник": ["наушник", "наушники", "вкладыши",
                "внутриканальные"],
    "мыш": ["мышь", "мышка", "курсор"],
    "клавиатур": ["клавиатура", "клавиши", "клавиша", "кнопки"],
    "экран": ["экран", "дисплей", "монитор", "отображение"],
    "звук": ["звук", "аудио", "громкость", "тихий", "громкий"],
    "доставк": ["доставка", "доставили", "привезли", "отправили"],
    "размер": ["размер", "величина", "маленький", "большой",
               "не подошёл", "не подошел"],
    "материал": ["материал", "ткань", "качество ткани", "состав"],
    "уход": ["стирк", "уход", "чистк", "промывк"],
    "подключени": ["подключени", "подключить", "подключил",
                   "коннект", "сопряжени"],
    "обновлени": ["обновлени", "обновить", "апдейт", "прошивк"],
    "гаранти": ["гаранти", "гарантия", "гарантийн"],
    "возврат": ["возврат", "вернуть", "обмен", "замена"],
    "сравнени": ["сравнени", "сравнить", "отличи", "разниц"],
    "подход": ["подходит", "подошёл", "подошел", "подходящ", "уместн"],
}


def find_relevant_reviews(reviews, question, top_n=10):
    """Ищет релевантные отзывы: разбивает вопрос на слова, расширяет синонимами, считает score."""
    question_lower = question.lower()
    question_tokens = re.findall(r'\w+', question_lower)

    expanded_keywords = set(question_tokens)

    for token in question_tokens:
        for key, synonyms in PROBLEM_KEYWORDS.items():
            if token in key or key in token:
                for syn in synonyms:
                    expanded_keywords.add(syn)

            for syn in synonyms:
                if token in syn or syn in token:
                    expanded_keywords.add(key)
                    for s in synonyms:
                        expanded_keywords.add(s)

    scored = []
    for review in reviews:
        review_lower = review.lower()
        score = 0
        matched = set()

        for kw in expanded_keywords:
            if len(kw) < 3:
                continue
            count = review_lower.count(kw)
            if count > 0:
                if kw not in matched:
                    score = score + count
                    matched.add(kw)

        if score > 0:
            scored.append([review, score])

    for i in range(len(scored)):
        for j in range(i + 1, len(scored)):
            if scored[j][1] > scored[i][1]:
                temp = scored[i]
                scored[i] = scored[j]
                scored[j] = temp

    result = []
    for item in scored[:top_n]:
        result.append((item[0], item[1]))
    return result


def summarize_solution(reviews_text, question):
    """Отправляет релевантные отзывы в GigaChat для суммаризации решений."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        with GigaChat(credentials=GIGACHAT_API_KEY, verify_ssl_certs=False) as client:
            response = client.chat(
                "Пользователь задал вопрос о товаре. Вот отзывы покупателей, "
                "в которых упоминается похожая проблема.\n\n"
                "Вопрос пользователя: " + question + "\n\n"
                "На основе отзывов дай КРАТКИЙ ответ:\n\n"
                "ЧТО ПОМОГЛО:\n"
                "- решение 1\n"
                "- решение 2\n\n"
                "ПРИМЕРЫ ИЗ ОТЗЫВОВ:\n"
                "- цитата 1\n"
                "- цитата 2\n\n"
                "Правила:\n"
                "- Только то, что реально написано в отзывах\n"
                "- Максимум 5 решений, отсортируй по популярности\n"
                "- Максимум 3 примера-цитаты\n"
                "- Без заголовков Markdown (#, ##)\n"
                "- Кратко и по делу\n\n"
                "Отзывы:\n\n" + reviews_text
            )
            return response.choices[0].message.content
    finally:
        loop.close()
