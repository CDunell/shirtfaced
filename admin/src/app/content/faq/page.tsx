import { getFaqContent, listFaqItems } from "@/db/content-queries";
import { ContentForm, type ContentFieldDef } from "@/components/ContentForm";
import {
  updateFaqIntroAction,
  addFaqItemAction,
  updateFaqItemAction,
} from "@/app/content/actions";
import { Button, Card, Field, Input, Textarea } from "@/components/ui";
import { DeleteFaqItemButton } from "@/components/DeleteFaqItemButton";

const INTRO_FIELDS: ContentFieldDef[] = [
  { name: "intro", label: "Intro (under the page title)", type: "textarea" },
];

export const dynamic = "force-dynamic";

export default async function FaqContentPage() {
  const [content, items] = await Promise.all([getFaqContent(), listFaqItems()]);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-6">
        <h1 className="display text-[40px]">FAQ page</h1>
        <ContentForm
          fields={INTRO_FIELDS}
          initial={{ intro: content?.intro ?? "" }}
          action={updateFaqIntroAction}
        />
      </div>

      <div className="flex flex-col gap-4">
        <h2 className="display text-[24px]">Questions</h2>

        {items.length === 0 && (
          <Card>
            <p className="text-ink/60">No questions yet.</p>
          </Card>
        )}

        {items.map((item) => (
          <Card key={item.id} className="flex flex-col gap-3">
            <form action={updateFaqItemAction.bind(null, item.id)} className="flex flex-col gap-3">
              <Field label="Question" htmlFor={`q-${item.id}`}>
                <Input id={`q-${item.id}`} name="question" defaultValue={item.question} required />
              </Field>
              <Field label="Answer" htmlFor={`a-${item.id}`}>
                <Textarea
                  id={`a-${item.id}`}
                  name="answer"
                  defaultValue={item.answer}
                  rows={3}
                  required
                />
              </Field>
              <div className="flex gap-3">
                <Field
                  label="Link URL (optional)"
                  htmlFor={`lh-${item.id}`}
                  hint="e.g. /shipping — leave both link fields blank for no link."
                >
                  <Input
                    id={`lh-${item.id}`}
                    name="linkHref"
                    defaultValue={item.linkHref ?? ""}
                    placeholder="/shipping"
                  />
                </Field>
                <Field label="Link label (optional)" htmlFor={`ll-${item.id}`}>
                  <Input
                    id={`ll-${item.id}`}
                    name="linkLabel"
                    defaultValue={item.linkLabel ?? ""}
                    placeholder="the shipping page"
                  />
                </Field>
              </div>
              <Field label="Order" htmlFor={`o-${item.id}`} hint="Lower numbers show first.">
                <Input
                  id={`o-${item.id}`}
                  name="sortOrder"
                  type="number"
                  defaultValue={item.sortOrder}
                  required
                  className="max-w-[120px]"
                />
              </Field>
              <div className="flex gap-2">
                <Button type="submit" variant="ghost">
                  Save
                </Button>
                <DeleteFaqItemButton id={item.id} question={item.question} />
              </div>
            </form>
          </Card>
        ))}
      </div>

      <div className="flex flex-col gap-3">
        <h2 className="display text-[24px]">Add a question</h2>
        <Card>
          <form action={addFaqItemAction} className="flex flex-col gap-3">
            <Field label="Question" htmlFor="new-question">
              <Input id="new-question" name="question" required />
            </Field>
            <Field label="Answer" htmlFor="new-answer">
              <Textarea id="new-answer" name="answer" rows={3} required />
            </Field>
            <div className="flex gap-3">
              <Field
                label="Link URL (optional)"
                htmlFor="new-linkHref"
                hint="e.g. /shipping — leave both link fields blank for no link."
              >
                <Input id="new-linkHref" name="linkHref" placeholder="/shipping" />
              </Field>
              <Field label="Link label (optional)" htmlFor="new-linkLabel">
                <Input id="new-linkLabel" name="linkLabel" placeholder="the shipping page" />
              </Field>
            </div>
            <Field label="Order" htmlFor="new-order" hint="Lower numbers show first.">
              <Input
                id="new-order"
                name="sortOrder"
                type="number"
                defaultValue={items.length}
                required
                className="max-w-[120px]"
              />
            </Field>
            <Button type="submit" className="self-start">
              Add question
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
