#!/usr/bin/env python3
"""
OSINT Terminal Tool
Scrapes and displays results from public OSINT sources directly in the terminal.
"""

import sys
import time
import socket
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# ── colors ────────────────────────────────────────────────────────────────────
R  = "\033[0m"
G  = "\033[32m"
BG = "\033[92m"
C  = "\033[36m"
Y  = "\033[33m"
RE = "\033[31m"
W  = "\033[97m"
DIM= "\033[90m"
B  = "\033[34m"
M  = "\033[35m"

def clr(text, color): return f"{color}{text}{R}"
def header(text):     print(f"\n{BG}{'─'*60}{R}\n{BG}  {text}{R}\n{BG}{'─'*60}{R}")
def subheader(text):  print(f"\n{C}  ┌─ {text} {'─'*(54-len(text))}┐{R}")
def row(k, v, c=W):   print(f"  {DIM}│{R}  {Y}{k:<22}{R}{c}{v}{R}")
def endrow():         print(f"  {DIM}└{'─'*57}┘{R}")
def err(text):        print(f"  {RE}[!] {text}{R}")
def info(text):       print(f"  {G}[*] {text}{R}")
def warn(text):       print(f"  {Y}[~] {text}{R}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
}

def fetch_json(url, extra_headers=None):
    req = urllib.request.Request(url, headers={**HEADERS, **(extra_headers or {})})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

def fetch_text(url, extra_headers=None):
    req = urllib.request.Request(url, headers={**HEADERS, **(extra_headers or {})})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode("utf-8", errors="ignore")

# ══════════════════════════════════════════════════════════════════════════════
#  IP LOOKUP
# ══════════════════════════════════════════════════════════════════════════════

def lookup_ip(ip):
    header(f"IP LOOKUP  →  {ip}")

    # 1. ip-api.com (free, no key)
    subheader("Geolocation  [ip-api.com]")
    try:
        d = fetch_json(f"http://ip-api.com/json/{ip}?fields=66846719")
        if d.get("status") == "success":
            row("IP",          d.get("query","—"))
            row("Country",     f"{d.get('country','—')} ({d.get('countryCode','—')})")
            row("Region",      d.get("regionName","—"))
            row("City",        d.get("city","—"))
            row("ZIP",         d.get("zip","—"))
            row("Lat / Lon",   f"{d.get('lat','—')}, {d.get('lon','—')}")
            row("Timezone",    d.get("timezone","—"))
            row("ISP",         d.get("isp","—"))
            row("Org",         d.get("org","—"))
            row("AS",          d.get("as","—"))
            row("Reverse DNS", d.get("reverse","—"))
            row("Mobile",      str(d.get("mobile","—")))
            row("Proxy/VPN",   str(d.get("proxy","—")), RE if d.get("proxy") else BG)
            row("Hosting",     str(d.get("hosting","—")))
        else:
            err(d.get("message","Query failed"))
    except Exception as e:
        err(f"ip-api: {e}")
    endrow()

    # 2. ipinfo.io (free tier, no key needed for basic)
    subheader("Network Info  [ipinfo.io]")
    try:
        d = fetch_json(f"https://ipinfo.io/{ip}/json")
        row("Hostname",   d.get("hostname","—"))
        row("Org / ASN",  d.get("org","—"))
        row("Anycast",    str(d.get("anycast","—")))
        if "abuse" in d:
            ab = d["abuse"]
            row("Abuse Email", ab.get("email","—"), RE)
            row("Abuse Phone", ab.get("phone","—"), RE)
    except Exception as e:
        err(f"ipinfo: {e}")
    endrow()

    # 3. AbuseIPDB (public check page scrape — limited info without key)
    subheader("Abuse Reports  [AbuseIPDB]")
    try:
        html = fetch_text(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90",
                          {"Key": "public", "Accept": "application/json"})
        # Fallback: parse confidence from public page
        raise Exception("API key required — visit https://www.abuseipdb.com/check/" + ip)
    except Exception as e:
        warn(str(e))
    endrow()

    # 4. Reverse DNS
    subheader("Reverse DNS  [socket]")
    try:
        host = socket.gethostbyaddr(ip)
        row("Hostname",  host[0])
        row("Aliases",   ", ".join(host[1]) if host[1] else "none")
    except Exception as e:
        err(f"rDNS failed: {e}")
    endrow()

    # 5. Open ports (common)
    subheader("Common Port Scan  [local]")
    common_ports = {21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",
                    80:"HTTP",110:"POP3",143:"IMAP",443:"HTTPS",
                    445:"SMB",3306:"MySQL",3389:"RDP",8080:"HTTP-Alt"}
    open_ports = []
    for port, name in common_ports.items():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((ip, port)) == 0:
                open_ports.append(f"{port}/{name}")
            s.close()
        except:
            pass
    if open_ports:
        row("Open Ports", "  ".join(open_ports), BG)
    else:
        row("Open Ports", "none detected (firewall or all closed)", DIM)
    endrow()

    # 6. Shodan link
    subheader("Further Research")
    print(f"  {DIM}│{R}  {B}Shodan:      {R}https://www.shodan.io/host/{ip}")
    print(f"  {DIM}│{R}  {B}Censys:      {R}https://search.censys.io/hosts/{ip}")
    print(f"  {DIM}│{R}  {B}GreyNoise:   {R}https://viz.greynoise.io/ip/{ip}")
    print(f"  {DIM}│{R}  {B}VirusTotal:  {R}https://www.virustotal.com/gui/ip-address/{ip}")
    print(f"  {DIM}│{R}  {B}RIPE Stat:   {R}https://stat.ripe.net/{ip}")
    endrow()

