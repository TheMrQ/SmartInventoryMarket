# Visual System

Status: `IN_PROGRESS` — P19 Inventory Control Room visual direction is approved for Dashboard refinement only. It must not be extended to other pages until separately approved.

## Intent

Smart Inventory Market is an operational workspace for managers making time-sensitive replenishment decisions. The visual system therefore favors legibility, calm hierarchy, and truthful evidence over dashboard decoration. One decision-focused surface may carry emphasis; the rest of the interface remains disciplined so stock risk, forecast evidence, and human-review actions are understandable at a glance.

## Typography

- **Inter Variable** is the body face for tables, forms, controls, navigation, supporting data, and long reading. Its compact clarity supports dense operations work.
- **Manrope Variable** is limited to page titles, major decision headlines, and principal quantitative values. Its broader geometry makes the most important operational signal distinct without reducing table density.
- Page titles use 30–34px, section headings use 18px, prominent metrics use 29–32px, body copy uses 14px, and supporting labels use 12px.
- Display type uses a restrained 700 weight; body uses normal-to-semibold weights. Avoid all-caps labels unless an existing data convention requires them.
- Quantitative values use `font-variant-numeric: tabular-nums` to keep changing counts visually stable.

## Palette and status semantics

| Role | Value | Use |
| --- | --- | --- |
| Deep navy | `#0F172A` | Navigation and high-contrast structural surfaces |
| Heading ink | `#172033` | Primary text and display metrics |
| Market blue | `#2563EB` | Primary actions, selected navigation, decision emphasis |
| Signal cyan | `#60A5FA` | Supporting blue signal accents only |
| Application canvas | `#F6F8FC` | Main workspace background |
| Alert amber | `#D97706` | Actual reorder/stockout attention, never decoration |
| Success green | `#15803D` | Healthy or completed states |
| Danger red | `#B91C1C` | Stockout/error states |

Status colors preserve their meaning across badges, data summaries, and charts. Text and surfaces do not rely on color alone: status names and accessible labels remain visible.

## Surfaces, borders, and spacing

There are three surface roles, deliberately reused rather than multiplied:

1. **Application canvas** — the quiet `#F6F8FC` workspace field.
2. **Operational panel** — white panels with fine cool-gray borders and near-flat shadows for charts, queues, tables, and supporting information.
3. **Decision panel** — a pale-blue surface with a primary-blue left rule, reserved for the immediate operational decision.

The spacing rhythm is 4, 8, 12, 16, 20, 24, and 28px. Borders establish grouping before elevation; shadows are light and only clarify interactive or layered surfaces. Rounded corners are compact (9–16px) and should not turn every data region into an identical card.

## Charts and data display

Charts must render only API-backed or persisted data. Dashboard charts use quiet horizontal gridlines, readable blue-gray axes, semantic series colors, and a white high-contrast tooltip surface. Gridlines support comparison rather than compete with values. Use tabular numeric formatting for counts; do not fabricate trend lines, forecast values, annotations, or empty-state data.

## Interaction and motion

Motion is a response to an action, not decoration. Buttons may lift one pixel and press back into place; rows can gain a subtle blue-gray reading surface; chart bars can soften on hover. Transitions use 160–200ms timing. Focus indicators remain a 3px light-blue outline with an offset. `prefers-reduced-motion` removes animation and reduces transition duration.

## Responsive and accessibility guidance

- Preserve a 320px minimum viewport and prevent layout-level horizontal overflow.
- At medium widths, Dashboard grids become one column or two summary columns; at narrow widths, the decision panel and summaries become a readable vertical sequence.
- Keep body text at 14px and supporting text at 12px rather than reducing data below legibility.
- Keep text/background contrast strong on white, canvas, navy, and decision surfaces. The market-blue action color is paired with text, icons, or labels rather than acting as the sole status signal.
- Keyboard focus, semantic headings, ARIA labels, and existing empty/loading states are part of the visual system and must remain intact.
