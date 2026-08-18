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
**Master:** approved 1365×768 master, SHA-256 `7fd91e38bc021298cc563f0c41e95d89e2ca5ef995bcb22eaa430258a2376e88`.  
**Delivery:** vertical 9:16 social edit assembled in post from several short Veo takes.  
**Raw take policy:** approximately **6 seconds per shot**; a 1.5–4 second keeper fragment is a successful take.  
**Audio:** discard/strip generated audio and build one continuous pub/band/crowd sound bed in post.

### Coverage rule — locked 19 August 2026

W01-P28 source-still discovery is finished. Do not issue further Nano source-coverage calls for this scene by default.

Repeated Damo/cue generations were provider-filtered. Subsequent non-Damo contact-sheet tests cleared the filter but did not reliably obey the requested 3×3/panel mapping. The approved master already contains the needed observations, so A/B/C/D now use deterministic exact-pixel crops from that master and E reuses A.

A deterministic crop changes framing only. It does not regenerate the pub, characters, crowd, lighting or props. Every derived frame records the parent-master SHA256 and its own frame SHA256. All current frames remain `approved_for_veo=false` until the owner's explicit approval decision.

The detailed active authority is `shots/W01-P28.md` §2.1.

### Shot package

| Shot | Raw target | Locked 9:16 source | Purpose / expected keeper |
| --- | ---: | --- | --- |
| **W01-P28-A — Wide discovery** | 6s | `w01-p28-a-wide-discovery` — x233/y0, 432×768, frame `f191a3c2…` | Establish that the room is already going off; viewer discovers Damo on the table. Expect ~2.5–4s usable. |
| **W01-P28-B — Damo close** | 6s | `w01-p28-b-damo-close` — x340/y0, 288×512, frame `b122de47…` | Brief identity/performance hit; face, upper body and cue dominate without turning into a portrait. Expect ~1.5–2.5s usable. |
| **W01-P28-C — Emma + Brock cutaway** | 6s | `w01-p28-c-emma-brock-crowd` — x816/y0, 432×768, frame `ef9eef28…` | Prove the room exists independently of Damo. Bar-side recurring crowd action stays inside the same master world. Expect ~2–3s usable. |
| **W01-P28-D — Band / crowd source** | 6s | `w01-p28-d-band-room-energy` — x700/y0, 432×768, frame `2f1328af…` | Reset attention to the actual musical source through crowd bodies, hands and drinks. Expect ~1.5–3s usable. |
| **W01-P28-E — Return wide / collision** | reuse A | Later keeper range from A; no second source still | Return to the incident with the same room/crowd continuity. Expect ~2–4s usable. |

### Editorial intent

Likely cut rhythm, adjusted after reviewing actual keeper ranges:

`A wide discovery -> B Damo close -> C Emma/Brock -> D band/crowd -> E return wide`

The finished scene is expected to be roughly **10–15 seconds**, assembled from the strongest moments rather than five complete six-second takes. Cuts may be abrupt; continuous post sound is what makes them feel like simultaneous observations of the same 11:05pm event.

### Motion constraints shared by all takes

- The scene already exists before the camera observes it.
- Background people continue independent pre-existing actions.
- No crowd semicircle or audience formation around Damo.
- Band remains the performance source; Damo remains a punter.
- No invented tattoos, jewellery, signage, people or hero lighting.
- Camera motion stays small and physically motivated: handheld sway, crowd bump, obstruction, imperfect reframe.
- Do not ask Veo to cut, teleport camera position, explain the whole room or manufacture an ending.
- Preserve the exact world and identities visible in each approved source frame rather than reconstructing the scene.

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
