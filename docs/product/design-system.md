# Resonance — Design system (v0.1)

Spec for Phase 4 implementation. **No color may be hardcoded in components** —
all values come from `DesignTokens` / active theme.

---

## Design principles

1. **Clarity over density** — breathable layouts (Things-inspired).
2. **Motion with purpose** — 200–350 ms, ease-out, respect Reduce Motion.
3. **Hierarchy through typography** — not color alone.
4. **Semantic color** — success/warning/error tokens, not raw greens/reds in views.
5. **Platform respect** — SwiftUI native controls styled via tokens, not fake iOS on Mac.

---

## Color tokens

| Token | Role | AppleMusicLight | AppleMusicDark |
|-------|------|-----------------|----------------|
| `color.background.primary` | Main canvas | `#F5F5F7` | `#1C1C1E` |
| `color.background.secondary` | Cards, sidebar | `#FFFFFF` | `#2C2C2E` |
| `color.background.elevated` | Sheets, popovers | `#FFFFFF` | `#3A3A3C` |
| `color.text.primary` | Body | `#1D1D1F` | `#F5F5F7` |
| `color.text.secondary` | Subtitles | `#6E6E73` | `#AEAEB2` |
| `color.text.tertiary` | Hints | `#AEAEB2` | `#636366` |
| `color.accent.primary` | CTA, links | `#FA2D48` | `#FA2D48` |
| `color.accent.secondary` | Secondary actions | `#5856D6` | `#5E5CE6` |
| `color.border.subtle` | Dividers | `#00000014` | `#FFFFFF1A` |
| `color.status.success` | Added, OK | `#34C759` | `#30D158` |
| `color.status.warning` | Partial, wait | `#FF9F0A` | `#FFD60A` |
| `color.status.error` | Failed | `#FF3B30` | `#FF453A` |
| `color.status.info` | Info, cache hit | `#007AFF` | `#0A84FF` |
| `color.lab.accent` | Laboratory | `#AF52DE` | `#BF5AF2` |

Accent inspired by Apple Music pink — **not** Apple copyrighted assets.

---

## Typography

| Token | macOS | iOS | Weight |
|-------|-------|-----|--------|
| `font.largeTitle` | 28 pt | 34 pt | Semibold |
| `font.title` | 22 pt | 28 pt | Semibold |
| `font.headline` | 17 pt | 17 pt | Semibold |
| `font.body` | 15 pt | 17 pt | Regular |
| `font.callout` | 13 pt | 16 pt | Regular |
| `font.caption` | 11 pt | 12 pt | Regular |
| `font.mono` | SF Mono 12 pt | SF Mono 12 pt | Regular |

**Font family :** system (`SF Pro` / `.system`). No custom web fonts in v1.

---

## Spacing scale (pt)

| Token | Value |
|-------|-------|
| `space.xs` | 4 |
| `space.sm` | 8 |
| `space.md` | 16 |
| `space.lg` | 24 |
| `space.xl` | 32 |
| `space.xxl` | 48 |

Screen margins : `space.lg` macOS, `space.md` iPhone.

---

## Radius

| Token | Value | Use |
|-------|-------|-----|
| `radius.sm` | 6 | Chips, badges |
| `radius.md` | 10 | Buttons, inputs |
| `radius.lg` | 14 | Cards |
| `radius.xl` | 20 | Sheets |

---

## Shadows (macOS)

| Token | Value |
|-------|-------|
| `shadow.card` | `0 2px 8px #00000014` |
| `shadow.elevated` | `0 8px 24px #0000001F` |

iOS : prefer native `.shadow` materials over custom shadows.

---

## Components

### Card (`ResonanceCard`)

- Background `color.background.secondary`
- Radius `radius.lg`
- Padding `space.md`
- Optional `shadow.card` macOS only

### Button

| Variant | Fill | Text |
|---------|------|------|
| Primary | `color.accent.primary` | white |
| Secondary | transparent | `color.accent.primary` border |
| Destructive | — | **not used** (no delete) |
| Ghost | transparent | `color.text.secondary` |

Min height 36 pt macOS, 44 pt iOS.

### Text field

- Background `color.background.elevated`
- Border `color.border.subtle`
- Focus ring `color.accent.primary` 2 pt

### List row (`TrackRow`)

- Leading : index or status icon
- Title `font.body` + artist `font.caption` `color.text.secondary`
- Trailing : confidence bar + badge

### Badge

| Variant | Background | Use |
|---------|------------|-----|
| `cache_hit` | `color.status.info` 15% | Identity cache |
| `acquisition` | `color.status.warning` 15% | Catalogue |
| `added` | `color.status.success` 15% | Import OK |
| `not_found` | `color.status.error` 15% | Miss |

Always pair with text label for a11y.

### Progress

- Bar : `color.accent.primary` on `color.background.elevated`
- Indeterminate : subtle pulse (respect Reduce Motion)

### Loading states

- **Skeleton** : shimmer `color.background.elevated` → `color.border.subtle`
- **Spinner** : `ProgressView` tint `color.accent.primary`

### Error banner

- Background `color.status.error` 12%
- Icon + message + optional action
- Never color-only

---

## Micro-interactions

| Action | Animation |
|--------|-----------|
| Button press | scale 0.98, 100 ms |
| Card appear | opacity + translateY 8 pt, 250 ms stagger |
| Section expand | height spring 0.35 s |
| Import progress tick | crossfade row status 150 ms |
| Theme switch | crossfade background 300 ms |

---

## Accessibility

- Minimum contrast **4.5:1** body text (WCAG AA)
- Large text **3:1**
- Focus visible on all interactive elements
- Status : icon + text + optional color
- Dynamic Type : layout reflow, no clipped text

---

## Internationalisation

- Strings via keys `home.title`, `import.manual.hint`, etc.
- Layout must tolerate FR strings ~30% longer than EN
- RTL : deferred (not v1)

## Related

- [theme-engine.md](theme-engine.md)
- [phase-4-wireframes.md](phase-4-wireframes.md)
