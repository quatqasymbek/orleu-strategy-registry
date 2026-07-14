# Реестр еженедельного исполнения — Streamlit Cloud

Этот проект повторяет логику предоставленного Claude Artifact:

- навигация по неделям;
- кабинет подразделения;
- форма новой записи;
- редактирование и удаление записей;
- статусы, сроки, комментарии и риски;
- отметка крупного проекта и дата очного доклада;
- свод руководителя по всем подразделениям;
- KPI-карточки;
- запрос отчёта выбранным подразделениям;
- отображение подразделений, которые не подали отчёт;
- фильтр по статусу и крупным проектам;
- график очных докладов;
- автоматическое обновление свода каждые 25 секунд.

## Аккаунты

При первом запуске аккаунты создаются автоматически:

```text
STRATEGY_ADMIN / 0000
CHAIRMAN       / 0000
```

Для всех подразделений, лабораторий, филиалов и представительств:

```text
Логин = код подразделения
Пароль = 1234
```

Примеры:

```text
DAI  / 1234
DSMS / 1234
DUMR / 1234
F_AKM / 1234
```

Департамент видит только собственный кабинет. `CHAIRMAN` видит свод руководителя. `STRATEGY_ADMIN` имеет доступ к обоим режимам, экспорту и настройкам.

## Локальный запуск

Требуется Python 3.11 или 3.12.

Дважды нажмите:

```text
RUN_LOCAL.cmd
```

Или выполните:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Адрес:

```text
http://localhost:8501
```

Локально приложение автоматически использует SQLite-файл `data/orleu_registry.db`.

## Развёртывание в Streamlit Community Cloud

### 1. Создайте постоянную PostgreSQL-базу

Подойдёт Supabase, Neon или другая управляемая PostgreSQL-база. Не используйте локальный SQLite для постоянной работы в Community Cloud.

Получите строку подключения, например:

```text
postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require
```

### 2. Загрузите проект в GitHub

В корне репозитория должны находиться:

```text
app.py
requirements.txt
database.py
auth.py
reference_data.py
ui.py
.streamlit/config.toml
```

Не загружайте `.streamlit/secrets.toml` и локальный `.db`.

### 3. Создайте приложение в Streamlit Community Cloud

- Repository: ваш GitHub-репозиторий;
- Branch: `main`;
- Main file path: `app.py`.

### 4. Добавьте Secret

В настройках приложения откройте **Secrets** и вставьте:

```toml
[database]
url = "postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
```

После перезапуска приложение автоматически создаст таблицы и стандартные аккаунты.

### 5. Получите URL

Streamlit выдаст адрес вида:

```text
https://orleu-strategy-registry.streamlit.app
```

## Структура данных

- `users` — аккаунты и роли;
- `weekly_entries` — недельные записи;
- `report_requests` — запросы отчётов;
- `audit_log` — журнал действий.

## Важное ограничение пилота

Пароли `1234` и `0000` сделаны специально для демонстрационной версии. Перед официальной эксплуатацией замените их или подключите корпоративный Microsoft Entra ID.