# ══════════════════════════════════════════════════════════════════════════════
#  USERNAME LOOKUP
# ══════════════════════════════════════════════════════════════════════════════

PLATFORMS = [
    ("GitHub",      "https://github.com/{}",                  "GitHub"),
    ("Twitter/X",   "https://twitter.com/{}",                 "Twitter"),
    ("Instagram",   "https://www.instagram.com/{}/",          "Instagram"),
    ("Reddit",      "https://www.reddit.com/user/{}/",        "Reddit"),
    ("TikTok",      "https://www.tiktok.com/@{}",             "TikTok"),
    ("Pinterest",   "https://www.pinterest.com/{}/",          "Pinterest"),
    ("Twitch",      "https://www.twitch.tv/{}",               "Twitch"),
    ("YouTube",     "https://www.youtube.com/@{}",            "YouTube"),
    ("LinkedIn",    "https://www.linkedin.com/in/{}/",        "LinkedIn"),
    ("Keybase",     "https://keybase.io/{}",                  "Keybase"),
    ("Pastebin",    "https://pastebin.com/u/{}",              "Pastebin"),
    ("HackerNews",  "https://news.ycombinator.com/user?id={}","HackerNews"),
    ("DevTo",       "https://dev.to/{}",                      "dev.to"),
    ("Medium",      "https://medium.com/@{}",                 "Medium"),
    ("Gitlab",      "https://gitlab.com/{}",                  "GitLab"),
    ("Replit",      "https://replit.com/@{}",                 "Replit"),
    ("Codecademy",  "https://www.codecademy.com/profiles/{}", "Codecademy"),
    ("Steam",       "https://steamcommunity.com/id/{}",       "Steam"),
    ("Roblox",      "https://www.roblox.com/user.aspx?username={}","Roblox"),
    ("Flickr",      "https://www.flickr.com/people/{}",       "Flickr"),
    ("Vimeo",       "https://vimeo.com/{}",                   "Vimeo"),
    ("SoundCloud",  "https://soundcloud.com/{}",              "SoundCloud"),
    ("Spotify",     "https://open.spotify.com/user/{}",       "Spotify"),
    ("Duolingo",    "https://www.duolingo.com/profile/{}",    "Duolingo"),
    ("Fiverr",      "https://www.fiverr.com/{}",              "Fiverr"),
]

NOT_FOUND_SIGNALS = [
    "page not found", "user not found", "404", "doesn't exist",
    "no user", "not available", "this account", "suspended",
    "profile not found", "isn't available"
]

def check_username_platform(name, label, url_tpl):
    url = url_tpl.format(urllib.parse.quote(name))
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as r:
            body = r.read(4096).decode("utf-8", errors="ignore").lower()
            code = r.status
        if code == 200:
            if any(sig in body for sig in NOT_FOUND_SIGNALS):
                return "NOT FOUND", url
            return "FOUND", url
        elif code in (404, 410):
            return "NOT FOUND", url
        else:
            return f"HTTP {code}", url
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "NOT FOUND", url
        return f"HTTP {e.code}", url
    except Exception as e:
        return f"ERROR", url

