import json
import unittest
from text_processing import dictionary, prepare_text, split_sentences


class TextProcessingTests(unittest.TestCase):
    def test_simple_text_unchanged(self):
        self.assertEqual(prepare_text("Guten Morgen, wie geht es?"), "Guten Morgen, wie geht es?")

    def test_markdown_and_whitespace(self):
        self.assertEqual(prepare_text("**Hallo**  [hier](https://example.org)\n weiter"),
                         "Hallo hier weiter")

    def test_pronunciation_dictionary(self):
        words = dictionary(json.dumps({"kWh": "Kilowattstunden", "HA": "Home Assistant"}))
        self.assertEqual(prepare_text("5 kWh, HA!", words), "5 Kilowattstunden, Home Assistant!")
        self.assertEqual(prepare_text("HAUSHALT", words), "HAUSHALT")

    def test_invalid_dictionary(self):
        for value in ('[]', '{"x": 1}', '{"x": ""}', '{not-json}', "z" * 4097):
            with self.subTest(value=value[:20]), self.assertRaises(ValueError):
                dictionary(value)

    def test_sentence_split(self):
        chunks = split_sentences("Ein erster Satz. " + "mehr " * 80, max_chars=80)
        self.assertTrue(all(0 < len(x) <= 80 for x in chunks))
        self.assertTrue(len(chunks) > 3)
        self.assertEqual(" ".join(chunks), ("Ein erster Satz. " + "mehr " * 80).strip())

    def test_huge_string_rejected(self):
        with self.assertRaises(ValueError):
            prepare_text("x" * 1000)


if __name__ == "__main__":
    unittest.main()
