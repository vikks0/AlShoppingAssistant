import re

POSITIVE_WORDS = [
    "отлично", "хорошо", "нравится", "рекомендую", "качество",
    "доволен", "довольна", "супер", "класс", "прекрасно",
    "замечательно", "великолепно", "идеально", "нормально",
    "быстрая доставка", "удобно", "красиво", "стильно",
    "мягкий", "тёплый", "лёгкий", "удобный", "качественный",
    "стоит", "окей", "okes", "лучший", "пятёрка", "5 из 5",
    "брака нет", "всё понравилось", "всё супер"
]

NEGATIVE_WORDS = [
    "плохо", "сломался", "дефект", "брак", "разочарован",
    "разочарована", "не рекомендую", "ужас", "отвратительно",
    "дорого", "неудобно", "медленно", "грубо", "некачественно",
    "треснул", "порвался", "выцвел", "сдулся", "не работает",
    "хуже", "самый плохой", "1 из 5", "одна звезда", "обман"
]


def count_sentiments(reviews):
    """Считает положительные и отрицательные отзывы по ключевым словам."""
    positive = 0
    negative = 0

    for review in reviews:
        text_lower = review.lower()

        pos_count = 0
        for word in POSITIVE_WORDS:
            if word in text_lower:
                pos_count = pos_count + 1

        neg_count = 0
        for word in NEGATIVE_WORDS:
            if word in text_lower:
                neg_count = neg_count + 1

        if pos_count > neg_count:
            positive = positive + 1
        elif neg_count > pos_count:
            negative = negative + 1

    return positive, negative


def _clean_markdown(text):
    """Убирает артефакты markdown (> * ** # и нумерацию) из ответов GigaChat."""
    text = re.sub(r'^\s*>+\s*\*?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'>\s*\*', '', text)
    text = re.sub(r'\*{1,2}', '', text)
    text = re.sub(r'^\d+\.\s*', '', text)
    text = text.strip()
    return text


def _parse_gpt_response(text):
    """Разбирает ответ GigaChat на: плюсы, минусы, рекомендация."""
    pluses = []
    minuses = []
    recommendation = ""
    current_section = None

    for line in text.split("\n"):
        line_clean = line.strip().lstrip("#").strip()
        line_lower = line_clean.lower()

        if "плюсы" in line_lower or "достоинства" in line_lower or "преимущества" in line_lower:
            current_section = "plus"
            continue
        elif "минусы" in line_lower or "недостатки" in line_lower or "жалобы" in line_lower:
            current_section = "minus"
            continue
        elif "рекоменда" in line_lower or "итог" in line_lower or "вердикт" in line_lower:
            current_section = "rec"
            continue

        if not line_clean:
            continue

        clean = line_clean.lstrip("-•*0123456789. ").strip()
        clean = _clean_markdown(clean)

        if not clean or len(clean) <= 2:
            continue

        if current_section == "plus":
            pluses.append(clean)
        elif current_section == "minus":
            minuses.append(clean)
        elif current_section == "rec":
            recommendation = recommendation + clean + " "

    return pluses[:5], minuses[:5], recommendation.strip()


def format_result(gpt_text, total_reviews, positive, negative):
    """Форматирует результат анализа для Telegram."""
    neutral = total_reviews - positive - negative

    if total_reviews > 0:
        pos_percent = round(positive / total_reviews * 100)
        neg_percent = round(negative / total_reviews * 100)
        neu_percent = round(neutral / total_reviews * 100)
    else:
        pos_percent = 0
        neg_percent = 0
        neu_percent = 0

    pluses, minuses, recommendation = _parse_gpt_response(gpt_text)

    result = ""
    result = result + "Анализ отзывов\n"
    result = result + "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    result = result + "Отзывов: " + str(total_reviews) + "\n"
    result = result + "Положительных: " + str(positive) + " (" + str(pos_percent) + "%)\n"
    result = result + "Нейтральных: " + str(neutral) + " (" + str(neu_percent) + "%)\n"
    result = result + "Отрицательных: " + str(negative) + " (" + str(neg_percent) + "%)\n"
    result = result + "━━━━━━━━━━━━━━━━━━━━━━━━\n"

    if pluses:
        result = result + "\nПлюсы\n"
        for p in pluses:
            result = result + "- " + p + "\n"

    if minuses:
        result = result + "\nМинусы\n"
        for m in minuses:
            result = result + "- " + m + "\n"

    if not pluses and not minuses and gpt_text:
        result = result + "\n" + gpt_text + "\n"

    result = result + "\nИтог\n"
    if recommendation:
        result = result + recommendation + "\n"
    elif pos_percent >= 70:
        result = result + "Рекомендуется к покупке.\n"
    elif pos_percent >= 40:
        result = result + "Есть замечания. Стоит подумать перед покупкой.\n"
    else:
        result = result + "Лучше поискать другой вариант.\n"

    return result


def format_comparison(results):
    """Форматирует результат сравнения товаров."""
    text = "Сравнение товаров\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i in range(len(results)):
        item = results[i]
        num = i + 1
        total = item["reviews_count"]
        pos = item["positive"]
        neg = item["negative"]

        if total > 0:
            pos_percent = round(pos / total * 100)
            neg_percent = round(neg / total * 100)
        else:
            pos_percent = 0
            neg_percent = 0

        pluses, minuses, _ = _parse_gpt_response(item["analysis"])

        url = item["url"]
        if len(url) > 50:
            short_url = url[:50] + "..."
        else:
            short_url = url

        text = text + "Товар " + str(num) + "\n"
        text = text + short_url + "\n"
        text = text + str(total) + " отзывов | +" + str(pos_percent) + "% | -" + str(neg_percent) + "%\n"

        if pluses:
            top_pluses = pluses[:3]
            text = text + "+ " + ", ".join(top_pluses) + "\n"
        if minuses:
            top_minuses = minuses[:3]
            text = text + "- " + ", ".join(top_minuses) + "\n"

        text = text + "\n" + "─" * 30 + "\n\n"

    if len(results) > 1:
        scores = []
        for i in range(len(results)):
            item = results[i]
            num = i + 1
            if item["reviews_count"] > 0:
                pos_percent = round(item["positive"] / item["reviews_count"] * 100)
            else:
                pos_percent = 0
            scores.append([num, pos_percent])

        for i in range(len(scores)):
            for j in range(i + 1, len(scores)):
                if scores[j][1] > scores[i][1]:
                    temp = scores[i]
                    scores[i] = scores[j]
                    scores[j] = temp

        text = text + "Итог\n"
        for rank in range(len(scores)):
            num = scores[rank][0]
            score = scores[rank][1]
            text = text + str(rank + 1) + ". Товар " + str(num) + ": " + str(score) + "% положительных\n"

        text = text + "\nТовар " + str(scores[0][0]) + " — лучший по отзывам покупателей."

    return text
