# spec-kit ↔ OpenProject: Preset und/oder Community-Extension

Übergabedokument aus der Session „Migration Sales Advisor" (Stand 2026-10-05). Dieses Thema gehört nicht zum MAS/R+V-Projekt.

## Ursprüngliche Frage (Daniel)

> Wie aufwendig wäre es, eine Community-Extension und/oder Presets für die Anbindung von spec-kit an OpenProject zu entwickeln und dabei den Open-Source-Community-MCP-Server von OpenProject zu benutzen?

## Ergebnis der Recherche

### spec-kit (github/spec-kit)

- **Extensions**: neue Commands `speckit.{ext-id}.{command}`, Hooks auf Lifecycle-Events (u. a. `taskstoissues`), mehrschichtige Konfiguration. Manifest `extension.yml` (`schema_version: "1.0"`, `id` nach `^[a-z0-9-]+$`, semver, `requires.speckit_version`, `provides` für commands/templates/scripts/hooks/events). Command-Dateien sind Markdown mit YAML-Frontmatter (`$ARGUMENTS`, `{SCRIPT}`, `__SPECKIT_COMMAND_<NAME>__`).
  - Lokaler Test: `specify extension add --dev <pfad>`
  - Veröffentlichung: GitHub-Release plus Catalog-Submission-Issue
- **Presets**: `preset.yml` (`schema_version`, `preset.id`, `preset.version`, `requires.speckit_version`, `provides.templates`), Verzeichnisse `templates/`, `commands/`, `scripts/`. Strategien: replace / prepend / append / wrap (`{CORE_TEMPLATE}`). Priorität: lokale Overrides > Presets > Extensions > Core.
  - Installation: `specify preset add`
  - Veröffentlichung: Preset-Submission-Issue (README, OSS-Lizenz, Tag v1.0.0)
  - Bundles: `bundle.yml`, `specify bundle build`
- **Kernaussage** (Issue #2223): Extensions können Core-Commands nicht überschreiben. Die Tracker-Auswahl (`speckit.taskstoissues`) gehört deshalb in ein **Preset**.

### Vorbilder

- `luno/spec-kit-preset-jira`: Preset, überschreibt `speckit.taskstoissues`, nutzt den Atlassian-MCP. Konfig-Reihenfolge: Argument → `.specify/presets/jira/jira-config.yml` → Env `SPECKIT_JIRA_PROJECT_KEY` → Rückfrage.
- `mbachorik/spec-kit-jira`: Extension mit `specstoissues`, `discover-fields`, `sync-status`, `jira-mapping.json`.

### OpenProject-MCP-Optionen

- Der offizielle OpenProject-MCP-Server (17.2, Schreibzugriff ab 17.8) ist ein **Enterprise-Add-on**.
- Community-Edition-Option: **`jtauschl/openproject-ce-mcp`** (MIT, Python, stdio, über 100 Tools, Preview-then-confirm bei Schreibaktionen, Projekt-Allowlists `OPENPROJECT_READ_PROJECTS` / `OPENPROJECT_WRITE_PROJECTS`, Installation `pipx install openproject-ce-mcp`, API-Token).
- Weitere Community-Server (kar-thik, brunofin, gerke-homelab, revytechinc, widjis, firsthalfhero) haben abweichende Tool-Namen.

### Aufwandsschätzung (eigene Schätzung; Testinstanz und spec-kit-Kenntnis vorausgesetzt)

| Variante | Aufwand (PT) |
|---|---|
| Preset (`taskstoissues` → OpenProject) | 2–3 |
| Extension (`discover-fields`, `sync-status`, Mapping) | 5–8 |
| Beides inkl. Doku, Tests, Catalog-Submission | 7–12 |
| Optional je Baustein: Versionen/Meilensteine, Zeiterfassung, bidirektionaler Sync | +1–3 |

### Risiken

- Preview-and-confirm-Reibung bei vielen Tasks
- Pro Projekt unterschiedliche Types, Status, Workflows, Pflicht-Custom-Fields in OpenProject
- Idempotenz über eine Mapping-Datei sicherstellen
- Nicht-deterministische Ausführung der Prompts durch das LLM
- spec-kit-Versionen ändern sich schnell
- Unterschiedliche Tool-Namen je MCP-Server

### Empfehlung

Zuerst das Preset, danach die Extension.

## Einschränkung der Recherche

WebFetch wurde für die GitHub-Verzeichnisseiten `extensions` und `presets` per robots.txt blockiert. Genutzt wurden stattdessen der Extension-Development-Guide, die docs/customization-Seiten und DeepWiki. Vor dem Bau die Schemas gegen die aktuelle spec-kit-Version prüfen.

## Vorgeschlagener nächster Schritt

Preset `spec-kit-preset-openproject` aufsetzen, das `speckit.taskstoissues` überschreibt:

```
spec-kit-preset-openproject/
├── preset.yml
├── commands/speckit.taskstoissues.md
├── openproject-config.template.yml
└── README.md
```

Danach die Extension mit `discover-fields`, `sync-status` und `openproject-mapping.json`.

Offene Entscheidungen für die neue Session: Ziel-MCP-Server (Empfehlung `jtauschl/openproject-ce-mcp`), Testinstanz von OpenProject, Lizenz, Repo-Name und -Ort.
