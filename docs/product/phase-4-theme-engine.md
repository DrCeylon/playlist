# Phase 4.3 — Shared theme registry and design tokens

Python provider-neutral theme engine for Resonance UI contracts.

## Package

`playlist_builder/ui/shared/theme/`

| Module | Role |
|--------|------|
| `tokens.py` | `DesignTokens` dataclass and merge helper |
| `models.py` | `Theme`, `ThemeDefinition`, `theme_to_option()` |
| `validation.py` | Required token set, color/spacing/radius checks |
| `loader.py` | JSON `.theme.json` parsing and `extends` resolution |
| `registry.py` | `ThemeRegistry` — register, get, list, load_bundled, validate |
| `manager.py` | `ThemeManager` — active theme, apply, subscribe |
| `themes/` | Bundled skins (JSON only) |

## Bundled themes

| ID | Display name | Notes |
|----|--------------|-------|
| `apple_music_light` | Apple Music Light | Default (`UserPreferences.theme_id`) |
| `apple_music_dark` | Apple Music Dark | OLED-friendly dark canvas |
| `classic_winamp_inspired` | Classic Laboratory | Extends dark theme; neon green/orange accents |

No font files, no provider assets, no Apple/Winamp bitmap skins.

## Theme file format

Files use camelCase top-level keys and dot-notation token paths aligned with
[design-system.md](design-system.md):

```json
{
  "id": "apple_music_dark",
  "displayName": "Apple Music Dark",
  "version": "1.0.0",
  "extends": null,
  "tokens": {
    "colors": { "color.background.primary": "#1C1C1E" },
    "typography": { "font.body": "15,regular" },
    "spacing": { "space.md": 16 },
    "radius": { "radius.lg": 14 },
    "shadows": { "shadow.card": "0 2px 8px #00000014" }
  },
  "metadata": { "author": "Resonance" }
}
```

Child themes may declare `"extends": "parent_id"` and override only diff tokens.
The loader merges parent tokens first, then child overrides.

## Validation

`ThemeRegistry.validate(theme)` checks:

- `id`, `display_name`, and `version` are non-empty
- All mandatory keys from `design-system.md` are present after merge
- Colors match `#RRGGBB` or `#RRGGBBAA`
- Spacing and radius values are integers `>= 0`
- Unknown token keys produce warnings (forward compatible)

Invalid themes cannot be registered.

## Runtime API

```python
registry = ThemeRegistry.load_bundled()
manager = ThemeManager(registry)
manager.apply("apple_music_dark")

for theme in registry.list():
  option = theme_to_option(theme)  # ThemeOption for UI selectors
```

`ThemeManager.subscribe(callback)` is called after each successful `apply()`.
`ThemeManager.unsubscribe(callback)` removes a previously registered listener.

## Errors

| Situation | Exception |
|-----------|-----------|
| Unknown `theme_id` | `ThemeNotFoundError` |
| Invalid theme structure on register | `ThemeValidationError` |
| Broken JSON / circular `extends` | `ThemeLoadError` |

## Tests

`tests/test_ui_shared_theme.py` :

- All bundled themes load and validate
- Inheritance merge (`classic_winamp_inspired` → `apple_music_dark`)
- `ThemeManager` subscriber notifications
- `ThemeOption` mapping
- No hardcoded colors in theme engine Python modules
- No provider-specific imports in `ui/shared/theme/`

## Related

- [theme-engine.md](theme-engine.md)
- [design-system.md](design-system.md)
- [phase-4-ui-architecture.md](../architecture/phase-4-ui-architecture.md)

## Next (not in 4.3)

- **4.4** — SwiftUI shell reads the same JSON from bundle
- **4.7** — User themes from Application Support
