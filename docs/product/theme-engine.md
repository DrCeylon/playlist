# Theme engine specification

Winamp-inspired **skin architecture**, modern execution. Themes are data — not
hardcoded Swift or Python branches in components.

---

## Architecture

```text
Theme (data file)
    ↓ loaded by
ThemeRegistry
    ↓ selected by
ThemeManager
    ↓ exposes
DesignTokens (resolved runtime values)
    ↓ consumed by
Components (SwiftUI) / ViewModels (status colors only via tokens)
```

---

## Core types (Python reference — Phase 4.3)

```python
@dataclass(frozen=True, slots=True)
class DesignTokens:
    colors: dict[str, str]      # token path → hex or rgba
    typography: dict[str, str]  # token → "size,weight"
    spacing: dict[str, int]
    radius: dict[str, int]
    shadows: dict[str, str]

@dataclass(frozen=True, slots=True)
class Theme:
    id: str
    display_name: str
    version: str
    tokens: DesignTokens
    metadata: dict[str, str] = field(default_factory=dict)

class ThemeRegistry:
    def register(self, theme: Theme) -> None: ...
    def get(self, theme_id: str) -> Theme: ...
    def list(self) -> tuple[Theme, ...]: ...

class ThemeManager:
    def __init__(self, registry: ThemeRegistry) -> None: ...
    @property
    def active(self) -> Theme: ...
    def apply(self, theme_id: str) -> None: ...
    def subscribe(self, callback: Callable[[Theme], None]) -> None: ...
```

Swift `ThemeManager` mirrors this API; tokens loaded from same JSON files in bundle.

---

## Theme file format (`.theme.json`)

```json
{
  "id": "apple_music_dark",
  "displayName": "Apple Music Dark",
  "version": "1.0.0",
  "extends": null,
  "tokens": {
    "colors": {
      "background.primary": "#1C1C1E",
      "accent.primary": "#FA2D48"
    },
    "typography": {
      "body": "15,regular"
    },
    "spacing": { "md": 16 },
    "radius": { "lg": 14 },
    "shadows": {}
  },
  "metadata": {
    "author": "Resonance",
    "inspiration": "Apple Music"
  }
}
```

### Inheritance (`extends`)

Optional. Child theme overrides only diff tokens. Resolution :

```text
resolved = merge(parent.tokens, child.tokens)
```

Enables `ClassicWinampInspiredTheme` to override accents while inheriting spacing.

---

## Bundled themes (v1)

| ID | Name | Notes |
|----|------|-------|
| `apple_music_light` | Apple Music Light | **Default** |
| `apple_music_dark` | Apple Music Dark | OLED-friendly |
| `classic_winamp_inspired` | Classic Laboratory | Neon accents on dark gray — homage not copy |

### Classic Winamp inspired (tokens preview)

| Token | Value | Note |
|-------|-------|------|
| `background.primary` | `#232323` | Dark gray |
| `accent.primary` | `#00FF99` | Electric green |
| `accent.secondary` | `#FF6600` | Orange peak |
| `font.mono` | prominent in Lab view | |

No Winamp assets, bitmap skins, or copyrighted graphics.

---

## Mandatory token set

Themes **must** define all keys in `design-system.md` or validation fails.

`ThemeRegistry.validate(theme)` checks :

- All required keys present (after `extends` merge)
- Colors match `#RRGGBB` or `#RRGGBBAA`
- Spacing/radius non-negative integers
- Unknown keys → warning (forward compatible)

---

## Loading strategy

| Source | Phase |
|--------|-------|
| Bundled `themes/*.theme.json` | 4.3 |
| User `~/Library/Application Support/Resonance/Themes/` | 4.7 |
| Remote packages | not planned |

---

## Migration strategy

1. **4.3** — Python ThemeRegistry + schema tests
2. **4.4** — Swift loader reads same JSON from bundle
3. **4.7** — User themes; version field for breaking changes
4. If token added : bump schema minor, default in base theme, validate all skins

---

## Limits

| Limit | Value | Reason |
|-------|-------|--------|
| Max custom themes | 50 user | Performance |
| Max file size | 256 KB | Security |
| No executable content | JSON only | Safety |
| No font files v1 | System fonts only | Licensing |

---

## Component contract

```swift
// Correct
.foregroundStyle(tokens.colors["text.primary"])

// Forbidden in components
.foregroundStyle(Color(red: 0.98, green: 0.18, blue: 0.28))
```

ViewModels expose **semantic** styles : `statusStyle: .success`, resolved by view
using tokens.

---

## Testing

```python
def test_all_bundled_themes_validate():
    registry = ThemeRegistry.load_bundled()
    for theme in registry.list():
        registry.validate(theme)  # no raise

def test_theme_manager_switch_notifies():
    ...
```

Swift : snapshot each theme on reference screen (Home, Import).

## Related

- [design-system.md](design-system.md)
- [ADR-011](../architecture/ADR-011-cross-platform-product-ui.md)
