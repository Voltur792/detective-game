"""Persistent, replayable detective cases with evidence-driven theories."""

from __future__ import annotations

import json
import math
import os
import secrets
import tempfile
import threading
from pathlib import Path

from .cases import CASES
from . import procedural

_LOCK = threading.RLock()


def _state_path() -> Path:
    root = os.environ.get("ASTRA_DETECTIVE_DATA_DIR")
    if not root:
        root = str(Path(os.environ.get("APPDATA") or Path.home() / ".local" / "share") / "detective-game")
    return Path(root) / "games.json"


def _load() -> dict:
    path = _state_path()
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _save(games: dict) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="games-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(games, out, ensure_ascii=False, separators=(",", ":"))
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _normal(value: str | None) -> str:
    return " ".join((value or "").strip().casefold().replace("ё", "е").split())


def _get(games: dict, code: str | None) -> dict | None:
    return games.get((code or "").strip().upper())


def _case_for_suspect(games: dict, suspect: str | None) -> tuple[str | None, int]:
    matching = []
    for candidate, state in games.items():
        if candidate == "_meta":
            continue
        if state.get("mode") == "procedural":
            found = procedural._resolve(suspect, state["suspects"])
        else:
            found = _choice(suspect, _case_variant(state)[0]["suspects"])
        if found:
            matching.append(candidate)
    return (matching[0] if len(matching) == 1 else None), len(matching)


def _choice(value: str, options, aliases: dict[str, str] | None = None) -> str | None:
    """Accept common Russian case endings in natural chat requests."""
    value = _normal(value)
    names = {name: name for name in options}
    names.update(aliases or {})
    if value in names:
        return names[value]
    words = value.split()
    for word in words:
        if len(word) < 3:
            continue
        matches = {target for name, target in names.items() if word[: min(3, len(name))] == name[: min(3, len(name))]}
        if len(matches) == 1:
            return matches.pop()
    return None


def _case_variant(game: dict) -> tuple[dict, dict]:
    # v0.1.0 games had no case/variant fields. Their proof clues remain valid.
    case = CASES[game.get("case", "museum")]
    variant = case["variants"][game.get("variant", "nina")]
    return case, variant


def _case_id(name: str) -> str | None:
    value = _normal(name)
    for key, case in CASES.items():
        if value in (key, _normal(case["title"]), *case["aliases"]) or any(alias in value for alias in case["aliases"] if len(alias) >= 4):
            return key
    return None


def list_cases() -> str:
    lines = ["Процедурные дела: кража, убийство, саботаж, вымогательство, подлог. В каждом от 8 до 24 подозреваемых; виновный, мотив и улики создаются заново.",
             "Классические дела с написанным сюжетом:"]
    lines.extend(f"• {case['title']} — {case['intro']}" for case in CASES.values())
    return "\n".join(lines) + "\nБез названия начинается новое процедурное дело."


