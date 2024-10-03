import datetime
import logging.config
from environs import Env
from seller import download_stock

import requests

from seller import divide, price_conversion

logger = logging.getLogger(__file__)


def get_product_list(page, campaign_id, access_token):
  """Получает список товаров из кампании на Яндекс Маркете с использованием пагинации.

  Args:
    page: Токен страницы для пагинации (str).
    campaign_id: ID кампании на Яндекс Маркете (int).
    access_token: Токен доступа к API Яндекс Маркета (str).

  Returns:
    Словарь с результатами запроса к API Яндекс Маркета, содержащий информацию о товарах (dict).
  """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {
        "page_token": page,
        "limit": 200,
    }
    url = endpoint_url + f"campaigns/{campaign_id}/offer-mapping-entries"
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def update_stocks(stocks, campaign_id, access_token):
  """Обновляет остатки товаров в кампании на Яндекс Маркете.

  Args:
    stocks: Список словарей с информацией об остатках товаров (list).
    campaign_id: ID кампании на Яндекс Маркете (int).
    access_token: Токен доступа к API Яндекс Маркета (str).

  Returns:
    Словарь с ответом от API Яндекс Маркета (dict).
  """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"skus": stocks}
    url = endpoint_url + f"campaigns/{campaign_id}/offers/stocks"
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def update_price(prices, campaign_id, access_token):
  """Обновляет цены товаров в кампании на Яндекс Маркете.

  Args:
    prices: Список словарей с информацией о ценах товаров (list).
    campaign_id: ID кампании на Яндекс Маркете (int).
    access_token: Токен доступа к API Яндекс Маркета (str).

    Returns:
        Словарь с ответом от API Яндекс Маркета (dict).
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"offers": prices}
    url = endpoint_url + f"campaigns/{campaign_id}/offer-prices/updates"
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def get_offer_ids(campaign_id, market_token):
    """Получает список артикулов (offer_id) товаров из кампании на Яндекс Маркете.

    Args:
        campaign_id: ID кампании на Яндекс Маркете (int).
        market_token: Токен доступа к API Яндекс Маркета (str).

    Returns:
        Список артикулов товаров (offer_id) (list).
    """
    page = ""
    product_list = []
    while True:
        some_prod = get_product_list(page, campaign_id, market_token)
        product_list.extend(some_prod.get("offerMappingEntries"))
        page = some_prod.get("paging").get("nextPageToken")
        if not page:
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer").get("shopSku"))
    return offer_ids


def create_stocks(watch_remnants, offer_ids, warehouse_id):
    """Создает список остатков товаров для обновления на Яндекс Маркете.

    Args:
        watch_remnants: Список остатков товаров от Casio (list).
        offer_ids: Список артикулов товаров (offer_id) из кампании на Яндекс Маркете (list).
        warehouse_id: ID склада на Яндекс Маркете (str).

    Returns:
        Список словарей с информацией об остатках товаров (list).
    """
    stocks = list()
    date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append(
                {
                    "sku": str(watch.get("Код")),
                    "warehouseId": warehouse_id,
                    "items": [
                        {
                            "count": stock,
                            "type": "FIT",
                            "updatedAt": date,
                        }
                    ],
                }
            )
            offer_ids.remove(str(watch.get("Код")))
    # Добавим недостающее из загруженного:
    for offer_id in offer_ids:
        stocks.append(
            {
                "sku": offer_id,
                "warehouseId": warehouse_id,
                "items": [
                    {
                        "count": 0,
                        "type": "FIT",
                        "updatedAt": date,
                    }
                ],
            }
        )
    return stocks


def create_prices(watch_remnants, offer_ids):
  """Создает список цен товаров для обновления на Яндекс Маркете.

  Args:
    prices: Словарь с ценами товаров (dict).
    offer_ids: Список артикулов товаров (offer_id) (list).

  Returns:
    Список словарей с информацией о ценах товаров для обновления (list).
  """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "id": str(watch.get("Код")),
                # "feed": {"id": 0},
                "price": {
                    "value": int(price_conversion(watch.get("Цена"))),
                    # "discountBase": 0,
                    "currencyId": "RUR",
                    # "vat": 0,
                },
                # "marketSku": 0,
                # "shopSku": "string",
            }
            prices.append(price)
    return prices


async def upload_prices(watch_remnants, campaign_id, market_token):
  """Обновляет цены товаров на Яндекс Маркете.

  Args:
    watch_remnants (List[Dict[str, Any]]): Список остатков товаров от Casio.
    campaign_id (str): ID кампании на Яндекс Маркете.
    market_token (str): Токен доступа к API Яндекс Маркета.

  Returns:
    List[Dict[str, Any]]: Список словарей, представляющих цены товаров для обновления.
  """
    offer_ids = get_offer_ids(campaign_id, market_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_prices in list(divide(prices, 500)):
        update_price(some_prices, campaign_id, market_token)
    return prices


async def upload_stocks(watch_remnants, campaign_id, market_token, warehouse_id):
  """Обновляет остатки товаров на Яндекс Маркете.

  Args:
    watch_remnants (List[Dict[str, Any]]): Список остатков товаров от Casio.
    campaign_id (str): ID кампании на Яндекс Маркете.
    market_token (str): Токен доступа к API Яндекс Маркета.
    warehouse_id (str): ID склада на Яндекс Маркете.

  Returns:
    tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: 
      Список словарей, представляющих остатки товаров с ненулевым количеством для обновления.
      Список словарей, представляющих все остатки товаров для обновления.
  """
    offer_ids = get_offer_ids(campaign_id, market_token)
    stocks = create_stocks(watch_remnants, offer_ids, warehouse_id)
    for some_stock in list(divide(stocks, 2000)):
        update_stocks(some_stock, campaign_id, market_token)
    not_empty = list(
        filter(lambda stock: (stock.get("items")[0].get("count") != 0), stocks)
    )
    return not_empty, stocks


def main():
  """Запускает процесс обновления остатков и цен на Яндекс Маркете для двух кампаний (FBS и DBS).

  Читает данные из файла .env, в котором должны быть заданы следующие переменные окружения:

  - MARKET_TOKEN (str): Токен доступа к API Яндекс Маркета.
  - FBS_ID (str): ID кампании на Яндекс Маркете для FBS.
  - DBS_ID (str): ID кампании на Яндекс Маркете для DBS.
  - WAREHOUSE_FBS_ID (str): ID склада на Яндекс Маркете для FBS.
  - WAREHOUSE_DBS_ID (str): ID склада на Яндекс Маркете для DBS.

  Использует функции upload_stocks и upload_prices для обновления остатков и цен на Яндекс Маркете.
  """
    env = Env()
    market_token = env.str("MARKET_TOKEN")
    campaign_fbs_id = env.str("FBS_ID")
    campaign_dbs_id = env.str("DBS_ID")
    warehouse_fbs_id = env.str("WAREHOUSE_FBS_ID")
    warehouse_dbs_id = env.str("WAREHOUSE_DBS_ID")

    watch_remnants = download_stock()
    try:
        # FBS
        offer_ids = get_offer_ids(campaign_fbs_id, market_token)
        # Обновить остатки FBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_fbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_fbs_id, market_token)
        # Поменять цены FBS
        upload_prices(watch_remnants, campaign_fbs_id, market_token)

        # DBS
        offer_ids = get_offer_ids(campaign_dbs_id, market_token)
        # Обновить остатки DBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_dbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_dbs_id, market_token)
        # Поменять цены DBS
        upload_prices(watch_remnants, campaign_dbs_id, market_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
