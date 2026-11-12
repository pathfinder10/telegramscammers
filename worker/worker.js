// telegramscammers.com — visitor country collector (Cloudflare Worker, free tier)
// KV binding: STATS   |   Secret: TOKEN (set via wrangler secret or dashboard)
// Endpoints:
//   GET /ping?p=/page.html   -> logs one visit (country from cf-ipcountry)
//   GET /stats?token=SECRET  -> JSON aggregates { total, countries, byDay }

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ---- visit ping (fire-and-forget from the site) ----
    if (url.pathname === "/ping") {
      const country = (request.headers.get("cf-ipcountry") || "XX").toUpperCase();
      const day = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
      const ttl = 60 * 60 * 24 * 120; // keep 120 days
      const bump = async (key) => {
        const cur = parseInt((await env.STATS.get(key)) || "0", 10);
        await env.STATS.put(key, String(cur + 1), { expirationTtl: ttl });
      };
      await bump(`t:${country}`);       // all-time per country
      await bump(`d:${day}:${country}`); // per day per country
      await bump(`d:${day}:_total`);     // per day total
      return new Response("ok", {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "no-store",
        },
      });
    }

    // ---- admin stats (secret token) ----
    if (url.pathname === "/stats") {
      if (url.searchParams.get("token") !== env.TOKEN) {
        return new Response("forbidden", { status: 403 });
      }
      const countries = {};
      const byDay = {};
      let cursor;
      do {
        const page = await env.STATS.list({ prefix: "t:", cursor });
        for (const k of page.keys) {
          countries[k.name.slice(2)] = parseInt((await env.STATS.get(k.name)) || "0", 10);
        }
        cursor = page.list_complete ? undefined : page.cursor;
      } while (cursor);
      do {
        const page = await env.STATS.list({ prefix: "d:", cursor });
        for (const k of page.keys) {
          const parts = k.name.slice(2).split(":");
          const day = parts[0], cc = parts[1];
          byDay[day] = byDay[day] || {};
          byDay[day][cc] = parseInt((await env.STATS.get(k.name)) || "0", 10);
        }
        cursor = page.list_complete ? undefined : page.cursor;
      } while (cursor);
      const total = Object.values(countries).reduce((a, b) => a + b, 0);
      return Response.json(
        { total, countries, byDay, generated: new Date().toISOString() },
        { headers: { "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store" } }
      );
    }

    return new Response("not found", { status: 404 });
  },
};
