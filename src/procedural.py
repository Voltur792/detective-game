"""Procedural, evidence-consistent mysteries with Bayesian suspect estimates."""

from __future__ import annotations

import math
import random
import secrets

NAMES = (
    "Антон", "Борис", "Вера", "Глеб", "Дарья", "Егор", "Жанна", "Захар",
    "Илья", "Кира", "Лада", "Леонид", "Марина", "Михаил", "Нина", "Оксана",
    "Павел", "Рита", "Руслан", "Светлана", "Сергей", "Тамара", "Тимур", "Ульяна",
    "Фёдор", "Элина", "Юрий", "Яна", "Алина", "Вадим", "Галина", "Денис",
)

MOTIVES = (
    "крупный долг", "давний конфликт с руководством", "угроза увольнения",
    "желание скрыть ошибку в работе", "выгода от сорванной сделки",
    "спор об авторстве", "давний личный счёт", "обещанная выплата от третьего лица",
    "попытка защитить репутацию", "финансовые трудности семьи",
)

TRACES = (
    "синяя нить", "частица красного лака", "серебристая пыль", "зелёное волокно",
    "жёлтая крошка упаковки", "капля фиолетовых чернил", "белый порошок мела",
    "клочок оранжевой изоленты", "полоска чёрной ткани", "крошка сургуча",
)

CRIMES = {
    "theft": {
        "label": "кража", "title": "Пропажа музейной печати",
        "intro": "Из закрытой витрины музея исчезла старинная печать. Посетители ещё не покинули здание.",
        "incident": "возле пустой витрины", "object": "футляр от печати",
        "ending": "Печать была вынесена из витрины и спрятана в футляре для последующей продажи.",
        "places": ("витрина", "пультовая", "раздевалка", "архив", "коридор", "проходная"),
        "roles": ("куратор", "реставратор", "охранник", "экскурсовод", "кассир", "техник", "архивариус", "фотограф", "уборщик", "менеджер", "администратор", "оценщик", "смотритель", "монтажник", "исследователь", "переводчик"),
    },
    "murder": {
        "label": "убийство", "title": "Смерть аудитора в гостинице",
        "intro": "В гостиничном номере найден мёртвым аудитор, готовивший важный доклад. Следствие установило отравление напитка; подробностей насилия в деле нет.",
        "incident": "возле чашки аудитора", "object": "флакон с остатками вещества из напитка",
        "ending": "Напиток аудитора был отравлен до того, как номер закрыли для гостей.",
        "places": ("номер", "пультовая", "прачечная", "офис", "бар", "вестибюль"),
        "roles": ("портье", "горничная", "бармен", "управляющий", "повар", "охранник", "бухгалтер", "курьер", "техник", "консьерж", "организатор", "официант", "водитель", "юрист", "постоялец", "администратор"),
    },
    "sabotage": {
        "label": "саботаж", "title": "Сорванное наблюдение",
        "intro": "Перед редким ночным наблюдением телескоп обсерватории перестал работать. Проверка показала намеренное вмешательство в питание купола.",
        "incident": "на панели телескопа", "object": "снятый модуль питания",
        "ending": "Питание телескопа было намеренно отключено перед наблюдением.",
        "places": ("купол", "серверная", "мастерская", "кабинет", "коридор", "проходная"),
        "roles": ("астроном", "инженер", "механик", "оператор", "охранник", "лаборант", "аналитик", "руководитель", "техник", "архивариус", "электрик", "программист", "стажёр", "фотограф", "администратор", "смотритель"),
    },
    "blackmail": {
        "label": "вымогательство", "title": "Угроза в радиостудии",
        "intro": "Руководителю радиостудии пришло требование денег под угрозой публикации закрытой аудиозаписи. Сообщение отправили из здания студии.",
        "incident": "возле компьютера, с которого отправили угрозу", "object": "копия закрытой аудиозаписи",
        "ending": "Угроза была отправлена из студии с использованием копии закрытой записи.",
        "places": ("студия", "серверная", "гримёрка", "редакция", "коридор", "вестибюль"),
        "roles": ("ведущий", "звукорежиссёр", "редактор", "продюсер", "охранник", "администратор", "гость эфира", "монтажёр", "техник", "журналист", "секретарь", "музыкант", "сценарист", "оператор", "архивариус", "менеджер"),
    },
    "forgery": {
        "label": "подлог", "title": "Подменённый договор",
        "intro": "В финансовом архиве оригинал договора заменили подделкой. Документ должен был разрешить незаконный перевод средств.",
        "incident": "на подменённом договоре", "object": "штамп для поддельной печати",
        "ending": "Оригинал договора был подменён, а поддельная печать подготовлена для незаконного перевода.",
        "places": ("архив", "терминал", "шкафчики", "бухгалтерия", "коридор", "холл"),
        "roles": ("бухгалтер", "кассир", "юрист", "аудитор", "охранник", "архивариус", "управляющий", "курьер", "операционист", "секретарь", "техник", "аналитик", "администратор", "консультант", "инспектор", "клиент"),
    },
}

