# Design QA — Premium Home Cover

- Source visual truth: `/var/folders/yd/75r1k1790gjd9wqmgg4vhdz00000gn/T/codex-clipboard-4eacf1d6-f34a-487b-b57c-60e806e0961b.png`
- Implementation screenshot: `design-evidence/home-390-v5.png`
- Viewport: 390 × 844
- State: home route, initial scroll position, entrance motion completed
- Browser: Codex in-app browser

## Full-view comparison evidence

The original proposal and `home-390-v5.png` were opened together in one comparison input. The implementation keeps the proposal's deep-violet identity, prominent greeting, AI entry, four primary actions, library story, and persistent navigation while intentionally increasing the cover's visual scale. The Yellow River Library is now a full-width photographic focal point rather than a faint decorative outline.

## Focused region comparison evidence

The above-the-fold region was reviewed at native 390px width. The brand lockup, 36px greeting, library crop, translucent location plaque, AI command bar, four primary actions, and tab-bar clearance remain fully visible without horizontal overflow or clipped controls. A separate lower-page crop was unnecessary because this iteration changes the cover only.

## Required fidelity surfaces

- Fonts and typography: strong editorial hierarchy; compact English eyebrow and UI labels remain legible; Chinese title wrapping is intentional and stable.
- Spacing and layout rhythm: the final 366px carousel cover creates impact without overextending the first screen; the AI command bar and four primary actions remain visible above the fold.
- Colors and tokens: deep violet, warm ivory, white, and restrained lime online status produce clear contrast and remain consistent with the app theme.
- Image quality and asset fidelity: four official university photographs are resized for mobile delivery, remain sharp at 390px, and use deliberate center crops without placeholder artwork.
- Copy and content: greeting, student name, library identity, AI promise, and primary task labels are realistic and concise.

## Findings

- No P0/P1/P2 findings remain.
- P3: confirm internal reuse approval for the selected official-site photographs before production release.

## Interaction and technical checks

- AI command bar click navigates to `#/pages/chat/index`.
- Browser console checked: no errors.
- `npm run type-check`: passed.
- `npm run build:h5`: passed.

## Comparison history

1. Earlier `home-390-v4.png`: architecture was reduced to a low-opacity texture, the title hierarchy was conservative, and the cover lacked a memorable focal point.
2. First fix: promoted the library to a full-bleed image and introduced editorial greeting typography in `home-390-v5.png`.
3. Final fix: reduced the cover height to 366px and replaced the single image with four official campus photographs plus autoplay, swipe, and numbered controls.
4. Post-fix evidence: `design-evidence/home-390-v6.png`; no actionable P0/P1/P2 differences remain.

## Follow-up — Official campus carousel and Chat UI

- Official source: [山一大全景校园](https://www.sdfmu.edu.cn/index/xysh/qjxy.htm)
- New implementation screenshots: `design-evidence/home-390-v6.png`, `design-evidence/home-390-v6-activity.png`, `design-evidence/chat-390-v3-welcome.png`
- Viewport: 390 × 844
- State: home carousel first slide and activity-center slide; chat empty state

### Home cover

Four official campus photographs are used as real assets: Yellow River Library, campus avenue, University Student Activity Center, and lakeside campus. The cover is reduced to 366px, supports autoplay, swipe gestures, and direct slide selection through 01–04 controls. Visual review confirmed legible copy and safe cropping on both the library and activity-center slides.

### Chat page

The empty chat state is now a compact Campus AI Desk layout with a deep-violet welcome panel, online status, streaming/interruption capability tags, four functional starter prompts, and a floating glass input dock above the tab bar. The starter prompt was clicked in-browser and produced a real streaming state; the resulting AI response rendered with source citations. Browser console had no errors.

### Follow-up comparison history

1. Earlier chat empty state: centered sparkle icon and generic white canvas made the second tab visually disconnected from the branded home.
2. Fix applied: introduced the Campus AI Desk panel, compact prompt grid, status hierarchy, and shared violet/warm-paper/glass tokens.
3. Post-fix evidence: `design-evidence/chat-390-v3-welcome.png`; no actionable P0/P1/P2 differences remain.

## Follow-up — Answer sources and teacher handoff

- Source visual truth: `/var/folders/yd/75r1k1790gjd9wqmgg4vhdz00000gn/T/codex-clipboard-6026627a-6336-44f9-a190-3c1357d2cd5b.png`
- Implementation screenshot: `design-evidence/chat-390-v4-response.png`
- Handoff state screenshot: `design-evidence/chat-390-v4-handoff.png`
- Viewport: 390 × 844
- State: completed AI answer with three sources; latest answer eligible for teacher escalation

### Comparison and findings

The reference chat phone and the completed implementation were opened together in one comparison input. The implementation now follows the reference's answer sequence: AI identity, readable response, compact numbered sources, and one purple teacher-handoff strip. Source rows use a consistent 01–03 hierarchy, verification metadata, and external-link affordance. The handoff strip appears only below the latest completed AI answer, so repeated messages do not create redundant escalation cards.

No P0/P1/P2 findings remain. The 6rem scroll safety spacer keeps the handoff strip clear of the fixed glass input dock.

### Interaction verification

- Starter prompt entered the streaming state and completed with sources.
- `转人工` was clicked successfully.
- The card changed to `已通知老师，请耐心等待回复`, and the input changed to the waiting state.
- Browser console: no errors.
- Type check and H5 production build: passed.

final result: passed
