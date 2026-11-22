# Keys and YouTube setup (all free)

## 1. Pollinations key (images and text)

1. Go to https://enter.pollinations.ai and sign in.
2. Create a key and save it in `secrets/pollinations_key.txt` (one line).

Without a key it still works, but images wait about 45 s each and carry a watermark strip (cropped automatically).

## 2. Google Cloud OAuth client (upload to YouTube)

One Google Cloud project can serve all your channels.

1. https://console.cloud.google.com → create a project (e.g. "My Shorts Uploader").
2. **APIs & Services → Library** → enable **YouTube Data API v3**.
3. **OAuth consent screen** (Google Auth Platform → Branding): app name, support email, and if possible a homepage and a privacy policy URL on a domain you own. Audience: **External**.
4. **Audience → Publish app** (move it from Testing to **In production**). In Testing mode tokens expire every 7 days and brand-account channels are often blocked (error 403 access_denied).
5. **Clients → Create client → Desktop app** → download the JSON → save it as `secrets/client_secret.json`.

Quota: the default 10,000 units/day allows about 6 uploads per day (1,600 units each), enough for 2 to 3 channels at 2 videos/day.

## 3. Create the channel, then authorize it

1. On YouTube: profile picture → Settings → **Add or manage your channels** → **Create a channel**. A brand-account channel is best (you can add managers later).
2. `toonshorts authorize <slug>`, sign in and **choose the channel** in the account list.
3. You will see "Google hasn't verified this app": click **Advanced → Go to (your app)**. It is your own app.
4. Tick both permissions and continue.

If the last page never loads (embedded browsers, remote PCs), run `toonshorts authorize <slug> --paste`: open the link it prints, finish consent, copy the full `http://localhost...?code=...` address from the page that fails to load and paste it in the terminal.

## Unverified apps and private uploads

Videos uploaded through API projects created after July 2020 that have not passed Google's audit can be locked as **private**. If that happens, either make them public manually in YouTube Studio, or request the audit (YouTube API Services, "Audit and Quota Extension" form). The audit asks for a working privacy policy page.
