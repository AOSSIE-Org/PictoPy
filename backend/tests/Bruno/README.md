<!-- markdownlint-disable MD033 MD041 -->

<div align="center">
  <h1>PictoPy API Test Collection</h1>
  <p>Bruno collection covering all PictoPy backend endpoints ,request definitions, environment setup, and inline tests for every route.</p>
</div>

<p align="center">
  <a href="https://fetch.usebruno.com?url=git%40github.com%3AAOSSIE-Org%2FPictoPy.git">
    <img src="https://fetch.usebruno.com/button.svg" alt="Fetch in Bruno" height="32"/>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Bruno-v3.4.2-orange?style=flat&logoColor=white" alt="Bruno Badge"/>
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green?style=flat&logo=fastapi&logoColor=white" alt="FastAPI Badge"/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python&logoColor=white" alt="Python Badge"/>
  <img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=flat" alt="License Badge"/>
</p>

---

## What is Bruno

[Bruno](https://www.usebruno.com/) is a free, open-source API client that stores collections as plain files directly on disk — no cloud sync, no account required, no paywalled collaboration. The collection lives in the repo alongside the code it tests, meaning every contributor gets the same requests, environments, and test assertions by simply cloning the project.

---

## Prerequisites

Before using this collection, make sure you have:

- Bruno installed ([see below](#installing-bruno))
- PictoPy backend running locally on port `52123`
- Python 3.10+

---

## Installing Bruno

<table>
<tr>
<td><strong>Arch Linux</strong></td>
<td>

```bash
yay -S bruno-bin
```

</td>
</tr>
<tr>
<td><strong>macOS</strong></td>
<td>

```bash
brew install bruno
```

</td>
</tr>
<tr>
<td><strong>Windows / Other</strong></td>
<td>Download from <a href="https://www.usebruno.com/downloads">usebruno.com/downloads</a></td>
</tr>
</table>

---

## Quick Start

**1. Start the PictoPy backend**

```bash
For detailed setup instructions, coding guidelines, and on how to start the backend, please check out our [CONTRIBUTING.md](./CONTRIBUTING.md) file.
```

**2. Open the collection in Bruno**

- Launch Bruno
- Click **Open Collection**
- Navigate to `backend/tests/Bruno/` inside the cloned repo
- Click **Open**

**3. Activate the environment**

Click the environment dropdown (top right) → select **Local Development server**

**4. Verify the connection**

Send `GET {{baseUrl}}/health` — a `200 OK` response means you are ready to go.

---

## Fetch in Bruno

Click the button at the top of this page, or use this link directly:

```
https://fetch.usebruno.com?url=git@github.com:AOSSIE-Org/PictoPy.git
```

> **Note:** The fetch button points to the upstream `AOSSIE-Org/PictoPy` repository. If you are working from a fork, open the collection locally by following the Quick Start steps above instead.

---

## Environment Variables

The collection ships with a `Local Development server` environment pre-configured. No changes are needed for local development.

| Variable | Default Value | Description |
|---|---|---|
| `baseUrl` | `http://localhost:52123` | Backend base URL |
| `taskId` | *(set after download/setup)* | Task ID returned by download or setup endpoints |
| `albumId` | *(set after create album)* | Album ID returned by create album |
| `folderId` | *(set after add folder)* | Folder ID returned by add folder |
| `clusterId` | *(set after clustering)* | Cluster ID returned by face cluster endpoints |

`taskId` is set automatically via `bru.setVar()` in the Tests tab of the download and setup requests. The others are filled manually after running the relevant create endpoint.

---

## Running Tests

### Single request

Click any request → **Tests** tab to view assertions → click **Send**.

Results appear at the bottom of the response panel — green for pass, red for fail.

### Entire collection

Right click the **PictoPy** collection in the sidebar → **Run Collection** → Bruno runs every request in order and shows a full summary.

---

## Pytest Tests

Every endpoint also has automated pytest coverage inside `backend/tests/`. These run automatically on every push via GitHub Actions and are the source of truth for CI.

```bash
cd backend/tests
pytest -v
```

Bruno is for manual exploration and quick verification during development. Pytest is for automation.

---

## Contributing
<a href="https://discord.gg/hjUhu33uAn"><img src="https://img.shields.io/discord/1022871757289422898?style=flat&logo=discord&logoColor=white&logoSize=auto&label=Discord&labelColor=5865F2&color=57F287" alt="Discord" height="30"></a>

Join the **[Discord Server](https://discord.gg/hjUhu33uAn) (Go to Projects->PictoPy)** to chat with everyone.

##### If you add a new backend endpoint, include the Bruno request and tests in the same PR. Keep the folder structure aligned with the OpenAPI spec tags so the collection stays consistent with the codebase.


Don't forget to star this repository if you find it useful! ⭐

---

<p align="center">© 2026 AOSSIE</p>