def start(case_name: str | None = "", suspect_count: int | None = 0) -> str:
    requested = _normal(case_name)
    generic = ("", "случайное", "случайный", "случайное дело", "любое", "random", "новое", "новое дело", "процедурное", "бесконечное")
    crime = procedural.crime_key(requested)
    if requested in generic or crime:
        try:
            generated = procedural.generate(crime=crime, count=suspect_count or None)
        except ValueError as exc:
            return str(exc)
        with _LOCK:
            games = _load()
            code = secrets.token_hex(4).upper()
            while code in games:
                code = secrets.token_hex(4).upper()
            games[code] = generated
            _save(games)
        return procedural.opening(generated, code)

    if requested != "классическое":
        case_id = _case_id(requested)
        if case_id is None:
            return "Такого дела нет.\n" + list_cases()
    else:
        case_id = None

    if suspect_count:
        return "Число подозреваемых задаётся для процедурного дела. Выбери преступление: кража, убийство, саботаж, вымогательство или подлог."

    with _LOCK:
        games = _load()
        meta = games.setdefault("_meta", {"seen_cases": []})
        if case_id is None:
            unseen = [key for key in CASES if key not in meta.get("seen_cases", [])]
            if not unseen:
                meta["seen_cases"] = []
                unseen = list(CASES)
            case_id = secrets.choice(unseen)
            meta.setdefault("seen_cases", []).append(case_id)
        case = CASES[case_id]
        variant_id = secrets.choice(list(case["variants"]))
        code = secrets.token_hex(4).upper()
        while code in games:
            code = secrets.token_hex(4).upper()
        games[code] = {"case": case_id, "variant": variant_id, "visited": [], "questions": [], "clues": [], "solved": False, "attempts": 0}
        _save(games)

    suspects = ", ".join(f"{name.capitalize()} ({role})" for name, role in case["suspects"].items())
    return (f"Дело «{case['title']}». Код дела: {code}.\n{case['intro']}\n"
            f"Подозреваемые: {suspects}.\n"
            f"Места для осмотра: {', '.join(case['places'])}. "
            "Расспрашивай подозреваемых, собирай улики и назови виновного, когда будет достаточно доказательств. "
            "Дело сохранено по коду; при повторном прохождении события могут сложиться иначе.")


def inspect(code: str, place: str) -> str:
    with _LOCK:
        games = _load()
        game = _get(games, code)
        if game is None:
            return "Дело не найдено. Проверь код или начни новое."
        if game.get("mode") == "procedural":
            reply, changed = procedural.inspect(game, place)
            if changed:
                _save(games)
            return reply
        case, variant = _case_variant(game)
        key = _choice(place, case["places"], case["place_aliases"])
        if key not in variant["scenes"]:
            return f"Неизвестное место. Доступны: {', '.join(case['places'])}."
        item = variant["scenes"][key]
        if key in game["visited"]:
            return item["text"] + "\n\nЭту улику ты уже записал."
        game["visited"].append(key)
        game["clues"].append(item["clue"])
        _save(games)
        return item["text"] + f"\n\nНовая улика: {item['clue']}."


def question(code: str, suspect: str, topic: str) -> str:
    with _LOCK:
        games = _load()
        if not code:
            code, count = _case_for_suspect(games, suspect)
            if not code:
                return "Укажи код дела из его начала: несколько дел подходят для допроса." if count else "Укажи код дела из его начала, чтобы начать допрос."
        game = _get(games, code)
        if game is None:
            return "Дело не найдено. Проверь код или начни новое."
        if game.get("mode") == "procedural":
            reply, changed = procedural.question(game, suspect, topic)
            if changed:
                _save(games)
            return reply
        case, variant = _case_variant(game)
        person = _choice(suspect, case["suspects"])
        if person not in case["suspects"]:
            return f"Можно опросить: {', '.join(name.capitalize() for name in case['suspects'])}."
        answers = dict(case["interviews"][person])
        answers.update(variant.get("answers", {}).get(person, {}))
        subject = _choice(topic, answers)
        if subject not in answers:
            return f"Спроси {person.capitalize()} об одном из предметов: {', '.join(answers)}."
        item = answers[subject]
        marker = f"{person}:{subject}"
        if marker in game["questions"]:
            return item["text"] + "\n\nЭтот ответ уже записан."
        game["questions"].append(marker)
        if item["clue"] and item["clue"] not in game["clues"]:
            game["clues"].append(item["clue"])
        _save(games)
        return item["text"] + (f"\n\nНовая улика: {item['clue']}." if item["clue"] else "")


