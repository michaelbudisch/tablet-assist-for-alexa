"""Regression tests for TAFA public article and recipe reader.

Pure HTML parsing is tested offline; never fetches a third-party URL.
"""
import ast
import html
from html.parser import HTMLParser
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "custom_components/tablet_assist_for_alexa/web_article.py"
BUNDLE = ROOT / "tafa_app/bundle/tablet_assist_for_alexa/web_article.py"


def parser_functions():
    tree = ast.parse(ARTICLE.read_text(encoding="utf-8"))
    selected = [
        item for item in tree.body if isinstance(item, (ast.FunctionDef, ast.ClassDef))
        and item.name in {"clean", "find_recipe", "steps_from", "ArticleParser"}
    ]
    scope = {"html": html, "HTMLParser": HTMLParser, "re": re, "json": json,
             "urlsplit": urlsplit, "MAX_VISIBLE": 10_000}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(ARTICLE), "exec"), scope)
    return scope


class WebArticleTests(unittest.TestCase):
    def test_public_recipe_is_extracted_without_made_up_ingredients(self):
        mod = parser_functions()
        content = """<!doctype html><title>Pfannkuchen</title>
            <script type="application/ld+json">
            {"@context":"https://schema.org","@type":"Recipe","name":"Pfannkuchen",
             "recipeYield":"4 Portionen","recipeIngredient":["200 g Mehl","2 Eier"],
             "recipeInstructions":[{"@type":"HowToStep","text":"Alle Zutaten verrühren."},
                                   {"@type":"HowToStep","text":"In der Pfanne ausbacken."}]}
            </script>
            <main><p>Das ist die öffentliche Einleitung auf der Rezeptseite.</p></main>"""
        parser = mod["ArticleParser"]()
        parser.feed(content)
        parsed = parser.result("https://example.org/pfannkuchen")
        self.assertEqual(parsed["recipe"]["ingredients"], ["200 g Mehl", "2 Eier"])
        self.assertEqual(parsed["recipe"]["steps"], ["Alle Zutaten verrühren.",
                                                     "In der Pfanne ausbacken."])
        self.assertEqual(parsed["recipe"]["yield"], "4 Portionen")
        self.assertIn("Pfannkuchen", parsed["voice_summary"])
        self.assertEqual(parsed["summary_source"], "excerpt")

    def test_non_recipe_content_is_not_fabricated(self):
        mod = parser_functions()
        parser = mod["ArticleParser"]()
        parser.feed("<title>Wissensartikel</title><p>Diese Seite enthält einen einfachen Absatz über die Erfindung des Buchdrucks.</p>")
        parsed = parser.result("https://example.org/artikel")
        self.assertIsNone(parsed["recipe"])
        self.assertIn("Buchdrucks", parsed["summary"])

    def test_secure_reader_contract_and_bundle(self):
        body = ARTICLE.read_text(encoding="utf-8")
        self.assertEqual(ARTICLE.read_bytes(), BUNDLE.read_bytes())
        self.assertIn("ipaddress.ip_address(row[\"host\"]).is_global", body)
        self.assertIn("allow_redirects=False", body)
        self.assertIn('\"tablet_assist_for_alexa\"', (ROOT / "custom_components/tablet_assist_for_alexa/const.py").read_text())
        self.assertIn("MAX_HTML = 650_000", body)

    def test_search_overlay_and_native_followup_contract(self):
        front = (ROOT / "custom_components/tablet_assist_for_alexa/frontend/response_overlay.js").read_text()
        self.assertIn("selected_index", front)
        self.assertIn('type:"tablet_assist_for_alexa/article_read"', front)
        self.assertIn("Zubereitung", front)
        self.assertIn("Zurück zu den Treffern", front)
        data = (ROOT / "custom_components/tablet_assist_for_alexa/local_data.py").read_text()
        self.assertIn('context_results["selected"] = index - 1', data)
        router = (ROOT / "custom_components/tablet_assist_for_alexa/conversation.py").read_text()
        self.assertIn('event["selected_index"]', router)
        self.assertIn("prefer_tafa_search", router)


if __name__ == "__main__":
    unittest.main()
