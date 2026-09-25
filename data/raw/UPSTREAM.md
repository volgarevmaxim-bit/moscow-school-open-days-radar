# Источник данных

Снапшот репозитория [volgarevmaxim-bit/schools-map-mathex](https://github.com/volgarevmaxim-bit/schools-map-mathex), ветка `main`.

| Файл | Что это | md5 |
|---|---|---|
| `schools_normalized.csv` | реестр 69 школ (mathex × Forbes) | `57b7fe570a1b31babd99c8dc4b97ed25` |
| `places.json` | 45 точек карты | `342b7f7e2d1249b5ec71a19b78745535` |
| `entities.json` | **канонический реестр**: 84 сущности (blue=22, red=53, green=9) с `kind`/`kind_source`; детсад-программы — green-сущности с `parent_id` | `e511b584f0f5ba3212b847b854efa883` |

- Upstream-коммит: `bacc4804d23131082dad2e4fd198ffa56a6da231` (merge Phase B, 2026-09-25)
- Дата загрузки: 2026-09-25
- Канон (`entities.json`) — предпочтительный источник: полный список сущностей с метками,
  не требует матчинга. CSV и places.json оставлены для обратной совместимости Этапа 1.
- Обновление снапшота — вручную: скопировать файлы из upstream, пересчитать md5, обновить SHA здесь.
