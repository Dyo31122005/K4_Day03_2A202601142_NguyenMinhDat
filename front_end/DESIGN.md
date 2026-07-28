---
name: Serene Commerce Assistant
colors:
  surface: '#fbf9f4'
  surface-dim: '#dbdad5'
  surface-bright: '#fbf9f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3ee'
  surface-container: '#f0eee9'
  surface-container-high: '#eae8e3'
  surface-container-highest: '#e4e2dd'
  on-surface: '#1b1c19'
  on-surface-variant: '#444842'
  inverse-surface: '#30312e'
  inverse-on-surface: '#f2f1ec'
  outline: '#747871'
  outline-variant: '#c4c8bf'
  surface-tint: '#546250'
  primary: '#52604e'
  on-primary: '#ffffff'
  primary-container: '#6a7965'
  on-primary-container: '#f7fff1'
  inverse-primary: '#bbcbb5'
  secondary: '#7c5450'
  on-secondary: '#ffffff'
  secondary-container: '#ffcbc6'
  on-secondary-container: '#7b534f'
  tertiary: '#675a41'
  on-tertiary: '#ffffff'
  tertiary-container: '#817358'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d7e7d0'
  primary-fixed-dim: '#bbcbb5'
  on-primary-fixed: '#121f10'
  on-primary-fixed-variant: '#3d4a39'
  secondary-fixed: '#ffdad6'
  secondary-fixed-dim: '#eebab5'
  on-secondary-fixed: '#2f1311'
  on-secondary-fixed-variant: '#623d3a'
  tertiary-fixed: '#f3e0c0'
  tertiary-fixed-dim: '#d6c4a5'
  on-tertiary-fixed: '#231a06'
  on-tertiary-fixed-variant: '#51452d'
  background: '#fbf9f4'
  on-background: '#1b1c19'
  surface-variant: '#e4e2dd'
typography:
  display-lg:
    fontFamily: Playfair Display
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
  headline-sm:
    fontFamily: Playfair Display
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1200px
  gutter: 24px
  margin-desktop: 64px
  margin-mobile: 20px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style

The design system is rooted in the philosophy of "Warm Minimalism," drawing inspiration from Scandinavian and Japanese lifestyle aesthetics. The brand personality is empathetic, calm, and reassuring—transforming the typically stressful process of returns and refunds into a moment of quiet efficiency.

The target audience consists of discerning consumers who value high-end service and aesthetic clarity. The UI avoids the tropes of "AI technology" (no glowing particles or robotic motifs) in favor of a human-centric, editorial feel. 

**Design Movement: Minimalist + Tactile Softness**
- **Generous Whitespace:** Prioritize breathing room to lower user anxiety.
- **Organic Geometry:** High-radius corners and soft layering create an approachable, non-technical environment.
- **Lifestyle Editorial:** The interface should feel like a premium home goods catalog rather than a software tool.

## Colors

The palette is intentionally organic and muted to evoke a sense of home and comfort.

- **Background (#F9F7F2):** A warm cream "Off-White" that reduces eye strain and feels more premium than pure white.
- **Primary - Sage Green (#7D8C78):** Used for success states, primary actions, and key navigation. It represents growth and calm resolution.
- **Secondary - Dusty Rose (#D4A39E):** Used for soft accents, notifications, or secondary decorative elements.
- **Tertiary - Sand (#E5D3B3):** Used for subtle dividers, progress bars, and background fills for secondary cards.
- **Surface - Pure White (#FFFFFF):** Reserved for elevated cards to create a clear visual hierarchy against the cream background.

## Typography

This design system employs a sophisticated pairing of a classic serif for display and a high-utility sans-serif for functional text.

- **Headlines (Playfair Display):** Should be used for welcome messages, page titles, and important headers. The high contrast of this serif adds an editorial, premium layer to the experience.
- **Body & UI (Inter):** Used for all functional text, instructions, and input labels. Inter’s clarity ensures that complex refund information remains legible and accessible.
- **Styling Note:** Maintain a slight tracking (letter spacing) increase for labels and a slight decrease for large display headers to enhance the "lifestyle brand" feel.

## Layout & Spacing

The layout is centered around a "Focus Container" model to keep the user’s attention on the conversation and the refund process.

- **Grid:** A 12-column fluid grid for desktop with wide 64px margins to emphasize whitespace. For mobile, a single-column layout with 20px side margins.
- **Spacing Rhythm:** Based on an 8px base unit. Vertical rhythm should be generous—use `stack-lg` (48px) between major sections to prevent a "cluttered dashboard" look.
- **Alignment:** Content is primarily left-aligned for natural reading gravity, but headers can be centered for onboarding or success states to create a moment of celebration.

## Elevation & Depth

Depth is conveyed through soft, natural stacking rather than harsh shadows. The design system uses **Ambient Shadows** and **Tonal Layers**.

- **Level 0 (Base):** The Cream background (#F9F7F2).
- **Level 1 (Cards):** Pure White (#FFFFFF) surfaces with a very soft, diffused shadow (Blur: 32px, Y: 8px, Opacity: 4% Black). These appear to float gently above the base.
- **Interactive Depth:** When a card or button is pressed, it should subtly "sink" (reduce shadow) to provide tactile feedback.
- **Glassmorphism (Minimal):** Use a subtle backdrop blur on fixed headers or navigation bars to maintain a sense of space while scrolling.

## Shapes

The shape language is defined by oversized, friendly radiuses that mimic organic forms.

- **Primary Radius:** 24px (rounded-xl) for main content cards and primary containers.
- **Secondary Radius:** 16px (rounded-lg) for buttons and input fields.
- **Full Radius:** Use pill-shapes for tags, chips, and the "AI Chat" bubbles to keep them distinct from functional UI cards.
- **Visual Style:** Avoid any sharp 90-degree corners to maintain the reassuring, non-confrontational aesthetic.

## Components

### Buttons
- **Primary:** Filled Sage Green (#7D8C78) with white text. High-pill radius. No heavy gradients; use a subtle 10% darker hover state.
- **Secondary:** Transparent with a thin Sand (#E5D3B3) border or a Tertiary Sand fill.

### Cards
- Always use a White (#FFFFFF) background on the Cream base.
- Padding should be generous (typically 32px).
- Incorporate lifestyle photography or soft-line illustrations within cards to provide context for the refund reason.

### Input Fields
- Soft Sand-colored borders (#E5D3B3) that turn Sage Green on focus.
- Backgrounds should be a slightly darker cream or white to differentiate from the page background.
- Label text should be Inter Bold at 14px (Label-md).

### Chat Bubbles
- **User:** Soft Sand (#E5D3B3) background, right-aligned.
- **Assistant:** White (#FFFFFF) with a thin border or soft shadow, left-aligned.
- **Note:** Never use a robot icon. Use a simple, elegant initial or a soft lifestyle-inspired abstract shape for the assistant's avatar.

### Chips & Status
- Use low-saturation pastel backgrounds for status chips (e.g., a very light Sage for "Refunded," a very light Rose for "Action Required").