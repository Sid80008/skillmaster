# Skill Quest — Product & UI Design Specification

**Status:** Canonical Design Specification
**Product:** Skill Quest
**Platform:** Responsive Web Application
**Design Reference:** Stitch-generated Skill Quest screens
**Backend:** Existing FastAPI application
**Purpose:** Single source of truth for product UX, visual design, screen architecture, interaction behavior, and frontend implementation.

---

# 1. PRODUCT OVERVIEW

## 1.1 What is Skill Quest?

Skill Quest is an exploration platform designed to help users discover genuinely new skills, activities, and experiences.

The core loop is:

**Discover → Try → Reflect → Learn about yourself → Discover again**

The product is intentionally designed around **exploration rather than optimization**.

The user should frequently encounter experiences outside their existing experiential neighborhood.

The primary question of the product is:

> **What should I try next?**

---

# 2. CORE PRODUCT PHILOSOPHY

## 2.1 Exploration over optimization

Skill Quest should optimize for meaningful exploration, not maximum engagement.

The product should avoid encouraging:

* repeated consumption
* endless recommendation feeds
* streaks
* points
* leaderboards
* engagement farming
* familiar-content bubbles
* repeatedly doing activities the user already knows

Approximately **95% of normal EXPLORE experiences should be genuinely novel** according to the backend's exploration logic.

The frontend must not weaken or bypass this principle.

---

# 3. EXPLORATION MODES

Skill Quest has three distinct modes.

## 3.1 EXPLORE

The default mode.

Purpose:

> **Try something meaningfully new.**

Characteristics:

* broad
* varied
* unfamiliar
* experimental
* relatively low commitment
* one experience at a time

EXPLORE is the main product experience.

---

## 3.2 MIX

Purpose:

> **Discover an unexpected experience created from meaningful connections between things the user has already experienced.**

Example:

**Photography + 3D Printing → Photogrammetry**

MIX should feel like discovery through connection.

It should not feel like a conventional recommendation feed.

---

## 3.3 LOCK-IN

Purpose:

> **Go deeper into something the user has consciously chosen.**

LOCK-IN is explicitly user-controlled.

The AI/system may identify that something appears promising, but it **must never activate LOCK-IN automatically**.

The user makes the decision.

The product distinction is:

> **EXPLORE = breadth**

> **LOCK-IN = depth**

---

# 4. PRODUCT PERSONALITY

Skill Quest should feel:

* Curious
* Premium
* Experimental
* Energetic
* Clean
* Mature
* Slightly playful
* Intelligent
* Human

It should NOT feel:

* childish
* corporate
* generic SaaS
* overly gamified
* clinical
* excessively futuristic
* social-media-like
* productivity-dashboard-like

Avoid directly resembling:

* Netflix
* Duolingo
* Notion
* generic AI dashboards
* generic startup landing pages

---

# 5. DESIGN REFERENCE

The existing Stitch designs are the primary visual reference.

Currently established Stitch screens:

1. Explore
2. Quest Detail
3. Active Quest

Additional screens should extend the same visual language:

4. Completion + Feedback
5. Discovery Profile
6. Exploration History
7. MIX
8. LOCK-IN
9. Authentication / Welcome
10. Application Navigation Shell

Do not independently redesign each screen.

The entire product must feel like one coherent application.

---

# 6. VISUAL DESIGN SYSTEM

## 6.1 General visual direction

Use the visual language established by Stitch.

Maintain consistency in:

* typography
* spacing
* colors
* border radius
* cards
* borders
* icons
* buttons
* navigation
* hierarchy
* interaction states

Avoid unnecessary decorative complexity.

---

## 6.2 Layout

The interface should feel spacious rather than dense.

Hierarchy:

1. Primary action
2. Current context
3. Supporting information
4. Secondary actions

Do not turn every piece of information into a separate card.

Cards should represent meaningful groups of information.

---

## 6.3 Typography

Follow the typography established by Stitch.

Use a clear hierarchy:

### Display

For major moments such as:

* primary page heading
* major discovery statement
* completion state

### Heading

For:

* quest titles
* section headings
* major content blocks

### Body

For:

* descriptions
* instructions
* explanations

### Secondary

For:

