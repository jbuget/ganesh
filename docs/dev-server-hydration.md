# Open issue: no hydration under `next dev`

**Status: unresolved.** The application is fully functional in production; only
the development server is affected.

## Symptom

Under `pnpm dev` the page is rendered server-side (the HTML is correct and
complete) but React never hydrates:

- no `__reactFiber$…` key on the DOM nodes;
- buttons do not react, no `useState` ever updates;
- no request goes out to the BFF, so the grid stays empty;
- **no error** in the console, and every chunk answers `200`.

Under `pnpm build && pnpm start` everything works: the grid, click-to-enter,
totals, month-to-month navigation.

## What has been ruled out

| Lead | Verdict |
|---|---|
| Application code | Ruled out: a `page.tsx` cut down to a `useState` counter hydrates no better |
| `QueryProvider` / React Query | Ruled out: a minimal layout with no provider changes nothing |
| Turbopack | Ruled out: `next dev --webpack` reproduces exactly the same symptom |
| A missing chunk, or a 404 | Ruled out: all 17 scripts answer `200` |
| A CSP blocking inline scripts | Ruled out: no CSP header, no `nonce` |
| Build cache | Ruled out: `rm -rf .next` and a restart change nothing |
| Invalid HTML | Fixed along the way (see below), but with no effect on this issue |

## The remaining lead

The Chrome extension used for testing injects a script into the page
(`chrome-extension://…/injected.js`). In development Next also loads its
`next-devtools` overlay, absent in production — that is the main difference
between the two modes. Interference between the two is the most plausible
hypothesis, but it could not be confirmed for want of a browser without
extensions to test in.

**First test to run:** open `http://localhost:3000` in a private window, or in a
browser with no extension. If the page hydrates, the problem comes from the
extension and not from the project.

## A related note, this one fixed

One real defect was found and fixed during this investigation: `DayCell`
rendered a `<button>` as a direct child of `<tr>`, which is invalid HTML and
breaks React hydration. The component now renders `<td><button/></td>`, and a
test locks the regression down (`DayCell.test.tsx`, "is a table cell, not a bare
button in the row").
