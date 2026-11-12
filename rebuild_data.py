#!/usr/bin/env python3
"""Rebuild accounts.json with normalized clusters, tiers, listing IDs, link statuses.

Fixes (per 2026-10-13 review):
- Look-alike chars (I/l) in invite hashes merged into one cluster
- Truncated invite hashes (<16 chars) marked link_status=incomplete
- Weak rows flagged (DocICU short handle, Mr_pri no link)
- Clusters keyed by normalized link (stable IDs), not display numbers
- Tiers: verified (evidence screenshot) / corroborated (shared link) / reported
- Listing IDs TS-001..TS-n, platform-neutral fields
"""
import json, re
from collections import defaultdict

SRC = 'accounts.json'

# evidence screenshots -> telegram handle substring
EVIDENCE_HANDLES = ['binco', 'clintonstock', 'crestedge', 'degainers', 'ftrad',
                    'gammasphere', 'mrquicker', 'nexacoin', 'qwacker', 'stockwise',
                    'trex', 'xyrofx']

def normalize_link(link):
    """Normalize a t.me link for clustering.
    Public handles: case-insensitive on Telegram -> lowercase.
    Private invite hashes: case-SENSITIVE (base64url) -> kept exactly as-is.
    (2026-10-15: reversed the earlier I/l confusable fold per standing rule —
    +l5YmFjIFwZQ4MDE8 and +l5YmFjlFwZQ4MDE8 are distinct invites.)
    """
    m = re.match(r'https?://t\.me/(\+?)(.+)', link.strip(), re.I)
    if not m:
        return link.strip().lower()
    plus, path = m.group(1), m.group(2).rstrip('/')
    if plus:
        return 't.me/+' + path
    return 't.me/' + path.lower()

def link_status(link):
    m = re.match(r'https?://t\.me/(\+?)(.+)', link.strip(), re.I)
    if not m:
        return 'incomplete'
    plus, path = m.group(1), m.group(2).rstrip('/')
    if plus and len(path) < 16:
        return 'incomplete'
    if not plus and len(path) <= 4:
        return 'incomplete'  # suspiciously short handle, likely truncated
    return 'ok'

def main():
    data = json.load(open(SRC))
    # normalize links per record
    for r in data:
        normed = []
        statuses = []
        for l in r.get('telegram_links', []):
            normed.append(normalize_link(l))
            statuses.append(link_status(l))
        r['telegram_links_norm'] = normed
        r['link_statuses'] = statuses
        r['link_status'] = ('none' if not normed else
                            'incomplete' if 'incomplete' in statuses else 'ok')
        r['platform'] = 'afterhour'
        r['destination_platform'] = 'telegram'

    # cluster by normalized link
    clusters = defaultdict(set)
    for r in data:
        for nl in r['telegram_links_norm']:
            clusters[nl].add(r['username'])
    shared = {nl: sorted(u) for nl, u in clusters.items() if len(u) >= 2}
    print(f'shared-link clusters: {len(shared)}')
    for nl, users in sorted(shared.items()):
        print(f'  {nl}: {", ".join(users)}')

    # near-duplicate check: links differing by <=2 chars (catch other splits)
    nls = sorted(clusters)
    for i in range(len(nls)):
        for j in range(i + 1, len(nls)):
            a, b = nls[i], nls[j]
            if abs(len(a) - len(b)) > 2:
                continue
            diff = sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))
            if diff <= 2 and diff > 0:
                print(f'NEAR-DUP ({diff}): {a}  vs  {b}')

    # tiers + listing ids — IDs ARE STABLE: never reassign an existing username's ID.
    # New usernames get max(existing)+1 and up. (2026-10-14: a rebuild reshuffled
    # all TS-### IDs and had to be repaired from backup. Never again.)
    import os as _os, json as _json
    existing_ids = {}
    if _os.path.exists(SRC):
        try:
            for _r in _json.load(open(SRC)):
                if _r.get('username') and _r.get('listing_id'):
                    existing_ids[_r['username']] = _r['listing_id']
        except Exception:
            pass
    _max = 0
    for _lid in existing_ids.values():
        try:
            _max = max(_max, int(_lid.split('-')[1]))
        except Exception:
            pass
    data.sort(key=lambda r: r['username'].lower())
    for r in data:
        if r['username'] not in existing_ids:
            _max += 1
            existing_ids[r['username']] = f'TS-{_max:03d}'
        r['listing_id'] = existing_ids[r['username']]
        has_evidence = any(e in h.lower()
                           for h in r.get('telegram_handles', [])
                           for e in EVIDENCE_HANDLES)
        in_shared = any(nl in shared for nl in r['telegram_links_norm'])
        r['tier'] = ('verified' if has_evidence
                     else 'corroborated' if in_shared else 'reported')
        r['cluster_key'] = next((nl for nl in r['telegram_links_norm']
                                 if nl in shared), None)
        # drop legacy numeric cluster fields
        r.pop('cluster_id', None)
        r.pop('cluster_handle', None)

    from collections import Counter
    print('tiers:', Counter(r['tier'] for r in data))
    print('link_status:', Counter(r['link_status'] for r in data))

    json.dump(data, open(SRC, 'w'), indent=1, ensure_ascii=False)
    # also emit a JS wrapper
    js = 'const ACCOUNTS = ' + json.dumps(data, ensure_ascii=False) + ';\n'
    open('accounts.js', 'w').write(js)
    # CSV export (open data)
    import csv
    with open('accounts.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['listing_id', 'tier', 'platform', 'afterhour_username',
                    'destination_platform', 'telegram_link', 'link_status',
                    'cluster_key', 'created_at', 'bio'])
        for r in data:
            links = r.get('telegram_links') or ['']
            for l, s in zip(links, r['link_statuses'] or ['none']):
                w.writerow([r['listing_id'], r['tier'], r['platform'],
                            r['username'], r['destination_platform'], l, s,
                            r.get('cluster_key') or '', r.get('created_at') or '',
                            (r.get('bio') or '').replace('\n', ' ')[:200]])
    print('wrote accounts.json, accounts.js, accounts.csv')

if __name__ == '__main__':
    main()
