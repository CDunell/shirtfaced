/**
 * Left sidebar shell, replacing the hamburger-at-every-width header (see
 * docs/ADMIN_STUDIO_UI_OVERHAUL_PLAN.md Phase 1). Mirrors Admin's own
 * Sidebar.tsx pattern so the two apps share one shape, not two independently
 * invented ones: Admin and Studio sit as a symmetric, always-visible pair
 * pinned at the bottom -- Studio shown active here, Admin linking out (the
 * exact reverse of Admin's own sidebar).
 */
import { useState } from "react";
import { cx } from "./ui";

const ADMIN_URL = "https://admin.shirtfaced.wtf";

const iconBase = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  width: 24,
  height: 24,
  "aria-hidden": true,
};
const IconMenu = () => (
  <svg {...iconBase}>
    <path d="M3.5 7h17M3.5 12h17M3.5 17h17" />
  </svg>
);
const IconClose = () => (
  <svg {...iconBase}>
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
);

const navItemClass = (active: boolean) =>
  cx(
    "press block appearance-none cursor-pointer rounded-[14px] px-3 py-2.5 text-left font-sans text-[13px] font-semibold tracking-wide uppercase no-underline",
    active ? "bg-ink text-paper" : "bg-transparent text-ink hover:bg-paper-2",
  );

export interface SidebarPipeline<Pipeline extends string> {
  id: Pipeline;
  label: string;
  blurb: string;
}
export interface SidebarView<View extends string, Pipeline extends string> {
  id: View;
  label: string;
  pipeline: Pipeline;
}

export function Sidebar<View extends string, Pipeline extends string>({
  pipelines,
  views,
  currentView,
  onPick,
  themeName,
  onToggleTheme,
}: {
  pipelines: SidebarPipeline<Pipeline>[];
  views: SidebarView<View, Pipeline>[];
  currentView: View;
  onPick: (id: View) => void;
  themeName: "light" | "dark";
  onToggleTheme: () => void;
}): React.JSX.Element {
  // Unlike Admin's Sidebar, currentView here is plain useState, not a router
  // pathname -- there's no back/forward navigation to catch, so closing the
  // drawer only needs to happen at the one place it's actually opened from.
  const [open, setOpen] = useState(false);

  const pick = (id: View) => {
    onPick(id);
    setOpen(false);
  };

  const body = (
    <>
      <span className="wordmark block px-4 pt-6 pb-3 text-[22px] text-ink dark:text-paper">
        shirtfaced / studio
      </span>

      <nav className="flex flex-1 flex-col gap-4 overflow-y-auto px-3 py-2">
        {pipelines.map((pipeline) => (
          <div key={pipeline.id} className="flex flex-col gap-1">
            <span className="px-3 text-[10px] font-bold tracking-[0.12em] text-ink/50 uppercase dark:text-paper/50">
              {pipeline.label} — {pipeline.blurb}
            </span>
            {views
              .filter((v) => v.pipeline === pipeline.id)
              .map((v) => (
                <button
                  key={v.id}
                  onClick={() => {
                    pick(v.id);
                  }}
                  className={navItemClass(currentView === v.id)}
                >
                  {v.label}
                </button>
              ))}
          </div>
        ))}
      </nav>

      <div className="px-3 pt-2">
        <button
          onClick={onToggleTheme}
          className="press flex h-11 w-full items-center justify-center rounded-[14px] border border-ink/15 text-[13px] font-semibold tracking-wide text-ink/70 uppercase hover:bg-paper-2 dark:border-paper/15 dark:text-paper/70 dark:hover:bg-white/5"
        >
          {themeName === "light" ? "Dark theme" : "Light theme"}
        </button>
      </div>

      {/* Pinned bottom: Admin | Studio, symmetric peers -- Admin's own sidebar
          mirrors this exact pair the other way round. */}
      <div className="mt-2 border-t border-ink/10 p-3 dark:border-paper/10">
        <div className="flex gap-1 rounded-[14px] bg-paper-2 p-1 dark:bg-white/5">
          <a
            href={ADMIN_URL}
            className="press flex-1 rounded-[10px] px-3 py-2 text-center text-[12px] font-bold tracking-wide text-ink/60 uppercase hover:bg-paper dark:text-paper/60 dark:hover:bg-white/10"
          >
            Admin
          </a>
          <span className="flex-1 rounded-[10px] bg-ink px-3 py-2 text-center text-[12px] font-bold tracking-wide text-paper uppercase dark:bg-paper dark:text-ink">
            Studio
          </span>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile top bar -- the sidebar collapses into a drawer below sm */}
      <div className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-ink/10 bg-paper px-4 sm:hidden dark:border-paper/10 dark:bg-ink">
        <span className="wordmark text-[22px] text-ink dark:text-paper">shirtfaced / studio</span>
        <button
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="studio-sidebar-drawer"
          onClick={() => {
            setOpen((x) => !x);
          }}
          className="grid h-11 w-11 place-items-center border-0 bg-transparent text-ink dark:text-paper"
        >
          {open ? <IconClose /> : <IconMenu />}
        </button>
      </div>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex bg-ink/40 sm:hidden"
          onClick={() => {
            setOpen(false);
          }}
        >
          <aside
            id="studio-sidebar-drawer"
            className="fade-rise flex h-full w-72 flex-col bg-paper dark:bg-ink"
            onClick={(event) => {
              event.stopPropagation();
            }}
          >
            {body}
          </aside>
        </div>
      ) : null}

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-ink/10 sm:flex dark:border-paper/10">
        {body}
      </aside>
    </>
  );
}