ALIASES = {
    "кража": "theft", "музей": "theft", "убийство": "murder", "смерть": "murder",
    "саботаж": "sabotage", "обсерватория": "sabotage", "вымогательство": "blackmail",
    "шантаж": "blackmail", "подлог": "forgery", "мошенничество": "forgery",
}


def crime_key(name: str) -> str | None:
    value = name.strip().casefold().replace("ё", "е")
    if value in CRIMES:
        return value
    for alias, key in ALIASES.items():
        if alias in value:
            return key
    return None


def _clue(identifier: str, title: str, text: str, likelihoods: dict[str, float] | None = None) -> dict:
    return {"id": identifier, "title": title, "text": text, "likelihoods": likelihoods or {}}


def generate(crime: str | None = None, seed: int | None = None, count: int | None = None) -> dict:
    """Generate a full case once; save the result so later code changes cannot rewrite it."""
    seed = secrets.randbits(64) if seed is None else seed
    rng = random.Random(seed)
    crime = crime or rng.choice(tuple(CRIMES))
    template = CRIMES[crime]
    count = count or rng.randint(10, 18)
    if not 8 <= count <= 24:
        raise ValueError("В деле должно быть от 8 до 24 подозреваемых.")
    names = rng.sample(NAMES, count)
    roles = rng.sample(template["roles"], min(count, len(template["roles"])))
    while len(roles) < count:
        roles.append(rng.choice(template["roles"]))
    motives = rng.sample(MOTIVES, min(count, len(MOTIVES)))
    suspects = {}
    for index, (name, role) in enumerate(zip(names, roles)):
        suspects[name] = {"role": role, "motive": motives[index % len(motives)]}
    culprit, decoy = rng.sample(names, 2)
    witness = rng.choice([name for name in names if name not in (culprit, decoy)])
    trace = rng.choice(TRACES)
    badge = rng.randint(100, 999)
    places = template["places"]
    motive = suspects[culprit]["motive"]

    clues = {
        places[0]: _clue("trace", "След на месте преступления",
            f"{template['incident'].capitalize()} обнаружен след: {trace}. Он не называет человека, но его можно сравнить с вещами подозреваемых."),
        places[1]: _clue("access", "Запись доступа в критическое время",
            f"Журнал зафиксировал пропуск №{badge} на имя «{culprit}» возле места происшествия. Чуть раньше там отметился и пропуск «{decoy}». Камера не показывает, кто держал пропуска.",
            {culprit: 3.0, decoy: 2.0}),
        places[2]: _clue("possession", "Предмет со совпадающим следом",
            f"В шкафчике с биркой «{culprit}» найден предмет: {template['object']}. На упаковке — совпадающий след: {trace}. Шкафчик заперт личным замком.",
            {culprit: 16.0}),
        places[3]: _clue("motive", "Документ о возможном мотиве",
            f"В рабочей переписке на имя «{culprit}» упомянуты {motive}. Это возможный мотив, но само по себе ещё не доказывает преступление.",
            {culprit: 2.5}),
        places[4]: _clue("red_herring", "След второго подозреваемого",
            f"На служебном маршруте нашли вещь с биркой «{decoy}». Это объясняет его запись в журнале и делает версию о его участии правдоподобной.",
            {decoy: 4.0}),
        places[5]: _clue("exoneration", "Независимая проверка маршрута",
            f"Независимая запись показывает «{decoy}» в другой зоне в критическую минуту. Свидетель «{witness}» подтверждает время; прежний след оказался ложной зацепкой.",
            {decoy: 0.08}),
    }
    return {
        "mode": "procedural", "generator_version": 1, "seed": seed, "crime": crime,
        "title": template["title"], "intro": template["intro"], "ending": template["ending"],
        "suspects": suspects, "culprit": culprit, "decoy": decoy, "witness": witness,
        "badge": badge, "places": list(places), "scenes": clues,
        "visited": [], "questions": [], "found": [], "solved": False, "attempts": 0,
    }


def opening(state: dict, code: str) -> str:
    people = ", ".join(f"{name} ({info['role']})" for name, info in state["suspects"].items())
    return (f"Дело «{state['title']}». Код дела: {code}.\n{state['intro']}\n"
            f"Подозреваемые ({len(state['suspects'])}): {people}.\n"
            f"Места: {', '.join(state['places'])}. "
            "Осматривай места, спрашивай об алиби, доступе и мотиве, оценивай версии и выдвигай обвинение. "
            "Все факты этого дела сохраняются по коду.")


def _resolve(value: str | None, options) -> str | None:
    value = (value or "").strip().casefold().replace("ё", "е")
    for option in options:
        if value == option.casefold().replace("ё", "е"):
            return option
    words = value.split()
    for word in words:
        if len(word) < 3:
            continue
        matches = [option for option in options if option.casefold().replace("ё", "е")[:3] == word[:3]]
        if len(matches) == 1:
            return matches[0]
    return None


