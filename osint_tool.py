#!/usr/bin/env python3
"""
OSINT Terminal Tool
Uses free, public APIs: ipinfo.io, haveibeenpwned.com, emailrep.io,
crt.sh, whois, sherlock (if installed), holehe (if installed), and more.
"""

import os
import sys
import json
import socket
import urllib.request
import urllib.error
import urllib.parse
import subprocess
import re
from datetime import datetime

# ── Color codes ──────────────────────────────────────────────────────────────
R  = "\033[91m"   # red
G  = "\033[92m"   # green
Y  = "\033[93m"   # yellow
B  = "\033[94m"   # blue
M  = "\033[95m"   # magenta
C  = "\033[96m"   # cyan
W  = "\033[97m"   # white
DIM= "\033[2m"
RST= "\033[0m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    clear()
    print(f"""{C}
  ██████╗ ██╗███████╗███████╗██╗   ██╗███████╗     ██████╗ ███████╗██╗███╗   ██╗████████╗
██╔══██╗██║██╔════╝██╔════╝╚██╗ ██╔╝██╔════╝    ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
██║  ██║██║███████╗███████╗ ╚████╔╝ ███████╗    ██║   ██║███████╗██║██╔██╗ ██║   ██║   
██║  ██║██║╚════██║╚════██║  ╚██╔╝  ╚════██║    ██║   ██║╚════██║██║██║╚██╗██║   ██║   
██████╔╝██║███████║███████║   ██║   ███████║    ╚██████╔╝███████║██║██║ ╚████║   ██║   
╚═════╝ ╚═╝╚══════╝╚══════╝   ╚═╝   ╚══════╝     ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝ {RST}
{DIM}                      Its just stalking twin{RST}
{Y}  For SKIBIDI USES ONLY.{RST}
""")

def divider(title=""):
    width = 70
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{B}{'─'*pad} {W}{title}{B} {'─'*(width-pad-len(title)-2)}{RST}")
    else:
        print(f"{B}{'─'*width}{RST}")

def fetch(url, headers=None, timeout=10):
    """Simple HTTP GET, returns parsed JSON or raw text."""
    req = urllib.request.Request(url, headers=headers or {
        "User-Agent": "Mozilla/5.0 (OSINT-Tool/1.0)"
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return json.loads(raw), None
            except json.JSONDecodeError:
                return raw, None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)

def ok(label, value):
    print(f"  {G}✔{RST} {W}{label:<22}{RST} {value}")

def warn(label, value):
    print(f"  {Y}⚠{RST} {W}{label:<22}{RST} {Y}{value}{RST}")

def err(label, value):
    print(f"  {R}✘{RST} {W}{label:<22}{RST} {R}{value}{RST}")

def info(msg):
    print(f"  {C}ℹ{RST} {msg}")

# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 1 – IP ADDRESS LOOKUP
# ─────────────────────────────────────────────────────────────────────────────
def lookup_ip(ip):
    divider(f"IP Lookup: {ip}")

    # Basic validation
    ip = ip.strip()

    # ipinfo.io – free, no key needed for basic info
    data, error = fetch(f"https://ipinfo.io/{ip}/json")
    if error or not isinstance(data, dict):
        err("ipinfo.io", error or "Unexpected response")
    else:
        ok("IP",          data.get("ip", "N/A"))
        ok("Hostname",    data.get("hostname", "N/A"))
        ok("City",        data.get("city", "N/A"))
        ok("Region",      data.get("region", "N/A"))
        ok("Country",     data.get("country", "N/A"))
        ok("Location",    data.get("loc", "N/A"))
        ok("Organization",data.get("org", "N/A"))
        ok("Timezone",    data.get("timezone", "N/A"))
        ok("Postal",      data.get("postal", "N/A"))

    divider("Reverse DNS")
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        ok("Reverse DNS", hostname)
    except Exception:
        warn("Reverse DNS", "No PTR record found")

    divider("Open Ports (common)")
    common_ports = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
        443: "HTTPS", 3306: "MySQL", 3389: "RDP", 8080: "HTTP-Alt"
    }
    found_any = False
    for port, name in common_ports.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        result = s.connect_ex((ip, port))
        s.close()
        if result == 0:
            ok(f"Port {port}", f"{G}OPEN{RST}  ({name})")
            found_any = True
    if not found_any:
        warn("Ports", "No common ports open / filtered")

# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 2 – EMAIL LOOKUP
# ─────────────────────────────────────────────────────────────────────────────
def lookup_email(email):
    email = email.strip()
    divider(f"Email Lookup: {email}")

    domain = email.split("@")[-1] if "@" in email else None

    # ── Have I Been Pwned (public breach list, no key needed for breaches) ──
    divider("Have I Been Pwned")
    encoded = urllib.parse.quote(email)
    data, error = fetch(
        f"https://haveibeenpwned.com/api/v3/breachedaccount/{encoded}?truncateResponse=false",
        headers={
            "User-Agent": "OSINT-Terminal-Tool",
            "hibp-api-key": ""          # key required for full detail; we get public breach names
        }
    )
    if error == "HTTP 401":
        # No API key – fall back to the public unauth endpoint
        data, error = fetch(
            f"https://haveibeenpwned.com/api/v2/breachedaccount/{encoded}",
            headers={"User-Agent": "OSINT-Terminal-Tool"}
        )
    if error == "HTTP 404":
        ok("Breaches", f"{G}No breaches found – good!{RST}")
    elif isinstance(data, list) and data:
        warn("Breaches found", f"{R}{len(data)} breach(es){RST}")
        for b in data[:10]:
            name  = b.get("Name", "?")
            year  = b.get("BreachDate", "")[:4]
            pwned = b.get("PwnCount", "?")
            types = ", ".join(b.get("DataClasses", [])[:4])
            print(f"    {R}•{RST} {name} ({year}) — {pwned:,} accounts — {DIM}{types}{RST}")
        if len(data) > 10:
            info(f"...and {len(data)-10} more. Check haveibeenpwned.com for full list.")
    elif error:
        warn("HIBP", f"Could not query ({error})")

    # ── emailrep.io ──────────────────────────────────────────────────────────
    divider("EmailRep.io")
    data, error = fetch(
        f"https://emailrep.io/{encoded}",
        headers={"User-Agent": "OSINT-Terminal-Tool", "Key": ""}
    )
    if isinstance(data, dict) and "reputation" in data:
        rep = data.get("reputation", "N/A")
        sus = data.get("suspicious", False)
        col = R if sus else G
        ok("Reputation",    f"{col}{rep}{RST}")
        ok("Suspicious",    f"{col}{sus}{RST}")
        refs = data.get("references", 0)
        ok("References",    str(refs))
        details = data.get("details", {})
        ok("Blacklisted",   str(details.get("blacklisted", "N/A")))
        ok("MX valid",      str(details.get("valid_mx", "N/A")))
        ok("Disposable",    str(details.get("disposable", "N/A")))
        ok("Free provider", str(details.get("free_provider", "N/A")))
        ok("Spam",          str(details.get("spam", "N/A")))
        ok("Spoofable",     str(details.get("spoofable", "N/A")))
        ok("Last seen",     str(details.get("last_seen", "N/A")))
        ok("Profiles",      str(details.get("profiles", [])))
    elif error:
        warn("emailrep.io", f"Could not query ({error})")

    # ── Domain MX check ─────────────────────────────────────────────────────
    if domain:
        divider(f"Domain Info: {domain}")
        try:
            mx = socket.getaddrinfo(domain, None)
            ok("Domain resolves", f"{G}Yes{RST}")
            # Try crt.sh for SSL certs
            crt, cerr = fetch(f"https://crt.sh/?q={domain}&output=json")
            if isinstance(crt, list) and crt:
                ok("SSL Certs found", str(len(crt)))
                issuers = set()
                for c in crt[:5]:
                    cn = c.get("common_name", "")
                    if cn:
                        issuers.add(cn)
                for cn in list(issuers)[:5]:
                    info(f"  Cert CN: {cn}")
            elif cerr:
                warn("crt.sh", cerr)
        except Exception:
            warn("Domain", "Could not resolve")

    # ── Holehe (if installed) ─────────────────────────────────────────────
    divider("Account Check (holehe)")
    _run_tool("holehe", [email], "holehe")

# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 3 – USERNAME LOOKUP
# ─────────────────────────────────────────────────────────────────────────────
def lookup_username(username):
    username = username.strip()
    divider(f"Username Lookup: {username}")

    # ── Sherlock (if installed) ───────────────────────────────────────────
    divider("Sherlock – Social Media")
    _run_tool("sherlock", [username, "--timeout", "10"], "sherlock")

    # ── Manual checks on a few open endpoints ────────────────────────────
    divider("Quick Profile Checks")
    checks = [
        ("GitHub",    f"https://api.github.com/users/{username}",   "login"),
        ("Reddit",    f"https://www.reddit.com/user/{username}/about.json", "name"),
        ("HackerNews",f"https://hacker-news.firebaseio.com/v0/user/{username}.json", "id"),
    ]
    for site, url, key in checks:
        d, e = fetch(url)
        if isinstance(d, dict) and d.get(key):
            ok(site, f"{G}Found{RST}  →  {url.split('/')[2]}/{username}")
            if site == "GitHub":
                ok("  Name",       d.get("name", "N/A"))
                ok("  Bio",        d.get("bio",  "N/A"))
                ok("  Followers",  str(d.get("followers", 0)))
                ok("  Public repos",str(d.get("public_repos", 0)))
                ok("  Created",    d.get("created_at","N/A")[:10])
        elif e == "HTTP 404" or d is None:
            warn(site, "Not found")
        else:
            warn(site, f"Inconclusive ({e})")

# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 4 – DOMAIN / URL LOOKUP
# ─────────────────────────────────────────────────────────────────────────────
def lookup_domain(domain):
    domain = domain.strip().lower()
    divider(f"Domain Lookup: {domain}")

    # ── DNS resolution ────────────────────────────────────────────────────
    divider("DNS Resolution")
    try:
        ips = socket.getaddrinfo(domain, None)
        unique_ips = list({r[4][0] for r in ips})
        for ip in unique_ips:
            ok("A Record", ip)
            # Auto-lookup each IP
            lookup_ip(ip)
    except Exception as e:
        err("DNS", str(e))

    # ── crt.sh certificate transparency ──────────────────────────────────
    divider("SSL Certificate Transparency (crt.sh)")
    crt, cerr = fetch(f"https://crt.sh/?q=%.{domain}&output=json")
    if isinstance(crt, list) and crt:
        ok("Certificates found", str(len(crt)))
        subdomains = set()
        for c in crt:
            name = c.get("name_value","").strip()
            for sub in name.split("\n"):
                sub = sub.strip().lower()
                if sub.endswith(domain) and sub != domain:
                    subdomains.add(sub)
        if subdomains:
            info(f"Subdomains discovered ({len(subdomains)}):")
            for s in sorted(subdomains)[:20]:
                print(f"    {C}•{RST} {s}")
    elif cerr:
        warn("crt.sh", cerr)

    # ── RDAP / WHOIS via rdap.org ─────────────────────────────────────────
    divider("RDAP / WHOIS")
    rdap, rerr = fetch(f"https://rdap.org/domain/{domain}")
    if isinstance(rdap, dict):
        ok("Status",  ", ".join(rdap.get("status", ["N/A"])))
        events = rdap.get("events", [])
        for ev in events:
            action = ev.get("eventAction","")
            date   = ev.get("eventDate","")[:10]
            if action in ("registration","expiration","last changed"):
                ok(action.title(), date)
        entities = rdap.get("entities", [])
        for ent in entities:
            roles = ent.get("roles", [])
            vcard = ent.get("vcardArray", [])
            if vcard and len(vcard) > 1:
                for entry in vcard[1]:
                    if entry[0] == "fn":
                        ok(f"Contact ({'/'.join(roles)})", entry[3])
    elif rerr:
        warn("RDAP", rerr)

# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 5 – PHONE NUMBER (basic)
# ─────────────────────────────────────────────────────────────────────────────
def lookup_phone(phone):
    phone = re.sub(r"[^\d+]", "", phone.strip())
    divider(f"Phone Lookup: {phone}")

    # numverify has a free tier but needs a key; we use an open lookup
    data, error = fetch(f"https://api.country.is/{phone[:3]}")   # rough country hint
    # phonevalidate via abstract – no-key free version
    data2, err2 = fetch(f"https://phonevalidation.abstractapi.com/v1/?phone={urllib.parse.quote(phone)}")
    if isinstance(data2, dict) and "country" in data2:
        ok("Valid",      str(data2.get("valid", "N/A")))
        ok("Country",    data2.get("country", {}).get("name", "N/A"))
        ok("Location",   data2.get("location", "N/A"))
        ok("Carrier",    data2.get("carrier", "N/A"))
        ok("Line type",  data2.get("line_type", "N/A"))
    else:
        # Parse country code ourselves
        cc_map = {
            "+1":"US/CA","+44":"UK","+92":"Pakistan","+91":"India",
            "+49":"Germany","+33":"France","+61":"Australia","+86":"China",
            "+7":"Russia","+55":"Brazil","+81":"Japan","+39":"Italy",
            "+34":"Spain","+82":"South Korea","+27":"South Africa",
        }
        for code, country in cc_map.items():
            if phone.startswith(code):
                ok("Country code",country)
                break
        else:
            warn("Country code","Unknown")
        warn("Note", "Full carrier/location lookup requires API key (numverify, abstractapi)")

    # PhoneInfoga (if installed)
    divider("PhoneInfoga")
    _run_tool("phoneinfoga", ["scan", "-n", phone], "phoneinfoga")

