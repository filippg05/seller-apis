import io
import logging.config
import os
import re
import zipfile
from environs import Env

import pandas as pd
import requests

logger = logging.getLogger(__file__)


def get_product_list(last_id, client_id, seller_token):
            """Получить список товаров магазина озон

    Args:
        last_id: Идентификатор последнего полученного товара для продолжения пагинации.
        client_id: Идентификатор клиента на Озон.
        seller_token: Токен продавца на Озон.

    Returns:
        Словарь с результатами запроса к API Озон, содержащий информацию о товарах.
    """

    url = "https://api-seller.ozon.ru/v2/product/list"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {
        "filter": {
            "visibility": "ALL",
        },
        "last_id": last_id,
        "limit": 1000,
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def get_offer_ids(client_id, seller_token):
        """Получает список артикулов (offer_id) товаров магазина на Озон.

    Args:
        client_id: Идентификатор клиента на Озон.
        seller_token: Токен продавца на Озон.

    Returns:
        Список артикулов (offer_id) товаров магазина.
    """
    last_id = ""
    product_list = []
    while True:
        some_prod = get_product_list(last_id, client_id, seller_token)
        product_list.extend(some_prod.get("items"))
        total = some_prod.get("total")
        last_id = some_prod.get("last_id")
        if total == len(product_list):
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer_id"))
    return offer_ids


def update_price(prices: list, client_id, seller_token):
        """Обновляет цены товаров на Озон.

    Args:
        prices: Список словарей, представляющих цены для обновления. Каждый словарь содержит:
            - offer_id: Артикул товара (offer_id)
            - price: Новая цена товара.
        client_id: Идентификатор клиента на Озон.
        seller_token: Токен продавца на Озон.

    Returns:
        Ответ от API Озон в формате JSON, содержащий информацию об успехе или неудаче обновления.
    """
    url = "https://api-seller.ozon.ru/v1/product/import/prices"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"prices": prices}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def update_stocks(stocks: list, client_id, seller_token):
        """Обновляет остатки товаров на Озон.

    Args:
        stocks: Список словарей, представляющих остатки для обновления. Каждый словарь содержит:
            - offer_id: Артикул товара (offer_id)
            - stock: Количество товара на складе.
        client_id: Идентификатор клиента на Озон.
        seller_token: Токен продавца на Озон.

    Returns:
        Ответ от API Озон в формате JSON, содержащий информацию об успехе или неудаче обновления.
    """
    url = "https://api-seller.ozon.ru/v1/product/import/stocks"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"stocks": stocks}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def download_stock():
    """Скачать файл ostatki с сайта casio
        Returns:
        Список словарей, представляющих данные об остатках товаров из файла "ostatki.xls".
        """
    # Скачать остатки с сайта
    casio_url = "https://timeworld.ru/upload/files/ostatki.zip"
    session = requests.Session()
    response = session.get(casio_url)
    response.raise_for_status()
    with response, zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(".")
    # Создаем список остатков часов:
    excel_file = "ostatki.xls"
    watch_remnants = pd.read_excel(
        io=excel_file,
        na_values=None,
        keep_default_na=False,
        header=17,
    ).to_dict(orient="records")
    os.remove("./ostatki.xls")  # Удалить файл
    return watch_remnants


def create_stocks(watch_remnants, offer_ids):
        """Создает список остатков для обновления на Озон.

    Args:
        watch_remnants: Список остатков товаров от Casio, полученный из файла "ostatki.xls".
        offer_ids: Список артикулов товаров (offer_id) магазина на Озон.

    Returns:
        Список словарей, представляющих остатки для обновления на Озон. Каждый словарь содержит:
            - offer_id: Артикул товара (offer_id)
            - stock: Количество товара на складе, преобразованное из формата Casio в числовой формат.
    """
    # Уберем то, что не загружено в seller
    stocks = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append({"offer_id": str(watch.get("Код")), "stock": stock})
            offer_ids.remove(str(watch.get("Код")))
    # Добавим недостающее из загруженного:
    for offer_id in offer_ids:
        stocks.append({"offer_id": offer_id, "stock": 0})
    return stocks


def create_prices(watch_remnants, offer_ids):
        """Создает список цен для обновления на Озон.

    Args:
        watch_remnants: Список остатков товаров от Casio, полученный из файла "ostatki.xls".
        offer_ids: Список артикулов товаров (offer_id) магазина на Озон.

    Returns:
        Список словарей, представляющих цены для обновления на Озон. Каждый словарь содержит:
            - auto_action_enabled: "UNKNOWN" (не используется)
            - currency_code: "RUB" (код валюты)
            - offer_id: Артикул товара (offer_id)
            - old_price: "0" (не используется)
            - price: Цена товара, преобразованная из формата Casio в числовой формат.
            """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "auto_action_enabled": "UNKNOWN",
                "currency_code": "RUB",
                "offer_id": str(watch.get("Код")),
                "old_price": "0",
                "price": price_conversion(watch.get("Цена")),
            }
            prices.append(price)
    return prices


def price_conversion(price: str) -> str:
       """Преобразует строку с ценой из формата Casio в числовой формат.

    Args:
        price: Строка с ценой в формате Casio, например, "5'990.00 руб.".

    Returns:
        Числовой формат цены, например, "5990".
    """
    return re.sub("[^0-9]", "", price.split(".")[0])


def divide(lst: list, n: int):
    """Разделяет список на части заданной длины.

    Args:
        lst: Список, который нужно разделить.
        n: Длина каждой части списка.

    Yields:
        Итератор, который возвращает части списка длиной n.
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def upload_prices(watch_remnants, client_id, seller_token):
        """Загрузить цены на товары.

    Args:
        watch_remnants: список остатков товаров
        client_id: id клиента
        seller_token: токен продавца

    Returns:
        Список цен
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_price in list(divide(prices, 1000)):
        update_price(some_price, client_id, seller_token)
    return prices


async def upload_stocks(watch_remnants, client_id, seller_token):
    """Загрузить остатки товаров.

    Args:
        watch_remnants: список остатков товаров
        client_id: id клиента
        seller_token: токен продавца

    Returns:
        Список остатков, которые не равны 0
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    stocks = create_stocks(watch_remnants, offer_ids)
    for some_stock in list(divide(stocks, 100)):
        update_stocks(some_stock, client_id, seller_token)
    not_empty = list(filter(lambda stock: (stock.get("stock") != 0), stocks))
    return not_empty, stocks


def main():
    """Загружает цены и остатки товаров с сайта Casio на Ozon.

    Функция:
        1. Скачивает файл остатков с сайта Casio.
        2. Получает список артикулов товаров (offer_id) из магазина на Ozon.
        3. Создает список остатков для обновления на Ozon.
        4. Создает список цен для обновления на Ozon.
        5. Обновляет остатки на Ozon.
        6. Обновляет цены на Ozon.

    Обработка ошибок:
        - Превышено время ожидания.
        - Ошибка соединения.
        - Неизвестная ошибка.
    """
    env = Env()
    seller_token = env.str("SELLER_TOKEN")
    client_id = env.str("CLIENT_ID")
    try:
        offer_ids = get_offer_ids(client_id, seller_token)
        watch_remnants = download_stock()
        # Обновить остатки
        stocks = create_stocks(watch_remnants, offer_ids)
        for some_stock in list(divide(stocks, 100)):
            update_stocks(some_stock, client_id, seller_token)
        # Поменять цены
        prices = create_prices(watch_remnants, offer_ids)
        for some_price in list(divide(prices, 900)):
            update_price(some_price, client_id, seller_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
