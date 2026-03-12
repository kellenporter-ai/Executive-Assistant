# Portal Economy Reference

Complete constants, formulas, and data structures for the `/game-balance` skill. All values extracted from production code.

**Source files:**
- `projects/Porters-Portal/lib/gamification.ts` — XP, costs, cosmetics, shop
- `projects/Porters-Portal/lib/achievements.ts` — achievements, skill trees, evolution, dailies
- `projects/Porters-Portal/lib/runewords.ts` — runeword definitions
- `projects/Porters-Portal/types.ts` — boss tiers, dungeon/arena structs
- `projects/Porters-Portal/functions/src/index.ts` — loot generation, rarity rolls, server-side math

---

## XP & Progression

- **Max Level:** 500
- **XP per level (tiered):**
  - Levels 1-50: 1,000 XP/level
  - Levels 51-200: 2,000 XP/level
  - Levels 201-350: 3,000 XP/level
  - Levels 351-450: 4,000 XP/level
  - Levels 451-500: 5,000 XP/level
- **MAX_XP_PER_SUBMISSION:** 500 (hard cap per engagement)
- **DEFAULT_XP_PER_MINUTE:** 10 (engagement time conversion)
- **Level-up bonus:** +100 Flux per level
- **Skill points:** 1 every 2 levels (even levels)

## Loot & Rarity

### Drop Rate Probabilities (base roll)
| Rarity | Probability | Roll Range |
|--------|------------|------------|
| UNIQUE | 2% | > 0.98 |
| RARE | 15% | 0.85-0.98 |
| UNCOMMON | 25% | 0.60-0.85 |
| COMMON | 58% | <= 0.60 |
| Custom overlay | 8% | If pool available |

### Affix Count by Rarity
| Rarity | Affixes | Distribution |
|--------|---------|-------------|
| COMMON | 0-1 | 50% chance of 1 |
| UNCOMMON | 2 | 1 prefix + 1 suffix |
| RARE | 3 | 2+1 or 1+2 randomly |
| UNIQUE | 3 | + unique stat + special effect |

### Tier Scaling (based on player level)
```
maxTierAvailable = min(10, floor(level / 50) + 1)
COMMON:   maxT = 50% of available
UNCOMMON: minT = 30%, maxT = 80%
RARE:     minT = 50%, maxT = 100%
UNIQUE:   minT = 80%, maxT = 100%
```

### Affix Value Formula
```
rollValue(tier) = max(1, tier * 5 + random(-2 to 2))
```

### Disenchant Values (Flux refund)
| Rarity | Base Flux | Bonus |
|--------|-----------|-------|
| COMMON | 2 | + tier bonus |
| UNCOMMON | 5 | + tier bonus |
| RARE | 15 | + tier bonus |
| UNIQUE | 50 | + tier bonus |

Bonus multiplier: `1 + (avgAffixTier * 0.2)`

## Flux (Currency) Economy

### Core Crafting Costs
| Action | Cost |
|--------|------|
| RECALIBRATE | 5 Flux |
| REFORGE | 25 Flux |
| OPTIMIZE | 50 Flux |
| SOCKET (add slot) | 30 Flux |
| ENCHANT (insert gem) | 15 Flux |
| UNSOCKET_BASE | 10 Flux |

### Unsocket Cost Formula
```
cost = 10 * rarityMult(item) * max(1, gemTier) * (1 + unsocketCount)
rarityMult: COMMON=1, UNCOMMON=2, RARE=4, UNIQUE=8
```

### Flux Shop Consumables
| Item | Cost | Limit |
|------|------|-------|
| XP Surge (1h, +50%) | 75 Flux | 2/day |
| XP Overdrive (3h, +50%) | 150 Flux | 1/day |
| Reroll Token | 50 Flux | 3/day |
| Name Color | 100 Flux | unlimited |
| Agent Cosmetics | 150-300 Flux | per type |
| Character Models | 0-1500 Flux | varies |

### Fortune Wheel (spin cost: 25 Flux)
Expected loss ~18.8 Flux per spin.

| Prize | Weight |
|-------|--------|
| 50 XP | 25 |
| 100 XP | 18 |
| 250 XP | 8 |
| 10 Flux | 20 |
| 25 Flux | 12 |
| 100 Flux | 3 |
| Common Item | 15 |
| Uncommon Item | 8 |
| Rare Item | 3 |
| Random Gem | 10 |
| Skill Point | 5 |
| Try Again | 15 |

## Combat Stats

**Base stats:** All four start at 10 (Tech, Focus, Analysis, Charisma)

### Stat Derivation
```
maxHp        = 100 + max(0, charisma - 10) * 5
armorPercent = min(analysis * 0.5, 50)
critChance   = min(focus * 0.01, 0.40)
critMultiplier = 2 + max(0, focus - 10) * 0.02
```

### Equipment Slots (8 total)
HEAD, CHEST, HANDS, FEET, BELT, AMULET, RING1, RING2

### Gear Score
```
scorePerItem = (avgAffixTier * 10) + rarityBonus
rarityBonus: COMMON=0, UNCOMMON=10, RARE=30, UNIQUE=60
totalScore = sum of all equipped items
```

## Gems

| Type | Stat |
|------|------|
| Ruby | Tech |
| Emerald | Focus |
| Sapphire | Analysis |
| Amethyst | Charisma |

