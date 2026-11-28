"""CPU-only checks for stable, genuinely distinct synthetic voice references."""
import hashlib
import unittest
from unittest.mock import patch

from reference_voice import REFERENCE_TEXT
from voice_variants import CHOICES, inventory, reference_id, variant_path, variant_style


class VariantTests(unittest.TestCase):
    def test_nine_profiles_are_distinct(self):
        base = "My original default German voice"
        self.assertEqual(len(CHOICES), 9)
        self.assertEqual(variant_style("1", base), base)
        self.assertEqual(len({variant_style(key, base) for key in CHOICES}), 9)
        self.assertEqual(len({reference_id(key, base) for key in CHOICES}), 9)

    def test_default_reference_hash_is_unchanged(self):
        base = "Original original"
        expected = hashlib.sha256(("v1\n" + base + "\n1\n" + REFERENCE_TEXT).encode()).hexdigest()[:24]
        self.assertEqual(reference_id("1", base), expected)
        self.assertEqual(variant_path("1", base).suffix, ".wav")

    def test_inventory_only_reports_prepared_fixed_voices(self):
        with patch("voice_variants.valid_reference", return_value=True):
            self.assertTrue(all(x["ready"] for x in inventory("base", "fixed")))
            self.assertTrue(all(not x["ready"] for x in inventory("base", "fast")))

    def test_unknown_variant_rejected(self):
        with self.assertRaises(ValueError):
            variant_style("10", "base")


if __name__ == "__main__":
    unittest.main()
