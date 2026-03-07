// =============================================================
// ADAPTIVE ENGINE — Copy this into each activity's <script> block
// =============================================================
// Usage:
//   const engine = new AdaptiveEngine('esl-vocab-match', questionBank);
//   const question = engine.next();
//   engine.answer(true);  // or engine.answer(false)
//   engine.save();
//
// questionBank format:
//   {
//     1: [ { ...question data... }, ... ],  // Tier 1 items (20+ recommended)
//     2: [ { ...question data... }, ... ],  // Tier 2
//     3: [ ... ], 4: [ ... ], 5: [ ... ]
//   }
//
// Engine state (persisted in localStorage):
//   - tier: current difficulty (1-5)
//   - correctStreak: consecutive correct answers
//   - wrongStreak: consecutive wrong answers
//   - totalCorrect / totalAttempts: lifetime stats
//   - seen: map of tier -> indices already shown this cycle

class AdaptiveEngine {
    constructor(storageKey, questionBank) {
        this.storageKey = storageKey;
        this.bank = questionBank;
        this.promoteThreshold = 4;  // correct in a row to move up
        this.demoteThreshold = 2;   // wrong in a row to move down
        this.tierLabels = { 1: 'Rookie', 2: 'Starter', 3: 'Pro', 4: 'All-Star', 5: 'Legend' };

        const saved = localStorage.getItem(this.storageKey);
        if (saved) {
            const data = JSON.parse(saved);
            this.tier = data.tier || 1;
            this.correctStreak = data.correctStreak || 0;
            this.wrongStreak = data.wrongStreak || 0;
            this.totalCorrect = data.totalCorrect || 0;
            this.totalAttempts = data.totalAttempts || 0;
            this.seen = data.seen || {};
        } else {
            this.tier = 1;
            this.correctStreak = 0;
            this.wrongStreak = 0;
            this.totalCorrect = 0;
            this.totalAttempts = 0;
            this.seen = {};
        }

        this._currentIndex = null;
    }

    get tierLabel() {
        return this.tierLabels[this.tier] || 'Rookie';
    }

    get accuracy() {
        return this.totalAttempts === 0 ? 0 : Math.round((this.totalCorrect / this.totalAttempts) * 100);
    }

    // Get the next question from the current tier
    next() {
        const tierItems = this.bank[this.tier];
        if (!tierItems || tierItems.length === 0) return null;

        // Initialize seen list for this tier if needed
        if (!this.seen[this.tier]) this.seen[this.tier] = [];

        // If all items seen, reshuffle
        if (this.seen[this.tier].length >= tierItems.length) {
            this.seen[this.tier] = [];
        }

        // Pick a random unseen item
        const unseenIndices = tierItems.map((_, i) => i).filter(i => !this.seen[this.tier].includes(i));
        const pick = unseenIndices[Math.floor(Math.random() * unseenIndices.length)];
        this.seen[this.tier].push(pick);
        this._currentIndex = pick;

        return { ...tierItems[pick], tier: this.tier, tierLabel: this.tierLabel };
    }

    // Record an answer
    answer(correct) {
        this.totalAttempts++;

        if (correct) {
            this.totalCorrect++;
            this.correctStreak++;
            this.wrongStreak = 0;

            if (this.correctStreak >= this.promoteThreshold && this.tier < 5) {
                this.tier++;
                this.correctStreak = 0;
                this.save();
                return { promoted: true, tier: this.tier, tierLabel: this.tierLabel };
            }
        } else {
            this.wrongStreak++;
            this.correctStreak = 0;

            if (this.wrongStreak >= this.demoteThreshold && this.tier > 1) {
                this.tier--;
                this.wrongStreak = 0;
                this.save();
                return { demoted: true, tier: this.tier, tierLabel: this.tierLabel };
            }
        }

        this.save();
        return { promoted: false, demoted: false, tier: this.tier, tierLabel: this.tierLabel };
    }

    // Persist to localStorage
    save() {
        localStorage.setItem(this.storageKey, JSON.stringify({
            tier: this.tier,
            correctStreak: this.correctStreak,
            wrongStreak: this.wrongStreak,
            totalCorrect: this.totalCorrect,
            totalAttempts: this.totalAttempts,
            seen: this.seen
        }));
    }

    // Reset all progress
    reset() {
        this.tier = 1;
        this.correctStreak = 0;
        this.wrongStreak = 0;
        this.totalCorrect = 0;
        this.totalAttempts = 0;
        this.seen = {};
        localStorage.removeItem(this.storageKey);
    }
}
