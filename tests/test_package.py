"""Offline checks of the package layout against Hermes's own Agent Plugins v1 loader.

Run with the Python of a Hermes install (the loader is imported from it):

    python -m unittest discover -s tests -v

No network access and no credentials are used.
"""

import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    from hermes_cli.agent_plugins import load_agent_plugin
except ImportError:  # pragma: no cover - only when run outside a Hermes environment
    load_agent_plugin = None

# The tool arguments the skills teach. The hosted server rejects unknown arguments,
# so every JSON example in a skill must stay inside these sets.
SEARCH_ARGS = {"query", "site", "published_after", "published_before", "max_results", "snippet_max_length"}
FETCH_ARGS = {"url", "prompt", "max_chars"}


def _json_examples(text):
    for block in re.findall(r"```json\n(.*?)```", text, flags=re.S):
        yield json.loads(block)


class ManifestTests(unittest.TestCase):
    def test_plugin_name_does_not_shadow_bundled_backend(self):
        manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        # Hermes bundles a web backend whose short name is `keenable`.
        self.assertEqual(manifest["name"], "keenable-plugin")

    def test_mcp_connection_is_keyless(self):
        config = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
        server = config["mcpServers"]["keenable"]
        self.assertEqual(server["type"], "streamable-http")
        self.assertEqual(server["url"], "https://api.keenable.ai/mcp")
        self.assertEqual(server["headers"], {"X-Keenable-Title": "hermes-plugin"})
        # An unresolved ${VAR} in a remote header makes Hermes refuse the server,
        # so the packaged connection must not reference any variable.
        self.assertNotIn("${", json.dumps(config))

    def test_skill_examples_use_supported_arguments(self):
        for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")):
            for example in _json_examples(skill_md.read_text(encoding="utf-8")):
                keys = set(example)
                allowed = FETCH_ARGS if "url" in keys else SEARCH_ARGS
                self.assertLessEqual(keys, allowed, f"{skill_md}: {sorted(keys - allowed)}")


@unittest.skipIf(load_agent_plugin is None, "needs a Hermes environment")
class HermesLoaderTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="keenable-plugin-data-")
        self.package = load_agent_plugin(ROOT, Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_loads_without_diagnostics(self):
        self.assertEqual(self.package.name, "keenable-plugin")
        self.assertEqual(self.package.diagnostics, ())

    def test_translated_server(self):
        self.assertEqual(set(self.package.mcp_servers), {"keenable"})
        server = self.package.mcp_servers["keenable"]
        self.assertEqual(server["url"], "https://api.keenable.ai/mcp")
        self.assertTrue(server["strict_redirect_headers"])

    def test_skills_discovered(self):
        self.assertEqual({skill.name for skill in self.package.skills}, {"keenable-search", "keenable-research"})


if __name__ == "__main__":
    unittest.main()
