# 🤖 Аксиома Оплаты Бот
![AI Assisted](https://img.shields.io/badge/AI-Assisted-blue)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2)
![GLM](https://img.shields.io/badge/GLM-4A90E2)

Telegram-бот для учёта оплат с сохранением в Baserow.
Позволяет авторизованным пользователям добавлять записи: номер заказа, вложение(pdf, картинка,..), сумма, примечание.
Автоматически сохраняет отправителя.
Позволяет начать диалог отправкой вложения или кнопкой "Добавить оплату".

При вводе номера заказа бот выполняет **интеллектуальный поиск** по списку существующих заказов из Baserow:
- Разбивает введённый текст на слова (токены) по пробелам.
- Ищет заказы, содержащие **все указанные токены**.
- Использует нечёткое сравнение (`partial_ratio`) для устойчивости к опечаткам.
- Если найдены совпадения — предлагает выбрать из списка, включая вариант «как есть».
- Если совпадений нет — всё равно даёт пользователю подтвердить введённый текст через интерфейс выбора.

## 💡 Технологии

- **Язык**: Python 3.12+
- **Фреймворк**: aiogram 3.x
- **HTTP-клиент**: httpx
- **Хранилище**: Baserow (через REST API)
- **Конфигурация**: python-dotenv
- **Поиск**: rapidfuzz (fuzzy matching)
- **Ретраи**: tenacity
- **Менеджер пакетов**: uv
- **Логирование**: logging

## 🛠️ Установка и запуск (локально)

### Настройка Baserow

Перед запуском бота убедитесь, что ваш инстанс Baserow имеет таблицы со следующими полями:

**Таблица оплат** (BASEROW_TABLE_ID):
- **Заказ** (Text) - для номера заказа.
- **Вложение** (File) - для pdf, картинок и т.п.
- **Сумма** (Number) - для суммы.
- **Примечание** (Long text) - для примечаний.
- **Отправитель** (Text) - для имени пользователя Telegram.

**Таблица заказов** (BASEROW_ORDERS_TABLE_ID):
- **Name** (Text) - для названия/номера заказа.
- **Статус** (Single Select) - для статуса заказа.

> ⚠️ Бот кэширует список заказов из поля «Name» для быстрого поиска. Заказы с исключёнными статусами пропускаются.

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/alex-ivanenko/aksioma-payments-bot.git
cd aksioma-payments-bot
```

### 2. Установите зависимости
```bash
uv sync
```

### 3. Настройте .env
Создайте файл `.env` в корне проекта на основе `.env.example` и заполните его своими данными:

- `TELEGRAM_BOT_TOKEN`: Токен вашего бота, полученный от [@BotFather](https://t.me/BotFather) в Telegram.
- `BASEROW_URL`: URL вашего инстанса Baserow (например, `https://baserow.local`).
- `BASEROW_TOKEN`: Database Token от Baserow.
- `BASEROW_TABLE_ID`: ID таблицы оплат (число из URL таблицы).
- `BASEROW_ORDERS_TABLE_ID`: ID таблицы заказов.
- `EXCLUDED_STATUSES`: Статусы заказов, которые нужно исключить из поиска (через запятую, по умолчанию: `Расчет,Отменен,Отложен`).
- `AUTHORIZED_USERS`: ID пользователей Telegram, которым разрешено использовать бота.

### 4. Запустите бота
```bash
uv run python -m bot.main
```
Бот запустится в режиме polling (если не задан WEBHOOK_HOST).

## 🌐 Webhook (опционально)
Для запуска в режиме webhook добавьте в `.env`:
- `WEBHOOK_HOST=https://ваш-домен.ngrok.io`
- `PORT=8080`

Бот автоматически переключится в режим webhook.

## 📝 Логирование
Бот ведёт логи в файл `logs/bot.log` (с ротацией: 5 МБ, 2 архива).
Также логи выводятся в консоль при запуске.

## 📂 Структура проекта
```text
baserow-aksioma-payment-bot/
├── bot/
│   ├── baserow_client.py   # Клиент для работы с Baserow API
│   ├── cache_manager.py    # Кэширование списка заказов
│   ├── config.py           # Загрузка конфигурации
│   ├── handlers.py         # Обработчики сообщений
│   ├── main.py             # Точка входа
│   └── states.py           # Состояния FSM
├── cache/
│   └── orders_cache.json
├── .env.example            # Шаблон конфигурации
├── .gitignore              # Файлы, исключённые из Git
├── pyproject.toml          # Зависимости (uv)
├── README.md               # Документация
└── aksioma-payments-bot.xml # Конфиг WinSW
```

## 📜 License
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