def inspect(state: dict, place: str) -> tuple[str, bool]:
    key = _resolve(place, state["places"])
    if key is None:
        return f"Неизвестное место. Доступны: {', '.join(state['places'])}.", False
    item = state["scenes"][key]
    if key in state["visited"]:
        return item["text"] + "\n\nЭта улика уже записана.", False
    state["visited"].append(key)
    state["found"].append(item["id"])
    return item["text"] + f"\n\nНовая улика: {item['title']}.", True


def question(state: dict, suspect: str, topic: str) -> tuple[str, bool]:
    name = _resolve(suspect, state["suspects"])
    if name is None:
        return "Назови одного из подозреваемых из описания дела.", False
    subject = _resolve(topic, ("алиби", "доступ", "мотив"))
    if subject is None:
        return "Можно спросить об алиби, доступе или мотиве.", False
    marker = f"{name}:{subject}"
    info = state["suspects"][name]
    if subject == "алиби":
        if name == state["decoy"]:
            reply = f"«{name}» признаёт, что проходил рядом до происшествия, но утверждает, что в критическую минуту был в другой зоне. Это можно проверить."
        else:
            reply = f"«{name}» утверждает: «В критическое время меня там не было». Журнал доступа позволяет проверить заявление."
    elif subject == "доступ":
        reply = f"«{name}» работает как {info['role']} и мог находиться в здании. Для проверки конкретного входа нужен журнал доступа."
    else:
        reply = f"У «{name}» есть возможный личный повод: {info['motive']}. Мотив сам по себе не доказывает участие."
    if marker in state["questions"]:
        return reply + "\n\nОтвет уже записан.", False
    state["questions"].append(marker)
    return reply, True


def _all_evidence(state: dict) -> dict[str, dict]:
    return {item["id"]: item for item in state["scenes"].values()}


def probabilities(state: dict) -> dict[str, float]:
    """Uniform prior updated by likelihood ratios for discovered evidence only."""
    names = list(state["suspects"])
    log_scores = {name: 0.0 for name in names}
    evidence = _all_evidence(state)
    for identifier in state["found"]:
        for name, ratio in evidence[identifier]["likelihoods"].items():
            log_scores[name] += math.log(ratio)
    offset = max(log_scores.values())
    strengths = {name: math.exp(score - offset) for name, score in log_scores.items()}
    total = sum(strengths.values())
    return {name: strength / total for name, strength in strengths.items()}


def theories(state: dict) -> str:
    odds = probabilities(state)
    ranking = sorted(odds, key=odds.get, reverse=True)
    lines = [f"Версии по найденным уликам в деле «{state['title']}»:"]
    lines.extend(f"• {name}: {odds[name]:.1%}" for name in ranking)
    return "\n".join(lines) + "\nОценка использует равные начальные шансы и отношения правдоподобия для открытых улик. Зависимые улики могут завышать уверенность."


def status(state: dict, code: str) -> str:
    evidence = _all_evidence(state)
    found = "\n".join(f"• {evidence[item]['title']}" for item in state["found"]) or "Пока нет улик."
    people = ", ".join(f"{name} ({info['role']})" for name, info in state["suspects"].items())
    return (f"Дело «{state['title']}» ({code}): {'раскрыто' if state['solved'] else 'расследуется'}.\n"
            f"Подозреваемые: {people}.\nМеста: {', '.join(state['places'])}.\n"
            f"Осмотрены: {', '.join(state['visited']) or 'ничего'}.\nУлики:\n{found}")


def hint(state: dict) -> str:
    for place in state["places"][:4]:
        if place not in state["visited"]:
            return f"Осмотри {place}: там может быть часть цепочки доказательств."
    if "exoneration" not in state["found"]:
        return f"Проверь {state['places'][5]}: ложный след стоит перепроверить."
    return "Сопоставь физический след, журнал доступа, найденный предмет и мотив. После этого можно предъявить обвинение."


def accuse(state: dict, suspect: str) -> tuple[str, bool]:
    name = _resolve(suspect, state["suspects"])
    if name is None:
        return "Назови одного из подозреваемых из описания дела.", False
    if state["solved"]:
        return f"Дело уже раскрыто. Виновный: {state['culprit']}.", False
    state["attempts"] += 1
    required = {"trace", "access", "possession"}
    if not required <= set(state["found"]):
        return "Пока недостаточно доказательств. Нужны след с места, запись доступа и предмет с совпадающим следом.", True
    odds = probabilities(state)
    if name == state["culprit"] and odds[name] >= 0.60:
        state["solved"] = True
        return (f"Дело раскрыто! Виновный — {name} ({state['suspects'][name]['role']}). "
                f"{state['ending']} Запись доступа, совпадающий след и найденный предмет подтверждают версию. "
                f"Возможный мотив: {state['suspects'][name]['motive']}."), True
    if name == state["culprit"]:
        return "Версия требует дополнительной проверки: изучи мотив и перепроверь ложный след.", True
    return f"Улики пока не складываются в убедительное обвинение против «{name}». Расследование продолжается.", True
