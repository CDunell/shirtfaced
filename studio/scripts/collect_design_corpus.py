"""Collect the design evidence corpus from Shopify storefronts.

Most graphic-apparel brands run Shopify, which serves a public, unauthenticated
``/products.json`` — structured product data with image URLs, titles, descriptions,
prices and tags. No API key, no HTML scraping, no bot-detection fight, and it is the
store's own data rather than something inferred from rendered markup.

That makes collection a deterministic script rather than an agent task: same brand
list in, same corpus out, re-runnable when a range changes, and auditable.

Writes ``var/design_corpus/`` per ``docs/DESIGN_CORPUS_SCHEMA.md``. Brands whose
store is not Shopify (or blocks the endpoint) are reported as skipped rather than
guessed at — a brand missing from the corpus is a known gap, not a silent one.

    python scripts/collect_design_corpus.py            # all brands
    python scripts/collect_design_corpus.py threadheads stussy
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CORPUS_ROOT = Path(__file__).resolve().parent.parent / "var" / "design_corpus"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Products per brand. The corpus is comparison evidence, not a catalogue mirror.
# Higher than it was now that every surface is in scope rather than tees alone --
# a dozen slots filled entirely with chest prints would leave headwear, drinkware
# and accessories unrepresented.
PRODUCTS_PER_BRAND = 18

# Images per product. Two was too few: brands commonly ship a close-up of the
# garment alongside a full-body shot of a model wearing it, and it is the close-up
# that can actually be measured -- a full-body frame puts the print in a few dozen
# pixels. Threadheads names them outright (Black-Close-Up, Black-Full-Body); most
# others number them. Taking six per product means the measurable shot is present
# to be chosen, rather than lost to a cap of two.
IMAGES_PER_PRODUCT = 6

# Filename fragments that reveal what a shot is. Not every store labels its
# images, so this is a hint recorded alongside the file, never a requirement.
SHOT_HINTS: tuple[tuple[str, str], ...] = (
    ("close-up", "close-up"),
    ("closeup", "close-up"),
    ("close_up", "close-up"),
    ("full-body", "full-body"),
    ("fullbody", "full-body"),
    ("full_body", "full-body"),
    ("flat", "flat"),
    ("back", "back"),
    ("front", "front"),
    ("detail", "detail"),
    ("model", "worn"),
)


def _shot_hint(url: str) -> str:
    """What the store's own filename says this shot is, if anything."""
    name = url.split("/")[-1].split("?")[0].lower()
    for fragment, label in SHOT_HINTS:
        if fragment in name:
            return label
    return ""


# Requested image width in pixels. Comfortably above what any of the scorecard's
# visual tests need — the thumbnail, blur and silhouette tests all reduce detail
# rather than demand it — and roughly 30x smaller than a full-resolution original.
IMAGE_WIDTH = 1200

# Politeness delay between requests to one store, in seconds.
REQUEST_DELAY = 0.4

# The surfaces Shirtfaced sells on: tees, hoodies, caps, hats, stubby holders.
#
# Set by the owner. Wider than tees and hoodies -- a cap's front panel and a
# stubby holder's wrap are different design problems from a chest print, and the
# constitution's scale roles (S0 micro signature through S4 jumbo) span that
# spread -- and narrower than every printable surface, which would pull in totes,
# socks and outerwear the brand does not make.
#
# Jumpers, sweatshirts and crews come in with hoodies: WORLD.md's range names
# jumpers, and they carry the same chest-and-back print geometry.
WANTED_TYPE_PATTERN = re.compile(
    # Tees, in all the cuts these stores name them by.
    r"t[- ]?shirt|(^|\W)tee|crop|boxy|baby ?tee|"
    # Hoodies and the jumper family.
    r"hood|sweat ?shirt|sweater|crew ?neck|jumper|pullover|"
    # Headwear.
    r"(^|\W)cap(\W|$)|(^|\W)hat(\W|$)|snapback|strapback|trucker|beanie|"
    r"bucket|a[- ]?frame|dad ?hat|five ?panel|"
    # Stubby holders, by every name they are sold under.
    r"stubby|stubbie|can cooler|drink cooler|koozie|coozie|coolie",
    re.IGNORECASE,
)

