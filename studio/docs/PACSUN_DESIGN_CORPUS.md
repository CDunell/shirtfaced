# PacSun design-corpus collector

Current-market acquisition only. It follows `DESIGN_CORPUS_SCHEMA.md`: real products, real source images and provenance; no scoring, taxonomy tags, archetypes or trend inference are persisted during collection.

## Run

```bash
cd studio
python -m app.scripts.collect_design_corpus pacsun --dry-run
python -m app.scripts.collect_design_corpus pacsun --limit 15
```

Optional: `--refresh`, `--start-url URL`.

The collector starts at `https://www.pacsun.com/mens/graphic-tees/` and follows the site's detected next/load-more link rather than assuming a pagination increment. It builds a candidate pool, excludes obvious construction/noise products, and chooses a deterministic 12–15 product sample spread across visibly different title/brand signals. Those selection signals are transient and are not written to product records.

Downloaded evidence lives at `studio/var/design_corpus/pacsun/`. `studio/.gitignore` already ignores `var/`, so competitor imagery remains local. The corpus manifest is rebuilt from the filesystem after acquisition rather than incremented by a worker.

## Schema gap

PacSun is a retailer and exposes third-party product brands/licences. `DESIGN_CORPUS_SCHEMA.md` currently defines no manufacturer/licensor field. The collector reads that value for transient sample selection but deliberately does not invent a persisted field. Add such a field to the governing schema first if downstream work needs it.

## PacSun-specific limitation

PacSun's category is a mixed retail grid and can contain packs, jerseys, polos, knits and other false positives. Filtering is therefore conservative. Product JSON-LD is preferred for product facts and images; CDN image URLs in product markup are a fallback. If PacSun changes its storefront markup or bot policy, failures are reported instead of silently skipped.
