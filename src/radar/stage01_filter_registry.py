"""
stage01_filter_registry — Этап 1 (Фаза 1): фильтрация реестра школ.

Вход:  data/raw/entities.json  (канон)
Выходы:
  data/schools_filtered.json       — полный лог решений (84 записи)
  data/intermediate/schools_excluded.csv  — 8 ручных исключений (5 ТЗ §3.1 + 3 гео-ревью)
  backlog/v2_non_blue_schools.csv         — 60 не-blue неисключённых

Запуск: PYTHONPATH=src python -m radar.stage01_filter_registry
"""

import csv
import hashlib
import json
import os
import pathlib
import re
import sys

# ── константы ────────────────────────────────────────────────────────────────
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CANON_PATH = REPO_ROOT / "data" / "raw" / "entities.json"
EXCLUSIONS_CONFIG = REPO_ROOT / "config" / "exclusions.json"
OUT_FILTERED = REPO_ROOT / "data" / "schools_filtered.json"
OUT_EXCLUDED_CSV = REPO_ROOT / "data" / "intermediate" / "schools_excluded.csv"
OUT_BACKLOG = REPO_ROOT / "backlog" / "v2_non_blue_schools.csv"

EXPECTED_MD5 = "e511b584f0f5ba3212b847b854efa883"
EXPECTED_COUNT = 84
EXPECTED_BLUE = 22
EXPECTED_INCLUDED = 16

# blue-исключения: 3 (ТЗ §3.1) + 3 (гео-ревью 2026-09-25), green-цели: 2 → итого 8
EXPECTED_MANUAL_EXCLUSIONS = 8
EXPECTED_RED_EXCLUDED = 53
EXPECTED_GREEN_EXCLUDED = 7  # green, не являющиеся целями исключений


# ── нормализация имени для матчинга ──────────────────────────────────────────
def normalize_name(name: str) -> str:
    """Привести имя к виду для fuzzy-матчинга: lower, снять кавычки/скобки."""
    s = name.lower()
    # Убрать « » " ' №
    for ch in ("«", "»", '"', "'", "№"):
        s = s.replace(ch, " ")
    # Слово "и" как разделитель → пробел (и между Pre-Nursery и Nursery)
    s = re.sub(r"\bи\b", " ", s)
    # Скобки, двоеточие, запятая, тире → пробел
    s = re.sub(r"[\(\)\[\]\{\}:;,/—–-]", " ", s)
    # Схлопнуть пробелы
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ── чтецы ────────────────────────────────────────────────────────────────────
def read_canon(path: pathlib.Path) -> dict:
    """Прочитать entities.json с utf-8-sig tolerance."""
    raw = path.read_bytes()
    if raw[:3] == b"\xef\xbb\xbf":
        text = raw.decode("utf-8-sig")
    else:
        text = raw.decode("utf-8")
    return json.loads(text)