UNWANTED_PATTERN = re.compile(
    # Non-products and undecorated stock. Threadheads lists "Blank Baby Tee" and
    # "Blank Boxy Tee" as their own product types -- no design to hold evidence of.
    r"gift ?card|e-?gift|voucher|subscription|donation|shipping|protection|"
    r"insurance|sample|test ?product|^blank |blank (tee|t-?shirt|hoodie|crop)|"
    # Skate hardware that happens to match "deck"/"trucker" style words.
    r"deck$|skateboard deck|griptape|bearings?$",
    re.IGNORECASE,
)


def _is_graphic_led(product: dict[str, Any]) -> bool:
    """Whether a product is one of the surfaces Shirtfaced sells on."""
    haystack = f"{product.get('product_type', '')} {product.get('title', '')}"
    if UNWANTED_PATTERN.search(haystack):
        return False
    return bool(WANTED_TYPE_PATTERN.search(haystack))


# brand slug -> (display name, storefront base URL, design tradition)
#
# The tradition tag is the point of the breadth. Design parameters -- arch type,
# badge construction, hierarchy, scale role, print mechanics -- are shared craft,
# but each tradition applies them differently: band merch is poster-derived and
# dense, varsity is arch-and-block, national-park is illustrated badge, workwear
# is chest-hit and patch. A corpus of one tradition teaches one dialect and reads
# its conventions as universal laws. Tagging lets a pattern be tested within a
# tradition and across them.
BRANDS: dict[str, tuple[str, str, str]] = {
    # Australian — the closest comparables, and the ones the brand actually competes with.
    "threadheads": ("Threadheads", "https://threadheads.com.au", "au-humour"),
    "thrills": ("Thrills", "https://thrills.co", "au-surf"),
    "barney-cools": ("Barney Cools", "https://barneycools.com", "au-streetwear"),
    "afends": ("Afends", "https://afends.com", "au-surf"),
    "misfit": ("Misfit", "https://misfitshapes.com", "au-surf"),
    "riot-society": ("Riot Society", "https://riotsociety.com", "streetwear"),
    "culture-kings": ("Culture Kings", "https://culturekings.com.au", "au-streetwear"),
    "santa-cruz-au": ("Santa Cruz Australia", "https://santacruzskateboards.com.au", "skate"),
    # Australian humour / novelty / slogan-led — the nearest thing to Shirtfaced's
    # own category, where the graphic is the joke rather than a brand mark.
    "dangerfield": ("Dangerfield", "https://dangerfield.com.au", "au-humour"),
    "beserk": ("Beserk", "https://beserk.com.au", "au-alt"),
    "the-tshirt-co": ("The T-Shirt Co", "https://www.thetshirtco.com.au", "au-humour"),
    "nena-and-pasadena": ("Nena & Pasadena", "https://nenaandpasadena.com.au", "au-streetwear"),
    "kiss-chacey": ("Kiss Chacey", "https://kisschacey.com.au", "au-streetwear"),
    "mr-simple": ("Mr Simple", "https://mrsimple.com.au", "au-basics"),
    "stm-goods": ("STM Goods", "https://stmgoods.com.au", "au-basics"),
    # Australian surf — graphic-led heritage, and the closest large-scale local
    # comparables for print-on-garment conventions.
    "rip-curl": ("Rip Curl", "https://ripcurl.com.au", "au-surf"),
    "billabong": ("Billabong", "https://www.billabong.com.au", "au-surf"),
    "quiksilver": ("Quiksilver", "https://www.quiksilver.com.au", "au-surf"),
    # Global streetwear / graphic-led — the documented research corpus.
    "stussy": ("Stüssy", "https://www.stussy.com", "streetwear"),
    "obey": ("Obey", "https://obeyclothing.com", "streetwear"),
    "represent": ("Represent", "https://au.representclo.com", "streetwear"),
    "brain-dead": ("Brain Dead", "https://wearebraindead.com", "streetwear"),
    "pleasures": ("Pleasures", "https://pleasuresnow.com", "streetwear"),
    # Hyphenated. onlineceramics.com is an unrelated UK pottery business.
    "online-ceramics": ("Online Ceramics", "https://online-ceramics.com", "art-merch"),
    "cactus-plant-flea-market": (
        "Cactus Plant Flea Market",
        "https://cactusplantfleamarket.com",
        "streetwear",
    ),
    "market-studios": ("Market Studios", "https://marketstudios.com", "streetwear"),
    "sporty-and-rich": ("Sporty & Rich", "https://sportyandrich.com", "streetwear"),
    "golf-wang": ("Golf Wang", "https://golfwang.com", "streetwear"),
    "born-x-raised": ("Born X Raised", "https://bornxraised.com", "streetwear"),
    "anti-social-social-club": (
        "Anti Social Social Club",
        "https://antisocialsocialclub.com",
        "streetwear",
    ),
    "rvca": ("RVCA", "https://www.rvca.com", "skate"),
    "brixton": ("Brixton", "https://brixton.com", "americana"),
    "huf": ("HUF", "https://hufworldwide.com", "skate"),
    "primitive": ("Primitive Skateboarding", "https://primitiveskate.com", "skate"),
    "the-hundreds": ("The Hundreds", "https://thehundreds.com", "streetwear"),
    "diamond-supply": ("Diamond Supply Co", "https://diamondsupplyco.com", "skate"),
    "thrasher": ("Thrasher", "https://shop.thrashermagazine.com", "skate"),
    "volcom": ("Volcom", "https://www.volcom.com", "skate"),
    "polar-skate": ("Polar Skate Co", "https://polarskateco.com", "skate"),
    "quasi": ("Quasi Skateboards", "https://quasiskateboards.com", "skate"),
    "dime": ("Dime MTL", "https://dimemtl.com", "skate"),
    "last-resort-ab": ("Last Resort AB", "https://lastresortab.com", "skate"),
    "welcome-skateboards": ("Welcome Skateboards", "https://welcomeskateboards.com", "skate"),
    "chocolate": ("Chocolate Skateboards", "https://chocolateskateboards.com", "skate"),
    "baker": ("Baker Skateboards", "https://bakerskateboards.com", "skate"),
    "deathwish": ("Deathwish Skateboards", "https://deathwishskateboards.com", "skate"),
    "toy-machine": ("Toy Machine", "https://toymachine.com", "skate"),
    "zero": ("Zero Skateboards", "https://zeroskateboards.com", "skate"),
    "roark": ("Roark", "https://www.roark.com", "outdoor"),
    "katin": ("Katin USA", "https://katinusa.com", "surf"),
    "salty-crew": ("Salty Crew", "https://saltycrew.com", "surf"),
    "rhythm": ("Rhythm", "https://rhythmlivin.com", "surf"),
    # --- Band, label and music merch: poster-derived, dense, type-led. ---
    "impericon": ("Impericon", "https://www.impericon.com", "band-merch"),
    "acdc": ("AC/DC Store", "https://shop.acdc.com", "band-merch"),
    "rockabilia": ("Rockabilia", "https://www.rockabilia.com", "band-merch"),
    "hello-merch": ("Hello Merch", "https://www.hellomerch.com", "band-merch"),
    "sub-pop": ("Sub Pop", "https://shop.subpop.com", "band-merch"),
    "matador-records": ("Matador Records", "https://store.matadorrecords.com", "band-merch"),
    "stones-throw": ("Stones Throw", "https://store.stonesthrow.com", "band-merch"),
    # --- Outdoor and national park: illustrated badge, landscape, arch. ---
    "parks-project": ("Parks Project", "https://parksproject.us", "outdoor"),
    "landmark-project": ("The Landmark Project", "https://www.thelandmarkproject.com", "outdoor"),
    "wild-tribute": ("Wild Tribute", "https://wildtribute.com", "outdoor"),
    "coal-headwear": ("Coal Headwear", "https://www.coalheadwear.com", "outdoor"),
    "topo-designs": ("Topo Designs", "https://www.topodesigns.com", "outdoor"),
    "poler": ("Poler", "https://poler.com", "outdoor"),
    "coalatree": ("Coalatree", "https://www.coalatree.com", "outdoor"),
    "roark-revival": ("Roark Revival", "https://roarkrevival.com", "outdoor"),
    "filson": ("Filson", "https://www.filson.com", "workwear"),
    "darn-tough": ("Darn Tough", "https://darntough.com", "outdoor"),
    # --- Fishing, hunting, western, rural. ---
    "aftco": ("AFTCO", "https://www.aftco.com", "fishing"),
    "huk": ("HUK", "https://huk.com", "fishing"),
    "ringers-western": ("Ringers Western", "https://ringerswestern.com", "au-western"),
    "outback-traders": ("Outback Traders", "https://outbacktraders.com.au", "au-western"),
    # --- Motorsport, moto, garage. ---
    "fasthouse": ("Fasthouse", "https://www.fasthouse.com", "moto"),
    "biltwell": ("Biltwell", "https://www.biltwellinc.com", "moto"),
    "lowbrow-customs": ("Lowbrow Customs", "https://lowbrowcustoms.com", "moto"),
    "gas-monkey": ("Gas Monkey Garage", "https://gasmonkeygarage.com", "moto"),
    "deus-au": ("Deus Ex Machina", "https://au.deuscustoms.com", "moto"),
    "dickies": ("Dickies", "https://www.dickies.com", "workwear"),
    # --- Varsity, team, sport. ---
    "homage": ("Homage", "https://www.homage.com", "varsity"),
    "sportiqe": ("Sportiqe", "https://sportiqe.com", "varsity"),
    "rowing-blazers": ("Rowing Blazers", "https://www.rowingblazers.com", "varsity"),
    "cricket-au": ("Cricket Australia", "https://shop.cricket.com.au", "au-sport"),
    # --- Craft beer and hospitality: AU, humour-adjacent, drinkware-heavy. ---
    "stone-and-wood": ("Stone & Wood", "https://shop.stoneandwood.com.au", "au-beer"),
    "pirate-life": ("Pirate Life", "https://piratelife.com.au", "au-beer"),
    "mountain-culture": ("Mountain Culture", "https://mountainculture.com.au", "au-beer"),
    "4-pines": ("4 Pines", "https://shop.4pinesbeer.com.au", "au-beer"),
    "onyx-coffee": ("Onyx Coffee Lab", "https://onyxcoffeelab.com", "hospitality"),
    "stumptown": ("Stumptown Coffee", "https://www.stumptowncoffee.com", "hospitality"),
    "sightglass": ("Sightglass Coffee", "https://sightglasscoffee.com", "hospitality"),
    # --- Novelty and slogan: the closest tradition to Shirtfaced's own. ---
    "sarcastic-me": ("Sarcastic Me", "https://sarcasticme.com", "novelty"),
    "crazy-dog": ("Crazy Dog T-Shirts", "https://www.crazydogtshirts.com", "novelty"),
    "pupsocks": ("PupSocks", "https://pupsocks.com", "novelty"),
    # --- Horror, alt, tattoo: dense illustration, heavy blacks. ---
    "blackcraft": ("Blackcraft Cult", "https://www.blackcraftcult.com", "alt-horror"),
    "cavity-colors": ("Cavity Colors", "https://cavitycolors.com", "alt-horror"),
    "fright-rags": ("Fright Rags", "https://www.fright-rags.com", "alt-horror"),
    "terror-threads": ("Terror Threads", "https://terrorthreads.com", "alt-horror"),
    "sourpuss": ("Sourpuss", "https://sourpussclothing.com", "alt-horror"),
    "kreepsville": ("Kreepsville 666", "https://kreepsville666.com", "alt-horror"),
    # --- Fitness. ---
    "wod-life": ("The WOD Life", "https://thewodlife.com.au", "fitness"),
    "barbell-apparel": ("Barbell Apparel", "https://barbellapparel.com", "fitness"),
    "born-primitive": ("Born Primitive", "https://www.bornprimitive.com", "fitness"),
    # --- Vintage reproduction and licensed. ---
    "junk-food": ("Junk Food Clothing", "https://www.junkfoodclothing.com", "vintage-licensed"),
    "chaser": ("Chaser Brand", "https://www.chaserbrand.com", "vintage-licensed"),
    # --- Surf and skate not already held. ---
    "stance": ("Stance", "https://www.stance.com", "skate"),
    "vissla": ("Vissla", "https://www.vissla.com", "surf"),
    "captain-fin": ("Captain Fin", "https://www.captainfin.com", "surf"),
    "workwear-hub": ("Workwear Hub", "https://www.workwearhub.com.au", "workwear"),
    "pnw-components": ("PNW Components", "https://www.pnwcomponents.com", "outdoor"),
    # --- Creator, publisher and fandom merch: licensed characters, dense line art. ---
    "dropout": ("Dropout", "https://store.dropout.tv", "creator-merch"),
    "the-yetee": ("The Yetee", "https://theyetee.com", "creator-merch"),
    "fangamer": ("Fangamer", "https://www.fangamer.com", "gaming"),
    "sanshee": ("Sanshee", "https://sanshee.com", "gaming"),
    "100-thieves": ("100 Thieves", "https://shop.100thieves.com", "esports"),
    "faze-clan": ("FaZe Clan", "https://shop.fazeclan.com", "esports"),
    # --- Veteran, tactical, patriotic: crest, banner, heavy type. ---
    "grunt-style": ("Grunt Style", "https://gruntstyle.com", "veteran"),
    "nine-line": ("Nine Line Apparel", "https://ninelineapparel.com", "veteran"),
    "black-rifle-coffee": ("Black Rifle Coffee", "https://blackriflecoffee.com", "veteran"),
    "ranger-up": ("Ranger Up", "https://rangerup.com", "veteran"),
    # --- Cycling and running: minimal, technical, wordmark-led. ---
    "ostroy": ("Ostroy", "https://ostroy.cc", "cycling"),
    "satisfy": ("Satisfy Running", "https://www.satisfyrunning.com", "running"),
    # --- Golf: crest, novelty, preppy-subverted. ---
    "dormie-workshop": ("Dormie Workshop", "https://www.dormieworkshop.com", "golf"),
    "malbon-golf": ("Malbon Golf", "https://www.malbongolf.com", "golf"),
    "eastside-golf": ("Eastside Golf", "https://eastsidegolf.com", "golf"),
    "bad-birdie": ("Bad Birdie", "https://www.badbirdie.com", "golf"),
    # --- Climbing, snow, adventure. ---
    "black-diamond": ("Black Diamond", "https://www.blackdiamondequipment.com", "outdoor"),
    "cotopaxi": ("Cotopaxi", "https://www.cotopaxi.com", "outdoor"),
    "howler-brothers": ("Howler Brothers", "https://howlerbrothers.com", "outdoor"),
    "free-fly": ("Free Fly Apparel", "https://www.freeflyapparel.com", "outdoor"),
    "duck-camp": ("Duck Camp", "https://www.duckcamp.com", "fishing"),
    "sea-to-summit": ("Sea to Summit", "https://seatosummit.com.au", "outdoor"),
    "kathmandu": ("Kathmandu", "https://www.kathmandu.com.au", "outdoor"),
    # --- Counterculture and cause-led. ---
    "cookies": ("Cookies", "https://cookiessf.com", "counterculture"),
    "elevated-faith": ("Elevated Faith", "https://elevatedfaith.com", "cause"),
    "madhappy": ("Madhappy", "https://www.madhappy.com", "cause"),
    "the-good-patch": ("The Good Patch", "https://www.thegoodpatch.com", "cause"),
    # --- Tattoo, barber, trade shop. ---
    "sullen": ("Sullen Clothing", "https://www.sullenclothing.com", "tattoo"),
    "inked-shop": ("Inked Shop", "https://inkedshop.com", "tattoo"),
    "suavecito": ("Suavecito", "https://www.suavecito.com", "barber"),
    "reuzel": ("Reuzel", "https://www.reuzel.com", "barber"),
    "heatonist": ("Heatonist", "https://heatonist.com", "hospitality"),
    # --- Mass-market novelty and print-on-demand: very high design volume. ---
    "shirt-was-cash": ("Shirt Was Cash", "https://www.shirtwascash.com", "novelty"),
    "tipsy-elves": ("Tipsy Elves", "https://www.tipsyelves.com", "novelty"),
    # --- Festival merch. ---
    "bonnaroo": ("Bonnaroo", "https://store.bonnaroo.com", "festival"),
    "glastonbury": ("Glastonbury", "https://shop.glastonburyfestivals.co.uk", "festival"),
    # --- More Australian labels. ---
    "assembly-label": ("Assembly Label", "https://www.assemblylabel.com", "au-basics"),
    "general-pants": ("General Pants", "https://www.generalpants.com", "au-streetwear"),
    "zanerobe": ("Zanerobe", "https://zanerobe.com", "au-streetwear"),
    "venroy": ("Venroy", "https://venroy.com.au", "au-basics"),
    "commas": ("Commas", "https://commas.cc", "au-basics"),
    "art-club-and-friends": (
        "Art Club & Friends",
        "https://www.artclubandfriends.com",
        "art-merch",
    ),
    # --- More Australian breweries: local humour, drinkware-heavy. ---
    "bracket-brewing": ("Bracket Brewing", "https://www.bracketbrewing.com", "au-beer"),
    "wildflower": ("Wildflower Brewing", "https://www.wildflowerbeer.com", "au-beer"),
    "range-brewing": ("Range Brewing", "https://rangebrewing.com", "au-beer"),
    "deeds-brewing": ("Deeds Brewing", "https://deedsbrewing.com.au", "au-beer"),
    "hop-nation": ("Hop Nation", "https://www.hopnation.com.au", "au-beer"),
    # --- US heritage and blank-adjacent. ---
    "velva-sheen": ("Velva Sheen", "https://velvasheen.com", "americana"),
    "altru": ("Altru Apparel", "https://www.altruapparel.com", "americana"),
    "marine-layer": ("Marine Layer", "https://www.marinelayer.com", "americana"),
    # --- Skate remaining. ---
    "ripndip": ("RIPNDIP", "https://www.ripndip.com", "skate"),
    "awake-ny": ("Awake NY", "https://www.awakenyclothing.com", "streetwear"),
    # --- Streetwear, deep. The construction Shirtfaced actually uses -- heavyweight
    # blanks, boxy cuts, back prints -- is this tradition's grammar; the joke is
    # the content sitting on top of it. Both halves need evidence. ---
    "kith": ("Kith", "https://kith.com", "streetwear"),
    "bape": ("BAPE", "https://us.bape.com", "streetwear"),
    "neighborhood": ("Neighborhood", "https://neighborhood.jp", "streetwear"),
    "wtaps": ("WTAPS", "https://www.wtaps.com", "streetwear"),
    "undefeated": ("Undefeated", "https://undefeated.com", "streetwear"),
    "extra-butter": ("Extra Butter", "https://shop.extrabutterny.com", "streetwear"),
    "packer-shoes": ("Packer Shoes", "https://packershoes.com", "streetwear"),
    "kicks-lab": ("Kicks Lab", "https://www.kickslab.com", "streetwear"),
    "cherry-la": ("Cherry LA", "https://cherryla.com", "streetwear"),
    "gallery-dept": ("Gallery Dept", "https://gallerydept.com", "streetwear"),
    "corteiz": ("Corteiz", "https://corteiz.com", "streetwear"),
    "places-plus-faces": ("Places+Faces", "https://placesplusfaces.com", "streetwear"),
    "eric-emanuel": ("Eric Emanuel", "https://ericemanuel.com", "streetwear"),
    "chinatown-market": ("Chinatown Market", "https://www.chinatownmarket.com", "streetwear"),
    "noah-ny": ("Noah", "https://noahny.com", "streetwear"),
    "aime-leon-dore": ("Aimé Leon Dore", "https://aimeleondore.com", "streetwear"),
    "kidsuper": ("KidSuper", "https://kidsuper.com", "streetwear"),
    # --- Skate, deeper. ---
    "frog-skateboards": ("Frog Skateboards", "https://frogskateboards.com", "skate"),
    "limosine": ("Limosine", "https://limosineskateboards.com", "skate"),
    # --- Humour and slogan, deeper: the graphic is the joke. ---
    "snorg-tees": ("Snorg Tees", "https://snorgtees.com", "novelty"),
    "busted-tees": ("BustedTees", "https://bustedtees.com", "novelty"),
    "six-dollar-shirts": ("6 Dollar Shirts", "https://www.6dollarshirts.com", "novelty"),
    "the-chivery": ("The Chivery", "https://www.thechivery.com", "novelty"),
    "topatoco": ("TopatoCo", "https://topatoco.com", "novelty"),
    "bad-idea-tshirts": ("Bad Idea T-Shirts", "https://www.badideatshirts.com", "novelty"),
    "donkey-tees": ("Donkey Tees", "https://www.donkeytees.com", "novelty"),
    # --- Australian multi-label retailers with own-label graphic ranges. ---
    "stussy-au": ("Stüssy Australia", "https://www.stussy.com.au", "au-streetwear"),
    "universal-store": ("Universal Store", "https://www.universalstore.com.au", "au-streetwear"),
    "up-there": ("Up There Store", "https://uptherestore.com", "au-streetwear"),
    "incu": ("Incu", "https://incu.com", "au-streetwear"),
    # --- Global majors. The brief is "how the biggest brands present content",
    # so these carry the most weight in any presentation recommendation. Several
    # of the very largest (Nike, Adidas, Supreme, Levi's, Vans, Carhartt,
    # Patagonia, Uniqlo, Zara, H&M) run custom platforms that refuse automated
    # access outright, and are absent for that reason rather than by choice --
    # a known gap in the reference set, not a silent one. ---
    "palace": ("Palace Skateboards", "https://www.palaceskateboards.com", "major-skate"),
    "champion": ("Champion", "https://www.champion.com", "major-heritage"),
    "reebok": ("Reebok", "https://www.reebok.com", "major-sport"),
    "dickies-global": ("Dickies", "https://www.dickies.com", "major-workwear"),
    "billabong-global": ("Billabong", "https://www.billabong.com", "major-surf"),
    "quiksilver-global": ("Quiksilver", "https://www.quiksilver.com", "major-surf"),
    "rip-curl-global": ("Rip Curl", "https://www.ripcurl.com", "major-surf"),
    "oneill": ("O'Neill", "https://www.oneill.com", "major-surf"),
    "dc-shoes": ("DC Shoes", "https://www.dcshoes.com", "major-skate"),
    "etnies": ("Etnies", "https://www.etnies.com", "major-skate"),
    "emerica": ("Emerica", "https://www.emerica.com", "major-skate"),
    "jack-wolfskin": ("Jack Wolfskin", "https://www.jackwolfskin.com", "major-outdoor"),
}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _fetch(url: str, timeout: int = 25) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


