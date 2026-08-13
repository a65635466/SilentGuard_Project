# Extractable Components

The frontend is static HTML/CSS and does not expose framework components suitable for Superdesign `DraftComponent` extraction.

## Panel

- Source: `front/style.css`
- Category: basic
- Description: Elevated white content container used throughout the app.
- Extractable props: none
- Hardcoded: CSS class `.panel`

## ResultCard

- Source: `front/style.css`
- Category: basic
- Description: Metric/status card used on the analysis result screen.
- Extractable props: none
- Hardcoded: CSS classes `.result-card`, `.result-label`, `.risk-score`, `.risk-level`

## EmailRecipientCard

- Source: `front/style.css`
- Category: basic
- Description: Email input and recipient display container.
- Extractable props: none
- Hardcoded: CSS classes `.email-recipient-card`, `.email-recipient-row`
