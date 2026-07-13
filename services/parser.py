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


def _collect_reviews(browser):
    soup = BeautifulSoup(browser.page_source, "html.parser")

    reviews = []

    for body in soup.find_all(attrs={"itemprop": "reviewBody"}):
        text = body.get_text(" ", strip=True)

        if text:
            reviews.append(text)

    return reviews


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

        reviews = _collect_reviews(browser)

        for attempt in range(10):
            try:
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                clicked = False
                buttons = browser.find_elements(By.CSS_SELECTOR, "button")
                for btn in buttons:
                    btn_text = btn.text.strip().lower()
                    if ("показать ещё" in btn_text or
                        "показать еще" in btn_text or
                        "все отзыв" in btn_text):
                        btn.click()
                        clicked = True
                        time.sleep(3)
                        break

                if not clicked:
                    break

                new_reviews = _collect_reviews(browser)
                if len(new_reviews) <= len(reviews):
                    break
                reviews = new_reviews

            except Exception:
                break

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