def lookup_username(name):
    header(f"USERNAME LOOKUP  →  {name}")

    # GitHub API for extra info
    subheader("GitHub Profile  [api.github.com]")
    try:
        d = fetch_json(f"https://api.github.com/users/{name}")
        row("Name",       d.get("name") or "—")
        row("Bio",        (d.get("bio") or "—")[:60])
        row("Location",   d.get("location") or "—")
        row("Company",    d.get("company") or "—")
        row("Blog",       d.get("blog") or "—")
        row("Email",      d.get("email") or "—", Y)
        row("Repos",      str(d.get("public_repos","—")))
        row("Followers",  str(d.get("followers","—")))
        row("Following",  str(d.get("following","—")))
        row("Created",    d.get("created_at","—")[:10])
        row("Updated",    d.get("updated_at","—")[:10])
        row("Twitter",    d.get("twitter_username") or "—", Y)
        row("Profile URL",d.get("html_url","—"), C)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            warn("No GitHub account found.")
        else:
            err(f"GitHub API: HTTP {e.code}")
    except Exception as e:
        err(f"GitHub API: {e}")
    endrow()

    # Reddit API
    subheader("Reddit Profile  [reddit.com/user]")
    try:
        d = fetch_json(f"https://www.reddit.com/user/{name}/about.json",
                       {"Accept": "application/json"})
        data = d.get("data", {})
        row("Name",       data.get("name","—"))
        row("Karma (post)",data.get("link_karma","—"))
        row("Karma (cmnt)",data.get("comment_karma","—"))
        row("Created",    datetime.utcfromtimestamp(data.get("created_utc",0)).strftime("%Y-%m-%d"))
        row("Verified",   str(data.get("verified","—")))
        row("NSFW",       str(data.get("over_18","—")))
        row("Gold",       str(data.get("is_gold","—")))
        row("Profile",    f"https://www.reddit.com/user/{name}/", C)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            warn("No Reddit account found.")
        else:
            err(f"Reddit: HTTP {e.code}")
    except Exception as e:
        err(f"Reddit: {e}")
    endrow()

    # Platform sweep
    subheader(f"Platform Sweep  [{len(PLATFORMS)} sites]")
    found, notfound, errors = [], [], []
    print(f"  {DIM}Scanning...{R}", end="", flush=True)
    for label, url_tpl, _ in PLATFORMS:
        status, url = check_username_platform(name, label, url_tpl)
        if status == "FOUND":
            found.append((label, url))
        elif status == "NOT FOUND":
            notfound.append(label)
        else:
            errors.append((label, status))
        print(f"{DIM}.{R}", end="", flush=True)
        time.sleep(0.1)
    print()

    if found:
        print(f"\n  {BG}✔ FOUND on {len(found)} platform(s):{R}")
        for label, url in found:
            print(f"  {G}  ✔  {Y}{label:<16}{R}{C}{url}{R}")
    if notfound:
        print(f"\n  {DIM}✘ Not found: {', '.join(notfound)}{R}")
    if errors:
        print(f"\n  {Y}  Errors (likely rate-limited):{R}")
        for label, status in errors:
            print(f"  {DIM}    {label}: {status}{R}")
    endrow()

    # WhatsMyName link
    subheader("Deep Scan Links")
    print(f"  {DIM}│{R}  {B}WhatsMyName: {R}https://whatsmyname.me/#{urllib.parse.quote(name)}")
    print(f"  {DIM}│{R}  {B}Sherlock:    {R}Run locally: sherlock {name}")
    print(f"  {DIM}│{R}  {B}IntelX:      {R}https://intelx.io/?s={urllib.parse.quote(name)}")
    endrow()

# ══════════════════════════════════════════════════════════════════════════════
#  EMAIL LOOKUP
# ══════════════════════════════════════════════════════════════════════════════