* metadata
* duration
* difficulty
* environment
* social context

### Microcopy

For:

* labels
* badges
* statuses

Avoid excessive uppercase text.

---

# 7. COLOR

Use the existing Stitch color system.

Primary accent should be reserved primarily for:

* primary actions
* active navigation
* selection
* focus
* important interactive states

Do not make every surface the accent color.

Prefer neutral surfaces with intentional accent usage.

Semantic colors may communicate:

* success
* warning
* error
* information

Never communicate important information through color alone.

---

# 8. SURFACES

Maintain a restrained surface hierarchy.

Possible levels:

* page background
* primary surface
* secondary surface
* interactive surface
* selected surface

Avoid:

* excessive shadows
* excessive gradients
* glowing surfaces
* excessive glassmorphism
* unnecessary nested cards

---

# 9. COMPONENT CONSISTENCY

Use a reusable component system.

Recommended components:

* `AppShell`
* `Navigation`
* `PageHeader`
* `QuestCard`
* `QuestMetadata`
* `PrimaryButton`
* `SecondaryButton`
* `StatusBadge`
* `ProgressIndicator`
* `FeedbackControl`
* `SkillCard`
* `ActivityFamilyBadge`
* `CategoryBadge`
* `ProfileSection`
* `DNACharacteristic`
* `HistoryEntry`
* `MixConnection`
* `LockInStage`
* `EmptyState`
* `ErrorState`
* `LoadingState`

Components should consume data.

They should not contain hardcoded domain data.

---

# 10. NAVIGATION

Primary destinations:

* **Explore**
* **History**
* **Profile**
* **MIX**
* **LOCK-IN**

Explore is the default destination.

Navigation should remain minimal.

## Desktop

Use the navigation pattern established by Stitch.

## Mobile

Use a compact touch-friendly navigation pattern.

Do not introduce unnecessary destinations.

---

# 11. SCREEN: EXPLORE

## Purpose

Explore is the main page.

It answers:

> **What can I try this weekend?**

## Main content

Display the current backend-generated exploration recommendation.

The following must be live backend data:

* quest title
* skill
* activity family
* category
* description
* duration
* difficulty
* cost
* environment
* social context
* recommendation explanation
* attempt state

## Primary action

**Start Quest / Accept Quest**

The action must operate on the backend.

Never simulate acceptance locally.

## Supporting content

May include:

* exploration context
* lightweight exploration statistics
* recent exploration
* navigation to Profile/History/MIX/LOCK-IN

Supporting information must not overpower the current discovery.

## Empty state

If no suitable recommendation exists:

* explain that no current experience is available
* provide retry/reload where appropriate
* do not invent a recommendation

---

# 12. SCREEN: QUEST DETAIL

## Purpose

Allow the user to decide whether they want to try the experience.

The screen should answer:

* What is this?
* What will I do?
* How long will it take?
* What will I need?
* What counts as finishing?

## Content

Show real backend data:

* title
* skill
* family
* category
* objective
* learn content
* doing instructions
* finish criteria
* stretch goals
* difficulty
* duration
* cost
* environment
* social context
* equipment

## Primary action

**Start Quest**

The action must use the real backend state.

---

# 13. SCREEN: ACTIVE QUEST

## Purpose

Guide the user through the current experience.

The screen should feel focused and distraction-free.

## Content

Display:

* quest title
* objective
* learning material
* doing instructions
* finish criteria
* stretch goals
* current state

## Actions

Depending on backend state:

* Continue
* Complete
* Abandon

All state changes must be persisted through the backend.

Never create frontend-only completion/progress state.

---

# 14. SCREEN: COMPLETION + FEEDBACK

## Purpose

Close the exploration loop.

The completion moment should feel satisfying without becoming a game reward system.

Avoid:

* XP explosions
* streak celebrations
* excessive confetti
* badges everywhere
* leaderboard comparisons

## Feedback

Collect:

1. Enjoyment
2. Curiosity
3. Deep Dive Interest
4. Would Repeat
5. Felt Difficulty

Feedback should be fast.

Use intuitive controls such as:

* segmented scales
* rating controls
* buttons
* sliders where appropriate

Do not create a long survey.

## Primary action