**Tiers:** 1-5 | **Stat per tier:** `tier * 5`

### Runewords (2-socket)
1. Binary (Ruby+Ruby): +15 Tech
2. Harmony (Emerald+Sapphire): +8 Focus, +8 Analysis
3. Catalyst (Ruby+Emerald): +8 Tech, +8 Focus
4. Resonance (Amethyst+Amethyst): +15 Charisma
5. Enigma (Sapphire+Amethyst): +10 Analysis, +6 Charisma

### Runewords (3-socket)
1. Quantum Entanglement (S+R+S): +18 Analysis, +10 Tech, +5% XP all
2. Nuclear Fusion (R+E+R): +20 Tech, +10 Focus, +5% XP engagement
3. Photosynthesis (E+E+R): +20 Focus, +8 Tech, +3 all stats
4. Supernova (R+S+A): +12 each stat, +8% XP all
5. Double Helix (E+A+E): +15 Focus, +15 Charisma, +4 Focus/Charisma
6. Singularity (A+S+R): +10 each stat, +10% XP all

## Boss System

- **Min participation:** 5 attempts, 1 correct
- **Top 5 reward multipliers:** [1.5x, 1.4x, 1.3x, 1.2x, 1.1x]
- **Shard count:** 10 (supports ~10 concurrent writes/sec)

### Unique Boss Items
1. Newton's Prism (AMULET): +50 Analysis, "+20% XP"
2. Tesla's Coils (HANDS): +45 Tech, "Bonus resources"
3. Curie's Determination (RING): +40 Focus, "Mental fatigue reduction"
4. Einstein's Relativistic Boots (FEET): +50 Tech, "Late submission grace"

## Daily Login (7-day cycle)

| Day | XP | Flux |
|-----|-----|------|
| 1 | 25 | 5 |
| 2 | 30 | 5 |
| 3 | 40 | 10 |
| 4 | 50 | 10 |
| 5 | 75 | 15 |
| 6 | 100 | 20 |
| 7 | 150 | 50 |

### Engagement Streak Multiplier
| Weeks | Multiplier |
|-------|-----------|
| 0 | 1.0x |
| 1-2 | 1.05x |
| 3-4 | 1.10x |
| 5-7 | 1.15x |
| 8-12 | 1.25x |
| 13+ | 1.50x |

## Daily Challenges

**Daily (pick 3):** XP Hunter (200 XP: 50XP+10F), Resource Explorer (2 resources: 75XP), Quiz Whiz (5 correct: 60XP+15F), Deep Focus (30 min: 80XP), Tinkerer (1 craft: 40XP+5F), Gear Up (equip: 30XP)

**Weekly (Mondays):** XP Surge (500 XP: 100XP+25F), Scholar (20 correct: 200XP+50F), Marathon (2 hours: 250XP+75F)

## Achievement Milestones

### Level Milestones
| Level | XP Reward | Flux |
|-------|-----------|------|
| 10 | 100 | 50 |
| 25 | 250 | 100 |
| 50 | 500 | 250 |
| 100 | 1,000 | 500 |
| 200 | 2,000 | 750 |
| 300 (secret) | 3,000 | 1,000 |
| 400 (secret) | 5,000 | 2,000 |
| 500 (secret) | 10,000 | 5,000 |

## Skill Trees (4 Specializations)

- **THEORIST:** Analysis + XP (capstone: +25% XP all sources)
- **EXPERIMENTALIST:** Tech + crafting (capstone: +20% craft results)
- **ANALYST:** Focus + streaks (capstone: +30% XP quiz answers)
- **DIPLOMAT:** Charisma + group (capstone: all party +10% XP)

Costs: 1-5 skill points per node.

## Item Sets (4 sets, 2/3-piece bonuses)

1. **Tesla's Arsenal:** 2pc +10 Tech, 3pc +25 Tech +10 Focus
2. **Newton's Laws:** 2pc +10 Analysis, 3pc +25 Analysis +10 Charisma
3. **Curie's Focus:** 2pc +10 Focus, 3pc +25 Focus +10 Analysis
4. **Diplomat's Ensemble:** 2pc +10 Charisma, 3pc +25 Charisma +10 Tech

## Evolution Tiers (Avatar Visual Progression)

Unlock levels: 1, 10, 25, 50, 75, 100, 150, 200, 250, 300, 350, 400, 450, 500

- **Glow:** 0.05 (Recruit) -> 1.0 (Eternal)
- **Particles:** 0 -> 15
- **Armor:** BASIC -> ENHANCED -> ADVANCED -> LEGENDARY -> MYTHIC
- **Wings:** NONE (1-150) -> ENERGY (150-300) -> CRYSTAL (300-400) -> PHOENIX (400+)
- **Crown:** NONE (1-50) -> CIRCLET (50-200) -> HALO (200-350) -> CROWN (350+)

## Arena

- **Rating brackets:** 0-500, 501-1000, 1001-1500, 1501-2000, 2001+
- **Typical rating change:** win +15, loss -10
- **Daily match limit:** 5
- **Modes:** AUTO_DUEL, QUIZ_RACE

## Player Roles (Derived from highest stat)

VANGUARD (Tech), STRIKER (Focus), SENTINEL (Analysis), COMMANDER (Charisma)
