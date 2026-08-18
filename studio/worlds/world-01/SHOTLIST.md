# SHIRTFACED --- WORLD 01 SHOTLIST

## Purpose

This is the authoritative production backlog and scene-status register for World 01.

It prevents repetition, balances hero products and camera positions, and ensures the visual universe expands rather than circles back on itself.

Generation-attempt history belongs in `CONTINUITY.md`; a rejected attempt does not automatically reject its scene.

------------------------------------------------------------------------

## Status

-   ⬜ Planned
-   🟡 In Progress
-   ✅ Approved
-   ❌ Rejected

------------------------------------------------------------------------

  ID        Scene                     Hero Product   Camera              Status
  --------- ------------------------- -------------- ------------------- --------
  W01-001   Walking between venues    T-shirt        Across street       ✅
  W01-002   Kebab shop                Mixed          Across street       ✅
  W01-003   Servo stop                Mixed          Across forecourt    ✅
  W01-004   Pedestrian crossing       Mixed          Opposite footpath   ✅
  W01-005   Beer garden               T-shirt        Nearby table        ✅
  W01-006   House-party kitchen       Hoodie         Dining room         ✅
  W01-007   Fast-food car park        Hoodie         Across car park     ✅
  W01-008   Bottle shop after close   Mixed          Across road         ❌
  W01-009   Apartment arrival         Cap            Front gate          ✅
  W01-010   Lookout                   Cap            Beside parked car   ✅
  W01-011   Kerbside window chat      T-shirt        Footpath at window  ✅
  W01-012   Apartment lobby           Hoodie waist   From the entrance   ✅
  W01-013   Apartment balcony back view  T-shirt     Inside lounge       ✅
  W01-014   Kitchen kick-ons II       Hoodie waist   Facing from hall    ✅
  W01-015   Sunrise balcony           Hoodie         Balcony doorway     ⬜
  W01-016   Servo breakfast run       Cap            Inside servo        ⬜
  W01-017   Bakery queue              T-shirt        Behind queue        ⬜
  W01-018   Beach sunrise detour      Cap            Dune path           ⬜
  W01-019   Bunnings sausage stop     Hoodie         Carpark             ⬜
  W01-020   Sunday recovery café      Cap            Window seat         ⬜

### W01-010 location note

The approved lookout scene is location-generic. Historical reference material may have called it a `City lookout`; do not reproduce an identifiable skyline, landmark or city-specific signature. Current `WORLD.md` location canon wins.

------------------------------------------------------------------------

## W01-P28 — 11:05pm live-music/pool-table sequence

**Status:** 🟡 In Progress  
**Master:** one approved 16:9 world master is the spatial source of truth.  
**Delivery:** vertical 9:16 social edit assembled in post from several short Veo takes.  
**Raw take policy:** generate approximately **6 seconds per shot**; do not require all 6 seconds to survive the edit. A 1.5–4 second keeper fragment is a successful take.  
**Audio:** generated audio is discarded/stripped. Build one continuous pub/band/crowd sound bed in post so cuts remain inside the same event.

### Coverage rule

Every clip resolves its source still before Veo; Veo does not choose scene coverage. The active W01-P28 path is now hybrid because repeated paid Nano full-scene coverage attempts containing Damo's pool-table action were output-filtered by Google even after neutral billiards wording.

- **A — Wide discovery** and **B — Damo close:** deterministic original-pixel 9:16 crop/reframe from the currently approved 16:9 master -> checksum -> human approval -> Veo first-frame I2V.
- **C — Emma + Brock** and **D — Band / crowd source:** approved master + only relevant identity refs -> explicitly selected `W01-P28Z-non-damo.nano-banana-coverage.txt` -> reviewed scene contact sheet -> selected-panel extraction -> human approval -> Veo first-frame I2V.
- **E — Return wide:** reuse A when the motion contains a strong return range. If a genuinely different return is required, derive another original-pixel master crop rather than buying another Damo/cue image regeneration.