**Submit Feedback**

After submission, return to the appropriate exploration state.

---

# 15. SCREEN: DISCOVERY PROFILE

## Purpose

This is not a social profile.

It answers:

> **What is my exploration revealing about me?**

## Content

Show real backend-derived information:

* exploration summary
* experienced skills
* explored categories
* explored activity families
* emerging characteristics
* Skill DNA
* cross-domain connections

Do not turn the screen into:

* leaderboard
* achievement dashboard
* productivity dashboard
* social profile

---

# 16. PROFILE VS SKILL DNA

These are different concepts.

## Profile

Behavioral/descriptive.

Example:

> You frequently experiment with hands-on activities.

## Skill DNA

Latent characteristics inferred from repeated evidence.

Example:

> Hands-on building + visual problem solving

Skill DNA should describe characteristics that can appear across unrelated domains.

Examples:

* experimentation
* precision
* visual thinking
* improvisation
* spatial reasoning
* hands-on construction
* collaboration
* problem solving

Do not present weak evidence as a permanent identity.

---

# 17. SCREEN: EXPLORATION HISTORY

## Purpose

Show the user's exploration journey.

Use a chronological structure.

Each entry can show:

* skill
* activity family
* category
* date
* completion state
* feedback summary
* mode

## Visual objective

The history should make **breadth** visible.

The user should be able to see how many different territories they have explored.

Do not make it look like a productivity log.

---

# 18. SCREEN: MIX

## Purpose

Present meaningful combinations discovered from the user's previous experiences.

## Structure

Each MIX candidate should communicate:

### Source A

First experienced skill/activity.

### Source B

Second experienced skill/activity from a distinct territory.

### Bridge

The meaningful mechanism connecting them.

### Result

The resulting skill/activity.

### Explanation

Why the combination makes sense.

### Action

Start MIX where supported.

## Example

**Photography**

*

**3D Printing**

↓

**Photogrammetry**

The bridge must be meaningful.

Never generate artificial combinations by simply concatenating keywords.

---

# 19. MIX VISUAL DESIGN

MIX should visually communicate connection.

Recommended conceptual composition:

```text
┌──────────────┐       ┌──────────────┐
│   SOURCE A   │       │   SOURCE B   │
│ Photography  │       │ 3D Printing  │
└──────┬───────┘       └──────┬───────┘
       │                       │
       └──────────┬────────────┘
                  ↓
           ┌──────────────┐
           │    BRIDGE    │
           │ 3D spatial   │
           │ reconstruction│
           └──────┬───────┘
                  ↓
           ┌──────────────┐
           │    RESULT    │
           │Photogrammetry│
           └──────────────┘
```

The result should feel surprising and meaningful.

---

# 20. SCREEN: LOCK-IN

## Purpose

Support deliberate deep learning.

LOCK-IN begins only when the user explicitly chooses it.

## Header

Clearly communicate:

**LOCK-IN**

Supporting message:

> You're moving from exploration to depth.

## Content

Show:

* selected skill
* current stage
* completed stages
* upcoming stages
* current activity
* overall progression

The backend is authoritative for progression.

---

# 21. LOCK-IN STATES

Possible states:

* No active LOCK-IN
* Active
* Paused where supported
* Completed
* Exited

The UI must reflect the actual backend state.

## Exit

Provide an explicit exit action.

Exiting must preserve historical information.

Never erase previous exploration.

---

# 22. AUTHENTICATION / WELCOME

Authentication should be minimal.

The user should reach the actual product quickly.

After authentication:

**Explore is the default destination.**

Handle:

* authentication loading
* invalid credentials
* expired session
* network failure
* logout

without breaking the application.

---

# 23. ROUTING

Recommended routes:

```text
/
 /auth
 /explore
 /quests/:attemptId
 /quests/:attemptId/active
 /quests/:attemptId/complete
 /history
 /profile
 /mix
 /lock-in
```

Protected routes must require authentication.

Browser refresh must preserve the current route.

Direct navigation to a valid route must work.

---

# 24. RESPONSIVE DESIGN

The application must support:

* Desktop
* Tablet
* Mobile

## Desktop

Use:

* persistent navigation where appropriate
* generous content width
* multiple columns when useful
* spacious layout