# ─────────────────────────────────────────────────────────────────────────────
#  MODULE 6 – NAME LOOKUP (people search via open sources)
# ─────────────────────────────────────────────────────────────────────────────
def lookup_name(name):
    name = name.strip()
    divider(f"Name Lookup: {name}")
    encoded = urllib.parse.quote(name)

    # GitHub search
    divider("GitHub Profiles")
    gh, ghe = fetch(f"https://api.github.com/search/users?q={encoded}&per_page=5")
    if isinstance(gh, dict) and gh.get("items"):
        for u in gh["items"][:5]:
            ok(u.get("login","?"), u.get("html_url",""))
    elif ghe:
        warn("GitHub", ghe)

    # Gravatar hash lookup (MD5 of email gives avatar)
    divider("Note")
    info("Full name-based people search (Spokeo, WhitePages, etc.) requires paid APIs.")
    info("Use the username or email modules if you have more identifiers.")
    info(f"Try manual Google dorking:  site:linkedin.com \"{name}\"")
    info(f"                            site:twitter.com  \"{name}\"")
    info(f"                            \"{name}\" filetype:pdf")

# ─────────────────────────────────────────────────────────────────────────────
#  HELPER – run external CLI tools if installed
# ─────────────────────────────────────────────────────────────────────────────
def _run_tool(tool, args, display_name):
    try:
        result = subprocess.run(
            [tool] + args,
            capture_output=True, text=True, timeout=120
        )
        output = (result.stdout or "") + (result.stderr or "")
        if output.strip():
            print(output.strip())
        else:
            warn(display_name, "No output returned")
    except FileNotFoundError:
        warn(display_name, f"Not installed. Install with: pip install {display_name}")
    except subprocess.TimeoutExpired:
        warn(display_name, "Timed out after 120s")
    except Exception as e:
        warn(display_name, str(e))

# ─────────────────────────────────────────────────────────────────────────────
#  MENU
# ─────────────────────────────────────────────────────────────────────────────
MENU = f"""
{C}┌─────────────────────────────────────────┐
│           SELECT LOOKUP TYPE            │
├─────────────────────────────────────────┤
│  {W}1{C} │ {Y}IP Address{C}                          │
│  {W}2{C} │ {Y}Email Address{C}                      │
│  {W}3{C} │ {Y}Username{C}                           │
│  {W}4{C} │ {Y}Domain / URL{C}                       │
│  {W}5{C} │ {Y}Phone Number{C}                       │
│  {W}6{C} │ {Y}Full Name{C}                          │
│  {W}0{C} │ {R}Exit{C}                               │
└─────────────────────────────────────────┘{RST}
"""

def main():
    banner()
    while True:
        print(MENU)
        choice = input(f"{C}osint{RST} » ").strip()

        if choice == "0":
            print(f"\n{G}Goodbye.{RST}\n")
            break
        elif choice == "1":
            val = input(f"  {Y}Enter IP address:{RST} ").strip()
            if val: lookup_ip(val)
        elif choice == "2":
            val = input(f"  {Y}Enter email address:{RST} ").strip()
            if val: lookup_email(val)
        elif choice == "3":
            val = input(f"  {Y}Enter username:{RST} ").strip()
            if val: lookup_username(val)
        elif choice == "4":
            val = input(f"  {Y}Enter domain (e.g. example.com):{RST} ").strip()
            if val: lookup_domain(val)
        elif choice == "5":
            val = input(f"  {Y}Enter phone number (e.g. +923001234567):{RST} ").strip()
            if val: lookup_phone(val)
        elif choice == "6":
            val = input(f"  {Y}Enter full name:{RST} ").strip()
            if val: lookup_name(val)
        else:
            warn("Input", "Invalid choice, try again.")

        input(f"\n{DIM}  Press Enter to return to menu...{RST}")
        banner()

if __name__ == "__main__":
    main()
