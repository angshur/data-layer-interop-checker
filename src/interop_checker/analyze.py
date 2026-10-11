"""Identity Fragmentation Score for a martech stack.

Tools are nodes; two tools are linked when they share at least one identifier. The score
(0 = unified, 100 = fully fragmented) combines how many disconnected clusters exist, how many
tools are isolated, and whether any tool acts as an identity hub. Port of the browser demo's logic.
"""
import math

# webish = the category tracks web behaviour (used by the duplicate-attribution rule)
CATEGORIES = {
    "cdp": True, "ad_platform": True, "web_analytics": True,
    "crm": False, "email_platform": False, "attribution": True,
}
IDENTIFIERS = ("email_hash", "cookie_id", "device_id", "phone", "crm_contact_id", "ip_address")


def js_round(x):
    """JavaScript Math.round (half up). Python's round() is half-to-even and would differ."""
    return int(math.floor(x + 0.5))


def _validate(tools):
    for t in tools:
        if t["category"] not in CATEGORIES:
            raise ValueError("unknown category %r for %s" % (t["category"], t["name"]))
        bad = [i for i in t["ids"] if i not in IDENTIFIERS]
        if bad:
            raise ValueError("unknown identifier(s) %s for %s" % (bad, t["name"]))


def _graph(tools):
    n = len(tools)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if set(tools[i]["ids"]) & set(tools[j]["ids"]):
                adj[i].add(j)
                adj[j].add(i)
    seen, components = [False] * n, []
    for i in range(n):
        if seen[i]:
            continue
        stack, comp = [i], []
        seen[i] = True
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nb in adj[cur]:
                if not seen[nb]:
                    seen[nb] = True
                    stack.append(nb)
        components.append(sorted(comp))
    return adj, components


def label(score):
    if score <= 25:
        return "Low fragmentation"
    if score <= 50:
        return "Moderate fragmentation"
    if score <= 75:
        return "High fragmentation"
    return "Severe fragmentation"


def analyze(tools):
    """tools: [{"name", "category", "ids": [...]}]. Returns score, label, flags (level, code, text)."""
    _validate(tools)
    n = len(tools)
    if n < 2:
        return {"score": 0, "label": label(0), "ready": False, "components": [],
                "flags": [{"level": "info", "code": "NEED_MORE_TOOLS", "text": "Add at least two tools."}]}
    adj, components = _graph(tools)
    isolated = [i for i in range(n) if not adj[i]]
    comp_frag = (len(components) - 1) / max(1, n - 1) * 50
    iso_pen = len(isolated) / n * 30
    max_deg = max(len(a) for a in adj)
    has_hub = max_deg == n - 1
    own_pen = 0 if has_hub else (10 if max_deg / (n - 1) >= 0.7 else 20)
    score = max(0, min(100, js_round(comp_frag + iso_pen + own_pen)))

    flags = []
    for i in isolated:
        flags.append({"level": "critical", "code": "ISOLATED_TOOL", "tool": tools[i]["name"],
                      "text": "%s shares no identifier with the rest of the stack; its data is siloed." % tools[i]["name"]})
    web = [i for i in range(n) if CATEGORIES[tools[i]["category"]]]
    disc_web = [i for i in web if not any(CATEGORIES[tools[j]["category"]] for j in adj[i])]
    if len(web) >= 2 and len(disc_web) >= 2:
        flags.append({"level": "critical", "code": "WEB_TOOLS_DISCONNECTED",
                      "text": "%d web-behaviour tools (%s) share no identifier with each other." % (
                          len(disc_web), ", ".join(tools[i]["name"] for i in disc_web))})
    if not has_hub:
        cdp = next((i for i in range(n) if tools[i]["category"] == "cdp"), None)
        if cdp is not None:
            flags.append({"level": "warning", "code": "CDP_NOT_UNIVERSAL", "tool": tools[cdp]["name"],
                          "text": "CDP %s does not share an identifier with every tool." % tools[cdp]["name"]})
        else:
            flags.append({"level": "warning", "code": "NO_IDENTITY_OWNER",
                          "text": "No tool owns identity resolution."})
    else:
        hub = next(i for i in range(n) if len(adj[i]) == n - 1)
        flags.append({"level": "good", "code": "IDENTITY_HUB", "tool": tools[hub]["name"],
                      "text": "%s connects to every other tool." % tools[hub]["name"]})
    if len(components) > 1:
        flags.append({"level": "critical", "code": "SPLIT_CLUSTERS",
                      "text": "The stack splits into %d disconnected clusters: %s." % (
                          len(components), " | ".join(" + ".join(tools[i]["name"] for i in c) for c in components))})
    all_ids = {x for t in tools for x in t["ids"]}
    if len(all_ids) >= 4 and not has_hub:
        flags.append({"level": "warning", "code": "MANY_SCHEMES_NO_KEY",
                      "text": "%d identifier schemes in play with no single resolution key." % len(all_ids)})
    crm_email = [i for i in range(n) if tools[i]["category"] in ("crm", "email_platform")]
    ads = [i for i in range(n) if tools[i]["category"] == "ad_platform"]
    comp_of = {i: k for k, c in enumerate(components) for i in c}
    # Linked means reachable through the identity graph (e.g. via a CDP), not only a direct shared id.
    if crm_email and ads and not any(comp_of[i] == comp_of[j] for i in crm_email for j in ads):
        flags.append({"level": "critical", "code": "CRM_ADS_DISCONNECTED",
                      "text": "Customer data in CRM/email is not connected to ad platforms; conversion data likely does not feed optimization."})
    if not flags:
        flags.append({"level": "good", "code": "NO_ISSUES", "text": "No major fragmentation issues detected."})
    return {"score": score, "label": label(score), "ready": True,
            "components": [[tools[i]["name"] for i in c] for c in components], "flags": flags}
