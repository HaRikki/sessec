# Reconstruction Limitations

This project is a *reconstruction* of what a browser can observe. It is not a copy of the original system.

## What cannot be cloned

- Server-side source code, business logic, databases, private APIs, API keys and credentials.

- Anything that depends on a logged-in session, payments, or third-party services you do not control.

- Dynamic behaviour implemented by server responses (search, filters, carts, comments, recommendations).

## How this project handles the gaps

- Forms were re-implemented against a *new* backend that stores submissions in your own database.

- Authentication (if present) is a new, empty user store - original accounts are not and cannot be imported.

- No passwords, cookies, session tokens or access tokens were collected from the original site.

- To rebuild private functionality, request an official API specification or database schema from the site owner.

## Snapshot caveats

- JavaScript was removed; pages are rendered snapshots. Trackers/analytics were always removed.

- Lazy-loaded content that never appeared while the page was scrolled may be missing.

- Assets hosted on third-party domains (other than common public font/library CDNs) were not downloaded.

- Embedded iframes (maps, videos) still load from their original providers.

## Legal

- Use this output only for websites you own or have written permission to copy. Respect licences of fonts, images and text.
