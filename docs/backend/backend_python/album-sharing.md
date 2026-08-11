# Album Sharing over the Local Network

PictoPy can serve a single album over the local network so that someone on the same Wi-Fi can browse it in a normal browser. Nothing is uploaded anywhere — the photos are streamed straight from the host machine, and the share disappears when PictoPy closes.

This page is for developers: running the backend yourself, driving the share API by hand, and understanding how the pieces fit. If you are looking for what sharing means for your photos and your privacy, read [Sharing Albums](../../overview/sharing-albums.md) instead.

Sharing an album from the desktop app is a menu item on the album card; everything below describes the machinery underneath it.

## Running the backend

Set up the environment once by following the [Manual Setup Guide](../../Manual_Setup_Guide.md) — create the environment, activate it, and `pip install -r requirements.txt` inside `backend/`.

After that there are two ways to start the server, both from the `backend/` directory:

```bash
python main.py
```

This is the plain entry point. It binds `localhost:52123` and is exactly what the packaged desktop app runs, so it is the closest match to production behaviour.

```bash
fastapi dev --port 52123
```

This adds auto-reload, which is nicer while editing. Both work with album sharing.

Check it came up:

```bash
curl http://localhost:52123/health
```

### If `fastapi dev` crashes on Windows

You may see `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f40d'`. The FastAPI CLI prints an emoji in its banner and the default Windows console codepage cannot encode it. This is unrelated to PictoPy. Either use `python main.py`, or set the encoding first:

```bash
set PYTHONIOENCODING=utf-8
```

## How sharing is wired

Three listeners, and only one of them is reachable from the network:

| Process | Address | Reachable from |
| --- | --- | --- |
| Main backend | `localhost:52123` | this machine only |
| Sync microservice | `localhost:52124` | this machine only |
| Share server | `0.0.0.0:52125` | any device that can route here |

The share server is a **second FastAPI app running inside the backend process**. It starts on demand when the first share is created and stops when the last one is revoked, so no port is left open while nothing is shared. If `52125` is busy it tries the next few ports.

The main backend is never bound beyond localhost, because it exposes shutdown, delete and metadata routes that must not be reachable by other devices. The share server only ever exposes `/s/{token}` and the two media routes beneath it.

Active shares live **in memory only**. There is no table and no file: quitting PictoPy ends every share, and no token is ever written to disk.

## Sharing an album by hand

### Find an album id

```bash
curl http://localhost:52123/albums/
```

### Start a share

```bash
curl -X POST http://localhost:52123/share/albums/<album_id> -H "Content-Type: application/json" -d "{}"
```

Add an expiry in minutes if you want one:

```bash
curl -X POST http://localhost:52123/share/albums/<album_id> -H "Content-Type: application/json" -d "{\"expires_in_minutes\": 120}"
```

The response carries the token and one candidate URL per network interface:

```json
{
  "success": true,
  "message": "Album is now shared on the local network",
  "data": {
    "token": "<share_token>",
    "album_name": "The Oddyseys",
    "image_count": 18,
    "port": 52125,
    "urls": [
      { "interface": "Wi-Fi", "ip": "10.170.93.60", "url": "http://10.170.93.60:52125/s/<share_token>" }
    ]
  }
}
```

### Pick the right URL

The list is ranked best-guess first — the interface holding the default route wins, virtual adapters such as VMware and WSL sort last, and disconnected interfaces sort below live ones. A machine with virtual adapters can easily surface four candidates, so **the first entry is a ranked guess, not a guarantee**. If the phone cannot load one, try the next.

You can inspect the ranking without creating a share:

```bash
curl http://localhost:52123/share/interfaces
```

### Open it

Put the chosen URL into the phone's browser, on the same Wi-Fi. The page needs no app and no account.

### List and revoke

```bash
curl http://localhost:52123/share/
```

```bash
curl -X DELETE http://localhost:52123/share/<token>
```

Revoking the last share stops the network listener entirely.

## When the phone cannot connect

Work through these in order.

**Check the firewall profile, not just the rule.** Windows commonly creates *Private*-only rules, and most Wi-Fi networks are classified *Public*. A Private-only rule on a Public network fails silently. Rules are per-binary rather than per-port, so a rule covering the
Python interpreter or `PictoPy_Server` covers whatever port sharing lands on.

```powershell
Get-NetConnectionProfile | Select-Object Name, NetworkCategory
```

**Confirm both devices are on the same network.** A laptop on wired Ethernet and a phone on Wi-Fi are often on different subnets. Some networks route between them and some deliberately do not.

**Suspect the network itself.** Many networks block device-to-device traffic — this is called AP or client isolation, and it is close to universal on guest Wi-Fi and common on corporate networks. If it is enabled, nothing on the PictoPy side can work around it.

To tell an isolated network apart from a broken setup, use a phone hotspot: connect the laptop to the phone's hotspot and share again. If it works there, the code is fine and the other network is blocking peer traffic. USB tethering does the same job and is more reliable still.

## Internet mode

Everything above is the local-network path. Reaching a share from outside the network is handled entirely on the Tauri side rather than in this backend: `frontend/src-tauri/src/services/tunnel.rs` spawns the system `ssh` client as a reverse tunnel to the share port, parses the assigned URL from its output, and closes it when PictoPy exits.

The backend needs no changes for this — the share server is already bound to `0.0.0.0`, so a tunnel forwarding to its port reaches it exactly as a phone on the LAN would. Nothing about tokens, passwords or expiry differs between the two modes.

## Running the tests

```bash
cd backend && pytest tests/test_share_routes.py tests/test_share_registry.py tests/test_network_utils.py
```

These cover token issue, expiry and revocation, the interface ranking, and the security invariants — most importantly that an image belonging to a different album cannot be fetched through a share token, and that the share server exposes nothing beyond `/s/{token}`.
