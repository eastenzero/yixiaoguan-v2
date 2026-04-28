### A. Existing SCSS inventory

| Variable | Teacher value | Student value | Notes |
|---|---|---|---|
| `$primary` | `#702ae1` | `#7C3AED` (via `$primary-40`) | unified → `#5b21b6` |
| `$surface` | `#faf5fb` | (n/a) | unified → `$bg-page` |
| `$on-surface` | `#2f2e32` | (n/a) | unified → `$text-primary` |
| `$bg-page` | (n/a) | `#F8FAFC` | unified → `#f9fafb` |
| `$bg-card` | (n/a) | `#FFFFFF` | unified → `#ffffff` |
| `$text-primary` | (n/a) | `#0F172A` | unified → `#111827` |
| `$text-secondary` | (n/a) | `#475569` | unified → `#6b7280` |
| `$success` | (n/a) | `#059669` | same in both |
| `$warning` | (n/a) | `#D97706` | same in both |
| `$error`/`$danger` | `#b41340` | `#DC2626` | unified → `#dc2626` |

**Conflicts found:** `$primary`, `$bg-page`, `$text-primary`, `$text-secondary`, `$surface`, `$on-surface` had different values across apps.

### B. Backward-compat aliases added

- **student-app:** `$primary-40 → $primary`, `$primary-90 → $primary-soft`, `$on-primary → $primary-on`, `$error → $danger`, `$border-color → $border`, `$text-tertiary → $text-muted`, `$bg-secondary → $bg-page`, `$font-family → $font-family-sans`
- **teacher-app:** `$surface → $bg-page`, `$on-surface → $text-primary`, `$background → $bg-page`, `$on-surface-variant → $text-secondary`, `$font-body/headline/label → $font-family-sans`, `$primary-container → $primary-soft`, `$primary-dim → $primary-hover`, `$primary-fixed-dim → $primary-soft`, `$on-primary-container → $primary`, `$on-primary-fixed → $text-inverse`, `$outline-variant → $border`, `$secondary-container → #ddd6fe`, `$tertiary-container → #fbcfe8`, `$surface-container*`, `$elevation-1/2/3`, `$gradient-primary/hero/btn`, `$error-container → #fee2e2`, `$backdrop-bar`, plus ~20 more MD3 aliases.

### C. Files created

- `apps/teacher-app/src/styles/tokens.scss` (157 lines)
- `apps/student-app/src/styles/tokens.scss` (157 lines)
- **Identical?** Yes (byte-for-byte copy)

### D. Files modified

- `apps/teacher-app/src/App.vue`: added `@import './styles/tokens.scss';` before global.scss; kept Manrope `@font-face`
- `apps/teacher-app/index.html`: added Material Symbols Outlined Google Fonts link
- `apps/teacher-app/src/styles/theme.scss`: removed conflicting definitions (`$primary`, `$surface`, `$on-surface`, etc.); now imports tokens.scss and keeps only leftover MD3 vars (`$primary-fixed`, `$on-secondary*`, `$on-tertiary*`, `$error-dim`, `$on-error`, `$on-error-container`)
- `apps/teacher-app/src/uni.scss`: added `@import '@/styles/tokens.scss';` before theme.scss (required so auto-injected `uni.scss` provides tokens to all pages)
- `apps/teacher-app/src/styles/global.scss`: no changes (no hardcoded hex to replace)
- `apps/student-app/src/App.vue`: added `@import '@/styles/tokens.scss';` before theme.scss; added Manrope `@font-face`; updated `font-family` to `'Manrope', 'PingFang SC', system-ui, sans-serif`; changed page `background` and `color` to token variables
- `apps/student-app/src/styles/theme.scss`: removed conflicting definitions (`$primary-40`, `$primary`, `$bg-page`, `$bg-card`, `$text-primary`, `$text-secondary`, `$text-inverse`, `$success`, `$warning`, `$error`, `$border-color`, `$font-family`, `$bg-secondary`); now imports tokens.scss and keeps only `$primary-10/20/30/50/60/70/80/95` and `$transition-base`

### E. Build verification

- **teacher-app build:** success (H5)
- **student-app build:** success (H5)

### F. Pending / followups for Sprint 2

- Verify Manrope font actually loads on student-app (CDN URL copied from teacher-app)
- Pages still hardcoding colors (top 3 offenders):
  - teacher: `dashboard/index.vue` (43), `questions/detail.vue` (20), `components/TopAppBar.vue` (5)
  - student: `home/index.vue` (85), `history/history.vue` (15), `components/CustomTabBar.vue` (5)
- Sprint 2 priority: rewrite `home/index.vue` and `dashboard/index.vue` to use token variables instead of hardcoded hex
- Visual regression: not tested (no screenshot tooling); user should spot-check after pulling
