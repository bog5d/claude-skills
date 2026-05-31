# CLI-Anything Harness Catalog

Last refreshed: 2026-05-26. Source: `cli-hub list` output.

## Available Harnesses (80 total: 64 harness, 16 public)

### 3D
- **blender** — 3D modeling, animation, and rendering via blender --background
- **freecad** — Parametric 3D CAD modeling via FreeCAD CLI (258 commands)

### AI
- **comfyui** — AI image generation workflow management via ComfyUI REST API
- **dify-workflow** — Dify workflow DSL editor CLI
- **generate-veo-video** — Google Veo 3.1 video generation via Vertex AI
- **jimeng** — ByteDance AI image and video generation CLI
- **minimax** — Chat and TTS via MiniMax AI API
- **minimax-cli** — MiniMax AI platform CLI for tokens, models, and more
- **notebooklm** — Experimental NotebookLM harness scaffold
- **novita** — AI models via Novita's OpenAI-compatible API
- **ollama** — Local LLM inference and model management via Ollama REST

### Audio
- **audacity** — Audio editing and processing via sox

### Automation
- **macrocli** — Layered macro runtime converting GUI workflows to CLI
- **n8n** — Workflow automation via n8n REST API (55+ commands)

### Communication
- **feishu** — Official Lark (Feishu) CLI for managing apps, bots
- **ve-twini** — Unified Twitter/X CLI bridging bird (GraphQL) and official API
- **wecom** — Official WeCom open-platform CLI
- **zoom** — Meeting management via Zoom REST API (OAuth2)

### Data Science
- **py4csr** — GxP-compliant agent harness for CDISC Clinical Study Reports

### Database
- **chromadb** — Vector database operations

### Debugging
- **lldb** — Stateful native debugging via LLDB with JSON CLI
- **unrealinsights** — Windows-first Unreal trace capture

### Design
- **inkstitch** — Machine-embroidery digitization
- **sketch** — Generate Sketch design files from JSON

### DevOps
- **1password-cli** — Official 1Password CLI
- **deployhq** — Deploy code, manage projects/servers
- **eth2-quickstart** — Hardened Ethereum node deployment
- **iterm2** — Control running iTerm2 instance
- **nslogger** — Capture and filter NSLogger iOS logs
- **pm2** — Node.js process management
- **sentry** — Official Sentry CLI for releases, debug files

### Diagrams
- **drawio** — Diagram creation and export via draw.io CLI
- **mermaid** — Mermaid Live Editor state files and renderer URLs

### Finance
- **firefly-iii** — Personal finance via Firefly III REST API

### Game / GameDev
- (multiple game-related harnesses available — check `cli-hub list`)

### Graphics
- **obsidian-cli** — Official Obsidian CLI for vault automation

### Mobile
- **android-cli** — Official Android terminal interface for SDK setup

### Music
- **musescore** — Music notation, transpose, export PDF/audio/MIDI
- **suno** — Music generation with Suno AI from lyrics and style tags

### Network
- **adguardhome** — DNS ad-blocking management
- **rms** — Teltonika RMS device management

### Office (most relevant for Hermes)
- **calibre** — E-book library management
- **libreoffice** — ODF documents, export to PDF/DOCX, calc/writer/impress
- **mubu** — Knowledge management and outlining
- **zotero** — CLI & MCP server for Zotero 7/8 (52 MCP tools + 70+ CLI commands)

### OSINT
- **intelwatch** — Competitive intelligence, M&A due diligence

### Project Management
- **seaclip** — Kanban board, 6-agent AI pipeline

### Science
- **stata** — Run Stata do-files and batch jobs
- **unimol_tools** — Molecular property prediction

### Scientific
- **qgis** — Geospatial project authoring and layout export

### Search
- **exa** — AI-powered web search via Exa API
- **hacker-feeds-cli** — GitHub Trending, Hacker News, Reddit, Product Hunt

### Streaming
- **obs-studio** — Streaming/recording scene management

### Testing
- **wiremock** — HTTP mock server management

### Video
- **kdenlive** — Video editing and rendering via melt
- **openscreen** — Screen recording editor
- **quietshrink** — Compress macOS screen recordings on Apple Silicon
- **shotcut** — Video editing via melt/ffmpeg
- **videocaptioner** — AI-powered video captioning

### Web
- **browser** — Browser automation via DOMShell MCP server
- **clibrowser** — Zero-dependency CLI browser for AI agents
- **contentful** — Official Contentful CLI
- **mailchimp** — Mailchimp Marketing API v3.0
- **safari** — Native macOS Safari automation via safari-mcp
- **sanity** — Official Sanity CLI
- **shopify** — Official Shopify CLI

## Priority Harnesses for Hermes (macOS)

These are the most immediately useful for existing Hermes workflows:

1. **libreoffice** — Document generation pipeline (soft-copyright, reports, manuals)
2. **gimp** — Image preprocessing before OCR
3. **blender** — Batch 3D rendering
4. **safari** — Browser automation without Browserbase
5. **obsidian-cli** — Vault automation (complements Hermes' obsidian skill)
6. **zotero** — Reference management with MCP tools
7. **calibre** — E-book/document format conversion