def status(code: str) -> str:
    with _LOCK:
        game = _get(_load(), code)
    if game is None:
        return "Дело не найдено. Проверь код или начни новое."
    if game.get("mode") == "procedural":
        return procedural.status(game, code.strip().upper())
    case, _ = _case_variant(game)
    clues = "\n".join(f"• {title}" for title in game["clues"]) or "Пока нет улик."
    return (f"Дело «{case['title']}» ({code.strip().upper()}): {'раскрыто' if game['solved'] else 'расследуется'}.\n"
            f"Осмотрены: {', '.join(game['visited']) or 'ничего'}.\nУлики:\n{clues}\n"
            f"Подозреваемые: {', '.join(name.capitalize() for name in case['suspects'])}. "
            f"Места: {', '.join(case['places'])}.")


def _evidence(case: dict, variant: dict) -> dict[str, dict[str, int]]:
    evidence = {item["clue"]: item["weights"] for item in variant["scenes"].values()}
    for person, topics in case["interviews"].items():
        merged = dict(topics)
        merged.update(variant.get("answers", {}).get(person, {}))
        for item in merged.values():
            if item["clue"]:
                evidence[item["clue"]] = item["weights"]
    return evidence


def theories(code: str) -> str:
    with _LOCK:
        game = _get(_load(), code)
    if game is None:
        return "Дело не найдено."
    if game.get("mode") == "procedural":
        return procedural.theories(game)
    case, variant = _case_variant(game)
    evidence = _evidence(case, variant)
    scores = {person: 0 for person in case["suspects"]}
    for title in game["clues"]:
        for person, weight in evidence.get(title, {}).items():
            scores[person] += weight
    strengths = {person: math.exp(min(max(score * 0.35, -20), 20)) for person, score in scores.items()}
    total = sum(strengths.values())
    ranking = sorted(strengths, key=strengths.get, reverse=True)
    lines = [f"Оценка версий по найденным уликам в деле «{case['title']}»:"]
    lines.extend(f"• {person.capitalize()}: {strengths[person] / total:.0%}" for person in ranking)
    return "\n".join(lines) + "\nОценка меняется после осмотра и допросов."


def hint(code: str) -> str:
    with _LOCK:
        game = _get(_load(), code)
    if game is None:
        return "Дело не найдено."
    if game.get("mode") == "procedural":
        return procedural.hint(game)
    case, variant = _case_variant(game)
    proof = set(variant["proof"])
    for place in case["places"]:
        item = variant["scenes"][place]
        if item["clue"] in proof and place not in game["visited"]:
            return f"Проверь {place}: там может быть важная часть цепочки событий."
    if not game["solved"]:
        return "Ключевые улики уже собраны. Сопоставь их и назови подозреваемого, которого они связывают с событием."
    return "Дело раскрыто. Можно начать другое расследование."


def accuse(code: str, suspect: str) -> str:
    with _LOCK:
        games = _load()
        if not code:
            code, count = _case_for_suspect(games, suspect)
            if not code:
                return "Укажи код дела из его начала: несколько дел подходят для обвинения." if count else "Укажи код дела из его начала, чтобы предъявить обвинение."
        game = _get(games, code)
        if game is None:
            return "Дело не найдено."
        if game.get("mode") == "procedural":
            reply, changed = procedural.accuse(game, suspect)
            if changed:
                _save(games)
            return reply
        case, variant = _case_variant(game)
        person = _choice(suspect, case["suspects"])
        if person not in case["suspects"]:
            return f"Назови одного подозреваемого: {', '.join(name.capitalize() for name in case['suspects'])}."
        if game["solved"]:
            return f"Дело уже раскрыто. Виновный: {variant['culprit'].capitalize()}."
        game["attempts"] += 1
        if not set(variant["proof"]) <= set(game["clues"]):
            result = "Для убедительного обвинения пока не хватает цепочки из трёх ключевых улик. Осмотри места и сопоставь след, маршрут и находку."
        elif person == variant["culprit"]:
            game["solved"] = True
            result = f"Дело раскрыто! {variant['solution']}"
        else:
            result = f"Версия о {person.capitalize()} не связывает все ключевые улики. Расследование продолжается."
        _save(games)
        return result