def lookup_email(email):
    header(f"EMAIL LOOKUP  →  {email}")
    domain = email.split("@")[-1] if "@" in email else ""

    # HaveIBeenPwned (public API v3 — no key for simple check)
    subheader("Breach Check  [HaveIBeenPwned]")
    try:
        # HIBP requires API key for breach lookup; use public paste check
        url = f"https://haveibeenpwned.com/api/v3/pasteaccount/{urllib.parse.quote(email)}"
        d = fetch_json(url, {"hibp-api-key": "public"})
        if isinstance(d, list):
            print(f"  {RE}Found in {len(d)} paste(s):{R}")
            for p in d[:5]:
                row("Source", p.get("Source","—"), RE)
                row("Date",   p.get("Date","—"))
        else:
            warn("No pastes found (or API key required for full results)")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  {BG}  ✔ Not found in any known pastes{R}")
        elif e.code == 401:
            warn("HIBP requires API key for full breach lookup.")
            print(f"  {B}  → Check manually: https://haveibeenpwned.com/account/{urllib.parse.quote(email)}{R}")
        else:
            err(f"HIBP: HTTP {e.code}")
    except Exception as e:
        err(f"HIBP: {e}")
    endrow()

    # Email format validation
    subheader("Format & Domain Validation  [local]")
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    valid = bool(re.match(pattern, email))
    row("Format valid",  "Yes" if valid else "No", BG if valid else RE)
    row("Username part", email.split("@")[0])
    row("Domain",        domain)
    if domain:
        try:
            ip = socket.gethostbyname(domain)
            row("Domain resolves", f"Yes → {ip}", BG)
        except:
            row("Domain resolves", "No (MX/A record not found)", RE)
    endrow()

    # MX records
    if domain:
        subheader(f"MX / DNS Records  [{domain}]")
        try:
            import subprocess
            result = subprocess.run(["nslookup", "-type=MX", domain],
                                    capture_output=True, text=True, timeout=5)
            lines = [l for l in result.stdout.splitlines() if "mail exchanger" in l.lower() or "MX" in l]
            if lines:
                for l in lines[:5]:
                    print(f"  {DIM}│{R}  {C}{l.strip()}{R}")
            else:
                warn("No MX records found via nslookup.")
        except FileNotFoundError:
            warn("nslookup not available. Check manually.")
        except Exception as e:
            err(str(e))
        endrow()

    # Username from email prefix across platforms
    prefix = email.split("@")[0]
    subheader(f"Username Sweep on prefix  [{prefix}]")
    info(f"Checking '{prefix}' as username on common platforms...")
    found_p = []
    for label, url_tpl, _ in PLATFORMS[:12]:
        status, url = check_username_platform(prefix, label, url_tpl)
        if status == "FOUND":
            found_p.append((label, url))
        print(f"{DIM}.{R}", end="", flush=True)
        time.sleep(0.1)
    print()
    if found_p:
        print(f"\n  {BG}  Accounts possibly linked to '{prefix}':{R}")
        for label, url in found_p:
            print(f"  {G}  ✔  {Y}{label:<16}{R}{C}{url}{R}")
    else:
        warn("No matching accounts found on checked platforms.")
    endrow()

    # Further links
    subheader("Deep Scan Links")
    print(f"  {DIM}│{R}  {B}HIBP:        {R}https://haveibeenpwned.com/account/{urllib.parse.quote(email)}")
    print(f"  {DIM}│{R}  {B}DeHashed:    {R}https://dehashed.com/search?query={urllib.parse.quote(email)}")
    print(f"  {DIM}│{R}  {B}Epieos:      {R}https://epieos.com/?q={urllib.parse.quote(email)}&t=email")
    print(f"  {DIM}│{R}  {B}IntelX:      {R}https://intelx.io/?s={urllib.parse.quote(email)}")
    endrow()

# ══════════════════════════════════════════════════════════════════════════════
#  DOMAIN LOOKUP
# ══════════════════════════════════════════════════════════════════════════════

