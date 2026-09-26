"""Astra tools for a chat-driven detective case."""

from astra_plugin_sdk import Plugin, tool

from . import game


class DetectiveGame(Plugin):
    @tool("Начать новое дело с Астрой. Пустой case_name создаёт процедурное дело; можно выбрать преступление (кража, убийство, саботаж, вымогательство, подлог) либо название классического дела. suspect_count — число подозреваемых от 8 до 24, 0 означает случайное число. Верни код дела пользователю для следующих действий в Astra или Telegram.")
    async def detective_start(self, case_name: str = "", suspect_count: int = 0) -> str:
        return game.start(case_name, suspect_count)

    @tool("Показать доступные детективные дела без разгадок. Используй, когда пользователь просит выбрать сюжет.")
    async def detective_list_cases(self) -> str:
        return game.list_cases()

    @tool("Осмотреть место в детективной игре. case_code — код из detective_start; place — место из описания текущего дела или detective_status. Передавай факты из ответа инструмента без выдуманных улик.")
    async def detective_inspect(self, case_code: str = "", place: str = "") -> str:
        return game.inspect(case_code, place)

    @tool("Опросить подозреваемого в детективном деле. suspect_name — имя из дела; case_code — код дела (можно опустить, если только одно дело с этим человеком); topic — алиби, доступ или мотив, по умолчанию алиби. suspect — старое имя параметра suspect_name. Передавай ответ инструмента без выдуманных показаний.")
    async def detective_question(self, suspect_name: str = "", case_code: str = "", topic: str = "алиби", suspect: str = "") -> str:
        return game.question(case_code, suspect_name or suspect, topic or "алиби")

    @tool("Показать собранные улики и ход детективного дела по его коду.")
    async def detective_status(self, case_code: str = "") -> str:
        return game.status(case_code)

    @tool("Оценить вероятности версий о подозреваемых в текущем деле по уже найденным уликам. Не раскрывает скрытые факты или готовый ответ.")
    async def detective_theories(self, case_code: str = "") -> str:
        return game.theories(case_code)

    @tool("Дать следующую подсказку по детективному делу, только если пользователь просит подсказку.")
    async def detective_hint(self, case_code: str = "") -> str:
        return game.hint(case_code)

    @tool("Проверить официальное обвинение в детективной игре. Вызывай, когда пользователь прямо называет виновного. suspect_name — имя подозреваемого; case_code — код дела, если он известен. suspect — прежнее имя параметра suspect_name.")
    async def detective_accuse(self, suspect_name: str = "", case_code: str = "", suspect: str = "") -> str:
        return game.accuse(case_code, suspect_name or suspect)


if __name__ == "__main__":
    DetectiveGame().run()