def read_exclusions_config(path: pathlib.Path) -> dict[str, list[str]]:
    """Прочитать группы ручных исключений: ТЗ §3.1 + гео-ревью."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {key: list(data.get(key, [])) for key in
            ("manual_exclusions", "geo_review_exclusions")}


# ── md5 ──────────────────────────────────────────────────────────────────────
def file_md5(path: pathlib.Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


# ── матчинг исключений ────────────────────────────────────────────────────────
def match_exclusions(
    exclusion_names: list[str], entities: list[dict]
) -> dict[str, dict]:
    """
    Для каждого имени из списка исключений найти ровно 1 сущность в каноне
    по нормализованному имени. Вернуть dict: exclusion_target_canon → entity.
    Падает с диагностикой при 0 или >1 кандидататах.
    """
    # Предварительно нормализовать имена сущностей
    canon_map: dict[str, list[dict]] = {}
    for e in entities:
        n = normalize_name(e["name"])
        canon_map.setdefault(n, []).append(e)
        # Также нормализовать name_normalized на всякий случай
        n2 = normalize_name(e["name_normalized"]).strip()
        if n2 and n2 != n:
            canon_map.setdefault(n2, []).append(e)

    result: dict[str, dict] = {}
    for target in exclusion_names:
        tn = normalize_name(target)
        candidates = canon_map.get(tn, [])
        if len(candidates) == 0:
            # Попробуем поиск подстрокой — матчинг по нормализованному должен сработать,
            # но проверим на случай разных пунктуационных вариантов
            for norm, cands in canon_map.items():
                if tn in norm or norm in tn:
                    candidates.extend(cands)
            # Дедупликация
            seen = set()
            deduped = []
            for c in candidates:
                if c["id"] not in seen:
                    seen.add(c["id"])
                    deduped.append(c)
            candidates = deduped

        if len(candidates) == 0:
            print(
                f"ОШИБКА: ни один кандидат не найден для исключения '{target}' "
                f"(нормализовано: '{tn}')",
                file=sys.stderr,
            )
            print("Доступные нормализованные имена в каноне:", file=sys.stderr)
            for e in entities:
                print(f"  id={e['id']:50s} norm='{normalize_name(e['name'])}'", file=sys.stderr)
            sys.exit(1)
        if len(candidates) > 1:
            ids = [c["id"] for c in candidates]
            print(
                f"ОШИБКА: для исключения '{target}' найдено {len(candidates)} кандидатов: {ids}",
                file=sys.stderr,
            )
            sys.exit(1)

        result[target] = candidates[0]

    return result


# ── сборка включённых записей ──────────────────────────────────────────────
def build_included_entry(e: dict) -> dict:
    return {
        "id": e["id"],
        "name": e["name"],
        "included": True,
        "kind": e["kind"],
        "kind_match": "blue",
        "kind_source": e["kind_source"],
        "address": e["address_normalized"],
        "mathex_url": e.get("mathex_url", None),
    }


def build_excluded_entry(e: dict, reason: str) -> dict:
    return {
        "id": e["id"],
        "name": e["name"],
        "included": False,
        "kind": e["kind"],
        "reason": reason,
    }


# ── review_flag для backlog ────────────────────────────────────────────────
def get_review_flag(e: dict) -> str:
    ks = e["kind_source"]
    if "не подтверждён" in ks:
        return "priority: приём с 1 класса не подтверждён"
    if "default:" in ks:
        return "kind by default (no signal)"
    return "kindergarten program"


# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 72)
    print("Этап 1 — Фильтрация реестра школ (v1 blue-only)")
    print("=" * 72)

    # 1. MD5 проверка канона
    canon_md5 = file_md5(CANON_PATH)
    print(f"\n[1] MD5 канона: {canon_md5}")
    assert canon_md5 == EXPECTED_MD5, (
        f"MD5 не совпадает! Ожидался {EXPECTED_MD5}, получен {canon_md5}"
    )

    # 2. Чтение канона
    canon = read_canon(CANON_PATH)
    entities = canon["entities"]
    assert len(entities) == EXPECTED_COUNT, (
        f"Ожидалось {EXPECTED_COUNT} сущностей, получено {len(entities)}"
    )
    blue_count = sum(1 for e in entities if e["kind"] == "blue")
    assert blue_count == EXPECTED_BLUE, (
        f"Ожидалось {EXPECTED_BLUE} blue, получено {blue_count}"
    )
    print(f"[2] Канон: {len(entities)} сущностей, blue={blue_count}")

    # 3. Чтение конфига и матчинг исключений (ТЗ §3.1 + гео-ревью)
    groups = read_exclusions_config(EXCLUSIONS_CONFIG)
    targets = [(g, n) for g, ns in groups.items() for n in ns]
    group_of = {n: g for g, n in targets}
    exclusion_names = [n for _, n in targets]
    print(f"[3] Ручные исключения ({len(exclusion_names)}):")
    for g, n in targets:
        print(f"    - [{g}] {n}")

    matches = match_exclusions(exclusion_names, entities)
    for target, ent in matches.items():
        print(f"    match: {target} → id={ent['id']} kind={ent['kind']}")

    excluded_ids = {ent["id"] for ent in matches.values()}
    assert len(excluded_ids) == EXPECTED_MANUAL_EXCLUSIONS, (
        f"Уникальных excluded id: {len(excluded_ids)}"
    )

    # 4. Сборка результатов (порядок как в каноне)
    included_entries: list[dict] = []
    all_entries: list[dict] = []
    excluded_rows: list[dict] = []  # для CSV
    backlog_rows: list[dict] = []   # для backlog CSV

    for e in entities:
        eid = e["id"]
        kind = e["kind"]

        if kind == "blue" and eid not in excluded_ids:
            # Включён
            entry = build_included_entry(e)
            included_entries.append(entry)
            all_entries.append(entry)
        elif eid in excluded_ids:
            # Ручное исключение: ТЗ §3.1 или гео-ревью
            target_name = None
            for t, ent in matches.items():
                if ent["id"] == eid:
                    target_name = t
                    break
            if group_of.get(target_name, "") == "geo_review_exclusions":
                reason = "manual exclusion (geo review)"
                verdict = "excluded; blue (geo review)"
            else:
                reason = "manual exclusion"
                verdict = ("excluded; blue" if kind == "blue"
                           else "excluded; green (out by kind anyway)")
            excluded_entry = build_excluded_entry(e, reason)
            all_entries.append(excluded_entry)
            excluded_rows.append({
                "exclusion_target": target_name,
                "canon_id": eid,
                "canon_name": e["name"],
                "kind": kind,
                "verdict": verdict,
            })
        else:
            # Не-blue, не исключение → отклонён
            if kind == "red":
                reason = "kind=red, v1 monitors blue only"
            else:  # green
                reason = "kind=green, v1 monitors blue only"
            excluded_entry = build_excluded_entry(e, reason)
            all_entries.append(excluded_entry)

        # Заполнение backlog (все не-blue кроме целей исключений)
        if kind != "blue" and eid not in excluded_ids:
            backlog_rows.append({
                "id": eid,
                "name": e["name"],
                "kind": kind,
                "kind_source": e["kind_source"],
                "review_flag": get_review_flag(e),
            })

    # 5. Ассерты
    assert len(included_entries) == EXPECTED_INCLUDED, (
        f"Ожидалось {EXPECTED_INCLUDED} включённых, получено {len(included_entries)}"
    )
    included_ids_list = [ent["id"] for ent in included_entries]
    assert len(set(included_ids_list)) == len(included_ids_list), (
        "Обнаружены дубликаты id среди включённых!"
    )

    # Счётчики для отладки
    cnt_manual_exclusion = sum(1 for e in all_entries if not e["included"] and e.get("reason") == "manual exclusion")
    cnt_geo_exclusion = sum(1 for e in all_entries if not e["included"] and e.get("reason") == "manual exclusion (geo review)")
    cnt_red = sum(1 for e in all_entries if not e["included"] and "kind=red" in e.get("reason", ""))
    cnt_green_excluded = sum(1 for e in all_entries if not e["included"] and "kind=green" in e.get("reason", ""))
    total_check = len(included_entries) + cnt_manual_exclusion + cnt_geo_exclusion + cnt_red + cnt_green_excluded

    assert total_check == EXPECTED_COUNT, (
        f"Контрольная сумма не сходится: {total_check} != {EXPECTED_COUNT} "
        f"(included={len(included_entries)}, manual={cnt_manual_exclusion}, geo={cnt_geo_exclusion}, "
        f"red={cnt_red}, green={cnt_green_excluded})"
    )

    # 6. Запись выходов

    # 6a. data/schools_filtered.json
    os.makedirs(OUT_FILTERED.parent, exist_ok=True)
    with open(OUT_FILTERED, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    print(f"\n[6a] Записан {OUT_FILTERED} ({len(all_entries)} записей)")

    # 6b. data/intermediate/schools_excluded.csv
    os.makedirs(OUT_EXCLUDED_CSV.parent, exist_ok=True)
    with open(OUT_EXCLUDED_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["exclusion_target", "canon_id", "canon_name", "kind", "verdict"]
        )
        writer.writeheader()
        writer.writerows(excluded_rows)
    print(f"[6b] Записан {OUT_EXCLUDED_CSV} ({len(excluded_rows)} строк)")

    # 6c. backlog/v2_non_blue_schools.csv
    os.makedirs(OUT_BACKLOG.parent, exist_ok=True)
    with open(OUT_BACKLOG, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "name", "kind", "kind_source", "review_flag"]
        )
        writer.writeheader()
        writer.writerows(backlog_rows)
    print(f"[6c] Записан {OUT_BACKLOG} ({len(backlog_rows)} строк)")

    # 7. Сводка
    print()
    print("-" * 72)
    print("СВОДКА")
    print(f"  Blue в каноне:   {blue_count}")
    print(f"  Включено (blue): {len(included_entries)}")
    print(f"    − blue исключения (ТЗ §3.1):   {sum(1 for r in excluded_rows if r['kind']=='blue' and 'geo' not in r['verdict'])}")
    print(f"    − blue исключения (гео-ревью): {sum(1 for r in excluded_rows if 'geo' in r['verdict'])}")
    print(f"    − green-цели:      {sum(1 for r in excluded_rows if r['kind']=='green')}")
    print(f"  Отклонено red:   {cnt_red}")
    print(f"  Отклонено green: {cnt_green_excluded}")
    print(f"  Контрольная сумма: {total_check} (ожидалось {EXPECTED_COUNT})")
    print(f"  Backlog: {len(backlog_rows)} не-blue")
    print()
    print("Включённые id:")
    for ent in included_entries:
        print(f"    {ent['id']}")


if __name__ == "__main__":
    main()