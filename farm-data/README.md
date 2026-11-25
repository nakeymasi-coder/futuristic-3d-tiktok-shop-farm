# Farm data — what every run reads (Glam, Nov 25)

These files live in the repo so every run uses the same saved data. Nobody pages all 264 showcase products on a run.

- `showcase-products.json`: the saved showcase product list (name, sold count, in stock). It's refreshed once a day, not every run.
- `weekly-lineup.json`: this week's products to promote, picked once a week from the saved list (in-stock best sellers). Glam's turmeric products are ALWAYS included every week and can run daily.
- `products/<listing id>/`: each lineup product's real listing photos, pulled once and saved here. If a photo won't download, that product is BLOCKED with the reason. Never a drawn or substituted photo.
  - `selling-points.md` in the same folder holds the approved, claim-safe selling points, with no health or growth claims. Story uses them.
- `angle-log.json`: the angle and hook each video used, per product, so videos don't repeat.
- `scorecard.json`: which videos worked and which didn't (views, watch time, sales where visible) and each one's formula (hook, angle, format), so winners get repeated. It starts from existing @glamorousgrammyglowup stats, read only. The posting freeze stays ON.
