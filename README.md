# Resonance

**Resonance** is an open, local-first platform for composing, managing, and synchronizing music playlists across multiple streaming services — starting with Apple Music, with experimental YouTube Music support.

The project ships as:

| Surface | Path | Who it's for |
|---------|------|--------------|
| **Resonance macOS app** | [`apps/resonance/`](apps/resonance/) | End users — SwiftUI shell over the Python engine |
| **Python engine** | [`playlist_builder/`](playlist_builder/) | Contributors — generation, import, sync, providers |
| **CLI tools** | Root scripts (`generate_playlist.py`, …) | Power users & automation |

📖 **User documentation (French):** [GitHub Wiki](https://github.com/DrCeylon/playlist/wiki)  
🛠 **Contributor docs:** [CONTRIBUTING.md](CONTRIBUTING.md) · [docs/](docs/README.md)

---

## Why Resonance exists

Most playlist tools lock you into one service or one workflow. Resonance separates three concerns:

1. **Composition** — turn seeds, keywords, and constraints into a playlist (scoring engine).
2. **Local library** — your playlists live on your machine first (single source of truth).
3. **Provider sync** — push, pull, and resolve conflicts with music services through a provider-neutral platform.

No Resonance account is required. No audio is stored in the cloud. Provider credentials stay on your device.

→ Full vision: [docs/PRODUCT_VISION.md](docs/PRODUCT_VISION.md)

---

## Quick start (contributors)

**Requirements:** Python 3.12+

```bash
git clone https://github.com/DrCeylon/playlist.git
cd playlist
./scripts/setup_dev.sh
source .venv/bin/activate
python -m pytest -q
```

**macOS (app + Apple Music import):**

```bash
make check-all    # pytest + Swift build
cd apps/resonance && swift run ResonanceMac
```

| Doc | Purpose |
|-----|---------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What's next |
| [AGENTS.md](AGENTS.md) | AI / automation agents |

---

## Quick start (users — CLI)

Legacy free workflow using Apple Music on macOS:

```bash
pip install -e ".[dev]"
python generate_playlist.py --name "My Playlist" --seed "Artist:Track" --output playlists/demo.json
python check_catalog.py --country us
python create_playlist.py   # macOS + Music.app
```

See the [wiki Guide de démarrage](wiki/Guide-de-demarrage.md) for details.

---

## Project status

| Area | State |
|------|-------|
| Playlist generation & scoring | ✅ Production |
| macOS app (generation, import, history) | ✅ Production |
| Local playlist repository | ✅ Production |
| Provider sync (plan / apply / conflicts) | ✅ Production |
| Apple Music gateway | ✅ Primary provider |
| YouTube Music | 🧪 Experimental read/import |
| Spotify / others | 📋 Planned |

Phase tracker: [wiki/Etat-des-Phases.md](wiki/Etat-des-Phases.md) · Tech debt: [docs/TECHNICAL_DEBT.md](docs/TECHNICAL_DEBT.md)

**Tests:** 490+ Python (`pytest -q`) · Swift on macOS CI

---

## Repository layout

```
apps/resonance/       SwiftUI macOS app (ResonanceCore, ResonanceDesign, ResonanceMac)
playlist_builder/     Python engine
  canonical/          Provider-neutral domain types
  app/                Use cases, sync, repository, bridge runtime
  integration/        Provider gateways (apple_music, youtube_music, …)
  ui/bridge/          JSON-RPC protocol
tests/                Python test suite
docs/                 ADRs, architecture, product docs
wiki/                 French user documentation (published to GitHub Wiki)
scripts/              Developer setup and checks
```

---

## License

[MIT](LICENSE) — see [GOVERNANCE.md](docs/GOVERNANCE.md) for project roles.

## Community

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security policy](SECURITY.md)
- [Support](SUPPORT.md)
- [Issues](https://github.com/DrCeylon/playlist/issues)
