# Keenable for Hermes Agent

Web search and page fetching through [Keenable's hosted MCP server](https://docs.keenable.ai/mcp-server),
plus two skills that teach the agent to search well and to research a question
across many sources. Works out of the box with **no API key and no account**.
An optional key only lifts the keyless rate limits.

The package is a portable Agent Plugins v1 package: `plugin.json`, one remote MCP
connection in `mcp.json`, and Markdown skills. It has no Python code, no runtime
dependencies, and no local processes. Requires **Hermes Agent 0.21.5 or later**
with its MCP support installed.

## How this relates to Hermes's built-in Keenable backend

Hermes already ships Keenable as a built-in web backend: it is one of the keyless
providers behind Hermes's own `web_search` and `web_extract` tools. This plugin
does not replace or reconfigure that backend. It registers no web search
provider and leaves `web_search` / `web_extract` provider selection unchanged.

What it adds:

- Keenable's MCP tools as direct tools, with the controls the built-in backend
  does not expose: single-site search (`site`), publish-date bounds
  (`published_after`, `published_before`), result count and snippet length, and
  page fetches that return only what a `prompt` asks for.
- Two skills: `keenable-search` (arguments, when to fetch, limits,
  troubleshooting) and `keenable-research` (split a question, search in
  parallel, fetch only the gaps, cite every claim).

## Install

From the Hermes plugin catalog (once the entry is listed):

```bash
hermes plugins install keenable-plugin
hermes plugins enable keenable-plugin
```

Directly from this repository:

```bash
hermes plugins install keenableai/keenable-hermes-plugin --no-enable
hermes plugins enable keenable-plugin
```

Start a new session so Hermes loads the enabled package. Then try:

> Use the Keenable search tool to find this week's release notes for Hermes Agent and cite them.

Hermes namespaces plugin skills to avoid collisions, and the prefix depends on
your Hermes version. Ask the agent to run `skills_list` and load
`keenable-research` or `keenable-search` with `skill_view`.

To remove it: `hermes plugins disable keenable-plugin` or
`hermes plugins remove keenable-plugin`.

## Tools and skills

| Hermes tool | Use |
| --- | --- |
| `mcp__keenable__search_web_pages` | Search the web. Returns title, URL and a text snippet per result. |
| `mcp__keenable__fetch_page_content` | Read a page as clean markdown, or only the part a `prompt` asks for. |

| Skill | Use |
| --- | --- |
| [keenable-search](skills/keenable-search/SKILL.md) | Tool arguments, when to fetch, keyless limits, troubleshooting. |
| [keenable-research](skills/keenable-research/SKILL.md) | Multi-source research with parallel searches, recency filters and citations. |

The server also advertises empty resource and prompt lists, so Hermes adds its
generic `list_resources`, `read_resource`, `list_prompts` and `get_prompt`
helpers for it. They return nothing useful and can be ignored; the API-key
entry below turns them off.

## Optional: API key

Without a key, requests use Keenable's shared public pool: 1,000 requests per
hour and at most 10 requests per second per IP address. A Keenable API key
removes the hourly cap (keys come with a free monthly allowance; create one in
the [console](https://app.keenable.ai/console)).

1. Store the key in the active Hermes profile:

   ```bash
   hermes config set KEENABLE_API_KEY <your key>
   ```

2. Merge [this entry](examples/api-key.yaml) into the same profile's `config.yaml`
   (keep your other `mcp_servers`):

   ```yaml
   mcp_servers:
     keenable:
       url: https://api.keenable.ai/mcp
       strict_redirect_headers: true
       headers:
         X-API-Key: "${KEENABLE_API_KEY}"
         X-Keenable-Title: hermes-plugin
       tools:
         resources: false
         prompts: false
   ```

3. Start a new session.

Good to know:

- A `config.yaml` server named `keenable` replaces the plugin's packaged keyless
  connection as a whole. Delete the entry to go back to keyless.
- Set the key first. Hermes refuses to connect a server whose header still
  contains an unset `${KEENABLE_API_KEY}`, and the Keenable tools disappear until
  the key is set or the entry is removed. This is also why the packaged
  connection carries no key placeholder: it has to work for everyone without one.
- Hermes's built-in Keenable web backend reads the same `KEENABLE_API_KEY`. If you
  have not configured another web backend or set another provider's key, Hermes's
  own `web_search` / `web_extract` then use Keenable with your key instead of the
  keyless rotation.

Never paste a key into chat, this repository, or `mcp.json`.

## Data flow

- Requests go to `https://api.keenable.ai/mcp` over HTTPS. Keenable receives the
  search queries, the URLs to fetch, and any fetch `prompt` the agent sends. With a
  `prompt`, Keenable reads the page server-side with a language model and returns
  only the answer.
- Every request carries `X-Keenable-Title: hermes-plugin`, an application label
  so Keenable can tell this integration's traffic apart. It carries no user or
  device identifier.
- `X-API-Key` is sent only if you configure it as described above.
- The package runs no local processes, background workers or self-updater, reads
  no credential files, and has no telemetry of its own. Hermes owns the MCP
  connection, configuration and approvals.
- Web content is untrusted. Both skills tell the agent not to follow
  instructions found in pages.

Keenable's [privacy policy](https://keenable.ai/privacy) and
[terms](https://keenable.ai/terms) apply to the hosted service.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| No `mcp__keenable__*` tools | Run `hermes plugins enable keenable-plugin` and start a new session. If you added the API-key entry, check that `KEENABLE_API_KEY` is set in that profile. |
| "Rate limit exceeded" | Wait and reduce the number of calls, or add an API key. |
| HTTP 401 "Invalid API key" | The configured key is wrong or revoked. Fix it, or delete the API-key entry to go back to keyless. |
| "Unknown parameter(s)" | The server rejects arguments it does not know. Use the arguments listed in the `keenable-search` skill. |
| "conflicts with native config; skipping" in the log | Expected when you added the API-key entry: your `config.yaml` entry is used instead of the packaged one. |

## Development

The installed plugin is data and Markdown. The tests import Hermes's own Agent
Plugins v1 loader, so run them with the Python of a Hermes install:

```bash
python -m unittest discover -s tests -v
hermes plugins validate . --install-deps
```

CI runs both against pinned Hermes releases (0.21.5 and 0.22.5) on every push.

## License

[MIT](LICENSE), copyright Keenable.
