# Design System Specification: The Ethereal Educator

## 1. Overview & Creative North Star: "The Digital Curator"
This design system moves away from the rigid, utilitarian nature of traditional educational management tools. Instead, it adopts the persona of **The Digital Curator**. The goal is to provide teachers with a workspace that feels like a premium digital atelier—spacious, calm, and intellectually stimulating.

We achieve this through **Organic Modernism**: a layout philosophy that favors breathing room over borders, and tonal depth over structural lines. By utilizing large radii (up to 3rem), glassmorphism, and intentional asymmetry, the H5 app transforms from a "form to fill" into a "canvas to manage."

---

## 2. Colors: Tonal Depth & The "No-Line" Rule
The palette is rooted in Material Design 3 Purple, but applied with editorial restraint. 

### The "No-Line" Rule
**Explicit Instruction:** Prohibit the use of 1px solid borders for sectioning or containment. Boundaries must be defined solely through background color shifts or subtle tonal transitions.
*   *Instead of a border:* Place a `surface-container-low` (#F7F2FA) card on a `surface` (#FFFBFF) background.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers, like stacked sheets of frosted glass.
*   **Level 0 (Base):** `surface` (#FFFBFF) - The infinite canvas.
*   **Level 1 (Subtle Inset):** `surface-container-low` (#F7F2FA) - Used for grouping minor related items.
*   **Level 2 (The Workhorse):** `surface-container` (#F1ECF4) - The primary background for interactive modules.
*   **Level 3 (High Focus):** `surface-container-highest` (#E6E0E9) - Used for temporary modal-like surfaces or highlighted teacher tasks.

### The Glass & Gradient Rule
*   **Navigation:** Use `white/80` with `backdrop-blur-xl` for bottom tabs and top headers. This ensures the content "bleeds" through, maintaining a sense of place.
*   **Signature Textures:** For high-impact CTA buttons or Hero sections, use a linear gradient: `primary` (#702ae1) to `primary-container` (#b28cff) at a 135-degree angle. This provides "soul" and prevents the UI from feeling flat and clinical.

---

## 3. Typography: Editorial Authority
We pair **Manrope** (Latin) with **PingFang SC** (Chinese) to create a tech-forward yet accessible tone.

*   **Display & Headlines:** Use `display-md` (2.75rem) for empty states or dashboard greetings. The oversized scale conveys confidence.
*   **Titles:** `title-lg` (1.375rem) is the standard for card headers. Ensure a generous `line-height` (1.5) to maintain the editorial feel.
*   **Body:** `body-md` (0.875rem) is the workhorse. Use `on-surface-variant` (#5d5b5f) for descriptions to reduce visual noise.
*   **Chinese Specifics:** For Chinese characters, increase the `letter-spacing` by 0.02em in headlines to prevent the "dense block" look common in mobile H5 apps.

---

## 4. Elevation & Depth: Tonal Layering
We replace drop shadows with **Ambient Light** and **Tonal Stacking**.

*   **The Layering Principle:** Depth is achieved by stacking tiers. A `surface-container-lowest` card placed on a `surface-container-low` section creates a soft, natural lift without needing a single pixel of shadow.
*   **Ambient Shadows:** If an element must "float" (e.g., a Floating Action Button), use a highly diffused shadow: `box-shadow: 0 12px 32px -4px rgba(112, 42, 225, 0.08)`. The shadow is tinted with the `primary` color, not grey, to mimic natural refraction.
*   **The "Ghost Border" Fallback:** If accessibility requires a container edge, use `outline-variant` (#afacb1) at **15% opacity**. High-contrast, 100% opaque borders are strictly forbidden.

---

## 5. Components: Fluidity & Tactility

### Pill-Shaped Buttons (The Signature Component)
*   **Primary:** Pill-shaped (9999px), Gradient background, `on-primary` text.
*   **Secondary:** `surface-container-high` background, `primary` text. No border.
*   **State:** On press, reduce scale to `0.96` to provide tactile feedback without complex animations.

### Cards & Lists
*   **The Divider Ban:** Never use horizontal `<hr>` lines. Use `1.5rem` (3xl) or `1rem` (2xl) vertical white space to separate list items.
*   **Grouping:** Use a `surface-container-low` background for the entire list block, with individual items separated by nothing but space.

### Interaction Elements
*   **Input Fields:** Ghost-style. No bottom line, no box. Use a `surface-container` background with a `1rem` (2xl) radius. The label sits in `label-md` above the field in `on-surface-variant`.
*   **Chips:** Pill-shaped, using `primary-90` for background and `on-primary-container` for text. They should feel like soft organic "bubbles."

---

## 6. Do's and Don'ts

### Do
*   **Do** embrace asymmetry. In a dashboard, a large "Greeting" card on the left followed by two smaller cards on the right creates visual interest.
*   **Do** use `animate-fade-up` (16px travel) for all page transitions to give the app a "rising" airy feel.
*   **Do** use Material Symbols Outlined with a weight of `300` to maintain the delicate, high-end aesthetic.

### Don't
*   **Don't** use 100% black (#000) for text. Always use `on-surface` (#2f2e32) to keep the purple-tinted harmony.
*   **Don't** use "Card Shadows" as a default. Use background color shifts first.
*   **Don't** cram content. If a screen feels full, it needs more vertical scrolling space. The "Digital Curator" never rushes the user.

---

## 7. Animation Philosophy
Every interaction must feel intentional.
*   **Entrance:** Elements should use `animate-fade-up` with staggered delays (50ms increments) to create a "waterfall" effect when a teacher opens a class list.
*   **Micro-interactions:** Toggles and radio buttons should morph smoothly, using a `cubic-bezier(0.34, 1.56, 0.64, 1)` spring curve to feel bouncy and responsive.