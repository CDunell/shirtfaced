import { Card } from "@/components/ui";
import { PromptWorkbench } from "@/components/PromptWorkbench";
import { fetchShots, fetchWorlds, StudioUnavailable, type StudioShot } from "@/lib/studio";

// Prompts are written fresh from the current canon on every request, so there is
// nothing here worth caching.
export const dynamic = "force-dynamic";

export default async function PromptsPage() {
  let worlds;
  try {
    worlds = await fetchWorlds();
  } catch (cause) {
    return (
      <div className="flex flex-col gap-6">
        <h1 className="display text-[40px]">Prompts</h1>
        <Card className="border-coral bg-coral/10">
          <p className="text-[14px]">
            {cause instanceof StudioUnavailable
              ? cause.message
              : "Studio could not be reached."}
          </p>
          <p className="mt-2 text-[13px] text-ink/50">
            Studio is a separate service. Admin holds no world documents and no
            OpenAI key; it asks Studio for the prompt and shows the answer.
          </p>
        </Card>
      </div>
    );
  }

  const shotsByWorld: Record<string, StudioShot[]> = {};
  for (const world of worlds) {
    const detail = await fetchShots(world.slug);
    shotsByWorld[world.slug] = [...detail.shots].sort((a, b) => a.sequence - b.sequence);
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="display text-[40px]">Prompts</h1>
        <p className="mt-1 text-[13px] text-ink/50">
          Writes the prompt the canon implies. Generates nothing, records nothing.
        </p>
      </div>
      <PromptWorkbench worlds={worlds} shotsByWorld={shotsByWorld} />
    </div>
  );
}