def lookup_domain(domain):
    # strip protocol
    domain = re.sub(r"^https?://", "", domain).split("/")[0]
    header(f"DOMAIN LOOKUP  →  {domain}")

    # DNS resolution
    subheader("DNS Resolution  [socket]")
    try:
        ip = socket.gethostbyname(domain)
        row("A Record (IPv4)", ip, BG)
    except Exception as e:
        err(f"DNS resolve failed: {e}")
        ip = None
    try:
        import subprocess
        for rtype in ["MX", "NS", "TXT"]:
            r = subprocess.run(["nslookup", f"-type={rtype}", domain],
                               capture_output=True, text=True, timeout=5)
            hits = [l.strip() for l in r.stdout.splitlines()
                    if rtype in l or "mail" in l.lower() or "nameserver" in l.lower()]
            if hits:
                row(f"{rtype} Records", hits[0][:60])
                for h in hits[1:3]:
                    row("", h[:60])
    except:
        pass
    endrow()

    # IP geo if resolved
    if ip:
        subheader(f"IP Geolocation for {ip}  [ip-api.com]")
        try:
            d = fetch_json(f"http://ip-api.com/json/{ip}?fields=66846719")
            if d.get("status") == "success":
                row("IP",       d.get("query","—"))
                row("Country",  f"{d.get('country','—')} ({d.get('countryCode','—')})")
                row("City",     d.get("city","—"))
                row("ISP",      d.get("isp","—"))
                row("Org",      d.get("org","—"))
                row("AS",       d.get("as","—"))
                row("Proxy",    str(d.get("proxy","—")), RE if d.get("proxy") else BG)
        except Exception as e:
            err(str(e))
        endrow()

    # SSL cert info
    subheader("SSL Certificate  [socket/ssl]")
    try:
        import ssl
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(6)
            s.connect((domain, 443))
            cert = s.getpeercert()
        row("Subject",    dict(x[0] for x in cert.get("subject",[])).get("commonName","—"))
        row("Issuer",     dict(x[0] for x in cert.get("issuer",[])).get("organizationName","—"))
        row("Valid From", cert.get("notBefore","—"))
        row("Valid To",   cert.get("notAfter","—"), BG)
        sans = cert.get("subjectAltName",[])
        if sans:
            row("SANs", ", ".join(v for _,v in sans[:6]))
    except Exception as e:
        err(f"SSL: {e}")
    endrow()

    # HTTP headers
    subheader("HTTP Headers  [urllib]")
    try:
        req = urllib.request.Request(f"https://{domain}", headers=HEADERS, method="HEAD")
        with urllib.request.urlopen(req, timeout=8) as r:
            hdrs = dict(r.headers)
        for k in ["Server","X-Powered-By","Content-Type","Strict-Transport-Security",
                   "X-Frame-Options","Content-Security-Policy","X-Content-Type-Options"]:
            if k in hdrs:
                row(k, hdrs[k][:70])
    except Exception as e:
        err(f"Headers: {e}")
    endrow()

    # robots.txt
    subheader("robots.txt  [urllib]")
    try:
        txt = fetch_text(f"https://{domain}/robots.txt")
        lines = [l.strip() for l in txt.splitlines() if l.strip() and not l.startswith("#")]
        for l in lines[:12]:
            print(f"  {DIM}│{R}  {C}{l[:70]}{R}")
        if len(lines) > 12:
            print(f"  {DIM}│  ... ({len(lines)-12} more lines){R}")
    except Exception as e:
        err(f"robots.txt: {e}")
    endrow()

    # Further links
    subheader("Deep Scan Links")
    print(f"  {DIM}│{R}  {B}VirusTotal:    {R}https://www.virustotal.com/gui/domain/{domain}")
    print(f"  {DIM}│{R}  {B}URLScan.io:    {R}https://urlscan.io/search/#domain:{domain}")
    print(f"  {DIM}│{R}  {B}crt.sh:        {R}https://crt.sh/?q={domain}")
    print(f"  {DIM}│{R}  {B}SecurityTrails:{R}https://securitytrails.com/domain/{domain}/dns")
    print(f"  {DIM}│{R}  {B}Shodan:        {R}https://www.shodan.io/search?query={domain}")
    print(f"  {DIM}│{R}  {B}BuiltWith:     {R}https://builtwith.com/{domain}")
    print(f"  {DIM}│{R}  {B}Wayback:       {R}https://web.archive.org/web/*/{domain}")
    endrow()

# ══════════════════════════════════════════════════════════════════════════════
#  PHONE LOOKUP
# ══════════════════════════════════════════════════════════════════════════════

