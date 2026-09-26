import os
import tempfile
import unittest

from src import game, procedural
from src.cases import CASES


class DetectiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["ASTRA_DETECTIVE_DATA_DIR"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("ASTRA_DETECTIVE_DATA_DIR", None)
        self.tmp.cleanup()

    def _seed(self, case_id, variant_id):
        code = f"{case_id}-{variant_id}".upper()
        states = game._load()
        states[code] = {"case": case_id, "variant": variant_id, "visited": [], "questions": [], "clues": [], "solved": False, "attempts": 0}
        game._save(states)
        return code

    def test_every_variant_has_three_discoverable_proofs_and_can_be_solved(self):
        for case_id, case in CASES.items():
            for variant_id, variant in case["variants"].items():
                with self.subTest(case=case_id, variant=variant_id):
                    code = self._seed(case_id, variant_id)
                    self.assertIn("не хватает", game.accuse(code, variant["culprit"]))
                    proof_places = [place for place, item in variant["scenes"].items() if item["clue"] in variant["proof"]]
                    self.assertEqual(len(proof_places), 3)
                    for place in proof_places:
                        self.assertIn("Новая улика", game.inspect(code, place))
                    wrong = next(person for person in case["suspects"] if person != variant["culprit"])
                    self.assertIn("Расследование продолжается", game.accuse(code, wrong))
                    self.assertIn("Дело раскрыто", game.accuse(code, variant["culprit"]))
                    self.assertTrue(game._load()[code]["solved"])

    def test_classic_case_rotation_and_case_selection(self):
        seen = set()
        for _ in CASES:
            opening = game.start("классическое")
            code = opening.split("Код дела: ")[1].split(".")[0]
            seen.add(game._load()[code]["case"])
        self.assertEqual(seen, set(CASES))
        opening = game.start("маяк")
        code = opening.split("Код дела: ")[1].split(".")[0]
        self.assertEqual(game._load()[code]["case"], "lighthouse")

    def test_procedural_crimes_are_solvable_with_many_suspects(self):
        for crime in procedural.CRIMES:
            for count in (8, 16, 24):
                for seed in range(10):
                    with self.subTest(crime=crime, count=count, seed=seed):
                        state = procedural.generate(crime=crime, seed=seed, count=count)
                        self.assertEqual(len(state["suspects"]), count)
                        self.assertAlmostEqual(sum(procedural.probabilities(state).values()), 1.0)
                        self.assertNotIn(state["culprit"], state["intro"])
                        before = procedural.probabilities(state)
                        for place in state["places"][:3]:
                            _, changed = procedural.inspect(state, place)
                            self.assertTrue(changed)
                        after = procedural.probabilities(state)
                        self.assertGreater(after[state["culprit"]], before[state["culprit"]])
                        self.assertGreaterEqual(after[state["culprit"]], 0.60)
                        wrong = next(name for name in state["suspects"] if name != state["culprit"])
                        self.assertIn("продолжается", procedural.accuse(state, wrong)[0])
                        self.assertIn("Дело раскрыто", procedural.accuse(state, state["culprit"])[0])

    def test_default_start_persists_a_new_procedural_case(self):
        opening = game.start(suspect_count=20)
        code = opening.split("Код дела: ")[1].split(".")[0]
        state = game._load()[code]
        self.assertEqual(state["mode"], "procedural")
        self.assertEqual(len(state["suspects"]), 20)
        self.assertEqual(len(state["places"]), 6)
        self.assertIn("Версии", game.theories(code))
        self.assertIn("Новая улика", game.inspect(code, state["places"][0]))
        self.assertEqual(len(game._load()[code]["found"]), 1)
        first_suspect = next(iter(state["suspects"]))
        game.question(code, first_suspect, "алиби")
        self.assertIn("Ответ уже записан", game.question(code, first_suspect, "алиби"))

    def test_null_case_name_starts_requested_ten_suspects(self):
        opening = game.start(None, 10)
        code = opening.split("Код дела: ")[1].split(".")[0]
        self.assertEqual(len(game._load()[code]["suspects"]), 10)

    def test_question_without_code_uses_only_unambiguous_case(self):
        state = procedural.generate(seed=12, count=10)
        person = next(iter(state["suspects"]))
        game._save({"FIRST": state})
        self.assertIn(person, game.question("", person, "алиби"))
        self.assertEqual(len(game._load()["FIRST"]["questions"]), 1)
        self.assertIn("недостаточно доказательств", game.accuse("", person))
        game._save({"FIRST": state, "SECOND": procedural.generate(seed=12, count=10)})
        self.assertIn("несколько дел", game.question("", person, "алиби"))
        self.assertIn("несколько дел", game.accuse("", person))

    def test_requested_crime_and_maximum_suspects(self):
        opening = game.start("убийство", suspect_count=24)
        code = opening.split("Код дела: ")[1].split(".")[0]
        state = game._load()[code]
        self.assertEqual(state["crime"], "murder")
        self.assertEqual(len(state["suspects"]), 24)
        self.assertIn("от 8 до 24", game.start("убийство", suspect_count=25))
        self.assertIn("процедурного дела", game.start("маяк", suspect_count=20))

    def test_theories_use_only_discovered_evidence(self):
        code = self._seed("museum", "vera")
        self.assertEqual(game.theories(code).count("25%"), 4)
        game.inspect(code, "пультовая")
        self.assertIn("Вера:", game.theories(code))
        self.assertNotIn("Виновный:", game.status(code))

    def test_old_case_stays_playable(self):
        code = "OLDCASE1"
        game._save({code: {"visited": ["зал"], "questions": [], "clues": ["Синий воск на витрине"], "solved": False, "attempts": 0}})
        self.assertIn("Астролябия", game.status(code))
        game.inspect(code, "пультовая")
        game.inspect(code, "мастерская")
        self.assertIn("Дело раскрыто", game.accuse(code, "Нина"))

    def test_repeat_visit_and_question_do_not_duplicate_clues(self):
        code = self._seed("museum", "nina")
        game.inspect(code, "в витрине")
        self.assertIn("уже записал", game.inspect(code, "зал"))
        game.question(code, "Нину", "про тележку")
        self.assertIn("уже записан", game.question(code, "Нина", "тележка"))
        self.assertEqual(len(game._load()[code]["clues"]), 2)


if __name__ == "__main__":
    unittest.main()