## Tablet

Collapse secondary content when necessary.

Keep the primary experience prominent.

## Mobile

Use:

* single-column layouts
* touch-friendly controls
* compact navigation
* readable typography
* clear primary actions

Never simply shrink the desktop design.

---

# 25. MOBILE RULES

Touch targets should be comfortably tappable.

Avoid:

* tiny icon-only controls
* hover-only interactions
* dense tables
* page-level horizontal scrolling
* desktop-only interactions

Primary actions must remain obvious.

---

# 26. LOADING STATES

All backend-driven screens need intentional loading states.

Prefer:

* skeletons
* subtle progress indicators
* preserved layout structure

Never display fake application data while waiting for the backend.

---

# 27. EMPTY STATES

Every data-driven section needs a meaningful empty state.

An empty state should explain:

1. What is empty
2. Why it may be empty
3. What the user can do next

Examples:

### History

> Your exploration journey starts here.

### MIX

> You haven't created enough cross-domain connections yet.

### LOCK-IN

> Nothing is locked in right now.

Do not populate empty states with invented data.

---

# 28. ERROR STATES

Errors should be:

* concise
* understandable
* actionable

Where possible provide:

**Retry**

Never expose raw backend stack traces to users.

---

# 29. INTERACTION PRINCIPLES

## Immediate feedback

Every important interaction should visibly respond.

## Backend authority

The backend is the source of truth.

## No fake progress

Never display progress that has not happened.

## No hidden mode changes

Important mode changes must be explicit.

Especially:

> **AI cannot activate LOCK-IN.**

---

# 30. RECOMMENDATION UX

Recommendations should not look like an infinite content feed.

Prefer:

> **One meaningful discovery**

over:

> **Twenty cards competing for attention**

The Explore page should create anticipation around the next experience.

---

# 31. NOVELTY COMMUNICATION

The backend internally manages novelty classifications.

Do not expose technical codes such as:

* N0
* N1
* N2
* N3
* N4
* N5

Instead, when useful, communicate them naturally:

* New territory
* Something different
* Outside your usual territory
* A new direction
* Unexpected connection

---

# 32. VARIETY

The system should explore across multiple dimensions:

* category
* activity family
* creative / technical
* physical / nonphysical
* social / solo
* screen / hands-on
* indoor / outdoor
* theory / practice
* construction / consumption
* individual / collaborative

Do not expose all these dimensions as a complicated user settings panel.

Variety should primarily be experienced through the recommendations.

---

# 33. USER CONTROL

The user controls:

* whether to accept a quest
* whether to start it
* whether to complete it
* whether to abandon it
* feedback
* whether to activate LOCK-IN
* whether to exit LOCK-IN

The system assists discovery.

It does not decide the user's identity or passions.

---

# 34. AI PRESENTATION

AI-generated explanations should be concise and useful.

AI may explain:

* why an experience is interesting
* what connection was discovered
* what characteristic may be emerging
* why a MIX candidate exists

AI must NOT:

* override core recommendation eligibility
* bypass novelty rules
* activate LOCK-IN
* fabricate history
* fabricate progress
* make unsupported psychological claims

---

# 35. DATA INTEGRITY

All runtime application data must originate from the backend.

Never hardcode:

* user information
* quest titles
* recommendations
* statistics
* profile values
* DNA values
* exploration history
* MIX candidates
* LOCK-IN progress
* feedback
* recommendation explanations

Static UI copy is allowed.

Mock data is allowed only in isolated development/test fixtures.

Mock data must never be part of production runtime behavior.

---

# 36. FRONTEND ARCHITECTURE

Create a clean API/service layer.

Do not scatter raw API requests across UI components.

Suggested organization:

```text
src/
  api/
    client
    auth
    quests
    profile
    exploration
    mix
    lockin

  components/
  pages/
  layouts/
  hooks/
  types/
  utils/
```

Adapt this structure to the existing frontend framework rather than rewriting the entire application unnecessarily.

---

# 37. SERVER STATE VS UI STATE

## Server state

Examples:

* current quest
* attempt
* attempt state
* profile
* DNA
* history
* MIX candidates
* LOCK-IN session
* progression

## UI state

