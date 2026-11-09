"""Tests for the red-flag rules. Run from the repository root:
    python -m unittest discover tests
No Ollama needed: these tests only check the rules.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from red_flags import check_red_flags  # noqa: E402

MUST_TRIGGER = [
    # English (including the M2 emergency cases)
    ("Crushing chest pain spreading to my left arm for 20 minutes", "chest_pain"),
    ("My right arm and the right side of my face suddenly feel weak and my speech is slurred", "stroke"),
    ("Sudden flashes of light and a dark curtain coming down over part of my vision in one eye", "sudden_vision_loss"),
    ("I heard a crack when I fell, my ankle looks bent the wrong way", "severe_injury"),
    ("I can't breathe properly and I'm gasping", "breathing"),
    ("My lips and tongue are swollen after eating peanuts", "allergic_swelling"),
    ("My father passed out and is not waking up", "unconscious_seizure"),
    ("I cut my hand and the bleeding won't stop", "heavy_bleeding"),
    ("I want to kill myself", "suicide_self_harm"),
    ("I was just hit by a car and my leg looks deformed", "severe_injury"),
    ("He is having a fit and shaking", "unconscious_seizure"),
    ("My water broke and contractions are every 3 minutes", "childbirth"),
    # Added 2026-11-09 (extended test set, cases 13 and 17)
    ("I have severe shortness of breath and my lips are turning blue.", "breathing"),
    ("My baby's lips look blue", "breathing"),
    ("I have a high fever, stiff neck and a severe headache", "meningitis_signs"),
    ("Stiff neck since this morning and now a fever of 39", "meningitis_signs"),
    ("He has a rash that does not fade when I press a glass on it", "meningitis_signs"),
    # French
    ("J'ai une douleur dans la poitrine qui descend dans le bras gauche", "chest_pain"),
    ("Ma mère a le visage paralysé d'un côté et du mal à parler", "stroke"),
    ("J'ai du mal à respirer depuis une heure", "breathing"),
    ("D'un coup je ne vois plus rien de l'oeil droit", "sudden_vision_loss"),
    ("Mon fils s'est évanoui et ne réagit pas", "unconscious_seizure"),
    ("J'ai les lèvres et la langue gonflées", "allergic_swelling"),
    ("J'ai de la fièvre et la nuque raide depuis ce matin", "meningitis_signs"),
    ("Ses lèvres deviennent bleues", "breathing"),
]

MUST_NOT_TRIGGER = [
    "I have no chest pain, just a cough",
    "Pas de douleur thoracique, juste un rhume",
    "Runny nose, mild sore throat and sneezing for two days",
    "I twisted my ankle playing football yesterday, it's swollen but I can walk",
    "I can still swallow and breathe fine",
    "Heartburn after most meals for two months",
    "I need my blood pressure prescription renewed, I feel fine",
    "J'ai mal à la gorge et le nez qui coule",
    # Phrases that caused false alarms in an earlier version of the rules
    "I hurt myself playing football",
    "I keep fit and run every day",
    "J'ai accouché il y a 3 mois et j'ai mal au dos",
    "I had a car accident last year and my back still hurts",
    "I feel short of breath when climbing stairs",
    "My neck is stiff because I slept badly",
    "I have a fever and a sore throat since yesterday",
    "My fingers turn white and blue in the cold",
    "J'ai un peu de fièvre et mal à la tête",
]


class RedFlagTests(unittest.TestCase):
    def test_emergencies_are_caught(self):
        for text, expected in MUST_TRIGGER:
            with self.subTest(text=text):
                flag = check_red_flags(text)
                self.assertIsNotNone(flag, "missed emergency")
                self.assertEqual(flag["id"], expected)

    def test_no_false_alarm(self):
        for text in MUST_NOT_TRIGGER:
            with self.subTest(text=text):
                self.assertIsNone(check_red_flags(text))

    def test_m2_cases(self):
        """Every EMERGENCY case of the M2 test set is caught; no other case triggers."""
        cases = json.loads((ROOT / "experiment" / "cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["id"]):
                flagged = check_red_flags(case["symptoms"]) is not None
                if case["expected_type"] == "EMERGENCY":
                    self.assertTrue(flagged, "missed emergency")
                else:
                    self.assertFalse(flagged, "false alarm")


if __name__ == "__main__":
    unittest.main()
