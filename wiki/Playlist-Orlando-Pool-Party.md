# Playlist Orlando Pool Party 2026

*La playlist signature du projet — 6 heures de bonne humeur, zéro reggaeton.*

## Concept

Une **pool party à Orlando** avec une montée progressive sur environ **6 heures**. Pensée pour mettre l'ambiance sans tuer la conversation au début, puis emmener tout le monde dans la piscine quand il faut.

**Contrainte absolue** : pas de reggaeton. Décision de papa. Non négociable. (Arthur et Léonard survivront.)

## Chiffres clés

| Métrique | Valeur |
|----------|--------|
| Sections | 7 |
| Morceaux | 96 |
| Durée estimée | ~6 h |
| Reggaeton | 0 |

## Les 7 sections

### 🌴 Warm Up Tropical (14 morceaux)

*On arrive à la pool. Serviettes, lunettes, premier splash.*

Kygo, Lost Frequencies, Klingande, Bakermat, Robin Schulz…  
Ambiance : tropical house douce, accessible, soleil couchant.

### ☀️ Sunny Vibes (14 morceaux)

*Le soleil est haut. Les enfants nagent. La playlist monte doucement.*

Harry Styles, Dua Lipa, The Weeknd, Pharrell, Bruno Mars, Mark Ronson…  
Ambiance : pop feel-good, classiques enjoués.

### 🍹 Pool Party Rising (14 morceaux)

*Les boissons fraîches arrivent. L'énergie monte.*

Purple Disco Machine, Calvin Harris, David Guetta, Meduza, Joel Corry…  
Ambiance : dance, EDM accessible, montée progressive.

### 🎉 Everybody In The Pool (14 morceaux)

*Peak time. Tout le monde est dedans. Même le papa.*

Avicii, Swedish House Mafia, Daft Punk, Modjo, Black Eyed Peas…  
Ambiance : festival, sing-along, classiques dance.

### 🌅 Golden Hour (12 morceaux)

*Le soleil descend. On ralentit un peu sans s'arrêter.*

Coldplay, RÜFÜS DU SOL, ODESZA, M83, The Killers…  
Ambiance : indie-dance, émotion, lumière dorée.

### 💃 Dance & Sing Along (14 morceaux)

*On ne peut plus s'arrêter. Même si on devrait.*

Sophie Ellis-Bextor, Dua Lipa, Lady Gaga, Queen, ABBA, Whitney Houston…  
Ambiance : dance floor, karaoke involontaire.

### 🌙 Night Pool Finale (14 morceaux)

*La soirée finit en beauté. Dernières nages sous les étoiles.*

Macklemore, Flo Rida, Pitbull, LMFAO, Disclosure, Purple Disco Machine…  
Ambiance : party finale, énergie maximale, fermeture en feu d'artifice.

## Courbe d'énergie

```
Énergie
  ▲
  │                              ╭──╮
  │                         ╭────╯  ╰──╮
  │                    ╭────╯          ╰──╮
  │               ╭────╯                  ╰──╮
  │          ╭────╯                          ╰──
  │     ╭────╯
  │╭────╯
  └────────────────────────────────────────────► Temps
   Warm  Sunny  Rising  Pool  Golden  Dance  Night
```

## Fichier source

```
playlists/orlando_pool_party_2026.json
```

## Lancer cette playlist

```bash
python3 check_catalog.py --country us
python3 create_playlist.py
```

## Personnalisation

Copie le fichier et adapte :

```bash
cp playlists/orlando_pool_party_2026.json playlists/ma_pool_party.json
# Édite le JSON
python3 create_playlist.py --playlist playlists/ma_pool_party.json
```

## Idées pour Arthur et Léonard

- Section **« Kids Energy »** avec leurs morceaux préférés
- Section **« Papa's Classics »** — Bon Jovi, Journey, Queen (déjà présents !)
- Durée adaptée : moins de morceaux = pool party plus courte

---

*Une playlist, c'est un parcours. Comme un sinistre bien géré : chaque phase a son rythme, son objectif, et sa fin en beauté.*
