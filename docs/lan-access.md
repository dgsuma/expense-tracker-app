# LAN & Phone Access (Docker on Windows)

How to access the Expense Tracker app and API from other devices on your local
network (e.g. an Android phone) when running the stack via `docker compose` on
a Windows host.

## TL;DR

| What | URL |
|------|-----|
| Web app (phone / PC) | `http://<PC-LAN-IP>:8080` |
| Swagger UI (phone / PC) | `http://<PC-LAN-IP>:8000/docs` |
| Web app (PC only) | `http://localhost:8080` |
| Swagger UI (PC only) | `http://localhost:8000/docs` |

Example with PC IP `192.168.1.2`: browse to `http://192.168.1.2:8080` on the phone.

> `/docs` (Swagger) is served by the **FastAPI** backend on port **8000**, not by
> the Flutter web app on port 8080. Requesting `http://…:8080/#/docs` fails with
> "GoException: no routes for location: /docs" because `/docs` is not a Flutter route.

## How it works (same-origin, no build-time IP)

The web container's nginx serves the Flutter app **and** proxies `/api/...` to
the API container (`proxy_pass http://api:8000`). The app calls `/api/...`
relative to whatever origin served it, so:

- **One build works from any address** — `localhost:8080`, any LAN IP, or a
  domain. No rebuild when the IP changes.
- **No CORS preflight** — API calls are same-origin from the browser's view.
- **No DHCP fragility** — nothing about the host's IP is baked into the build.

You only need to rebuild the web image when the app *code* changes, never for
network changes.

## Prerequisites

1. Phone and PC on the **same Wi-Fi** network.
2. Find the PC's LAN IP:
   ```powershell
   Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -ne 'WellKnown' }
   ```
   Use the Wi-Fi adapter address (e.g. `192.168.1.2`).

## One-time setup

### 1. Bring the stack up

```powershell
docker compose up -d --build
```

That's it — no `WEB_API_BASE_URL` needed. The web build defaults to same-origin
API calls.

### 2. (Optional) CORS — only for direct API access, not the web app

The web app calls the API **same-origin** through the nginx proxy, so it needs
**no** CORS entry. You only need a CORS origin if a browser will call the API
**directly** on port 8000 — e.g. using Swagger UI (`http://<PC-LAN-IP>:8000/docs`)
from the phone. To allow that, add the origin to `API_CORS_ORIGINS` in `.env`:

```dotenv
API_CORS_ORIGINS=http://localhost:8080,http://localhost:5000,http://192.168.1.2:8080
```

Restart the API to pick it up:

```powershell
docker compose up -d --force-recreate api
```

### 3. Allow inbound firewall ports (Administrator PowerShell)

Windows Firewall blocks inbound traffic on "Public" network profiles by default.
Add allow rules (requires elevation):

```powershell
New-NetFirewallRule -DisplayName "ExpenseTracker-Web-8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
New-NetFirewallRule -DisplayName "ExpenseTracker-API-8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

Alternatively set the Wi-Fi network profile to **Private**
(Settings → Network & Internet → Wi-Fi → your network → Private).

## Critical: WSL2 networking mode (Docker Desktop on Windows)

> **This is the step most likely to be missed.** If the containers are healthy
> and `localhost:8080` works on the PC but the phone (and even the PC's own LAN
> IP) times out, the cause is almost always WSL2 **mirrored** networking.

Docker Desktop's WSL2 backend has two networking modes:

- **mirrored** — container ports bind inside the WSL2 VM's network namespace.
  `localhost:8080` works on the PC, but the ports are **not** reachable on the
  LAN IP from the Windows host or external devices. `netsh interface portproxy`
  to `127.0.0.1` does **not** reliably bridge this.
- **NAT** (recommended) — Docker publishes ports to the Windows host's
  `0.0.0.0`, so they listen on every interface including the LAN IP and are
  reachable from other devices.

Check the current mode in `C:\Users\<you>\.wslconfig`:

```ini
[wsl2]
networkingMode=NAT
```

If it says `mirrored`, change it to `NAT`, then apply:

```powershell
wsl --shutdown
# restart Docker Desktop, then:
docker compose up -d
```

Verify the ports are bound on the host (look for `0.0.0.0:8080` / `0.0.0.0:8000`):

```powershell
netstat -an | findstr LISTENING | findstr "8080 8000"
```

In NAT mode you should see `0.0.0.0:8080` and `0.0.0.0:8000`. Then no
`portproxy` rules are needed.

## Verify

From the PC (substitute your current LAN IP):

```powershell
curl http://192.168.1.2:8080/                  # web app -> HTTP 200
curl http://192.168.1.2:8080/api/v1/auth/login -X POST `
  -H "Content-Type: application/json" `
  -d '{"email":"you@example.com","password":"..."}'
# -> HTTP 200 through the nginx proxy (same-origin path the app uses)
```

Then open `http://192.168.1.2:8080` on the phone and log in.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `localhost:8080` works, `<LAN-IP>:8080` times out | WSL2 mirrored mode | Switch to NAT mode (above) |
| `netstat` shows no `0.0.0.0:8080` listener | Docker port proxy not bound | Restart Docker Desktop; check NAT mode |
| Connection refused / timeout from phone only | Windows Firewall | Add inbound rules (step 3) |
| Site can't be reached at the OLD IP | PC's IP changed (DHCP) | Just use the new IP — no rebuild needed |
| Web loads but `/api/...` returns 502 | API container down / not on network | `docker compose up -d` and check `api` is healthy |
| `/docs` 404 / "no routes for location" | Wrong port | Swagger is on `:8000/docs`, not `:8080` |

## Caveats

- **DHCP:** if the PC's IP changes, just browse to the new IP — the same build
  keeps working (nothing is baked in). Set a DHCP reservation / static IP for
  the PC in your router only so the *bookmark* stays stable, not to keep the
  app working.
- **Security:** this exposes the API and web app to your whole LAN over plain
  HTTP with no TLS. Fine for a trusted home network; do **not** do this on an
  untrusted network. For real remote access use HTTPS via the Kubernetes
  ingress (see [kubernetes.md](kubernetes.md)) or a tunnel such as Tailscale.
- **Native Android app:** the same-origin default only applies to web builds.
  A native APK can't use nginx proxying, so build it with an absolute API URL:
  ```powershell
  flutter build apk --dart-define=API_BASE_URL=http://192.168.1.2:8000
  ```
  See [mobile-app.md](mobile-app.md).