Examples:

* selected tab
* open modal
* temporary form values
* navigation state
* feedback input before submission
* loading state

Never use UI state as a second source of truth for backend state.

---

# 38. API INTEGRATION

Existing backend endpoints include:

```text
GET  /api/v1/quests/current

GET  /api/v1/quests/attempts/{attempt_id}/challenge

POST /api/v1/quests/attempts/{attempt_id}/feedback

GET  /api/v1/quests/attempts/{attempt_id}/feedback

GET  /api/v1/profile/

GET  /api/v1/profile/dna

GET  /api/v1/profile/categories

GET  /api/v1/exploration/

GET  /api/v1/mix/candidates

POST /api/v1/lock-in/activate

GET  /api/v1/lock-in/current

POST /api/v1/lock-in/exit
```

Before integration:

* inspect actual response schemas
* inspect authentication requirements
* inspect request bodies
* inspect error responses

Never guess the API contract.

---

# 39. BACKEND RESPONSIBILITY

Do not duplicate backend business logic in the frontend.

The backend owns:

* novelty
* fatigue
* recommendation ranking
* profile calculation
* Skill DNA
* MIX discovery
* LOCK-IN progression
* historical state
* quest lifecycle

The frontend owns:

* presentation
* navigation
* interaction
* forms
* visual state
* API communication

---

# 40. CONTENT TONE

Copy should be:

* concise
* curious
* confident
* human
* slightly playful

Avoid:

* corporate jargon
* fake motivational language
* excessive hype
* AI-sounding copy
* productivity clichés

Prefer:

> **Try something different.**

over:

> **Unlock your ultimate potential through personalized experiential growth.**

---

# 41. MOTION

Motion should be subtle and purposeful.

Use motion for:

* page transitions
* state changes
* feedback
* MIX connections
* completion moments

Avoid:

* constant movement
* excessive bouncing
* distracting animations
* gamification-style celebration

Respect reduced-motion preferences.

---

# 42. ACCESSIBILITY

Support:

* keyboard navigation
* visible focus states
* semantic controls
* accessible labels
* adequate contrast
* readable typography
* touch-friendly controls
* screen-reader-compatible state changes

Never communicate important information through color alone.

---

# 43. DESIGN ANTI-PATTERNS

Do NOT introduce:

* XP
* streaks
* leaderboards
* excessive badges
* endless recommendation feeds
* follower counts
* engagement metrics
* fake personalization
* repetitive recommendation cards
* automatic LOCK-IN
* fake progress
* fake statistics
* generic dashboard layouts

These are outside the current product design.

---

# 44. DESIGN-TO-CODE RULE

Stitch is the primary visual reference.

When implementing:

**Preserve the Stitch design.**

Only deviate where required for:

* responsiveness
* accessibility
* backend integration
* routing
* real functionality
* missing backend capability

Do not redesign a component merely because another implementation is easier.

---

# 45. FUNCTIONALITY RULE

Every visible interactive control must work.

If backend functionality exists:

**connect it.**

If backend functionality does not exist:

**do not fake it.**

Instead:

* implement an honest unavailable/empty state, or
* leave the feature visually present but clearly non-functional only if that state is part of the approved design

Never pretend that a backend action succeeded.

---

# 46. CORE USER JOURNEY

The most important journey is:

```text
AUTH
  ↓
EXPLORE
  ↓
QUEST DETAIL
  ↓
ACTIVE QUEST
  ↓
COMPLETE
  ↓
FEEDBACK
  ↓
EXPLORE AGAIN
```

Secondary journeys:

```text
EXPLORE
  ↓
PROFILE
  ↓
DISCOVER PATTERNS
```

```text
EXPLORE
  ↓
MIX
  ↓
UNEXPECTED CONNECTION
  ↓
NEW EXPERIENCE
```

```text
EXPLORE
  ↓
USER CHOOSES LOCK-IN
  ↓
PROGRESSION
  ↓
DEEP LEARNING
  ↓
EXIT / COMPLETE
  ↓
EXPLORE
```

---

# 47. EMOTIONAL DESIGN

The intended emotional progression is:

## Explore

**Curiosity**

> "Interesting. I haven't tried this."

## Quest Detail