A deterministic crop changes framing only. It does not regenerate the pub, characters, crowd, lighting or props. Every derived frame records the parent-master SHA256 and its own crop/frame SHA256. A Nano non-Damo observation also remains subordinate to the same master and does not remove Damo from the event; its phone simply faces another part of the room.

The detailed active authority is `shots/W01-P28.md` §2.1. Do not issue another paid full-scene Nano retry with Damo/cue coverage merely to rephrase the same action.

### Shot package

| Shot | Raw target | 9:16 source / focus | Purpose / expected keeper |
| --- | ---: | --- | --- |
| **W01-P28-A — Wide discovery** | 6s | Approved original-pixel master crop: Damo + full pool-table incident, retaining band and surrounding crowd | Establish that the room is already going off; viewer discovers Damo on the table. Expect ~2.5–4s usable. |
| **W01-P28-B — Damo close** | 6s | Tighter approved original-pixel crop from the same master: face, upper body, cue overhead, enough neighbouring bodies/geography to stay documentary | Brief identity/performance hit. Head back, eyes shut, roaring; no hero re-staging. Expect ~1.5–2.5s usable. |
| **W01-P28-C — Emma + Brock cutaway** | 6s | Approved extracted panel from the explicit non-Damo Nano coverage family, using Emma/Brock identity refs only as needed | Prove the room exists independently of Damo. They continue their own pre-existing behaviour, not a reaction shot staged for him. Expect ~2–3s usable. |
| **W01-P28-D — Band / crowd source** | 6s | Approved extracted band/room panel from the explicit non-Damo coverage family; no Damo identity ref required | Reset attention away from Damo, add rhythm and explain what everyone is actually singing to. Expect ~1.5–3s usable. |
| **W01-P28-E — Return wide / collision** | 6s | Prefer later keeper range from A; otherwise another approved original-pixel window across pool table + foreground crowd | Return to the incident with foreground obstruction, crowd surge or a small phone bump; leave on energy rather than a generated ending. Expect ~2–4s usable. |

### Editorial intent

Likely cut rhythm, adjusted after reviewing actual keeper ranges:

`A wide discovery -> B Damo close -> C Emma/Brock -> D band/crowd -> E return wide`

The finished scene is expected to be roughly **10–15 seconds**, assembled from the strongest moments rather than five complete six-second takes. Cuts may be abrupt; continuous post sound is what makes them feel like simultaneous observations of the same 11:05pm event.

### Motion constraints shared by all five takes

- The scene already exists before the camera observes it.
- Background people continue independent pre-existing actions.
- No crowd semicircle or audience formation around Damo.
- Band remains the performance source; Damo remains a punter.
- No invented tattoos, jewellery, signage, people or hero lighting.
- Camera motion stays small and physically motivated: handheld sway, crowd bump, obstruction, imperfect reframe.
- Do not ask Veo to cut, teleport camera position, explain the whole room or manufacture an ending.

------------------------------------------------------------------------

## Rotation Rules

Before selecting the next scene:

1. Use the highest-priority Planned scene unless continuity requires otherwise.
2. Rotate hero products evenly.
3. Avoid repeating the previous camera position.
4. Introduce one new environment every 3--5 approved scenes.
5. Reject any scene that repeats an existing emotional beat.
6. Resolve recurring cast identity and applicable appearance state before an identity-critical shot becomes generation-ready.
7. Treat rejected generation attempts as attempt history in `CONTINUITY.md`; update this file only when the scene itself changes status.

------------------------------------------------------------------------

## Future Buckets

### Night Out

- Taxi rank
- Pool table
- Live music
- Rooftop
- Motel

### Transition

- Apartment/building lobby
- Stairwell
- Kerbside window
- Petrol station
- Walk home

Small enclosed spaces should normally be converted to their larger social context: use a lobby rather than putting the group inside a lift, and kerb/window interaction rather than staging the group inside a car cabin.

### Kick-ons

- Balcony
- Lounge room
- Backyard firepit
- Kitchen round two

### Morning After

- Servo coffee
- Bakery
- Beach
- Fish and chips
- Corner café