# Garment words trailing a product handle. Many brands sell one artwork across a
# whole garment range -- Threadheads' first twelve matches were three designs on
# four garments each -- and for a corpus about graphic construction that is 4x
# redundancy, not 4x evidence.
GARMENT_SUFFIX = re.compile(
    r"[-_ ]*(oversized[-_ ]?)?(t[-_ ]?shirt|tee|hoodie|sweatshirt|sweater|crew(neck)?|"
    r"jumper|long[-_ ]?sleeve|pullover|jersey)s?$",
    re.IGNORECASE,
)


def _design_key(handle: str) -> str:
    """The artwork a handle belongs to, with its garment suffix removed.

    ``lets-start-a-cult-hoodie`` and ``lets-start-a-cult-t-shirt`` are one design.
    Handles with no garment suffix are returned unchanged and so stay distinct.
    """
    stripped = GARMENT_SUFFIX.sub("", handle).strip("-_ ")
    return stripped or handle


def collect_brand(slug: str, name: str, site_url: str, tradition: str) -> dict[str, Any]:
    """Collect one brand. Returns a result row; never raises on network failure."""
    try:
        raw = _fetch(f"{site_url}/products.json?limit=250")
        products = json.loads(raw).get("products", [])
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError) as error:
        return {
            "brand_slug": slug,
            "status": "skipped",
            "reason": f"{type(error).__name__}: {error}",
        }

    if not products:
        return {"brand_slug": slug, "status": "skipped", "reason": "no products returned"}

    candidates = [p for p in products if _is_graphic_led(p) and p.get("images")]
    if not candidates:
        return {
            "brand_slug": slug,
            "status": "skipped",
            "reason": "no graphic-led products matched",
        }

    # One product per artwork. Keeps the first garment carrying each design, so a
    # brand contributes eighteen designs rather than three designs six times over.
    deduped: list[dict[str, Any]] = []
    seen_designs: set[str] = set()
    for product in candidates:
        key = _design_key(product.get("handle") or "")
        if key in seen_designs:
            continue
        seen_designs.add(key)
        deduped.append(product)

    # Spread the sample across product types rather than taking whatever the store
    # happens to list first. Threadheads' first eighteen deduped products were
    # eighteen sweatshirts; Culture Kings lists 144 caps before most of its tees.
    # Round-robin by type gives headwear, drinkware and accessories a place in the
    # sample without hard-coding what share each should get.
    by_type: dict[str, list[dict[str, Any]]] = {}
    for product in deduped:
        by_type.setdefault((product.get("product_type") or "unknown").lower(), []).append(product)

    wanted = []
    while len(wanted) < PRODUCTS_PER_BRAND and any(by_type.values()):
        for bucket in by_type.values():
            if bucket and len(wanted) < PRODUCTS_PER_BRAND:
                wanted.append(bucket.pop(0))

    brand_dir = CORPUS_ROOT / slug
    (brand_dir / "products").mkdir(parents=True, exist_ok=True)
    (brand_dir / "brand.json").write_text(
        json.dumps(
            {
                "brand_slug": slug,
                "brand_name": name,
                "site_url": site_url,
                "design_tradition": tradition,
                "acquired_at": _now(),
                "notes": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    product_count = 0
    image_count = 0
    for product in wanted[:PRODUCTS_PER_BRAND]:
        handle = product.get("handle") or str(product.get("id"))
        product_dir = brand_dir / "products" / handle
        product_dir.mkdir(parents=True, exist_ok=True)

        saved_images: list[str] = []
        provenance: list[dict[str, Any]] = []
        for index, image in enumerate(product.get("images", [])[:IMAGES_PER_PRODUCT], start=1):
            src = image.get("src")
            if not src:
                continue
            # Shopify's CDN resizes on request. Originals run to 12MB PNGs, which is
            # tens of gigabytes across the corpus and no more design information: the
            # graphic, its silhouette and its type are all legible well below that.
            sized = f"{src}{'&' if '?' in src else '?'}width={IMAGE_WIDTH}"
            try:
                data = _fetch(sized)
            except (urllib.error.URLError, TimeoutError, OSError):
                continue

            extension = ".png" if src.split("?")[0].lower().endswith(".png") else ".jpg"
            filename = f"image-{index:02d}{extension}"
            (product_dir / filename).write_bytes(data)
            saved_images.append(filename)
            provenance.append(
                {
                    "provenance_id": f"{slug}/{handle}/image-{index:02d}",
                    "source_id": f"{slug}/{handle}",
                    "acquired_at": _now(),
                    "acquisition_method": "shopify_products_json",
                    "content_hash": f"sha256:{hashlib.sha256(data).hexdigest()}",
                    "byte_size": len(data),
                    "content_type": "image/png" if extension == ".png" else "image/jpeg",
                    "shot_hint": _shot_hint(src),
                    # The URL actually fetched, width parameter included -- the hash
                    # above is of this response, not of the unresized original.
                    "source_url": sized,
                }
            )
            time.sleep(REQUEST_DELAY)

        if not saved_images:
            continue

        variants = product.get("variants") or [{}]
        (product_dir / "product.json").write_text(
            json.dumps(
                {
                    "product_id": f"{slug}/{handle}",
                    "brand_slug": slug,
                    "name": product.get("title", ""),
                    "source_url": f"{site_url}/products/{handle}",
                    "category": (product.get("product_type") or "").lower() or "unknown",
                    "price": str(variants[0].get("price") or ""),
                    "description": _strip_html(product.get("body_html", ""))[:2000],
                    "images": saved_images,
                    "acquired_at": _now(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (product_dir / "provenance.json").write_text(
            json.dumps(provenance, indent=2), encoding="utf-8"
        )

        product_count += 1
        image_count += len(saved_images)

    if product_count == 0:
        return {"brand_slug": slug, "status": "skipped", "reason": "no images could be downloaded"}

    return {
        "brand_slug": slug,
        "status": "collected",
        "product_count": product_count,
        "image_count": image_count,
    }


def write_manifest(results: list[dict[str, Any]]) -> None:
    """Built once, after collection — never by a collector, to avoid racing writers."""
    CORPUS_ROOT.mkdir(parents=True, exist_ok=True)
    (CORPUS_ROOT / "manifest.json").write_text(
        json.dumps(
            {
                "generated_at": _now(),
                "brands": [
                    {
                        "brand_slug": r["brand_slug"],
                        "product_count": r["product_count"],
                        "image_count": r["image_count"],
                    }
                    for r in results
                    if r["status"] == "collected"
                ],
                "skipped": [
                    {"brand_slug": r["brand_slug"], "reason": r["reason"]}
                    for r in results
                    if r["status"] == "skipped"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main(argv: list[str]) -> int:
    selected = argv[1:] or list(BRANDS)
    unknown = [slug for slug in selected if slug not in BRANDS]
    if unknown:
        print(f"Unknown brand slug(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    results = []
    for slug in selected:
        name, site_url, tradition = BRANDS[slug]
        result = collect_brand(slug, name, site_url, tradition)
        results.append(result)
        if result["status"] == "collected":
            print(
                f"  {slug:<28} {result['product_count']:>3} products  "
                f"{result['image_count']:>3} images"
            )
        else:
            print(f"  {slug:<28} skipped — {result['reason'][:70]}")

    write_manifest(results)

    collected = [r for r in results if r["status"] == "collected"]
    print(
        f"\n{len(collected)}/{len(results)} brands, "
        f"{sum(r['product_count'] for r in collected)} products, "
        f"{sum(r['image_count'] for r in collected)} images"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
