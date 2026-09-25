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

Python 3.11 · Telethon (upstream-чтение + downstream-отправка) · DeepSeek (классификация/экстракция/суммаризация) · GitHub Actions (суточный + недельный cron, off-peak окно по МСК) · state в Actions Cache/Artifacts.

## Статус

🚧 Этап 1 выполнен (2026-09-25): `data/schools_filtered.json` — реестр v1, **19 школ** (канон 84 сущности: blue=22 − 3 ручных исключения ТЗ §3.1; 2 дошкольные цели исключений — green, отсеклись kind-фильтром). Сборка идемпотентна: `PYTHONPATH=src python -m radar.stage01_filter_registry`; backlog v2 — 60 не-blue школ (`backlog/v2_non_blue_schools.csv`). Ждём: ревью реестра владельцем (вкл. 4 международные школы) и ответы на вопросы 2–4 (DeepSeek / alter-ego / cron).
