/**
 * Application shell.
 *
 * Thirteen destinations in two pipelines, rendered through the shared Sidebar
 * (Phase 1 of docs/ADMIN_STUDIO_UI_OVERHAUL_PLAN.md) -- previously a
 * hamburger-at-every-width header held them; that panel and its icons moved
 * into Sidebar.tsx, which Admin's own sidebar now mirrors the shape of.
 */
import { useState } from "react";
import { useSyncDarkClass } from "./components/ui";
import { Sidebar } from "./components/Sidebar";
import { WorkBench } from "./components/WorkBench";
import { DesignsBench } from "./components/DesignsBench";
import { DesignPromptBench } from "./components/DesignPromptBench";
import { DesignGalleryBench } from "./components/DesignGalleryBench";
import { EmailBench } from "./components/EmailBench";
import { VintageEvidenceBench } from "./components/VintageEvidenceBench";
import { VintageResearchBench } from "./components/VintageResearchBench";
import { PromptWorkbench } from "./components/PromptWorkbench";
import { ServiceStatus } from "./components/ServiceStatus";
import { SocialBench } from "./components/SocialBench";
import { WorldPage } from "./components/WorldPage";
import { CastBench } from "./components/CastBench";
import { ScenesBench } from "./components/ScenesBench";
import { LocationsBench } from "./components/LocationsBench";
import type { WorkItem } from "./api/concepts";
import type { ThemeName } from "./theme";
export interface AppProps {
  themeName: ThemeName;
  onToggleTheme: () => void;
}
type View =
  | "design-prompt"
  | "design-gallery"
  | "work"
  | "prompts"
  | "concepts"
  | "evidence"
  | "research"
  | "cast"
  | "locations"
  | "scenes"
  | "social"
  | "email"
  | "dashboard";
/** Which pipeline a destination belongs to.
 *
 * Phase 2a of DESIGN_FLOW_PLAN.md. The 14 August audit's largest structural
 * finding was two pipelines interleaved in one interface, and that it is the
 * first thing a person hits: ten destinations in one row, in no order, with
 * nothing saying that Prompts and Social are world work and Designs and Score
 * are product work.
 *
 * This does not move anything. Relocating world screens is Phase 2b and waits
 * on the campaign UI shape (session handover §4.3). Grouping what is already
 * here depends on nothing anyone else is building, and answers the question a
 * newcomer actually has.
 */
type Pipeline = "product" | "world";

const PIPELINES: { id: Pipeline; label: string; blurb: string }[] = [
  {
    id: "product",
    label: "Product",
    blurb: "Evidence to a printed design.",
  },
  {
    id: "world",
    label: "World",
    blurb: "Canon to a photograph to a customer.",
  },
];

const VIEWS: { id: View; label: string; pipeline: Pipeline }[] = [
  // The direct tool: an idea in, a paste-ready generation prompt out. No
  // brief, no queue, no review -- everything Designs below also does, minus
  // all of it. Leads the list because it answers what most people actually
  // want on the first visit.
  { id: "design-prompt", label: "Prompt", pipeline: "product" },
  // Every concept a batch actually rendered and someone looked at -- proof,
  // not a live feed. Sits next to Prompt because it answers the question
  // Prompt's "hit and miss by nature" line raises: hit and miss how, exactly.
  { id: "design-gallery", label: "Gallery", pipeline: "product" },
  // Product: evidence → research → concept → design → approved version → print.
  // Work leads because it is the answer to "what should I be doing", and the
  // other destinations are where its rows send you.
  { id: "work", label: "Work", pipeline: "product" },
  { id: "evidence", label: "Evidence", pipeline: "product" },
  { id: "research", label: "Research", pipeline: "product" },
  // Compose and Score used to be destinations here. Phase 5 folded them into
  // Designs: they are steps of one journey, not places to go.
  { id: "concepts", label: "Designs", pipeline: "product" },
  // World: canon → shot → photograph → decision → social → customer.
  { id: "dashboard", label: "Dashboard", pipeline: "world" },
  { id: "prompts", label: "Prompts", pipeline: "world" },
  // Cast comes before Prompts' output in the order the work happens: a shot
  // cannot lock an identity that has no approved reference.
  { id: "cast", label: "Cast", pipeline: "world" },
  // Locations then Scenes, in the order the work happens: a scene is built into
  // a place, and its coverage is cut from the master that results.
  { id: "locations", label: "Locations", pipeline: "world" },
  { id: "scenes", label: "Scenes", pipeline: "world" },
  // Print was here. It printed a design onto a photograph by dragging four
  // corners onto the garment, and the owner's account of it is that it never
  // got off the ground and was replaced by defined zones. The zone-based print
  // lives inside Designs and reads the approved version. Removed 15 August 2026.
  { id: "social", label: "Social", pipeline: "world" },
  { id: "email", label: "Email", pipeline: "world" },
];
export function App({ themeName, onToggleTheme }: AppProps): React.JSX.Element {
  // Mirrors themeName onto <html class="dark"> for Tailwind's dark: variant.
  // Base Web components keep taking their theme from BaseProvider in
  // main.tsx directly -- this only covers the Tailwind-rebuilt chrome.
  useSyncDarkClass(themeName);
  // Work is the front door: it is the one screen that answers what to do
  // without knowing which screen owns what.
  const [view, setView] = useState<View>("work");
  // What Work sent us to, so Designs can open straight onto it. Cleared once
  // consumed, so navigating away and back does not silently re-open it.
  const [focus, setFocus] = useState<{ conceptId: string; attemptId: string | null } | null>(null);
  return (
    <div className="min-h-screen bg-paper sm:flex dark:bg-ink">
      <Sidebar
        pipelines={PIPELINES}
        views={VIEWS}
        currentView={view}
        onPick={setView}
        themeName={themeName}
        onToggleTheme={onToggleTheme}
      />
      <main className="min-w-0 flex-1 px-4 py-9">
        <div className="mx-auto max-w-5xl">
        {view === "design-prompt" ? (
          <DesignPromptBench />
        ) : view === "design-gallery" ? (
          <DesignGalleryBench />
        ) : view === "work" ? (
          <WorkBench
            onOpen={(item: WorkItem) => {
              // Every row lands on the screen that can actually do the thing.
              setFocus({ conceptId: item.concept_id, attemptId: item.attempt_id });
              setView("concepts");
            }}
          />
        ) : view === "prompts" ? (
          <PromptWorkbench />
        ) : view === "concepts" ? (
          <DesignsBench
            focus={focus}
            onFocusConsumed={() => {
              setFocus(null);
            }}
          />
        ) : view === "evidence" ? (
          <VintageEvidenceBench />
        ) : view === "research" ? (
          <VintageResearchBench />
        ) : view === "cast" ? (
          <CastBench />
        ) : view === "locations" ? (
          <LocationsBench />
        ) : view === "scenes" ? (
          <ScenesBench />
        ) : view === "social" ? (
          <SocialBench />
        ) : view === "email" ? (
          <EmailBench />
        ) : (
          <>
            <h1 className="display text-ink dark:text-paper">Dashboard</h1>
            <p className="text-[15px] leading-relaxed text-ink/80 dark:text-paper/80">
              A private production tool for building coherent Shirtfaced photographic worlds.
            </p>
            <WorldPage />
            <ServiceStatus />
          </>
        )}
        </div>
      </main>
    </div>
  );
}
