## Автоматизация обновления данных в интернет-магазинах

Этот набор скриптов автоматизирует процесс обновления цен и остатков товаров в двух крупных интернет-магазинах: Ozon и Яндекс.Маркет.

Как работают скрипты:

• Загрузка данных: Скрипты получают информацию о наличии товаров из внешней системы, например, из CSV-файла или базы данных. Для Ozon скрипт загружает информацию с сайта casio.ru. 
• Обработка данных: Скрипты преобразуют полученные данные в формат, понятный API соответствующего интернет-магазина.
• Обновление данных: Скрипты отправляют обновленные данные о запасах и ценах в API интернет-магазина, обновляя информацию о ваших товарах. 

Что вам нужно сделать:

1. Настройка переменных окружения:
  * Создайте файл .env в папке со скриптом.
  * Заполните значения переменных окружения:
   * Ozon:
    ```
    OZON_CLIENT_ID=ваш_client_id_ozon
    OZON_API_KEY=ваш_api_key_ozon
    ```
   * Яндекс.Маркет:
    ```
    MARKET_TOKEN=ваш_токен_яндекс_маркета
    CAMPAIGN_ID=ваш_id_кампании
    WAREHOUSE_ID=ваш_id_склада 
    ```
  * Получите необходимые значения в личном кабинете на сайтах Ozon и Яндекс.Маркет.
2. Запуск скриптов:
  * Откройте командную строку (cmd.exe в Windows) или терминал (в macOS или Linux).
  * Перейдите в папку со скриптом.
  * Выполните команду python your_file.py (замените your_file.py на имя скрипта).

Дополнительная информация:

• Скрипты используют API Ozon и Яндекс.Маркет. Вам нужно будет зарегистрироваться на сайтах и получить доступ к API.
• Скрипт для Ozon требует наличия файла ostatki.xls в той же папке. Файл с остатками товаров должен быть в формате, который поддерживается скриптом.
• Скрипты работают только с ценами и остатками товаров. 

В общем: скрипты упрощают процесс обновления информации в ваших интернет-магазинах, экономя время и силы.
