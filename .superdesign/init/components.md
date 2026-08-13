# Components

SilentGuard currently uses a static HTML/CSS frontend without standalone reusable component files. Shared UI primitives are represented by CSS classes rather than exported components.

## CSS-Based Primitives

- `.panel`: white elevated content container
- `.primary-button`: dark primary action button
- `.secondary-button`: light secondary action button
- `.result-card`: metric/status card
- `.status-banner`: feedback state banner
- `.email-recipient-card`: email input/status container
- `.scenario-card`: selectable sample scenario card

Source files:

- `front/index.html`
- `front/style.css`
- `front/app.js`
