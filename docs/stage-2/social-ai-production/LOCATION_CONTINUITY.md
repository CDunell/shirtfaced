# shirtfaced — Location Continuity Contract

**Status:** ACTIVE contract  
**Scope:** Persistent generated locations and spatial continuity across campaign media

---

## 1. Purpose

Locations are persistent production entities. A servo, pub, motel pool, suburban street or carpark is not re-invented independently for every angle.

The system must be able to answer:

- where the scene takes place
- which visual/spatial facts are locked
- which environmental facts may change
- which references define the location
- how adjacent shots relate spatially

---

## 2. Canonical location record

A location belongs to one campaign and should carry:

- UUID
- campaign FK
- stable location code/name
- description
- geographic/environment intent
- interior/exterior
- fixed architecture
- fixed props/signage
- entrances/exits
- practical light sources
- default time/lighting state
- reference media assets
- floorplan/spatial JSONB where useful
- allowed variation
- forbidden drift

---

## 3. Spatial truth

For multi-angle scenes persist enough information to preserve:

- relative position of doors/windows/counters/roads/vehicles
- left/right relationships
- main movement axis
- camera-side/screen-direction constraints
- prop positions
- light-source positions
- foreground obstruction opportunities

The contract is not CAD. It is the minimum stable spatial truth needed to stop generated coverage contradicting itself.

---

## 4. Environmental state

Scene-level state may vary from the location default:

- time of day
- weather
- wet/dry surfaces
- crowd density
- open/closed signage state
- lighting practicals on/off
- vehicle presence
- temporary props
- damage/mess progression

The scene records these changes. The location record remains the persistent identity.

---

## 5. Reference hierarchy

Purpose-tag location references:

- establishing exterior
- establishing interior
- reverse angle
- key architectural detail
- floorplan/spatial reference
- lighting-state reference
- approved prior shot

A prior generated shot does not automatically become canon. It becomes a continuity reference only when selected/approved for that purpose.

---

## 6. Location review dimensions

Applicable world-review gates may include:

- location identity match
- architectural geometry consistency
- fixed-prop continuity
- screen-direction consistency
- environment/time state
- lighting-source continuity
- weather/surface continuity
- vehicle position/identity where relevant
- prohibited branding/signage

Unexplained location rearrangement is a continuity failure even if the individual shot looks plausible.

---

## 7. Generation-ready requirement

A scene-bound campaign shot cannot be generation-ready if its required location identity or state is unresolved.

Non-scene campaign shots still resolve location when the shot claims one; environmental plates and inserts may intentionally be location-neutral only when specified that way.
