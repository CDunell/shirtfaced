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

Every exclusion below is structural: the source cannot hold evidence about
graphic construction by a brand, because no brand made the choices. That is a
property of the source, not a judgement about quality. Exclusions that would be
judgements live in ``ICONS_AND_INDIES`` instead, as a selection, and are not
applied by ``is_excluded``.
"""

from __future__ import annotations

# --- Tier 1: print-on-demand marketplaces ------------------------------------
#
# Brand-slug spelling is inconsistent across the two corpus roots --
# "the-yetee" under design_corpus/, "theyetee" under design_corpus_flat/.
# Both are excluded rather than picking the one that happens to match.
MARKETPLACES: frozenset[str] = frozenset(
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

# --- Tier 2: novelty and joke-tee marketplaces -------------------------------
#
# Promoted from flagged to excluded on 2026-08-13. The file previously held
# these "flagged but deliberately not excluded yet -- narrower call, awaiting
# confirmation". The owner confirmed while reviewing the corpus for a retro
# collection: "most of the corpus is crap clipart or fast fashion, I want the
# icons and Indies". Same structural defect as tier 1 -- an upload queue rather
# than a design direction -- so it moves to the same list.
NOVELTY_MARKETPLACES: frozenset[str] = frozenset(
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
        "shirt-was-cash",
        "bad-idea-tshirts",
    }
)

# --- Tier 3: retailers, not brands -------------------------------------------
#
# These sell other labels' garments. A "product" collected from them is somebody
# else's design filed under the shop's name, so every brand-level number they
# contribute is wrong twice -- once for the shop, once for the label whose work
# it actually is. The most damaging exclusion in this file, because unlike a
# marketplace these look exactly like brands from the outside.
RETAILERS: frozenset[str] = frozenset(
    {
        "culture-kings",
        "general-pants",
        "universal-store",
        "incu",
        "up-there",
        "impericon",
        "inked-shop",
        "workwear-hub",
    }
)

# --- The retailers deliberately not excluded ---------------------------------
#
# These are exactly the shape above and are absent from that set on purpose. Do
# not "fix" it by adding them.
#
# The owner named City Beach on 15 August 2026 as a source of current retail
# design -- what is on the shelf now, at volume -- and asked for it as its own
# tradition, then asked for the USA equivalents. Both halves of tier 3's
# objection are answered by construction:
#
#   Filed under the shop's name. It is not. Every product records the label that
#   actually made it in ``product.json``'s ``retail_brand`` -- from Shopify's
#   ``vendor`` for the American shops, from the tile payload for City Beach --
#   so no brand-level number is ever attributed to a retailer.
#
#   Wrong for the shop's own tradition. They have no shared one with any label.
#   The tradition is ``current-retail``, which only these write, so a retailer's
#   stock cannot move the medians of ``skate``, ``au-surf`` or any other
#   tradition a label belongs to. ``advise()`` filters on tradition before it
#   takes a median.
#
# What they can hold evidence about is the thing being asked: how graphic
# apparel is presented and sold right now. That is a property of the shelf, and
# a shop is the only place a shelf exists.
#
# The shop is the directory name, so an Australian-only or American-only cut
# stays a filter away without a second tradition.
CURRENT_RETAIL: frozenset[str] = frozenset(
    {
        # Australia
        "city-beach",
        # USA -- skate
        "ccs",
        "nj-skateshop",
        "kcdc",
        "black-sheep-skate",
        "35th-north",
        # USA -- surf
        "jacks-surfboards",
        "hss-surf",
        "val-surf",
        "cleanline-surf",
        "hansen-surf",
        # USA -- street
        "dtlr",
    }
)

# Noted rather than acted on: ``undefeated`` and ``packer-shoes`` sit in BRANDS
# as ``streetwear`` and are multi-label retailers too, so their tradition is
# carrying other labels' work. Pre-existing and left alone -- reclassifying
# somebody else's call is churn, and now that ``retail_brand`` is recorded the
# attribution is at least recoverable.

# --- Tier 4: licensed reproduction -------------------------------------------
#
# The artwork is a property owner's -- a film, a comic, a band's estate -- and
# the label's contribution is printing and placement, not the graphic. Useful
# evidence about garment and placement; misleading evidence about graphic
# construction, which is what the corpus is for.
LICENSED_REPRODUCTION: frozenset[str] = frozenset(
    {
        "chaser",
        "junk-food",
        "fright-rags",
        "cavity-colors",
    }
)

EXCLUDED_BRANDS: frozenset[str] = (
    MARKETPLACES | NOVELTY_MARKETPLACES | RETAILERS | LICENSED_REPRODUCTION
)

# --- Traditions that never belong in the measurement corpus ------------------
#
# Collected into ``var/design_archive/`` by ``collect_design_corpus.py`` with
# DESIGN_CORPUS_ROOT set, so a miner walking design_corpus/ will not meet them.
# Listed anyway: the two roots may be joined later, and at that point a vintage
# reseller's decades-old stock and a licensed reprint would both move layout
# medians that describe how brands lay out work today.
EXCLUDED_TRADITIONS: frozenset[str] = frozenset({"vintage-reseller", "licensed-reprint"})

# --- A selection, not an exclusion -------------------------------------------
#
# The 59 brands the owner named when scoping a retro collection: "the icons and
# Indies". Heritage labels with archive depth, plus modern independents with
# their own direction.
#
# This is DIRECTION, and CLAUDE.md is explicit that direction is the owner's and
# that the corpus does not set it. So it is not wired into ``is_excluded`` and
# nothing outside a deliberately scoped run should read it. A brand's absence
# here says it was not wanted for one collection -- not that it is defective
# evidence. Absence from EXCLUDED_BRANDS is the load-bearing statement.
ICONS_AND_INDIES: frozenset[str] = frozenset(
    {
        # Skate -- heritage
        "thrasher",
        "santa-cruz-au",
        "baker",
        "toy-machine",
        "zero",
        "deathwish",
        "chocolate",
        "volcom",
        # Skate -- modern independents
        "polar-skate",
        "quasi",
        "dime",
        "frog-skateboards",
        "limosine",
        "welcome-skateboards",
        "huf",
        "primitive",
        "last-resort-ab",
        "ripndip",
        # Streetwear -- heritage
        "stussy",
        "stussy-au",
        "bape",
        "obey",
        "the-hundreds",
        "undefeated",
        "neighborhood",
        "wtaps",
        # Streetwear -- modern independents
        "brain-dead",
        "born-x-raised",
        "noah-ny",
        "awake-ny",
        "cherry-la",
        "gallery-dept",
        "pleasures",
        "corteiz",
        "golf-wang",
        "kidsuper",
        "places-plus-faces",
        "market-studios",
        "aime-leon-dore",
        # Surf
        "katin",
        "captain-fin",
        "vissla",
        "misfit",
        "thrills",
        "rhythm",
        # Art and label independents
        "online-ceramics",
        "art-club-and-friends",
        "sub-pop",
        "matador-records",
        "stones-throw",
        "hello-merch",
        # Workwear and kustom heritage
        "filson",
        "carhartt",
        "dickies",
        "deus-au",
        "biltwell",
        "lowbrow-customs",
        # Counterculture
        "cookies",
        "sullen",
    }
)


def is_excluded(brand_slug: str) -> bool:
    """Whether this brand cannot hold brand-level design evidence, structurally."""
    return brand_slug in EXCLUDED_BRANDS


def is_excluded_tradition(tradition: str) -> bool:
    """Whether a tradition tag belongs outside the measurement corpus."""
    return tradition in EXCLUDED_TRADITIONS


def in_selection(brand_slug: str) -> bool:
    """Whether the owner named this brand for the icons-and-indies collection.

    Not a quality gate. Use only when a run is deliberately scoped to that
    selection; never as a filter on the corpus at large.
    """
    return brand_slug in ICONS_AND_INDIES
