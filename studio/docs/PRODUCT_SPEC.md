# Product Specification

## Product

**Shirtfaced Studio**

A private creative production tool for generating, reviewing and preserving coherent Shirtfaced photographic campaigns.

## Primary outcome

The user can type or click:

> Continue Shirtfaced World 1.

The system chooses the next valid shot and completes the preparation, generation and review workflow without requiring the user to restate the world rules.

## User

One creative director and brand owner.

## Core principles

### Canon before prompt

The world definition governs every prompt.

### Memory is explicit

Continuity must come from stored state, not conversational memory.

### Human approval is final

Models propose. The user decides.

### Every image teaches the system

Approved and rejected images update continuity. Only approved reusable rules update canon.

### Product is incidental

The photograph must work without Shirtfaced placement.

### Existing Oracle deployment

The application will run in the user's existing Oracle Cloud environment.

Operational state is stored in the existing PostgreSQL database.

Development may run locally, but production assumptions must match PostgreSQL and persistent Oracle-hosted deployment.

## Main entities

- World
- Canon document
- Continuity document
- Shot
- Prompt plan
- Generation attempt
- Image asset
- Automated review
- Human decision
- Canon proposal
- Reference image
- Audit event

## Main screens

### Dashboard

Shows:

- active worlds;
- next planned shot;
- current hero-product rotation;
- recent approved images;
- pending decisions;
- approximate API spend.

### World page

Shows:

- world title and status;
- canon;
- continuity;
- shotlist;
- rotation state;
- reference images;
- rejected drift;
- **Continue World** action.

### Generation page

Shows:

- generated image;
- production prompt;
- selected shot;
- hero product;
- camera perspective;
- automated verdict;
- successes;
- drift;
- proposed permanent rules;
- approve, reject and variation actions.

### History

Shows all attempts and decisions with filters for:

- approved;
- rejected;
- pending;
- reference;
- scene;
- hero product;
- camera position.

## User actions

- Continue world.
- Approve image.
- Reject image with a reason.
- Request variation with instructions.
- Promote approved image to reference.
- Approve or reject a canon proposal.
- Edit planned shot metadata.
- Add a shot manually.
- Disable a shot.
- Export world state.

## Next-shot selection

Version 1 selection is deterministic.

Select the first eligible planned shot ordered by:

1. explicit priority ascending;
2. sequence ascending;
3. creation time ascending.

A shot is ineligible when:

- disabled;
- already approved;
- currently generating;
- blocked by a dependency;
- it repeats the immediately preceding hero product when another eligible option exists;
- it repeats the immediately preceding camera perspective when another eligible option exists.

The selector must record why the shot was selected.

## Review outcomes

Automated review:

- `approved`
- `approved_with_note`
- `rejected`

Human decision:

- `approved`
- `rejected`
- `variation_requested`

The automated verdict never substitutes for the human decision.

## Success criteria

- One-command generation works.
- State survives restart.
- The selected shot is explainable.
- Product and camera rotation are visible.
- No canonical update occurs without approval.
- Every generated image is traceable to its prompt, model settings and source world version.
- Rejected attempts remain available for learning and audit.
