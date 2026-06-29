# Playlist Orlando Pool Party 2026

*L'exemple fourni avec le projet — la pool party du créateur, pas un modèle imposé.*

→ Tu veux autre chose ? Crée ton propre JSON. L'outil s'adapte à **tes** goûts.

## Concept

Une **pool party à Orlando** avec montée progressive sur ~6 heures. C'est le cas d'usage qui a lancé le projet — et la playlist d'exemple incluse dans le repo.

**Note du créateur** : cette version n'inclut pas de reggaeton. C'est **sa** préférence personnelle pour **cette** playlist. Toi, tu fais ce qui te plaît — l'outil ne t'impose rien.

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

## Idées de playlists (pour tout le monde)

| Idée | Mots-clés suggérés | Exclusions possibles |
|------|-------------------|---------------------|
| Pool party | tropical, dance, rising | *(aucune obligation)* |
| Running | énergique, steady, 45min | ballades |
| Soirée reggaeton | reggaeton, party, latin | — |
| Étude | chill, lo-fi, instrumental | explicit |
| Anniversaire kids | happy, sing-along | explicit |
| Jazz dinner | jazz, smooth, steady | — |

*Chaque ligne est un exemple. Tes exclusions sont **tes** règles, pas celles du créateur.*

---

*Une playlist, c'est un parcours. Comme un sinistre bien géré : chaque phase a son rythme, son objectif, et sa fin en beauté.*
