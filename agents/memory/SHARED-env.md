# Shared Memory — Environment

Environment facts, hardware constraints, deployment targets, and tool/infrastructure gotchas.

---

## Environment

- **Student hardware:** Chromebook, 1366x768 viewport, trackpad input, integrated GPU
- **Browser target:** Chrome (latest stable on ChromeOS)
- **Deploy target:** Firebase Hosting + Cloud Functions v2

## Known Gotchas — Environment & Infrastructure

- **Python 3.14 compat** — System Python is 3.14.3 (very new). Some packages (lxml, snowballstemmer) pin older versions that lack 3.14 wheels and fail to build from source. Workaround: install the package `--no-deps`, then install its dependencies separately — newer versions of the pinned deps usually work fine at runtime even if version specifiers don't match.
