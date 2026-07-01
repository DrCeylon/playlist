# Vision et objectif

*Pourquoi cette application existe — la boussole du projet.*

---

## En une phrase

**Générer des playlists Apple Music à partir de mots-clés ou de morceaux de référence** — simplement, proprement, pour tout le monde.

---

## L'objectif

Tu donnes une **intention musicale**. L'application construit la playlist.

Deux façons d'exprimer cette intention :

| Mode | Tu fournis… | L'app… |
|------|-------------|--------|
| **Manuel** | Un fichier JSON avec sections et morceaux choisis | Crée la playlist dans Apple Music |
| **Assisté** *(Phase 2)* | Des mots-clés, des morceaux de référence, des contraintes | Propose et assemble une playlist, puis la crée |
| **App Resonance** *(Phase 4)* | Interface macOS SwiftUI | Génération + import Apple Music |

Les modes coexistent. C'est **composer à la main**, **générer en CLI**, ou **utiliser l'app** selon ton envie.

### Exemples concrets

**Mode manuel** — tu sais exactement ce que tu veux :
```
« 7 sections, montée progressive, 96 morceaux, pool party. »
→ Fichier JSON → create_playlist.py
```

**Mode assisté** — tu as une direction, pas une tracklist :
```
« Morceaux de référence : Kygo – Firestone, Avicii – Levels »
« Mots-clés : tropical, dance, rising energy »
« Durée : 4 h, pas de shuffle »
→ Génération → prévisualisation → Apple Music
```

---

## Pour qui ?

**Tout le monde.**

Pas un outil fermé pour un usage privé. Un projet perso ouvert, que n'importe qui peut cloner, adapter, et faire sien.

- Tu veux une playlist pool party ? OK
- Tu veux du reggaeton toute la nuit ? OK *(c'est ton choix, pas le mien)*
- Tu veux une playlist étude, running, anniversaire ? OK
- Tu veux juste comprendre comment ça marche ? OK

Le créateur du repo a ses **préférences personnelles** (voir Orlando), mais l'outil n'impose aucun style musical à personne.

---

## Nature du projet

| Question | Réponse |
|----------|---------|
| Commercial ? | Non — projet perso |
| Open source ? | Oui — fork, adapte, améliore |
| Produit Guidewire ? | Non — side project sans lien employeur |
| App iOS ? | Objectif long terme |
| MusicKit payant requis ? | Non — workflow gratuit disponible |

---

## Où on en est aujourd'hui

```
CLI manuel (JSON)                 OK
CLI generate_playlist              OK
Verification catalogue             OK
Creation Apple Music               OK
Gateway providers Phases 2-3       OK
Contrats UI Phase 4.1              OK
Engine Bridge Phase 4.2            OK
Theme engine Phase 4.3             OK
App macOS shell Phase 4.4          OK
Builder playlist Phase 4.5         OK
Import UX Phase 4.6                OK
App iOS Phase 4.9                  A faire
```

La **CLI** reste le socle fiable.  
La **Phase 4** apporte l'interface **Resonance** — même moteur, expérience produit.

---

## Ce qui ne changera pas

Quel que soit le mode (manuel ou assisté) :

1. **Apple Music** comme destination
2. **Ordre des sections** respecté
3. **Non destructif** — on crée, on ne supprime pas
4. **Gratuit d'abord** — pas de licence payante obligatoire
5. **Liberté musicale totale** — tu écoutes ce que tu veux

---

## La phrase du créateur

> *« J'ai construit ça pour moi, pour Arthur et Léonard, et pour tous ceux qui en ont marre de cliquer 96 morceaux à la main. Donne-moi une vibe ou une liste — je te sors une playlist. »*

---

→ Suite : [À propos](A-propos) · [Phase 2 — Génération](Phase-2-Generation) · [Phase 4 — Resonance](Phase-4-Interface-Resonance) · [Feuille de route iOS](Feuille-de-route-iOS)
