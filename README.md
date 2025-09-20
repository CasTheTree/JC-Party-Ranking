# Song Score Cards — GitHub Pages

A static, single-file web app that turns a scores CSV (+ optional avatars ZIP and people CSV) into **transparent PNG** cards per song. Runs fully in the browser.

## Publish on GitHub Pages

1. **Create a new repo** on GitHub, e.g. `song-score-cards`.
2. **Upload these files** to the repo root:
   - `index.html`
   - `404.html`
   - `.nojekyll`
   - `assets/` (optional, for any images/icons you add)
3. Commit to the **`main`** branch.
4. In the repo: **Settings → Pages**:
   - **Source:** `Deploy from a branch`
   - **Branch:** `main` / `/ (root)`
5. Your site will build in ~1 minute. The URL will look like:
   - `https://<your-username>.github.io/song-score-cards/`

## Optional: custom domain
- In Settings → Pages, add your domain (e.g. `cards.example.com`). Then, create a `CNAME` DNS record pointing to `<your-username>.github.io.`

## Local preview
Just open `index.html` in a modern browser (Chrome/Edge/Firefox/Safari). No server required.

---

Built from a Streamlit app into static HTML/JS (Papa Parse + JSZip + FileSaver).