def lookup_phone(phone):
    digits = re.sub(r"\D", "", phone)
    header(f"PHONE LOOKUP  →  {phone}")

    subheader("Number Analysis  [local]")
    row("Raw input",    phone)
    row("Digits only",  digits)
    row("Length",       str(len(digits)))

    # Country code guess
    cc_map = {
        "1":"USA/Canada","44":"UK","91":"India","92":"Pakistan",
        "49":"Germany","33":"France","86":"China","81":"Japan",
        "7":"Russia","39":"Italy","34":"Spain","55":"Brazil",
        "61":"Australia","82":"South Korea","20":"Egypt",
        "966":"Saudi Arabia","971":"UAE","90":"Turkey",
    }
    detected_cc = "Unknown"
    for code in sorted(cc_map, key=len, reverse=True):
        if digits.startswith(code):
            detected_cc = f"+{code} — {cc_map[code]}"
            break
    row("Country Code", detected_cc, C)
    row("Format E.164", f"+{digits}" if not phone.startswith("+") else phone)
    endrow()

    subheader("Carrier Lookup  [numverify-style]")
    # Free public phone API
    try:
        d = fetch_json(f"https://phonevalidation.abstractapi.com/v1/?api_key=free&phone={digits}")
        row("Valid",     str(d.get("valid","—")))
        row("Country",   d.get("country",{}).get("name","—"))
        row("Location",  d.get("location","—"))
        row("Carrier",   d.get("carrier","—"), Y)
        row("Line type", d.get("line_type","—"), C)
    except:
        warn("Carrier API unavailable (key required). Analysis based on local data only.")
    endrow()

    subheader("Deep Scan Links")
    enc = urllib.parse.quote(phone)
    enc_d = urllib.parse.quote(digits)
    print(f"  {DIM}│{R}  {B}NumLookup:   {R}https://www.numlookup.com/?number={enc}")
    print(f"  {DIM}│{R}  {B}Truecaller:  {R}https://www.truecaller.com/search/us/{enc_d}")
    print(f"  {DIM}│{R}  {B}WhoCalledMe: {R}https://www.whocalledme.com/PhoneNumber/{enc_d}")
    print(f"  {DIM}│{R}  {B}800notes:    {R}https://800notes.com/Phone.aspx/{enc}")
    print(f"  {DIM}│{R}  {B}Google:      {R}https://www.google.com/search?q=%22{enc}%22")
    print(f"  {DIM}│{R}  {B}Epieos:      {R}https://epieos.com/?q={enc}&t=phone")
    endrow()

# ══════════════════════════════════════════════════════════════════════════════
#  MENU
# ══════════════════════════════════════════════════════════════════════════════

def banner():
    print(f"""
{BG}
  ██████╗ ███████╗██╗███╗   ██╗████████╗
  ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
  ██║   ██║███████╗██║██╔██╗ ██║   ██║   
  ██║   ██║╚════██║██║██║╚██╗██║   ██║   
  ╚██████╔╝███████║██║██║ ╚████║   ██║   
   ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝   {R}
{C}  Open Source Intelligence Terminal  v2.0{R}
{DIM}  Results pulled live from public APIs & services{R}
""")

def menu():
    banner()
    print(f"  {W}Select lookup type:{R}\n")
    print(f"  {G}[1]{R} 🌐  IP Address")
    print(f"  {G}[2]{R} 👤  Username")
    print(f"  {G}[3]{R} ✉   Email")
    print(f"  {G}[4]{R} 🔗  Domain / URL")
    print(f"  {G}[5]{R} 📞  Phone Number")
    print(f"  {G}[0]{R} ❌  Exit\n")

def get_choice():
    return input(f"  {BG}osint@terminal{R}{G}:~${R} ").strip()

def main():
    while True:
        menu()
        choice = get_choice()
        if choice == "0":
            print(f"\n  {DIM}Goodbye.{R}\n")
            break
        elif choice in ("1","2","3","4","5"):
            labels = {
                "1": ("IP address",    "e.g. 8.8.8.8",        lookup_ip),
                "2": ("username",      "e.g. johndoe",         lookup_username),
                "3": ("email",         "e.g. user@example.com",lookup_email),
                "4": ("domain/URL",    "e.g. example.com",     lookup_domain),
                "5": ("phone number",  "e.g. +14155552671",    lookup_phone),
            }
            label, example, fn = labels[choice]
            target = input(f"\n  {Y}Enter {label} {DIM}({example}){R}{G}:{R} ").strip()
            if not target:
                err("No input provided.")
                time.sleep(1)
                continue
            try:
                fn(target)
            except KeyboardInterrupt:
                print(f"\n  {Y}Interrupted.{R}")
            print(f"\n  {DIM}{'─'*60}{R}")
            input(f"  {DIM}Press Enter to return to menu...{R}")
        else:
            err("Invalid choice.")
            time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {DIM}Interrupted. Exiting.{R}\n")
        sys.exit(0)
