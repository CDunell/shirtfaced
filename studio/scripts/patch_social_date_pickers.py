from pathlib import Path


path = Path(__file__).resolve().parents[1] / "web" / "src" / "components" / "SocialBench.tsx"
text = path.read_text(encoding="utf-8")

old = '''                    <input
                      type="datetime-local"
                      aria-label="Schedule time"
                      onChange={(event) => {
                        const value = event.target.value;
                        if (value)
                          void act(() => scheduleSocialJob(job.id, new Date(value).toISOString()));
                      }}
                    />
'''

new = '''                    <form
                      className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}
                      onSubmit={(event) => {
                        event.preventDefault();
                        const form = new FormData(event.currentTarget);
                        const date = String(form.get("schedule-date") ?? "");
                        const time = String(form.get("schedule-time") ?? "");
                        if (!date || !time) return;
                        void act(() =>
                          scheduleSocialJob(job.id, new Date(`${date}T${time}`).toISOString()),
                        );
                      }}
                    >
                      <input
                        type="date"
                        name="schedule-date"
                        aria-label="Schedule date"
                        required
                        defaultValue={
                          job.scheduled_at
                            ? new Date(job.scheduled_at).toLocaleDateString("en-CA")
                            : undefined
                        }
                        className={css({
                          minHeight: "36px",
                          padding: "0 8px",
                          borderRadius: "8px",
                          border: `1px solid ${theme.colors.borderOpaque}`,
                          backgroundColor: theme.colors.backgroundPrimary,
                          color: theme.colors.contentPrimary,
                          font: "inherit",
                        })}
                      />
                      <input
                        type="time"
                        name="schedule-time"
                        aria-label="Schedule time"
                        required
                        step={300}
                        defaultValue={
                          job.scheduled_at
                            ? new Date(job.scheduled_at).toTimeString().slice(0, 5)
                            : undefined
                        }
                        className={css({
                          minHeight: "36px",
                          padding: "0 8px",
                          borderRadius: "8px",
                          border: `1px solid ${theme.colors.borderOpaque}`,
                          backgroundColor: theme.colors.backgroundPrimary,
                          color: theme.colors.contentPrimary,
                          font: "inherit",
                        })}
                      />
                      <Button size={SIZE.mini} type="submit" disabled={busy}>
                        Set schedule
                      </Button>
                    </form>
'''

if old not in text:
    raise SystemExit("Expected datetime-local scheduler block was not found")

path.write_text(text.replace(old, new, 1), encoding="utf-8")
