# Design System Document: Academic Sophistication for the Modern Campus

## 1. Overview & Creative North Star
**Creative North Star: "The Academic Curator"**

In the context of a medical university, "professionalism" often falls into the trap of looking clinical or sterile. This design system rejects that. Instead, it adopts the persona of a **Digital Curator**: an authoritative yet fluid editorial experience that prioritizes clarity, intellectual depth, and calm.

To move beyond the "standard app" look, we leverage **intentional asymmetry** and **tonal layering**. We break the rigid grid by allowing large headlines to drive the layout, using white space as a structural element rather than a void. This is not just an assistant; it is a premium tool that reflects the prestige of a medical institution.

---

## 2. Colors & Surface Philosophy

The palette is rooted in a deep, scholarly purple, balanced by a sophisticated range of neutral surfaces that mimic the texture of fine ivory paper.

### The Palette (Token Mappings)
*   **Primary Tier:** 
    *   `primary`: #630ed4 (The core brand anchor)
    *   `primary_container`: #7c3aed (Action surfaces)
    *   `on_primary_fixed`: #25005a (Deepest contrast for text on light backgrounds)
*   **Surface Tier:**
    *   `background`: #f7f9fb (Cool, clinical slate-tinted white)
    *   `surface_container_lowest`: #ffffff (Pure card elevation)
    *   `surface_container_low`: #f2f4f6 (Section grouping)
*   **Semantic Tier:**
    *   `success`: #059669 | `warning`: #d97706 | `error`: #ba1a1a

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders for sectioning or containment. Boundaries must be defined solely through background color shifts. 
*   *Implementation:* A `surface_container_lowest` card should sit on a `surface_container_low` background. The contrast is felt, not seen as a harsh line.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of semi-transparent materials. 
*   **Level 0:** `background` (The base)
*   **Level 1:** `surface_container_low` (In-page sectioning)
*   **Level 2:** `surface_container_lowest` (The interactive card)

### The "Glass & Gradient" Rule
For high-impact elements (Hero headers, persistent CTAs), use a signature gradient transitioning from `primary` (#5B21B6) to `primary_container` (#8B5CF6) at a 135-degree angle. For floating navigation bars, use **Glassmorphism**: `surface_container_lowest` at 80% opacity with a 20px backdrop-blur to allow the content to "bleed" through softly.

---

## 3. Typography: The Editorial Voice

We prioritize **Chinese-first typography** using a clean, modern sans-serif stack (system defaults like PingFang SC), supplemented by **Manrope** for alphanumeric characters to provide a global, academic feel.

*   **Display (Display-LG/MD):** Used for large, expressive data points or welcome messages. These should be set with tight letter spacing (-0.02em) to feel intentional.
*   **Headlines (Headline-SM):** 1.5rem. Your primary navigational anchor. Use high-contrast colors (`on_surface`) to command attention.
*   **Title (Title-MD):** 1.125rem. Used for card headers. This is the "Label" of the academic file.
*   **Body (Body-MD):** 0.875rem. The workhorse. Ensure a generous line height (1.6) to accommodate complex medical terminology without visual crowding.
*   **Labels (Label-SM):** 0.6875rem. All-caps for English or bold for Chinese to denote status or categories.

---

## 4. Elevation & Depth

We avoid the "Material Design 1" look. Depth is achieved through light and tone, not darkness and shadows.

*   **The Layering Principle:** Instead of shadows, use the Spacing Scale to create "breathing room." A card's importance is signaled by its proximity to white (`surface_container_lowest`).
*   **Ambient Shadows:** If a card must "float" (e.g., a critical notification), use a tinted shadow: `rgba(124, 58, 237, 0.08)` with a 40px Blur and 10px Y-offset. It should feel like a soft purple glow, not a grey smudge.
*   **The "Ghost Border" Fallback:** If accessibility requires a stroke, use `outline_variant` at **15% opacity**. This provides a hint of a boundary without breaking the "No-Line" rule.

---

## 5. Components

### Cards & Lists
*   **Rule:** Forbid divider lines. Use `1.5rem` (md) vertical white space to separate items.
*   **Styling:** Large rounded corners (`lg`: 2rem / 32px) for main containers.
*   **Interactions:** On press, a card should not "shrink," but rather shift its background color to `surface_container_high`.

### Buttons
*   **Primary:** Uses the signature Purple Gradient. No border. Roundedness: `full` (pill-shape) for actions, `md` (24px) for utility.
*   **Secondary:** `primary_fixed` background with `on_primary_fixed` text. This provides a soft, "academic ink" look.
*   **Tertiary:** No background. Text only in `primary`.

### Input Fields
*   **Visuals:** Forgo the "bottom line" or "heavy box." Use a `surface_container_high` filled background with `sm` (0.5rem) rounded corners.
*   **States:** On focus, the background remains, but a `primary` 2px "Ghost Border" (20% opacity) appears.

### Signature Component: The "Medical Insight" Chip
*   A specialized chip for campus status. Background: `surface_tint` at 10% opacity. Text: `primary`. This provides a "highlighted text" effect similar to a researcher's mark-up.

---

## 6. Do's and Don'ts

### Do:
*   **Use Asymmetric Margins:** Give the left side of your typography more "air" than the right to create an editorial feel.
*   **Embrace Large Radii:** Stick to `lg` (2rem) for any container that holds content.
*   **Prioritize Hierarchy:** Use `primary` color only for the most important action on the screen.

### Don't:
*   **Don't use 100% Black:** Never use #000000. Use `on_surface` (#191C1E) for a softer, premium contrast.
*   **Don't use Divider Lines:** If you feel the need for a line, increase your padding or change the background tone instead.
*   **Don't use Default Shadows:** Standard grey shadows look "cheap." Always tint your shadows with the primary purple.
*   **Don't Crowd the Header:** The top of the mobile screen (375px) should always have at least 24px of "empty" breathing room below the status bar.

---
*This system is designed to evolve. When in doubt, prioritize the "calmness" of the interface over the density of the data.*