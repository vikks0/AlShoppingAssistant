import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def is_wb_url(url):
    return "wildberries.ru" in url


def get_wb_product_id(url):
    match = re.search(r'/catalog/(\d+)', url)
    if match:
        return match.group(1)
    parts = url.split('/')
    for part in parts:
        if part.isdigit():
            return part
    return None


def create_browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def get_wb_reviews(url):
    browser = None
    try:
        product_id = get_wb_product_id(url)
        if not product_id:
            return None

        browser = create_browser()
        page_url = "https://www.wildberries.ru/catalog/" + product_id + "/feedbacks"
        browser.get(page_url)
        time.sleep(15)

        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        reviews = []

        cards = soup.select(".comments__item.feedback")
        for card in cards:
            text_items = card.select("[class*='feedback__text--item']")
            if text_items:
                parts = []
                for item in text_items:
                    parts.append(item.get_text(strip=True))
                review_text = " ".join(parts)
                if review_text and len(review_text) > 10:
                    reviews.append(review_text)

        return reviews

    except Exception:
        return None
    finally:
        if browser:
            browser.quit()


def get_reviews(url):
    if not is_wb_url(url):
        return None
    return get_wb_reviews(url)