**Anticipation**

> "I understand what I'm actually going to do."

## Active Quest

**Focus**

> "I'm doing it."

## Completion

**Reflection**

> "What did I actually enjoy about this?"

## Profile

**Self-discovery**

> "That's an interesting pattern about me."

## MIX

**Surprise**

> "How did those two things connect?"

## LOCK-IN

**Commitment**

> "I want to go deeper into this."

---

# 48. FINAL PRODUCT INVARIANT

The entire interface must reinforce one principle:

> **Skill Quest helps users explore farther outward, rather than remain inside what they already know.**

Affinity, Profile, Skill DNA, previous experience, and recommendation intelligence may help the system discover better new territory.

They must never become a reason to repeatedly show the same experiential neighborhood.

---

# 49. IMPLEMENTATION PRIORITY

When making implementation decisions, prioritize in this order:

1. Correct backend state
2. Core exploration UX
3. Stitch visual fidelity
4. Clear user control
5. Responsive behavior
6. Accessibility
7. Loading/error/empty states
8. Secondary visual polish

Never sacrifice correctness of exploration state for visual polish.

---

# 50. FINAL QUALITY CHECKLIST

Before considering the frontend complete:

## Core screens

* [ ] Explore
* [ ] Quest Detail
* [ ] Active Quest
* [ ] Completion + Feedback
* [ ] Discovery Profile
* [ ] Exploration History
* [ ] MIX
* [ ] LOCK-IN
* [ ] Authentication
* [ ] Navigation/App Shell

## Functionality

* [ ] Authentication works
* [ ] Explore loads real recommendation
* [ ] Quest Detail loads real data
* [ ] Quest state is backend-driven
* [ ] Active Quest reflects real state
* [ ] Completion works
* [ ] Feedback submission works
* [ ] Profile uses real backend data
* [ ] DNA uses real backend data
* [ ] History uses real backend data
* [ ] MIX uses real backend data
* [ ] LOCK-IN uses real backend state
* [ ] Navigation works
* [ ] Protected routes work
* [ ] Browser refresh works

## Data integrity

* [ ] No fake runtime user data
* [ ] No fake runtime quests
* [ ] No fake statistics
* [ ] No fake DNA
* [ ] No fake history
* [ ] No fake MIX candidates
* [ ] No fake LOCK-IN progress
* [ ] No fake recommendation state
* [ ] No frontend duplication of core backend algorithms

## UX

* [ ] EXPLORE remains the default
* [ ] Exploration remains the dominant experience
* [ ] LOCK-IN requires explicit user action
* [ ] MIX feels meaningfully different from normal recommendations
* [ ] Recommendations do not become an infinite feed
* [ ] Variety is visible through experience rather than excessive controls
* [ ] User remains in control

## Responsive

* [ ] Desktop
* [ ] Tablet
* [ ] Mobile
* [ ] No page-level horizontal overflow
* [ ] Touch controls are usable
* [ ] Navigation adapts correctly

## Quality

* [ ] Loading states
* [ ] Empty states
* [ ] Error states
* [ ] Accessibility
* [ ] Reduced-motion support
* [ ] Frontend build passes
* [ ] Backend tests remain passing
* [ ] Production build contains no mock runtime data

---

# 51. SOURCE-OF-TRUTH HIERARCHY

When different requirements appear to conflict:

### 1. Backend contracts

Determine:

* data
* state
* business logic
* permissions
* historical truth

### 2. This `design.md`

Determines:

* product philosophy
* UX principles
* screen intent
* interaction rules
* design direction

### 3. Stitch designs

Determine:

* exact visual composition
* typography
* spacing
* colors
* component appearance
* visual hierarchy

### 4. Frontend implementation

Translates the above into working responsive UI.

The implementation should adapt to the first three sources, not redefine them.

---

# 52. NON-NEGOTIABLE RULE

**Do not optimize Skill Quest into a conventional recommendation or productivity application.**

The product exists to help people discover what they have **not yet tried**.

The interface should always make that principle visible.

**EXPLORE is the default.**

**MIX creates unexpected connections.**

**LOCK-IN is deliberate depth chosen by the user.**

**The backend owns truth.**

**The user owns the decision.**
