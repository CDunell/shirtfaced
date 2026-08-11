"""Which corpus brands are real precedent, and which are marketplace noise.

Print-on-demand marketplaces (Redbubble, TeePublic, Threadless, Qwertee,
the-yetee/theyetee, Cotton Bureau) aren't brands with creative direction --
anyone can upload anything. Their designs were sitting in the corpus mixed in
with actual streetwear labels, uncredited as anything different, and at least
two measurement scripts (``mine_arrangement.py``, ``mine_placement.py``) were
built to walk only ``design_corpus_flat/`` -- which turns out to hold nothing
but these six. Every number those two scripts ever produced was measuring
marketplace submissions and calling it "the corpus."

Excluded here, not deleted from disk -- the images stay, this is a read-time
filter every miner should apply.

Tier 2 (novelty/joke-tee marketplaces: busted-tees, crazy-dog, donkey-tees,
tipsy-elves, six-dollar-shirts, snorg-tees, sarcastic-me, the-chivery,
pupsocks, topatoco, sanshee, fangamer, rockabilia) has the same structural
problem and is flagged but deliberately not excluded yet -- narrower call,
awaiting confirmation.
"""

from __future__ import annotations

# Brand-slug spelling is inconsistent across the two corpus roots --
# "the-yetee" under design_corpus/, "theyetee" under design_corpus_flat/.
# Both are excluded rather than picking the one that happens to match.
EXCLUDED_BRANDS: frozenset[str] = frozenset(
    {
        "redbubble",
        "teepublic",
        "threadless",
        "qwertee",
        "theyetee",
        "the-yetee",
        "cottonbureau",
    }
)

FLAGGED_NOT_EXCLUDED: frozenset[str] = frozenset(
    {
        "busted-tees",
        "crazy-dog",
        "donkey-tees",
        "tipsy-elves",
        "six-dollar-shirts",
        "snorg-tees",
        "sarcastic-me",
        "the-chivery",
        "pupsocks",
        "topatoco",
        "sanshee",
        "fangamer",
        "rockabilia",
    }
)


def is_excluded(brand_slug: str) -> bool:
    return brand_slug in EXCLUDED_BRANDS
