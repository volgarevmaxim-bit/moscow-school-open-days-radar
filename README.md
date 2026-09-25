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

🅿️ Паркинг (с 2026-09-25): реализация приостановлена до рефакторинга дата-флоу upstream schools-map-mathex — см. [`docs/ТЗ_аудит_schools-map-mathex_v1.md`](docs/ТЗ_аудит_schools-map-mathex_v1.md). При возобновлении — обновить снапшот `data/raw/` и SHA в `UPSTREAM.md`.
