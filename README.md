# openhouse-radar

Еженедельный радар дней открытых дверей в школах Москвы.

Telegram-каналы школ из реестра → LLM-классификация (DeepSeek) → сводка в Telegram (Saved Messages): анонсы мероприятий для будущих учеников (дата, адрес, регистрация) + заголовки прочих сообщений + heartbeat «за неделю не было».


> **Репозиторий:** https://github.com/volgarevmaxim-bit/moscow-school-open-days-radar
> **Локальная папка:** `C:\Users\volga\openhouse-radar` — внутреннее имя проекта; имя репо на GitHub отличается.

## Документы

- ТЗ (v4, финал уточнений): [`docs/ТЗ_радар_дней_открытых_дверей_v4.md`](docs/ТЗ_радар_дней_открытых_дверей_v4.md)
- План работ: [`docs/PLAN.md`](docs/PLAN.md)
- Handoff: `HANDOFF.md` (локальный, вне git — в .gitignore)

## Источники данных

Снапшот из [volgarevmaxim-bit/schools-map-mathex](https://github.com/volgarevmaxim-bit/schools-map-mathex) — фиксация коммита и дата в [`data/raw/UPSTREAM.md`](data/raw/UPSTREAM.md).

## Стек

Python 3.11 · Telethon (upstream-чтение + downstream-отправка) · DeepSeek V4.1 Flash через ProxyAPI (OpenAI-совместимый шлюз, `config/llm.json`) · GitHub Actions (суточный + недельный cron, off-peak окно по МСК) · state в Actions Cache/Artifacts.

## Статус

🚧 Этап 1 выполнен, гео-гейт закрыт (решение владельца 2026-09-25): `data/schools_filtered.json` — реестр v1, **16 школ** (канон 84 сущности: blue=22 − 3 исключения ТЗ §3.1 − 3 гео-исключения: Cambridge International, Brookes Moscow International, MCS/Magic Castle; дошкольные цели §3.1 — green, отсеклись kind-фильтром; французский лицей Дюма оставлен — канал двуязычный FR/RU, тест-кейс суммаризатора). Сборка идемпотентна: `PYTHONPATH=src python -m radar.stage01_filter_registry`; backlog v2 — 60 не-blue школ (`backlog/v2_non_blue_schools.csv`). LLM-шлюз проверен: ProxyAPI, `deepseek/deepseek-v4.1-flash` (`scripts/smoke_proxyapi.py`, 200 OK). Ждём: вопрос 3 (alter-ego Telegram — блокирует Этап 2) и вопрос 4 (cron).
