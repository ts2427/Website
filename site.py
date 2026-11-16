#!/usr/bin/env python3
"""
Timothy D. Spivey — personal / academic site. Single file, no other assets.

    pip install flask
    python site.py            # dev server at http://127.0.0.1:5000
    python site.py --build    # writes index.html + blog/ + threshold/

Everything you edit is in the CONTENT section at the top. The HTML, CSS, and JS
are in TEMPLATE at the bottom; you shouldn't need to touch it.

Drop a headshot named headshot.jpg beside this file and it will be picked up
automatically. Anything marked TODO needs a real value before you publish.
"""

import os
import re
import sys
from datetime import date, datetime
from xml.sax.saxutils import escape as xml_escape

from flask import (Flask, render_template_string, request, redirect,
                   url_for, flash, send_from_directory, abort)

HERE = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# CONTENT — edit everything below
# =============================================================================

SITE = {
    "name": "Timothy D. Spivey",
    # The hero renders the name with a small "drop" animation on the period
    # after the middle initial, mirroring the reference design.
    "hero_name_before_dot": "Timothy D",
    "hero_name_after_dot": " Spivey",
    "title": "Empirical Researcher & Data Scientist",
    "affiliation": "Doctoral Candidate (ABD), Business Administration — Business Analytics",
    "institution": "University of South Alabama · Mitchell College of Business",
    "meta_description": (
        "Timothy D. Spivey — empirical researcher and data scientist studying mandatory "
        "breach disclosure timing, cybersecurity governance, and the ethical use of data."
    ),
    "email": "tspivey@pensacolastate.edu",
    "location_lines": ["Pensacola State College", "Pensacola, Florida"],
    "cv_url": "timothy-spivey-cv.pdf",
    "links": {
        "linkedin": "https://www.linkedin.com/in/tispivey/",
        "linkedin_label": "Timothy D. Spivey on LinkedIn",
        "scholar": "https://scholar.google.com/citations?user=S9sSV1EAAAAJ&hl=en",
        # The firm's standalone site (launched 2026-08-25). The old
        # /threshold/ page here is now a redirect stub to it.
        "firm": "https://thresholddatasciences.com",
    },
    # Where the contact form posts. Formspree is the easiest option for a static
    # deploy: sign up, create a form, paste the endpoint here. Leave blank to use
    # the local Flask /contact route instead.
    "contact_endpoint": "https://formsubmit.co/tspivey@pensacolastate.edu",
    # Google Analytics 4 Measurement ID (looks like "G-XXXXXXXXXX"). Leave blank
    # to omit the tracking snippet entirely.
    "ga_measurement_id": "G-Q1XYCGEW06",
    # Canonical origin of the deployed site (no trailing slash). Used for
    # canonical URLs, Open Graph tags, and the blog's RSS feed.
    "base_url": "https://timothydspivey.com",
}

NAV = [
    {"label": "About", "href": "#about"},
    {"label": "Research", "href": "#research"},
    {"label": "Publications", "href": "#publications"},
    {"label": "Teaching", "href": "#teaching"},
    {"label": "Consulting", "href": "https://thresholddatasciences.com"},
    {"label": "Blog", "href": "blog/"},
    {"label": "Contact", "href": "#contact"},
]

# Sidebar profile card in the About section.
ABOUT_CARD = {
    "role": "Doctoral Candidate (ABD) — Business Analytics",
    "school": "University of South Alabama",
    "secondary_role": "Adjunct Instructor · Pensacola State College",
    "school_logos": [
        {"src": "https://commons.wikimedia.org/wiki/Special:FilePath/University%20of%20South%20Alabama%20logo.png?width=400",
         "alt": "University of South Alabama"},
        {"src": "https://en.wikipedia.org/wiki/Special:FilePath/Logo-of-Pensacola-State-College.svg",
         "alt": "Pensacola State College"},
    ],
    # Keep these methodological, not results — no coefficients before the defense.
    "stats": [
        {"value": "2", "label": "Publications"},
        {"value": "6", "label": "Research Areas"},
    ],
}

ABOUT = {
    "heading": "Researcher, Analyst & Educator",
    "paragraphs": [
        "Timothy D. Spivey is a doctoral candidate in Business Administration with a "
        "Business Analytics emphasis at the University of South Alabama, where his "
        "dissertation examines what mandatory breach disclosure timing actually does "
        "— to markets, to organizations, and to boards.",

        "The question is not whether disclosure matters. It is whether mandating "
        "when a firm discloses produces the benefit regulators assumed it would. "
        "Across three empirical channels, his work finds real costs and little of "
        "the intended benefit. The empirical backbone is a natural experiment built "
        "on the FCC's 2007 mandatory disclosure rule (47 CFR § 64.2011), applied to "
        "1,054 breach events from 2006 to 2025.",

        "Outside the dissertation, he supervises management information systems at "
        "Mediacom Communications and teaches entrepreneurship and small business "
        "accounting as an adjunct at Pensacola State College. Nearly twenty years of "
        "telecom operations sits underneath the research: he has built the reporting "
        "pipelines, sat in the escalation calls, and watched compliance decisions get "
        "made under real pressure. That is why the empirical questions he chases are "
        "the ones practitioners recognize.",

        "He holds an MBA in Business Analytics from the University of West Florida "
        "and a BAS in Organizational Administration from Pensacola State College — "
        "where he now teaches.",
    ],
    # Fallback if headshot.jpg is ever removed — the local file wins when present.
    "portrait": ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
                 "width='220' height='220'%3E%3Crect width='220' height='220' "
                 "fill='%230d1b2a'/%3E%3Ctext x='110' y='132' font-family='Georgia' "
                 "font-size='64' fill='%23eaf4fb' text-anchor='middle'%3ETS%3C/text%3E"
                 "%3C/svg%3E"),
    "portrait_alt": "Timothy D. Spivey",
    "keywords": [
        "Mandatory Disclosure",
        "Cybersecurity Governance",
        "Event Studies",
        "Capital Markets",
        "IT Ethics",
        "Business Analytics",
    ],
}

GALLERY = [
    {
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/MitchellCollegeofBusiness.JPG?width=1200",
        "alt": "Mitchell College of Business, University of South Alabama",
        "caption": "Mitchell College of Business",
    },
    {
        "image": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&q=70",
        "alt": "Equity market data on screen",
        "caption": "Breach Disclosure & Market Response Research",
    },
    {
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/MoultonBellTower.jpg?width=1200",
        "alt": "Moulton Bell Tower, University of South Alabama",
        "caption": "University of South Alabama",
    },
]

RESEARCH = {
    "intro": (
        "What happens when regulation meets reality — mandatory disclosure, "
        "cybersecurity governance, and the ethical use of data, measured empirically."
    ),
    "cards": [
        {
            "title": "Markets & Breach Pricing",
            "image": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=70",
            "alt": "Stock market chart",
            "text": (
                "How mandatory disclosure timing affects equity valuations and how "
                "investors price breach risk. Does forcing faster disclosure protect "
                "markets, or does it amplify volatility?"
            ),
        },
        {
            "title": "Post-Disclosure Uncertainty",
            "image": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=70",
            "alt": "Data center operations",
            "text": (
                "The operational friction of disclosure: how mandates strain "
                "organizational capacity, extend remediation timelines, and leave "
                "information asymmetries standing even after the report is filed."
            ),
        },
        {
            "title": "Boards & Governance Disruption",
            "image": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800&q=70",
            "alt": "Boardroom meeting",
            "text": (
                "Board-level response and decision-making under disclosure pressure. "
                "How compliance requirements reshape governance structures without "
                "necessarily improving security outcomes."
            ),
        },
        {
            "title": "AI Résumé Screening & Hiring Ethics",
            "image": "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=800&q=70",
            "alt": "Documents and screening",
            "text": (
                "Algorithmic bias in hiring systems and the over-education paradox, "
                "framed through social exchange theory and organizational justice "
                "theory."
            ),
        },
        {
            "title": "Privacy in Analytics Workflows",
            "image": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800&q=70",
            "alt": "Data privacy and security",
            "text": (
                "What actually causes privacy problems inside enterprise analytical "
                "pipelines, and where governance breaks down."
            ),
        },
        {
            "title": "Applied Data Engineering",
            "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=70",
            "alt": "Analytics dashboard",
            "text": (
                "Reproducible research infrastructure: 1,054 breach events across "
                "nineteen years, normalized from inconsistent public sources into a "
                "Python and Snowflake pipeline matched to market data."
            ),
        },
    ],
}

PUBLICATIONS = {
    "intro": "Practitioner research on security culture and IT governance.",
    "entries": [
        {
            "year": "2024",
            "title": ("Navigating the Shadows — A Comprehensive Framework for "
                      "Anticipating, Identifying, and Managing Shadow IT in "
                      "Organizations"),
            "authors": "Spivey, T. D., & McIlveene, T.",
            "venue": "ISACA Journal, 6",
            "kind": "Journal Article",
            "status": "Published",
            "url": "",
        },
        {
            "year": "2023",
            "title": "To Fear or Not to Fear: How to Create an Optimal Security Culture",
            "authors": "Batchelor, J. H., Spivey, T. D., & McIlveene, T.",
            "venue": "ISACA Journal, 6, 34–37",
            "kind": "Journal Article",
            "status": "Published",
            "url": "",
        },
    ],
}

SERVICE = {
    "intro": "Editorial review service and professional memberships.",
    "review": [
        {
            "role": "Peer Reviewer",
            "venue": "Journal of Risk and Financial Management (MDPI)",
            "years": "2025 – Present",
            "note": ("International peer-reviewed journal, Q1 in Business, "
                     "Management and Accounting; indexed in Scopus, EconBiz, "
                     "EconLit, and RePEc."),
        },
        {
            "role": "Peer Reviewer",
            "venue": "Business Strategy & Development (Wiley)",
            "years": "2025 – Present",
            "note": ("International peer-reviewed journal covering strategic "
                     "management, business development, and organizational "
                     "growth."),
        },
    ],
    "affiliations": [
        {
            "name": "ISACA",
            "detail": ("Information Systems Audit and Control Association — "
                       "professional association for IT audit, governance, "
                       "and security."),
        },
    ],
}

TEACHING = {
    "intro": (
        "Business and professional writing courses taught across Northwest Florida "
        "institutions, alongside doctoral study."
    ),
    "photo": "clocktower.jpg",
    "photo_alt": "M. J. Menge clock tower, Pensacola State College",
    "institutions": [
        {
            "name": "Pensacola State College",
            "role": "Adjunct Instructor",
            "years": "2025 – Present",
            "building": "clocktower.jpg",
            "building_alt": "M. J. Menge clock tower, Pensacola State College",
            "logo": "https://en.wikipedia.org/wiki/Special:FilePath/Logo-of-Pensacola-State-College.svg",
            "logo_alt": "Pensacola State College logo",
            "courses": ["Introduction to Entrepreneurship", "Small Business Accounting"],
        },
        {
            "name": "University of West Florida",
            "role": "Graduate Teaching Assistant",
            "years": "2022 – 2024",
            "building": "https://commons.wikimedia.org/wiki/Special:FilePath/John%20C.%20Pace%20Library%2C%20University%20of%20West%20Florida.jpg?width=1000",
            "building_alt": "John C. Pace Library, University of West Florida",
            "logo": "https://commons.wikimedia.org/wiki/Special:FilePath/Univers%20of%20west%20florida%20logo.png?width=400",
            "logo_alt": "University of West Florida logo",
            "courses": ["Writing for Business: Theory and Practice"],
        },
    ],
}

CONSULTING = {
    "firm": "Threshold Data Sciences",
    "tagline": "Empirical insight. Practical guidance.",
    "heading": "Where Research Meets Practice",
    "pitch": (
        "Whether you need analytics infrastructure built, a research question answered "
        "with defensible methods, or counsel on governance and disclosure, Threshold "
        "Data Sciences brings the same rigor to consulting that peer review demands of "
        "research. I don't only advise on this — I study it."
    ),
    "focus": [
        {
            "title": "Data Science & Analytics",
            "detail": ("Forecasting, data pipelines, executive dashboards, and "
                       "reporting infrastructure that stakeholders actually use."),
        },
        {
            "title": "Research & Measurement",
            "detail": ("Study design, causal inference, and statistical analysis — "
                       "answers you can defend, not just charts."),
        },
        {
            "title": "Governance, Risk & Compliance",
            "detail": ("Breach disclosure strategy, board oversight, and security "
                       "spend prioritization, grounded in the empirical evidence."),
        },
    ],
    "cta_label": "Send an Inquiry",
    "cta_href": "#contact",
}

CONTACT = {
    "intro": "Research collaboration, speaking, teaching, or consulting — reach out.",
    "topics": [
        "Research Collaboration",
        "Speaking / Presentation",
        "Teaching Inquiry",
        "Consulting Engagement",
        "Request CV",
        "Other",
    ],
}

BLOG = {
    "name": "Threshold Effects",
    "label": "Essays & Research Notes",
    "tagline": ("Rules change what organizations are required to do. They "
                "rarely change what they are. A weekly research series on the "
                "gap between the two — regulation, disclosure, governance, and "
                "the organizational capacity that actually decides outcomes."),
    "meta_description": (
        "Threshold Effects — essays and research notes by Timothy D. Spivey on "
        "mandatory breach disclosure, cybersecurity governance, and the practice "
        "of data science."
    ),
}

# Each post is one dict. To publish: add an entry here and rerun
#     python site.py --build
# Newest date sorts first. Set "draft": True to keep a post out of the build.
# The body is plain HTML — <p>, <h2>, <blockquote>, <ul>, <pre><code>, <img>
# are all styled. Keep slugs stable once published; they become the URL.
POSTS = [
    {
        "slug": "why-threshold-effects",
        "title": "Why “Threshold Effects”",
        "date": "2026-08-25",
        "tags": ["Meta"],
        "summary": ("The name comes from econometrics — a relationship that "
                    "changes character once a variable crosses a critical "
                    "value. It is also a fair description of everything this "
                    "blog will be about."),
        "body": """
<p>In econometrics, a threshold effect is a relationship that changes character
once a variable crosses a critical value. Below the line, one regime; above it,
another. The relationship is not linear, and pretending it is will mislead you
precisely when the stakes are highest.</p>

<p>Most of the questions I study live on lines like these. The moment a breach
becomes reportable. The day a disclosure deadline arrives. The point at which a
board stops treating security as an IT expense and starts treating it as a
governance problem. My dissertation asks what mandatory disclosure timing
actually does — to markets, to organizations, and to boards — and the honest
answer so far is that the interesting action is almost never in the average.
It is at the thresholds.</p>

<p>The name is also, admittedly, an echo of
<a href="https://thresholddatasciences.com" target="_blank">Threshold Data
Sciences</a>, the consulting practice where the research meets paying problems.
The pun was sitting right there.</p>

<h2>What to expect</h2>

<p>Research notes as the dissertation moves toward defense — methods,
measurement decisions, and the occasional dead end, because dead ends are data
too. Commentary on disclosure regulation as it keeps evolving. Notes from
teaching entrepreneurship and small business accounting, and from nearly twenty
years of telecom operations that keep the empirical questions honest.</p>

<p>The cadence will be honest rather than ambitious: I will write when I have
something worth saying, and not otherwise. If that suits you, there is an
<a href="feed.xml">RSS feed</a>.</p>
""",
    },
    # ------------------------------------------------------------------
    # The original Threshold Effects series, first published on LinkedIn
    # (July–August 2026), archived here as posts No. 001–011.
    # ------------------------------------------------------------------
    {
        "slug": "the-faster-is-better-assumption",
        "title": "The Faster-Is-Better Assumption",
        "date": "2026-07-20",
        "tags": ["Mandatory Disclosure", "Cybersecurity", "Research"],
        "summary": ("The assumption behind mandatory breach disclosure timing "
                    "is that faster equals better. Across 1,054 breach events "
                    "and three empirical channels, that assumption doesn't "
                    "hold up well."),
        "body": """
<p>The assumption behind mandatory breach disclosure timing is that faster =
better. Markets get cleaner signals. Firms recover faster. Uncertainty
drops.</p>

<p>I've been testing that assumption for a while now. It doesn't hold up
well.</p>

<p>Using event study methodology across 1,054 breach events, with the FCC's
2007 disclosure rule as a natural experiment, my research traces what
regulatory timing actually does to pricing efficiency, post-disclosure
uncertainty, and governance structures. The consistent finding: real costs,
across all three channels, without the regulatory payoff. Faster disclosure
moves the information asymmetry problem — it doesn't solve it.</p>

<p>That thread connects back to earlier work during my MBA on the cable and
telecom industry, where the same gap kept showing up between policy intent and
market reality.</p>

<p>Three ISACA Journal publications, a co-authored empirical paper in
progress, and nearly 20 years in telecom operations underneath all of it.</p>

<p>Still a lot of work left on this. If any of it connects with work you're
doing, I'd love to hear about it.</p>

<hr />
<p><em>No. 001 in the Threshold Effects series. First published on LinkedIn,
July 20, 2026.</em></p>
""",
    },
    {
        "slug": "cover-yourself-8-ks",
        "title": "Cover-Yourself 8-Ks",
        "date": "2026-07-22",
        "tags": ["Mandatory Disclosure", "Regulatory Policy", "Cybersecurity"],
        "summary": ("When the SEC required four-business-day incident "
                    "disclosure, firms responded with “cover yourself "
                    "8-Ks.” Organizations don't respond to regulatory "
                    "intent — they respond to regulatory incentives."),
        "body": """
<p>Mandatory disclosure rules are built on an assumption that organizations
will respond to transparency requirements with transparency.</p>

<p>The evidence suggests otherwise.</p>

<p>When the SEC required public companies to disclose material cybersecurity
incidents within four business days, something unexpected happened. Instead of
producing cleaner market signals, companies started filing mandatory
disclosures for incidents that didn't even meet the materiality threshold. SEC
officials had a name for it: "cover yourself 8-Ks." Firms were disclosing not
because the incident warranted it — but because they were afraid of being
second-guessed later.</p>

<p>The SEC had to issue clarifying guidance in May 2024 to correct the
behavior. The guidance worked. But the episode reveals something worth paying
attention to.</p>

<p>Organizations don't respond to regulatory intent. They respond to
regulatory incentives. And those two things are not the same.</p>

<p>A rule designed to reduce information asymmetry between firms and investors
produced strategic disclosure behavior instead — firms managing perception
rather than informing markets. That gap between intent and outcome is where
the real cost lives, and it shows up more often than the policy debate
acknowledges.</p>

<p>The question regulators should be asking isn't just what information do
markets need — it's how will organizations behave when required to provide
it?</p>

<p>We're not great at answering that second question yet.</p>

<hr />
<p><em>No. 002 in the Threshold Effects series. First published on LinkedIn,
July 22, 2026.</em></p>
""",
    },
    {
        "slug": "paper-trails-and-shadow-ai",
        "title": "Paper Trails and Shadow AI",
        "date": "2026-07-27",
        "tags": ["AI Governance", "Shadow AI", "Compliance"],
        "summary": ("Only 37% of compliance leaders can measure whether their "
                    "programs work — and half the U.S. workforce is using AI "
                    "at work without knowing if it's allowed. Why did we "
                    "think a document was going to govern a behavior?"),
        "body": """
<p>Organizations invest significant resources building compliance programs —
policies, training, audits, documentation.</p>

<p>How much of that investment actually changes behavior versus simply
documenting that the organization tried?</p>

<p>According to Gartner, only 37% of compliance leaders are confident in their
ability to measure program effectiveness. That's not a data collection
problem. That's a design problem.</p>

<p>In my experience, the gap between a compliance program that documents
effort and one that actually shifts behavior comes down to a single question:
do the people who wrote the policy understand why the behavior they're trying
to govern exists in the first place?</p>

<p>Most of the time, they don't. And a rule written without that understanding
doesn't change behavior — it just creates a paper trail.</p>

<p>Curious what others are seeing on the ground.</p>

<p>ISACA's 2026 AI Pulse Poll surveyed 3,400 digital trust professionals and
found that 90% believe employees at their organizations are using AI tools.
Only 38% have a formal comprehensive AI policy. One in four have no policy at
all.</p>

<p>KPMG's research puts the behavioral picture in even sharper focus. Half of
the U.S. workforce reports using AI tools at work without knowing whether it's
allowed. Another 44% admit to knowingly using AI in ways that contravene
company policies and guidelines. Only 41% of employees report that their
organization has any policy guiding AI use at all.</p>

<p>Read those numbers together. Then read them again.</p>

<p>This isn't a compliance gap. It's a governance design problem.</p>

<p>AI policy travels top-down as a document — authored by leadership, signed
once, filed somewhere. AI behavior travels peer-to-peer as a habit — spread
through shared prompts, chat threads, and a colleague saying "you have to try
this." Those two channels don't touch each other. A rule that travels one path
and a behavior that travels the other will diverge no matter how well the rule
is written.</p>

<p>The productivity calculus makes it worse. When the reward for using an
unapproved tool is concrete, recurring, and personal — and the risk is
abstract, deferred, and someone else's problem — the behavior wins. Every
time.</p>

<p>We've seen this pattern before. Shadow IT didn't disappear because
organizations wrote better policies. It persisted because the tools people
weren't supposed to use worked better than the ones they were supposed to use.
AI is following the same road at a much faster speed.</p>

<p>The question worth asking isn't how do we enforce the policy we already
have. It's why did we think a document was going to govern a behavior in the
first place.</p>

<hr />
<p><em>No. 003 in the Threshold Effects series. First published on LinkedIn,
July 27, 2026.</em></p>
""",
    },
    {
        "slug": "shadow-it-was-the-rehearsal",
        "title": "Shadow IT Was the Rehearsal",
        "date": "2026-07-29",
        "tags": ["Shadow IT", "AI Governance", "ISACA"],
        "summary": ("Shadow IT persisted because unsanctioned tools solved "
                    "real problems faster than approved ones. AI governance "
                    "is replaying the same dynamic — in months instead of "
                    "years."),
        "body": """
<p>In 2025 I published a piece in the ISACA Journal on shadow IT governance —
specifically how and why employees adopt unauthorized technology outside of
sanctioned IT channels, and what that means for organizational security
culture.</p>

<p>The core finding wasn't surprising in hindsight: employees don't adopt
shadow IT because they're trying to create risk. They adopt it because the
unsanctioned tools solve a real problem faster than the approved ones do. The
productivity gain is immediate and personal. The governance risk is diffuse
and deferred. When those two things compete, behavior wins over policy almost
every time.</p>

<p>What made shadow IT hard to govern wasn't the technology. It was the gap
between how the policy traveled — top-down, documented, signed — and how the
behavior traveled — peer-to-peer, through habit, through a colleague saying
"just use this."</p>

<p>Organizations that never closed that gap didn't close it by writing better
shadow IT policies. Most just learned to live with it.</p>

<p>Reading the AI governance data coming out in 2026, I keep seeing the same
dynamic — same incentive structure, same behavioral pattern, same governance
gap. The difference is speed and scale. Shadow IT crept in over years. AI is
doing the same thing in months, across every function, at every level of the
organization.</p>

<p>A policy document didn't solve shadow IT. It's not going to solve this
either.</p>

<hr />
<p><em>No. 004 in the Threshold Effects series. First published on LinkedIn,
July 29, 2026.</em></p>
""",
    },
    {
        "slug": "three-rules-same-outcome",
        "title": "Three Rules, Same Outcome",
        "date": "2026-08-03",
        "tags": ["Regulatory Policy", "Mandatory Disclosure",
                 "Organizational Behavior"],
        "summary": ("AI governance, compliance programs, mandatory "
                    "disclosure: three domains, three rules, same outcome. "
                    "The rule changes what organizations are required to do. "
                    "It rarely changes what they are."),
        "body": """
<p>In my series over the past three weeks, the same pattern has shown up in
three different places.</p>

<p>AI governance: ISACA found that 90% of organizations believe employees are
using AI tools. Only 38% have a formal policy. KPMG found half the U.S.
workforce uses AI at work without knowing whether it's allowed.</p>

<p>Compliance programs: Gartner found that only 37% of compliance leaders are
confident they can measure program effectiveness. The investment is real. The
evidence that it changes behavior is not.</p>

<p>Mandatory disclosure: When the SEC required companies to report material
cybersecurity incidents within four business days, firms started filing
disclosures for incidents that didn't meet the materiality threshold. A rule
designed to produce cleaner signals produced strategic noise instead.</p>

<p>Three domains. Three rules. Same outcome.</p>

<p>Here's what the research says about why.</p>

<p>Doshi, Dowell, and Toffel (Strategic Management Journal, 2013) studied how
thousands of establishments responded to a mandatory environmental disclosure
program. Responses weren't uniform — they were moderated by organizational
characteristics. The fastest improvement came from establishments near their
headquarters and those owned by private firms. Same mandate, different
organizations, different outcomes.</p>

<p>Haapamäki and Sihvonen (International Journal of Accounting Information
Systems, 2026) analyzed 3,440 cybersecurity disclosures filed under the SEC's
new 10-K requirement. Disclosure quality varied with firm size, auditor
quality, and peer practices — and firms' actual cyber histories showed no
influence at all. Strategic discretion persisted under the mandate. And the
market's response to these newly required disclosures? Minimal. Investors and
analysts barely reacted.</p>

<p>The DOJ — in its own Corporate Enforcement Policy — draws the same
distinction. "Paper programs" versus effective ones. And what separates them
isn't the document. It's culture, leadership commitment, and reporting trust.
Characteristics that predate the rule and persist regardless of it.</p>

<p>The pattern across all of it: the rule changes what organizations are
required to do. It rarely changes what they are.</p>

<p>We keep passing rules that tell companies what to do — and the companies
that were already going to do it, do it. The ones that weren't, don't. The
rule itself changes very little.</p>

<hr />
<p><em>No. 005 in the Threshold Effects series. First published on LinkedIn,
August 3, 2026.</em></p>
""",
    },
    {
        "slug": "wanted-the-best-counterexample",
        "title": "Wanted: The Best Counterexample",
        "date": "2026-08-05",
        "tags": ["Regulatory Policy", "Organizational Behavior"],
        "summary": ("The honest version of an argument has to survive its "
                    "best counterexample. So: what's the strongest case of a "
                    "rule that actually changed what organizations are?"),
        "body": """
<p>On Monday I made an argument: rules change what organizations are required
to do, but rarely change what they are. The research I cited backs it. So does
most of what I've seen in 20 years of operations.</p>

<p>But the honest version of that argument has to survive its best
counterexample — and I'd rather go looking for it than wait for it to find
me.</p>

<p>So here's the question: what's the strongest case you've seen of a rule
that actually changed what organizations are? Not compliance on paper — real,
durable change in how firms behave, staff, invest, or think. A regulation that
built capacity rather than just revealing who already had it.</p>

<p>Seatbelt-style engineering mandates? SOX internal controls, a decade on?
Something in your industry I've never heard of?</p>

<p>I have a candidate or two of my own, but I'm more interested in yours.</p>

<p>Best counterexample gets a genuine rethink in a future post.</p>

<hr />
<p><em>No. 006 in the Threshold Effects series. First published on LinkedIn,
August 5, 2026.</em></p>
""",
    },
    {
        "slug": "what-the-broadband-labels-revealed",
        "title": "What the Broadband Labels Revealed",
        "date": "2026-08-10",
        "tags": ["Telecom", "FCC", "Mandatory Disclosure"],
        "summary": ("The FCC's broadband nutrition labels were identical for "
                    "all 35 ISPs a 2025 study scored. What the mandate "
                    "produced depended entirely on what each organization "
                    "already was."),
        "body": """
<p>In 2021, Congress mandated "broadband nutrition labels" — standardized
disclosures of pricing, fees, and speeds, modeled on FDA food labels. The FCC
adopted the rules in November 2022. Unanimously. Full compliance was required
by October 2024.</p>

<p>I've spent nearly 20 years in this industry. Here's how it played out.</p>

<p>A 2025 study by Obar and Chen (York University, presented at TPRC) assessed
35 ISPs against ten FCC-mandated criteria — label placement, formatting,
machine-readability, required policy links. The average score: 5.2 out of 10.
Only sixteen of 35 properly placed labels at the point of sale. Not a single
provider received full marks.</p>

<p>On average, compliance tracked size — larger ISPs scored 5.8, medium 5.4,
smaller 3.75. But the averages hide the more interesting finding. Three small
ISPs scored zero. No compliant label at all. And one of the highest scores in
the entire study — 7.5 out of 10 — belonged to Sonic, one of the smallest
providers in the sample, tied with Google Fiber.</p>

<p>That's not a size effect. That's a capacity effect. And it's consistent
with what the academic literature has been saying for years. Research on SEC
disclosure compliance (Ettredge et al., Review of Accounting Studies) found
noncompliant firms weren't smaller than compliant ones — they had weaker
governance. Work on regulatory cost (Trebbi et al.) documents economies of
scale in compliance. A 2026 study of environmental regulation found the same
thing: regulatory pressure hits firms as a common constraint, and the
differences in outcomes come from internal capabilities — not from the
regulation.</p>

<p>The mandate was identical for all 35 providers. What it produced depended
entirely on what each organization already was. The rule didn't create
compliance capacity. It revealed who had it.</p>

<p>Meanwhile, enforcement never materialized — and at its July 2026 Open
Meeting, the FCC scaled the label requirements back, citing compliance
burdens.</p>

<p>The label was supposed to fix an information asymmetry between providers
and consumers. The asymmetry that actually determined the outcome was inside
the firms — between organizations with the capacity to comply and
organizations without it.</p>

<hr />
<p><em>No. 007 in the Threshold Effects series. First published on LinkedIn,
August 10, 2026.</em></p>
""",
    },
    {
        "slug": "the-dashboard-is-green",
        "title": "The Dashboard Is Green",
        "date": "2026-08-12",
        "tags": ["Metrics", "Goodhart's Law", "Data Governance"],
        "summary": ("Goodhart's Law and Campbell's Law warned us fifty years "
                    "ago: the metric changes what the organization reports, "
                    "not what the organization is. We built the dashboards "
                    "anyway."),
        "body": """
<p>If you build reporting infrastructure for a living, you've watched this
happen.</p>

<p>Leadership picks a metric. The metric becomes a target. The target gets a
dashboard. And then the number starts improving — while the thing the number
was supposed to measure doesn't move at all. Sometimes it gets worse.</p>

<p>Everyone in the room knows. Nobody says it. The dashboard is green.</p>

<p>This pattern has a name — two, actually. Goodhart's Law (1975): when a
measure becomes a target, it ceases to be a good measure. Campbell's Law
(1976): the more a quantitative indicator is used for decision-making, the
more it corrupts the very process it was meant to monitor. Two researchers,
working independently, warned us fifty years ago. We built the dashboards
anyway.</p>

<p>The case studies are brutal. Wells Fargo set a cross-selling target — eight
accounts per customer — and wired incentives to it. Employees opened millions
of unauthorized accounts. The metric hit its numbers right up until the moment
it detonated. In the English NHS, an 18-week treatment target produced exactly
what Bevan and Hood documented in Public Administration: delayed referrals to
keep the clock from starting, minor procedures scheduled to reset it, easy
cases prioritized while complex ones waited. Wait-time metrics improved.
Waiting didn't.</p>

<p>Here's what fifty years of evidence says, and it's the same thing this
series has been saying about federal rules: the metric changes what the
organization reports. It doesn't change what the organization is. People don't
game numbers because they're dishonest — they game them because the metric
became the job, and the metric was never the job.</p>

<p>Every reporting requirement — a federal disclosure rule, a compliance
program, a KPI on an executive dashboard — is a bet that measuring a thing
will improve it. Fifty years of research says: only if the capacity and the
culture underneath already point that way. Otherwise you get a green dashboard
and a red reality.</p>

<p>You've seen this one. What was the metric?</p>

<hr />
<p><em>No. 008 in the Threshold Effects series. First published on LinkedIn,
August 12, 2026.</em></p>
""",
    },
    {
        "slug": "say-something-vs-build-something",
        "title": "Say Something vs. Build Something",
        "date": "2026-08-17",
        "tags": ["Regulatory Policy", "SOX", "Telecom"],
        "summary": ("There are rules that require organizations to say "
                    "something and rules that require them to build "
                    "something. Only the second kind has a track record of "
                    "changing what organizations are."),
        "body": """
<p>For five weeks I've made the same argument from different angles: rules
change what organizations are required to do, but rarely change what they are.
Disclosure mandates get absorbed by whatever the organization already is — its
capacity, its culture, its governance.</p>

<p>A fair question follows: can regulation change what organizations are at
all?</p>

<p>Yes. But not the kind we keep writing.</p>

<p>There are two kinds of mandates. Rules that require organizations to SAY
something — disclose the breach, post the label, file the 8-K. And rules that
require organizations to BUILD something. The evidence from five weeks of
posts is about the first kind. The second kind behaves differently, and my own
industry produced the best example I know.</p>

<p>In 1996 and 1999, the FCC ordered wireless carriers to be able to locate
911 callers — Phase II required latitude and longitude within 50 to 300
meters. There was no document a carrier could file to satisfy that. The FCC's
own implementation record describes what compliance required: developing new
location technologies, upgrading networks, and coordinating across carriers,
vendors, and public safety agencies. Carriers fought it. They requested
waivers. Deployment ran slow. But you cannot paper-comply with an accuracy
standard — and the capability got built. The location infrastructure that
mandate forced into existence now underpins far more than emergency
calling.</p>

<p>SOX Section 404 tells a similar story with an honest asterisk. It didn't
just require companies to report on internal controls — it required the
controls to exist and to survive an audit. John Coates and Suraj Srinivasan's
review of more than 120 studies (Accounting Horizons, 2014) found the
institutions SOX created survived intact and financial reporting quality
appears to have improved — though causal attribution is weak, and the costs
fell disproportionately on smaller firms. Even a capacity mandate routes
through capacity distribution. There's no escaping that. But note what nobody
claims about Section 404: that firms satisfied it with a filing.</p>

<p>So here's the pattern, stated plainly.</p>

<p>Disclosure mandates are cheap to write, cheap to comply with, and cheap to
verify — which is exactly why we keep writing them. A timing window costs the
regulator a paragraph and costs the firm a template. Capacity mandates are
expensive, slow, contested, and hard to specify. They're also the only kind
with a track record of changing what organizations are.</p>

<p>We regulate the announcement because the announcement is what we can afford
to regulate. Then we're surprised the announcement is all we get.</p>

<p>If the outcome is what we want, the capacity is what we have to require.
Everything else is asking organizations to describe themselves — and they
will, in exactly the way five weeks of evidence predicts.</p>

<hr />
<p><em>No. 009 in the Threshold Effects series. First published on LinkedIn,
August 17, 2026.</em></p>
""",
    },
    {
        "slug": "a-fair-fight-with-sox-404",
        "title": "A Fair Fight with SOX 404",
        "date": "2026-08-19",
        "tags": ["SOX", "Regulatory Policy", "Compliance"],
        "summary": ("Arguing against myself: SOX Section 404 is the strongest "
                    "counterexample to this series' thesis. The argument "
                    "survives — but comes out more precise than it went in."),
        "body": """
<p>I've spent six weeks arguing that rules change what organizations are
required to do — but rarely change what they are. Today I'm arguing against
myself, because every argument deserves a fair fight against its best
counterexample.</p>

<p>The strongest one I know is Sarbanes-Oxley (SOX) Section 404. And the case
is real. It didn't ask firms to describe their internal controls — it required
the controls to exist and survive an independent audit. Two decades later, the
infrastructure it forced into existence — control documentation, testing
regimes, audit committee muscle — is simply how public-company financial
reporting works now. Coates and Srinivasan's review of more than 120 studies
(Accounting Horizons, 2014) found the institutions SOX built survived intact
and reporting quality appears to have improved. If my thesis were "regulation
never changes organizations," SOX would break it.</p>

<p>But the same review cuts back the other way on three fronts.</p>

<p>Causal attribution is weak. Reporting quality rose after SOX, but the
research can't cleanly separate the rule's effect from everything else that
changed after Enron and WorldCom — including the scared-straight effect of
watching two giants implode.</p>

<p>The costs fell disproportionately on smaller firms — so heavily that
Congress permanently exempted thousands of smaller companies from the audit
requirement. The mandate that worked was also the mandate a large share of
firms were eventually excused from. Capacity determined who could even afford
to be changed by it.</p>

<p>And the part of SOX that worked was precisely the part that couldn't be
satisfied with paperwork. The certification and disclosure provisions — the
say-something parts — produced exactly the boilerplate this series has been
documenting for six weeks.</p>

<p>So the honest scorecard: regulation can change what organizations are —
when it mandates capability, verifies it independently, and the regulated
firms can bear the cost. That's a narrow gate, and most rules never attempt
it, because that kind of rule is expensive, slow, and fought at every
step.</p>

<p>My argument survives — but it comes out more precise than it went in.
That's what counterexamples are for.</p>

<hr />
<p><em>No. 010 in the Threshold Effects series. First published on LinkedIn,
August 19, 2026.</em></p>
""",
    },
    {
        "slug": "gulf-coast-who-the-money-moves-through",
        "title": "Gulf Coast: Who the Money Moves Through",
        "date": "2026-08-24",
        "tags": ["BEAD", "Broadband", "Gulf Coast", "Telecom"],
        "summary": ("BEAD is finally putting fiber in the ground around "
                    "northwest Florida and south Alabama. Five years of "
                    "process decided who gets to build — and it wasn't "
                    "construction capability that decided."),
        "body": """
<p>The largest broadband investment in American history is about to start
putting fiber in the ground in the counties around us. Florida was allocated
$1.16 billion. Alabama, $1.4 billion. The unserved locations this money
targets are disproportionately rural — the Panhandle, the Black Belt, the
counties between Pensacola and Montgomery. I've spent nearly 20 years in this
industry, in this region. So I've been watching this one closely.</p>

<p>Here's the timeline that should get more attention than it does.</p>

<p>The law passed in November 2021. Florida filed its letter of intent in July
2022. The challenge process — determining which locations actually qualify —
wasn't approved until April 2025. Then in June 2025, the federal government
rewrote the program rules mid-stream, rescinding prior guidance and giving
every state 90 days to redo its work. Florida's final proposal went in that
October. NTIA approved it in January 2026. Construction: spring 2026.</p>

<p>Five years from law to shovels. The first half-decade of the largest
infrastructure investment in broadband history produced, almost exclusively,
compliance documents.</p>

<p>Now look at who came through the process. Alabama's provisional award list
is instructive. The largest single award went to Comcast — $157 million.
AT&amp;T took $93 million. That part surprises no one. But keep reading the
list: Millry Telephone, $9.4 million. Farmers Telecommunications, $8.3
million. Ardmore Telephone, $3.2 million. Small rural Alabama telcos,
competing and winning.</p>

<p>What separated the small providers who won from the ones who never made
the list wasn't size — it was the capacity to survive the process. Federal
grant applications, letters of credit, environmental reviews, labor
certifications, challenge filings. The providers with grant-writing and
compliance muscle got through a five-year gauntlet. The ones without it aren't
on the list — and their absence doesn't show up in any official record. The
communities they might have served just wait for someone bigger.</p>

<p>Here's the honest tension. BEAD is the kind of program I've argued FOR in
this series — it mandates building something real, not describing something.
You can't paper-comply with fiber in the ground. Some of that process is the
legitimate price of spending $42 billion carefully. But a build-something
program wrapped in five years of say-something process inherits the flaw it
was designed to avoid: the compliance stack, not the construction capability,
decides who gets to build.</p>

<p>For northwest Florida and south Alabama, that's not an abstraction. It
determines which counties get fiber from a national carrier on a national
timeline — and which ones get it from a local provider who answers the
phone.</p>

<p>The money is finally moving. Worth watching who it moves through.</p>

<hr />
<p><em>No. 011 in the Threshold Effects series. First published on LinkedIn,
August 24, 2026.</em></p>
""",
    },
]


# =============================================================================
# APP — you shouldn't need to edit past this line
# =============================================================================

app = Flask(__name__)
app.secret_key = "change-me-before-deploying"  # only used for flash messages

PORTRAIT_FILE = os.path.join(HERE, "headshot.jpg")


def portrait_url(building=False):
    """Local headshot.jpg if present, otherwise the placeholder in ABOUT."""
    if os.path.exists(PORTRAIT_FILE):
        return "headshot.jpg" if building else url_for("portrait")
    return ABOUT["portrait"]


def render(building=False):
    if SITE["contact_endpoint"]:
        action = SITE["contact_endpoint"]
    elif building:
        action = "#contact"
    else:
        action = url_for("contact")

    return render_template_string(
        TEMPLATE,
        site=SITE,
        nav=NAV,
        about_card=ABOUT_CARD,
        about=ABOUT,
        gallery=GALLERY,
        research=RESEARCH,
        publications=PUBLICATIONS,
        service=SERVICE,
        teaching=TEACHING,
        consulting=CONSULTING,
        contact=CONTACT,
        portrait_url=portrait_url(building),
        form_action=action,
        year=date.today().year,
    )


def render_threshold():
    """/threshold/ is a redirect stub: the firm site lives at its own
    domain now. GitHub Pages cannot 301, so meta-refresh + canonical."""
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8" />\n'
        '<meta http-equiv="refresh" content="0; '
        'url=https://thresholddatasciences.com/" />\n'
        '<link rel="canonical" href="https://thresholddatasciences.com/" />\n'
        '<meta name="robots" content="noindex" />\n'
        "<title>Threshold Data Sciences</title>\n</head>\n<body>\n"
        "<p>Threshold Data Sciences has moved to\n"
        '<a href="https://thresholddatasciences.com/">'
        "thresholddatasciences.com</a>.</p>\n</body>\n</html>\n"
    )


# The Threshold Effects series now has its canonical home on the firm site.
# These posts stay readable here, but each carries a rel=canonical link to
# its numbered counterpart so search engines treat the new site as the
# record. Numbers match the "No. 0XX" footers in the posts themselves.
SERIES_CANONICAL = {
    "the-faster-is-better-assumption": 1,
    "cover-yourself-8-ks": 2,
    "paper-trails-and-shadow-ai": 3,
    "shadow-it-was-the-rehearsal": 4,
    "three-rules-same-outcome": 5,
    "wanted-the-best-counterexample": 6,
    "what-the-broadband-labels-revealed": 7,
    "the-dashboard-is-green": 8,
    "say-something-vs-build-something": 9,
    "a-fair-fight-with-sox-404": 10,
    "gulf-coast-who-the-money-moves-through": 11,
}


def _published_posts():
    posts = [p for p in POSTS if not p.get("draft")]
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def _post_view(post):
    """Post dict plus the derived fields the templates need."""
    d = datetime.strptime(post["date"], "%Y-%m-%d")
    words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", post["body"])))
    view = dict(post)
    view["display_date"] = f"{d.strftime('%B')} {d.day}, {d.year}"
    view["minutes"] = max(1, round(words / 200))
    view["href"] = post["slug"] + ".html"
    view["url"] = f"{SITE['base_url']}/blog/{post['slug']}.html"
    n = SERIES_CANONICAL.get(post["slug"])
    view["canonical"] = (
        f"https://thresholddatasciences.com/threshold-effects/no-{n:03d}/"
        if n else view["url"])
    return view


def render_blog():
    return render_template_string(
        BLOG_TEMPLATE,
        site=SITE,
        blog=BLOG,
        posts=[_post_view(p) for p in _published_posts()],
        page_title=f"{BLOG['name']} | {SITE['name']}",
        page_desc=BLOG["meta_description"],
        page_url=f"{SITE['base_url']}/blog/",
        year=date.today().year,
    )


def render_post(post):
    view = _post_view(post)
    return render_template_string(
        POST_TEMPLATE,
        site=SITE,
        blog=BLOG,
        post=view,
        page_title=f"{view['title']} | {BLOG['name']}",
        page_desc=view["summary"],
        page_url=view["url"],
        canonical=view["canonical"],
        year=date.today().year,
    )


def blog_feed_xml():
    items = []
    for p in _published_posts():
        link = f"{SITE['base_url']}/blog/{p['slug']}.html"
        pub = datetime.strptime(p["date"], "%Y-%m-%d").strftime(
            "%a, %d %b %Y 12:00:00 GMT")
        items.append(
            "<item>"
            f"<title>{xml_escape(p['title'])}</title>"
            f"<link>{link}</link>"
            f'<guid isPermaLink="true">{link}</guid>'
            f"<pubDate>{pub}</pubDate>"
            f"<description>{xml_escape(p['summary'])}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        f"<title>{xml_escape(BLOG['name'])}</title>"
        f"<link>{SITE['base_url']}/blog/</link>"
        f"<description>{xml_escape(BLOG['meta_description'])}</description>"
        f"<language>en-us</language>"
        + "".join(items)
        + "</channel></rss>\n"
    )


@app.route("/")
def index():
    return render()


@app.route("/threshold/")
def threshold_page():
    return render_threshold()


@app.route("/blog/")
def blog_index():
    return render_blog()


@app.route("/blog/<slug>.html")
def blog_post(slug):
    for p in _published_posts():
        if p["slug"] == slug:
            return render_post(p)
    abort(404)


@app.route("/blog/feed.xml")
def blog_feed():
    return app.response_class(blog_feed_xml(), mimetype="application/rss+xml")


@app.route("/headshot.jpg")
def portrait():
    return send_from_directory(HERE, "headshot.jpg")


@app.route("/clocktower.jpg")
def clocktower():
    return send_from_directory(HERE, "clocktower.jpg")


@app.route("/timothy-spivey-cv.pdf")
def cv():
    return send_from_directory(HERE, "timothy-spivey-cv.pdf")


# Static on GitHub Pages too: Pages serves /retention-playbook from the .html file.
@app.route("/retention-playbook")
@app.route("/retention-playbook.html")
def retention_playbook():
    return send_from_directory(HERE, "retention-playbook.html")


@app.route("/contact", methods=["POST"])
def contact():
    """Local fallback — prints the submission to your terminal.

    For a real deploy set SITE["contact_endpoint"] to a Formspree URL (or wire
    an SMTP send in here); a static host cannot run this route.
    """
    fields = {k: request.form.get(k, "") for k in
              ("first_name", "last_name", "email", "topic", "message")}
    app.logger.info("Contact form submission: %s", fields)
    flash("Thanks - your message was received.")
    return redirect(url_for("index") + "#contact")


def build():
    """Write standalone index.html + blog/ you can upload to any static host."""
    out = os.path.join(HERE, "index.html")
    with app.test_request_context():
        html = render(building=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("Wrote", out)

    th_dir = os.path.join(HERE, "threshold")
    os.makedirs(th_dir, exist_ok=True)
    th_out = os.path.join(th_dir, "index.html")
    with app.test_request_context():
        th_html = render_threshold()
    with open(th_out, "w", encoding="utf-8") as fh:
        fh.write(th_html)
    print("Wrote", th_out)

    blog_dir = os.path.join(HERE, "blog")
    os.makedirs(blog_dir, exist_ok=True)
    with app.test_request_context():
        pages = [("index.html", render_blog())]
        pages += [(p["slug"] + ".html", render_post(p))
                  for p in _published_posts()]
    pages.append(("feed.xml", blog_feed_xml()))
    for name, content in pages:
        path = os.path.join(blog_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print("Wrote", path)

    if not SITE["contact_endpoint"]:
        print("Note: set SITE['contact_endpoint'] to a Formspree URL - the "
              "contact form has nowhere to post in a static build.")


# =============================================================================
# TEMPLATE — HTML, CSS, and JS
# =============================================================================

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{ site.name }} | {{ site.title }}</title>
  <meta name="description" content="{{ site.meta_description }}" />
  <meta property="og:title" content="{{ site.name }} — {{ site.title }}" />
  <meta property="og:description" content="{{ site.meta_description }}" />
  <meta property="og:type" content="profile" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet" />
{% if site.ga_measurement_id %}
  <!-- Google Analytics 4 -->
  <script async src="https://www.googletagmanager.com/gtag/js?id={{ site.ga_measurement_id }}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', '{{ site.ga_measurement_id }}');
  </script>
{% endif %}
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --navy:   #0d1b2a;
      --blue:   #223b52;          /* deep navy secondary */
      --accent: #b8970a;          /* gold */
      --accent-lit: #e2c84b;      /* lit gold */
      --light:  #f8f2dc;          /* pale gold tint */
      --sand:   #f4f2ed;
      --text:   #16222d;
      --muted:  #5a6a78;
      --border: #ddd9cd;
      --white:  #ffffff;
      --radius: 12px;
      --shadow: 0 4px 24px rgba(13,27,42,.08);
      --shadow-lg: 0 12px 48px rgba(13,27,42,.14);
    }

    html { scroll-behavior: smooth; }

    body {
      font-family: 'Inter', sans-serif;
      color: var(--text);
      background: var(--white);
      line-height: 1.65;
      -webkit-font-smoothing: antialiased;
    }

    /* NAV */
    nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      backdrop-filter: blur(14px) saturate(160%);
      background: rgba(255,255,255,.88);
      border-bottom: 1px solid var(--border);
      height: 64px;
      display: flex; align-items: center;
    }
    .nav-inner {
      max-width: 1100px; margin: 0 auto; padding: 0 2rem;
      width: 100%;
      display: flex; align-items: center; justify-content: space-between;
    }
    .nav-logo {
      font-family: 'Playfair Display', serif;
      font-size: 1.15rem; font-weight: 700;
      color: var(--navy); text-decoration: none;
    }
    .nav-links { display: flex; gap: 2rem; list-style: none; }
    .nav-links a {
      text-decoration: none; font-size: .875rem; font-weight: 500;
      color: var(--muted); transition: color .2s;
    }
    .nav-links a:hover { color: var(--accent); }

    /* HERO */
    #hero {
      min-height: 100vh;
      background: linear-gradient(135deg, var(--navy) 0%, #16293d 60%, var(--blue) 100%);
      display: flex; align-items: center; justify-content: center;
      text-align: center; padding: 7rem 2rem 4rem;
      position: relative; overflow: hidden;
    }
    #hero::before {
      content: '';
      position: absolute; inset: 0;
      background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Ccircle cx='30' cy='30' r='1' fill='rgba(255,255,255,.06)'/%3E%3C/svg%3E") repeat;
      pointer-events: none;
    }
    .hero-content { position: relative; z-index: 1; max-width: 720px; }
    .hero-badge {
      display: inline-flex; align-items: center; gap: .5rem;
      background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.2);
      color: rgba(255,255,255,.9); font-size: .78rem; font-weight: 600;
      letter-spacing: .08em; text-transform: uppercase;
      padding: .35rem 1rem; border-radius: 999px; margin-bottom: 1.5rem;
    }
    .hero-badge span { width: 6px; height: 6px; background: var(--accent-lit); border-radius: 50%; }
    h1 {
      font-family: 'Playfair Display', serif;
      font-size: clamp(2.4rem, 6vw, 4rem); font-weight: 700;
      color: var(--white); line-height: 1.15; margin-bottom: 1rem;
    }
    .hero-subtitle { font-size: 1.15rem; color: rgba(255,255,255,.78); margin-bottom: .5rem; }
    .hero-institution { font-size: .95rem; color: rgba(255,255,255,.55); margin-bottom: 2.5rem; }
    .hero-ctas { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
    .btn {
      display: inline-flex; align-items: center; gap: .5rem;
      padding: .75rem 1.75rem; border-radius: 8px;
      font-size: .9rem; font-weight: 600;
      text-decoration: none; transition: all .22s; cursor: pointer; border: none;
    }
    .btn-primary { background: var(--white); color: var(--navy); }
    .btn-primary:hover { background: var(--light); transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,.18); }
    .btn-outline { background: transparent; color: var(--white); border: 1.5px solid rgba(255,255,255,.45); }
    .btn-outline:hover { background: rgba(255,255,255,.1); border-color: rgba(255,255,255,.75); transform: translateY(-1px); }
    .scroll-hint {
      position: absolute; bottom: 2rem; left: 50%; transform: translateX(-50%);
      color: rgba(255,255,255,.4); font-size: .78rem; letter-spacing: .06em;
      text-transform: uppercase; display: flex; flex-direction: column; align-items: center; gap: .5rem;
      animation: bounce 2.4s infinite;
    }
    @keyframes bounce { 0%,100%{transform:translateX(-50%) translateY(0)} 50%{transform:translateX(-50%) translateY(6px)} }

    .drop-dot {
      display: inline-block;
      animation: dropDot .7s cubic-bezier(.34,1.1,.4,1) 1.3s both;
    }
    @keyframes dropDot {
      0%   { transform: translateY(-2.2em); opacity: 0; }
      55%  { transform: translateY(.12em); opacity: 1; }
      72%  { transform: translateY(-.06em); }
      86%  { transform: translateY(.03em); }
      100% { transform: translateY(0); }
    }
    @media (prefers-reduced-motion: reduce) {
      .drop-dot { animation: none; }
      .scroll-hint { animation: none; }
      html { scroll-behavior: auto; }
    }

    /* SECTIONS */
    section { padding: 5rem 2rem; }
    .container { max-width: 1100px; margin: 0 auto; }
    .section-label {
      font-size: .72rem; font-weight: 700; letter-spacing: .12em;
      text-transform: uppercase; color: var(--accent); margin-bottom: .6rem;
    }
    .section-title {
      font-family: 'Playfair Display', serif;
      font-size: clamp(1.7rem, 3vw, 2.4rem); font-weight: 700;
      color: var(--navy); line-height: 1.2; margin-bottom: 1rem;
    }
    .section-desc { font-size: 1rem; color: var(--muted); max-width: 560px; margin-bottom: 3rem; }
    .divider { width: 48px; height: 3px; background: var(--accent); border-radius: 2px; margin: 1rem 0 3rem; }

    /* ABOUT */
    #about { background: var(--sand); }
    .about-grid { display: grid; grid-template-columns: 1fr 1.6fr; gap: 4rem; align-items: start; }
    .about-card {
      background: var(--white); border-radius: var(--radius);
      padding: 2rem; box-shadow: var(--shadow); border: 1px solid var(--border);
    }
    .about-photo {
      width: 110px; height: 110px;
      border-radius: 50%;
      object-fit: cover; object-position: center top;
      border: 3px solid var(--light);
      box-shadow: 0 4px 16px rgba(13,27,42,.14);
      margin-bottom: 1.25rem;
      display: block;
    }
    .about-name { font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: var(--navy); margin-bottom: .25rem; }
    .about-role { font-size: .85rem; color: var(--accent); font-weight: 600; margin-bottom: .2rem; }
    .about-school { font-size: .82rem; color: var(--muted); }
    .about-second-role { font-size: .78rem; color: var(--muted); font-style: italic; margin: .3rem 0 .75rem; padding-top: .3rem; border-top: 1px solid var(--border); }
    .school-logos { display: flex; align-items: center; gap: 1.25rem; margin-bottom: 1.25rem; }
    .school-logo { height: 70px; width: auto; max-width: 48%; object-fit: contain; display: block; }
    .about-stat-row { display: flex; gap: 1.5rem; margin-bottom: 1.5rem; }
    .about-stat { text-align: center; }
    .about-stat strong { display: block; font-size: 1.4rem; font-weight: 700; color: var(--navy); }
    .about-stat span { font-size: .75rem; color: var(--muted); }
    .about-links { display: flex; flex-direction: column; gap: .6rem; }
    .about-link {
      display: flex; align-items: center; gap: .6rem;
      font-size: .83rem; color: var(--muted); text-decoration: none; transition: color .2s;
    }
    .about-link:hover { color: var(--accent); }
    .about-link svg { width: 14px; flex-shrink: 0; }
    .about-bio p { color: var(--muted); font-size: 1rem; line-height: 1.75; margin-bottom: 1rem; }
    .about-bio p:last-child { margin-bottom: 0; }
    .tags { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.5rem; }
    .tag {
      background: var(--light); color: var(--blue); font-size: .78rem; font-weight: 600;
      padding: .3rem .85rem; border-radius: 999px; border: 1px solid rgba(184,151,10,.3);
    }

    /* GALLERY */
    #gallery { background: var(--white); padding: 0; }
    .gallery-strip {
      display: grid;
      grid-template-columns: 1.4fr 1fr 1fr;
      height: 340px;
      overflow: hidden;
    }
    .gallery-item {
      position: relative; overflow: hidden;
    }
    .gallery-item img {
      width: 100%; height: 100%;
      object-fit: cover;
      transition: transform .5s ease;
      display: block;
    }
    .gallery-item:hover img { transform: scale(1.04); }
    .gallery-caption {
      position: absolute; bottom: 0; left: 0; right: 0;
      background: linear-gradient(transparent, rgba(13,27,42,.7));
      color: rgba(255,255,255,.9);
      font-size: .78rem; font-weight: 600;
      padding: 1.5rem .75rem .6rem;
      letter-spacing: .03em;
    }

    /* RESEARCH */
    #research { background: var(--sand); }
    .research-card-img {
      width: 100%; height: 160px;
      object-fit: cover;
      border-radius: 8px;
      margin-bottom: 1rem;
      display: block;
    }
    .research-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
    .research-card {
      background: var(--white); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 1.75rem;
      transition: all .22s; position: relative; overflow: hidden;
    }
    .research-card::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, var(--accent), var(--accent-lit));
      transform: scaleX(0); transform-origin: left; transition: transform .3s;
    }
    .research-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-3px); }
    .research-card:hover::before { transform: scaleX(1); }
    .research-card h3 { font-size: 1rem; font-weight: 700; color: var(--navy); margin-bottom: .5rem; }
    .research-card p { font-size: .875rem; color: var(--muted); line-height: 1.65; }

    /* PUBLICATIONS */
    #publications { background: var(--sand); }
    .pub-list { display: flex; flex-direction: column; gap: 1.25rem; }
    .pub-item {
      background: var(--white); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 1.5rem 1.75rem;
      display: flex; gap: 1.25rem; align-items: flex-start; transition: box-shadow .22s;
    }
    .pub-item:hover { box-shadow: var(--shadow); }
    .pub-year {
      flex-shrink: 0; font-size: .75rem; font-weight: 700; letter-spacing: .05em;
      color: var(--accent); background: var(--light);
      padding: .3rem .7rem; border-radius: 6px; margin-top: .15rem;
    }
    .pub-title { font-size: .95rem; font-weight: 600; color: var(--navy); margin-bottom: .3rem; }
    .pub-title a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--accent); }
    .pub-authors { font-size: .82rem; color: var(--muted); margin-bottom: .25rem; }
    .pub-journal { font-size: .82rem; color: var(--accent); font-style: italic; }
    .pub-type {
      display: inline-block; font-size: .7rem; font-weight: 700;
      letter-spacing: .06em; text-transform: uppercase; color: var(--muted);
      border: 1px solid var(--border); padding: .15rem .5rem; border-radius: 4px; margin-top: .5rem;
    }
    .pub-type + .pub-type { margin-left: .4rem; }

    /* SERVICE & AFFILIATIONS */
    #service { background: var(--white); }
    .service-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 1.5rem; align-items: start; }
    @media (max-width: 768px) { .service-grid { grid-template-columns: 1fr; } }
    .service-card {
      background: var(--sand); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 1.5rem 1.75rem;
    }
    .service-card h3 { font-size: 1rem; font-weight: 700; color: var(--navy); margin-bottom: 1rem; }
    .service-item { margin-bottom: 1.1rem; }
    .service-item:last-child { margin-bottom: 0; }
    .service-role { font-size: .92rem; font-weight: 600; color: var(--navy); }
    .service-role em { color: var(--accent); }
    .service-years {
      font-size: .72rem; font-weight: 700; letter-spacing: .05em;
      color: var(--accent); text-transform: uppercase; margin: .15rem 0 .3rem;
    }
    .service-item p { font-size: .82rem; color: var(--muted); line-height: 1.6; }

    /* TEACHING */
    #teaching { background: var(--sand); }
    .teaching-header {
      display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; margin-bottom: 3rem;
    }
    .teaching-photo {
      width: 100%; height: 240px; object-fit: cover; border-radius: var(--radius);
      box-shadow: var(--shadow-lg); display: block;
    }
    @media (max-width: 768px) { .teaching-header { grid-template-columns: 1fr; } }
    .institution-timeline { display: flex; flex-direction: column; gap: 1.75rem; margin-top: 2.5rem; }
    .institution-block {
      display: grid; grid-template-columns: 220px 1fr; gap: 2rem; align-items: center;
      background: var(--white); border: 1px solid var(--border); border-radius: var(--radius);
      padding: 1.5rem; box-shadow: var(--shadow); transition: all .2s;
    }
    .institution-block:hover { box-shadow: var(--shadow-lg); transform: translateY(-2px); }
    .institution-media { position: relative; }
    .institution-building { width: 100%; height: 130px; object-fit: cover; border-radius: 8px; display: block; }
    .institution-logo {
      width: 52px; height: 52px; object-fit: contain; background: var(--white);
      border-radius: 8px; padding: 5px; border: 1px solid var(--border);
      position: absolute; bottom: -12px; left: -12px; box-shadow: var(--shadow);
    }
    .institution-logo-only {
      height: 130px; display: flex; align-items: center; justify-content: center;
      background: var(--sand); border-radius: 8px;
    }
    .institution-logo-only img { width: 120px; height: auto; max-height: 100px; object-fit: contain; }
    .institution-name { font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 700; color: var(--navy); }
    .institution-role { font-size: .82rem; color: var(--muted); margin-top: .1rem; }
    .institution-years { font-size: .78rem; color: var(--accent); font-weight: 700; letter-spacing: .04em; margin: .2rem 0 .9rem; text-transform: uppercase; }
    .institution-courses { display: flex; flex-wrap: wrap; gap: .65rem; }
    .institution-courses span {
      font-size: .95rem; background: var(--sand); border: 1px solid var(--border);
      padding: .55rem 1.1rem; border-radius: 999px; color: var(--text);
    }
    @media (max-width: 640px) {
      .institution-block { grid-template-columns: 1fr; }
      .institution-building { height: 170px; }
    }

    /* CONSULTING */
    #consulting { background: var(--white); }
    .consult-tagline {
      font-size: .78rem; font-weight: 700; letter-spacing: .12em;
      text-transform: uppercase; color: var(--muted); margin-bottom: 1.5rem;
    }
    .consult-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }
    .consult-card {
      background: var(--sand); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 1.75rem; transition: all .2s;
    }
    .consult-card:hover { background: var(--light); border-color: rgba(184,151,10,.35); transform: translateY(-2px); }
    .consult-card h3 { font-size: 1rem; font-weight: 700; color: var(--navy); margin-bottom: .5rem; }
    .consult-card p { font-size: .875rem; color: var(--muted); line-height: 1.65; }
    .btn-accent { background: var(--accent); color: var(--navy); }
    .btn-accent:hover { background: var(--accent-lit); transform: translateY(-1px); box-shadow: 0 4px 16px rgba(184,151,10,.35); }
    .btn-outline-navy { background: transparent; color: var(--navy); border: 1.5px solid var(--border); margin-left: .75rem; }
    .btn-outline-navy:hover { border-color: var(--accent); color: var(--accent); transform: translateY(-1px); }

    /* CV STRIP */
    #cv {
      background: linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%);
      padding: 4rem 2rem; text-align: center;
    }
    #cv h2 {
      font-family: 'Playfair Display', serif;
      font-size: clamp(1.6rem, 3vw, 2.2rem); color: var(--white); margin-bottom: .75rem;
    }
    #cv p { color: rgba(255,255,255,.7); font-size: 1rem; margin-bottom: 2rem; }
    .cv-buttons { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }

    /* CONTACT */
    #contact { background: var(--sand); }
    .contact-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; }
    .contact-info h3 { font-size: 1.1rem; font-weight: 700; color: var(--navy); margin-bottom: 1.5rem; }
    .contact-item { display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 1.25rem; }
    .contact-icon {
      width: 40px; height: 40px; flex-shrink: 0;
      background: var(--white); border: 1px solid var(--border);
      border-radius: 10px; display: flex; align-items: center; justify-content: center;
    }
    .contact-icon svg { width: 18px; color: var(--accent); }
    .contact-label { font-size: .75rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: .2rem; }
    .contact-value { font-size: .95rem; color: var(--navy); font-weight: 500; }
    .contact-value a { color: var(--accent); text-decoration: none; }
    .contact-form {
      background: var(--white); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 2rem; box-shadow: var(--shadow);
    }
    .contact-form h3 { font-size: 1.1rem; font-weight: 700; color: var(--navy); margin-bottom: 1.25rem; }
    .flash {
      background: #e8f8f0; border: 1px solid #27ae60; color: #1e8449;
      border-radius: 8px; padding: .7rem 1rem; font-size: .85rem; margin-bottom: 1rem;
    }
    .form-group { margin-bottom: 1rem; }
    .form-group label { display: block; font-size: .82rem; font-weight: 600; color: var(--text); margin-bottom: .4rem; }
    .form-group input, .form-group textarea, .form-group select {
      width: 100%; padding: .65rem .9rem;
      border: 1.5px solid var(--border); border-radius: 8px;
      font-family: 'Inter', sans-serif; font-size: .9rem; color: var(--text);
      background: var(--white); transition: border-color .2s; outline: none;
    }
    .form-group input:focus, .form-group textarea:focus, .form-group select:focus { border-color: var(--accent); }
    .form-group textarea { resize: vertical; min-height: 110px; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .btn-submit {
      width: 100%; background: var(--navy); color: var(--white);
      padding: .8rem; border-radius: 8px; font-size: .92rem; font-weight: 600;
      border: none; cursor: pointer; transition: all .22s; font-family: 'Inter', sans-serif;
    }
    .btn-submit:hover { background: var(--blue); transform: translateY(-1px); box-shadow: 0 4px 16px rgba(13,27,42,.35); }

    /* FOOTER */
    footer {
      background: var(--navy); color: rgba(255,255,255,.5);
      text-align: center; padding: 2rem; font-size: .82rem;
    }
    footer strong { color: rgba(255,255,255,.8); }

    /* RESPONSIVE */
    @media (max-width: 768px) {
      .about-grid { grid-template-columns: 1fr; gap: 2rem; }
      .contact-grid { grid-template-columns: 1fr; }
      .form-row { grid-template-columns: 1fr; }
      .nav-links { display: none; }
      .gallery-strip { grid-template-columns: 1fr; height: auto; }
      .gallery-item { height: 220px; }
    }
  </style>
</head>
<body>

<nav>
  <div class="nav-inner">
    <a href="#hero" class="nav-logo">{{ site.name }}</a>
    <ul class="nav-links">
      {% for item in nav %}<li><a href="{{ item.href }}">{{ item.label }}</a></li>{% endfor %}
    </ul>
  </div>
</nav>

<section id="hero">
  <div class="hero-content">
    <div class="hero-badge"><span></span>Academic Portfolio</div>
    <h1>{{ site.hero_name_before_dot }}<span class="drop-dot">.</span>{{ site.hero_name_after_dot }}</h1>
    <p class="hero-subtitle">{{ site.title }}</p>
    <p class="hero-institution">{{ site.affiliation }}<br/>{{ site.institution }}</p>
    <div class="hero-ctas">
      <a href="#research" class="btn btn-primary">
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
        View Research
      </a>
      <a href="#contact" class="btn btn-outline">Get in Touch</a>
    </div>
  </div>
  <div class="scroll-hint">
    <span>Scroll</span>
    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"/></svg>
  </div>
</section>

<section id="about">
  <div class="container">
    <div class="about-grid">
      <div>
        <div class="about-card">
          <img src="{{ portrait_url }}" alt="{{ about.portrait_alt }}" class="about-photo" />
          <div class="about-name">{{ site.name }}</div>
          <div class="about-role">{{ about_card.role }}</div>
          <div class="about-school">{{ about_card.school }}</div>
          <div class="about-second-role">{{ about_card.secondary_role }}</div>
          <div class="school-logos">
            {% for l in about_card.school_logos %}
            <img src="{{ l.src }}" alt="{{ l.alt }}" class="school-logo" />
            {% endfor %}
          </div>
          <div class="about-stat-row">
            {% for s in about_card.stats %}
            <div class="about-stat"><strong>{{ s.value }}</strong><span>{{ s.label }}</span></div>
            {% endfor %}
          </div>
          <div class="about-links">
            <a href="{{ site.links.scholar }}" target="_blank" class="about-link">
              <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 14l9-5-9-5-9 5 9 5z"/><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"/></svg>
              Google Scholar Profile
            </a>
            <a href="{{ site.links.linkedin }}" target="_blank" class="about-link">
              <svg fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 11.001-4.124 2.062 2.062 0 01-.001 4.124zM7.114 20.452H3.558V9h3.556v11.452z"/></svg>
              {{ site.links.linkedin_label }}
            </a>
            <a href="mailto:{{ site.email }}" class="about-link">
              <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              {{ site.email }}
            </a>
            <a href="{{ site.links.firm }}" class="about-link">
              <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 21h18M5 21V7l7-4 7 4v14M9 9h1m4 0h1M9 13h1m4 0h1M9 17h1m4 0h1"/></svg>
              Threshold Data Sciences
            </a>
          </div>
        </div>
      </div>

      <div class="about-bio">
        <div class="section-label">About</div>
        <h2 class="section-title">{{ about.heading }}</h2>
        <div class="divider"></div>
        {% for p in about.paragraphs %}<p>{{ p }}</p>{% endfor %}
        <div class="tags">
          {% for k in about.keywords %}<span class="tag">{{ k }}</span>{% endfor %}
        </div>
      </div>
    </div>
  </div>
</section>

<section id="gallery">
  <div class="gallery-strip">
    {% for g in gallery %}
    <div class="gallery-item">
      <img src="{{ g.image }}" alt="{{ g.alt }}" loading="lazy" />
      <div class="gallery-caption">{{ g.caption }}</div>
    </div>
    {% endfor %}
  </div>
</section>

<section id="research">
  <div class="container">
    <div class="section-label">Scholarship</div>
    <h2 class="section-title">Research Interests</h2>
    <p class="section-desc">{{ research.intro }}</p>
    <div class="divider"></div>
    <div class="research-grid">
      {% for c in research.cards %}
      <div class="research-card">
        <img src="{{ c.image }}" alt="{{ c.alt }}" class="research-card-img" loading="lazy" />
        <h3>{{ c.title }}</h3>
        <p>{{ c.text }}</p>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<section id="publications">
  <div class="container">
    <div class="section-label">Scholarship</div>
    <h2 class="section-title">Selected Publications</h2>
    <p class="section-desc">{{ publications.intro }}</p>
    <div class="divider"></div>
    <div class="pub-list">
      {% for p in publications.entries %}
      <div class="pub-item">
        <div class="pub-year">{{ p.year }}</div>
        <div>
          <div class="pub-title">
            {% if p.url %}<a href="{{ p.url }}" target="_blank">{{ p.title }}</a>{% else %}{{ p.title }}{% endif %}
          </div>
          <div class="pub-authors">{{ p.authors }}</div>
          <div class="pub-journal">{{ p.venue }}</div>
          <span class="pub-type">{{ p.kind }}</span><span class="pub-type">{{ p.status }}</span>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<section id="service">
  <div class="container">
    <div class="section-label">Scholarship</div>
    <h2 class="section-title">Service &amp; Affiliations</h2>
    <p class="section-desc">{{ service.intro }}</p>
    <div class="divider"></div>
    <div class="service-grid">
      <div class="service-card">
        <h3>Editorial &amp; Review Service</h3>
        {% for r in service.review %}
        <div class="service-item">
          <div class="service-role">{{ r.role }} · <em>{{ r.venue }}</em></div>
          <div class="service-years">{{ r.years }}</div>
          <p>{{ r.note }}</p>
        </div>
        {% endfor %}
      </div>
      <div class="service-card">
        <h3>Professional Affiliations</h3>
        {% for a in service.affiliations %}
        <div class="service-item">
          <div class="service-role">{{ a.name }}</div>
          <p>{{ a.detail }}</p>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</section>

<section id="teaching">
  <div class="container">
    <div class="teaching-header">
      <div>
        <div class="section-label">Classroom</div>
        <h2 class="section-title">Courses Taught</h2>
        <p class="section-desc" style="margin-bottom:0">{{ teaching.intro }}</p>
        <div class="divider" style="margin-bottom:0"></div>
      </div>
      <div>
        <img src="{{ teaching.photo }}" alt="{{ teaching.photo_alt }}" class="teaching-photo" loading="lazy" />
      </div>
    </div>
    <div class="institution-timeline">
      {% for inst in teaching.institutions %}
      <div class="institution-block">
        {% if inst.building %}
        <div class="institution-media">
          <img src="{{ inst.building }}" alt="{{ inst.building_alt }}" class="institution-building" loading="lazy" />
          <img src="{{ inst.logo }}" alt="{{ inst.logo_alt }}" class="institution-logo" loading="lazy" />
        </div>
        {% else %}
        <div class="institution-logo-only">
          <img src="{{ inst.logo }}" alt="{{ inst.logo_alt }}" loading="lazy" />
        </div>
        {% endif %}
        <div>
          <div class="institution-name">{{ inst.name }}</div>
          <div class="institution-role">{{ inst.role }}</div>
          <div class="institution-years">{{ inst.years }}</div>
          <div class="institution-courses">
            {% for c in inst.courses %}<span>{{ c }}</span>{% endfor %}
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<section id="cv">
  <h2>Download Full Curriculum Vitae</h2>
  <p>Academic history, complete publication list, applied work, and service record.</p>
  <div class="cv-buttons">
    <a href="{{ site.cv_url }}" target="_blank" class="btn btn-primary">
      <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2"/></svg>
      Download CV (PDF)
    </a>
    <a href="{{ site.links.scholar }}" target="_blank" class="btn btn-outline">Google Scholar</a>
  </div>
</section>

<section id="contact">
  <div class="container">
    <div class="section-label">Connect</div>
    <h2 class="section-title">Get in Touch</h2>
    <p class="section-desc">{{ contact.intro }}</p>
    <div class="divider"></div>
    <div class="contact-grid">
      <div class="contact-info">
        <h3>Contact Information</h3>
        <div class="contact-item">
          <div class="contact-icon">
            <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          </div>
          <div>
            <div class="contact-label">Email</div>
            <div class="contact-value">{{ site.email }}</div>
          </div>
        </div>
        <div class="contact-item">
          <div class="contact-icon">
            <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          </div>
          <div>
            <div class="contact-label">Location</div>
            <div class="contact-value">{{ site.location_lines | join('<br/>') | safe }}</div>
          </div>
        </div>
        <div class="contact-item">
          <div class="contact-icon">
            <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 14l9-5-9-5-9 5 9 5z"/><path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z"/></svg>
          </div>
          <div>
            <div class="contact-label">Scholar</div>
            <div class="contact-value"><a href="{{ site.links.scholar }}" target="_blank">Google Scholar Profile</a></div>
          </div>
        </div>
        <div class="contact-item">
          <div class="contact-icon">
            <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 21h18M5 21V7l7-4 7 4v14M9 9h1m4 0h1M9 13h1m4 0h1M9 17h1m4 0h1"/></svg>
          </div>
          <div>
            <div class="contact-label">Consulting</div>
            <div class="contact-value"><a href="{{ site.links.firm }}">{{ consulting.firm }}</a></div>
          </div>
        </div>
      </div>

      <div class="contact-form">
        <h3>Send a Message</h3>
        {% with messages = get_flashed_messages() %}
          {% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}
        {% endwith %}
        <form method="post" action="{{ form_action }}">
          {% if site.contact_endpoint %}
          <input type="hidden" name="_subject" value="Message from timothydspivey.com" />
          <input type="hidden" name="_captcha" value="false" />
          <input type="hidden" name="_next" value="https://timothydspivey.com/thanks.html" />
          <input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off" />
          {% endif %}
          <div class="form-row">
            <div class="form-group">
              <label>First Name</label>
              <input type="text" name="first_name" placeholder="Jane" required />
            </div>
            <div class="form-group">
              <label>Last Name</label>
              <input type="text" name="last_name" placeholder="Smith" required />
            </div>
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" name="email" placeholder="jane@example.com" required />
          </div>
          <div class="form-group">
            <label>Subject</label>
            <select name="topic">
              <option value="">Select a topic&hellip;</option>
              {% for t in contact.topics %}<option>{{ t }}</option>{% endfor %}
            </select>
          </div>
          <div class="form-group">
            <label>Message</label>
            <textarea name="message" placeholder="Your message&hellip;" required></textarea>
          </div>
          <button class="btn-submit" type="submit">Send Message</button>
        </form>
      </div>
    </div>
  </div>
</section>

<footer>
  <p><strong>{{ site.name }}</strong> &nbsp;&middot;&nbsp; {{ site.title }} &nbsp;&middot;&nbsp; {{ site.institution }}</p>
  <p style="margin-top:.4rem">&copy; {{ year }} {{ site.name }}. All rights reserved.</p>
</footer>

<script>
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        navLinks.forEach(a => a.style.color = '');
        const active = document.querySelector('.nav-links a[href="#' + e.target.id + '"]');
        if (active) active.style.color = 'var(--accent)';
      }
    });
  }, { threshold: 0.4 });
  sections.forEach(s => observer.observe(s));

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduceMotion) {
    const cards = document.querySelectorAll('.research-card, .pub-item, .consult-card, .institution-block, .about-card');
    cards.forEach(c => {
      c.style.opacity = '0';
      c.style.transform = 'translateY(18px)';
      c.style.transition = 'opacity .45s ease, transform .45s ease';
    });
    const cardObserver = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          setTimeout(() => {
            e.target.style.opacity = '1';
            e.target.style.transform = 'translateY(0)';
          }, 60);
          cardObserver.unobserve(e.target);
        }
      });
    }, { threshold: 0.1 });
    cards.forEach(c => cardObserver.observe(c));
  }
</script>
</body>
</html>
"""


# --- Blog templates -----------------------------------------------------------
# Blog pages live at /blog/, so links back to the main page are root-absolute
# ("/#about") and links within the blog are relative — both work on the Flask
# dev server and on the static deploy.

_BLOG_HEAD = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{ page_title }}</title>
  <meta name="description" content="{{ page_desc }}" />
  <meta property="og:title" content="{{ page_title }}" />
  <meta property="og:description" content="{{ page_desc }}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{{ page_url }}" />
  <link rel="canonical" href="{{ canonical or page_url }}" />
  <link rel="alternate" type="application/rss+xml" title="{{ blog.name }}" href="/blog/feed.xml" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;700&display=swap" rel="stylesheet" />
{% if site.ga_measurement_id %}
  <!-- Google Analytics 4 -->
  <script async src="https://www.googletagmanager.com/gtag/js?id={{ site.ga_measurement_id }}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', '{{ site.ga_measurement_id }}');
  </script>
{% endif %}
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --navy:   #0d1b2a;
      --blue:   #223b52;
      --accent: #b8970a;
      --accent-lit: #e2c84b;
      --light:  #f8f2dc;
      --sand:   #f4f2ed;
      --text:   #16222d;
      --muted:  #5a6a78;
      --border: #ddd9cd;
      --white:  #ffffff;
      --radius: 12px;
      --shadow: 0 4px 24px rgba(13,27,42,.08);
      --shadow-lg: 0 12px 48px rgba(13,27,42,.14);
    }

    html { scroll-behavior: smooth; }

    body {
      font-family: 'Inter', sans-serif;
      color: var(--text);
      background: var(--white);
      line-height: 1.65;
      -webkit-font-smoothing: antialiased;
    }

    /* NAV (same as main page) */
    nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      backdrop-filter: blur(14px) saturate(160%);
      background: rgba(255,255,255,.88);
      border-bottom: 1px solid var(--border);
      height: 64px;
      display: flex; align-items: center;
    }
    .nav-inner {
      max-width: 1100px; margin: 0 auto; padding: 0 2rem;
      width: 100%;
      display: flex; align-items: center; justify-content: space-between;
    }
    .nav-logo {
      font-family: 'Playfair Display', serif;
      font-size: 1.15rem; font-weight: 700;
      color: var(--navy); text-decoration: none;
    }
    .nav-links { display: flex; gap: 2rem; list-style: none; }
    .nav-links a {
      text-decoration: none; font-size: .875rem; font-weight: 500;
      color: var(--muted); transition: color .2s;
    }
    .nav-links a:hover, .nav-links a.active { color: var(--accent); }

    /* BLOG HEADER BAND */
    .blog-hero {
      background: linear-gradient(135deg, var(--navy) 0%, #16293d 60%, var(--blue) 100%);
      padding: 9.5rem 2rem 4.5rem;
      text-align: center;
      position: relative; overflow: hidden;
    }
    .blog-hero::before {
      content: '';
      position: absolute; inset: 0;
      background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Ccircle cx='30' cy='30' r='1' fill='rgba(255,255,255,.06)'/%3E%3C/svg%3E") repeat;
      pointer-events: none;
    }
    .blog-hero-inner { position: relative; z-index: 1; max-width: 760px; margin: 0 auto; }
    .blog-kicker {
      font-size: .72rem; font-weight: 700; letter-spacing: .14em;
      text-transform: uppercase; color: var(--accent-lit); margin-bottom: .75rem;
    }
    .blog-hero h1 {
      font-family: 'Playfair Display', serif;
      font-size: clamp(2.2rem, 5.5vw, 3.6rem); font-weight: 700;
      color: var(--white); line-height: 1.12; margin-bottom: 1rem;
    }
    .blog-tagline { font-size: 1.02rem; color: rgba(255,255,255,.72); max-width: 620px; margin: 0 auto; }
    .blog-hero-meta {
      display: flex; gap: .9rem; justify-content: center; align-items: center; flex-wrap: wrap;
      font-size: .82rem; color: rgba(255,255,255,.6); margin-top: 1.25rem;
    }
    .blog-hero-meta a { color: var(--accent-lit); text-decoration: none; }
    .blog-hero-meta a:hover { text-decoration: underline; }
    .back-link {
      display: inline-flex; align-items: center; gap: .4rem;
      font-size: .82rem; font-weight: 600; letter-spacing: .04em;
      color: var(--accent-lit); text-decoration: none; margin-bottom: 1.25rem;
    }
    .back-link:hover { text-decoration: underline; }

    /* POST LIST */
    .wrap { max-width: 780px; margin: 0 auto; padding: 4rem 2rem 5rem; }
    .post-list { display: flex; flex-direction: column; gap: 1.5rem; }
    .post-card {
      background: var(--white); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 1.9rem 2rem;
      transition: all .22s; position: relative; overflow: hidden;
    }
    .post-card::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, var(--accent), var(--accent-lit));
      transform: scaleX(0); transform-origin: left; transition: transform .3s;
    }
    .post-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-3px); }
    .post-card:hover::before { transform: scaleX(1); }
    .post-card-meta {
      display: flex; align-items: center; gap: .75rem; flex-wrap: wrap;
      font-size: .78rem; color: var(--muted); margin-bottom: .6rem;
    }
    .post-date {
      font-size: .75rem; font-weight: 700; letter-spacing: .05em;
      color: var(--accent); background: var(--light);
      padding: .25rem .7rem; border-radius: 6px;
    }
    .post-card h2 { font-family: 'Playfair Display', serif; font-size: 1.35rem; line-height: 1.25; margin-bottom: .55rem; }
    .post-card h2 a { color: var(--navy); text-decoration: none; }
    .post-card h2 a:hover { color: var(--accent); }
    .post-card p { font-size: .92rem; color: var(--muted); line-height: 1.7; }
    .post-card-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 1.1rem; flex-wrap: wrap; gap: .75rem; }
    .tags { display: flex; flex-wrap: wrap; gap: .5rem; }
    .tag {
      background: var(--light); color: var(--blue); font-size: .74rem; font-weight: 600;
      padding: .25rem .8rem; border-radius: 999px; border: 1px solid rgba(184,151,10,.3);
    }
    .read-more {
      font-size: .84rem; font-weight: 600; color: var(--accent); text-decoration: none;
    }
    .read-more:hover { text-decoration: underline; }
    .empty-note { text-align: center; color: var(--muted); font-size: .95rem; }

    /* ARTICLE */
    .post-header-meta {
      display: flex; gap: .9rem; justify-content: center; align-items: center; flex-wrap: wrap;
      font-size: .84rem; color: rgba(255,255,255,.65); margin-top: 1.1rem;
    }
    .post-header-meta .tag { background: rgba(255,255,255,.1); color: rgba(255,255,255,.85); border-color: rgba(255,255,255,.25); }
    article { max-width: 720px; margin: 0 auto; padding: 3.5rem 2rem 4rem; }
    .post-body { font-size: 1.03rem; line-height: 1.8; }
    .post-body p { margin-bottom: 1.3rem; }
    .post-body h2 {
      font-family: 'Playfair Display', serif;
      font-size: 1.55rem; color: var(--navy); line-height: 1.25;
      margin: 2.4rem 0 .8rem;
    }
    .post-body h3 { font-size: 1.12rem; font-weight: 700; color: var(--navy); margin: 1.9rem 0 .6rem; }
    .post-body a { color: var(--accent); text-decoration: none; border-bottom: 1px solid rgba(184,151,10,.45); }
    .post-body a:hover { border-bottom-color: var(--accent); }
    .post-body blockquote {
      border-left: 3px solid var(--accent);
      padding: .3rem 0 .3rem 1.3rem; margin: 1.6rem 0;
      color: var(--muted); font-style: italic;
    }
    .post-body ul, .post-body ol { margin: 0 0 1.3rem 1.5rem; }
    .post-body li { margin-bottom: .45rem; }
    .post-body code {
      background: var(--sand); border: 1px solid var(--border); border-radius: 4px;
      padding: .1rem .4rem; font-size: .87em;
    }
    .post-body pre {
      background: var(--navy); color: #dbe7f3;
      padding: 1.25rem 1.4rem; border-radius: 8px;
      overflow-x: auto; margin-bottom: 1.3rem; font-size: .88rem; line-height: 1.6;
    }
    .post-body pre code { background: none; border: none; color: inherit; padding: 0; font-size: inherit; }
    .post-body img { max-width: 100%; border-radius: 8px; display: block; margin: 1.6rem auto; }
    .post-body figcaption { text-align: center; font-size: .8rem; color: var(--muted); margin-top: -1rem; margin-bottom: 1.6rem; }
    .post-body hr { border: none; border-top: 1px solid var(--border); margin: 2.2rem 0; }
    .post-end {
      margin-top: 3rem; padding-top: 1.75rem; border-top: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;
    }
    .post-end a { font-size: .88rem; font-weight: 600; color: var(--accent); text-decoration: none; }
    .post-end a:hover { text-decoration: underline; }

    /* FOOTER (same as main page) */
    footer {
      background: var(--navy); color: rgba(255,255,255,.5);
      text-align: center; padding: 2rem; font-size: .82rem;
    }
    footer strong { color: rgba(255,255,255,.8); }

    @media (max-width: 768px) {
      .nav-links { display: none; }
      .blog-hero { padding: 8rem 1.5rem 3.5rem; }
      .wrap, article { padding-left: 1.5rem; padding-right: 1.5rem; }
    }
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
    }
  </style>
</head>
<body>

<nav>
  <div class="nav-inner">
    <a href="/" class="nav-logo">{{ site.name }}</a>
    <ul class="nav-links">
      <li><a href="/#about">About</a></li>
      <li><a href="/#research">Research</a></li>
      <li><a href="/#publications">Publications</a></li>
      <li><a href="/#teaching">Teaching</a></li>
      <li><a href="/#consulting">Consulting</a></li>
      <li><a href="/blog/" class="active">Blog</a></li>
      <li><a href="/#contact">Contact</a></li>
    </ul>
  </div>
</nav>
"""

_BLOG_FOOT = r"""
<footer>
  <p><strong>{{ site.name }}</strong> &nbsp;&middot;&nbsp; {{ site.title }} &nbsp;&middot;&nbsp; {{ site.institution }}</p>
  <p style="margin-top:.4rem">&copy; {{ year }} {{ site.name }}. All rights reserved.</p>
</footer>
</body>
</html>
"""

BLOG_TEMPLATE = _BLOG_HEAD + r"""
<header class="blog-hero">
  <div class="blog-hero-inner">
    <div class="blog-kicker">{{ blog.label }}</div>
    <h1>{{ blog.name }}</h1>
    <p class="blog-tagline">{{ blog.tagline }}</p>
    <div class="blog-hero-meta">
      <span>by {{ site.name }}</span>
      <span>&middot;</span>
      <a href="feed.xml">RSS feed</a>
    </div>
  </div>
</header>

<main class="wrap">
  <div class="post-list">
  {% for post in posts %}
    <div class="post-card">
      <div class="post-card-meta">
        <span class="post-date">{{ post.display_date }}</span>
        <span>{{ post.minutes }} min read</span>
      </div>
      <h2><a href="{{ post.href }}">{{ post.title }}</a></h2>
      <p>{{ post.summary }}</p>
      <div class="post-card-foot">
        <div class="tags">
          {% for tag in post.tags %}<span class="tag">{{ tag }}</span>{% endfor %}
        </div>
        <a class="read-more" href="{{ post.href }}">Read the post &rarr;</a>
      </div>
    </div>
  {% else %}
    <p class="empty-note">Nothing here yet — the first post is on its way.</p>
  {% endfor %}
  </div>
</main>
""" + _BLOG_FOOT

POST_TEMPLATE = _BLOG_HEAD + r"""
<header class="blog-hero">
  <div class="blog-hero-inner">
    <a href="./" class="back-link">&larr; {{ blog.name }}</a>
    <h1>{{ post.title }}</h1>
    <div class="post-header-meta">
      <span>{{ post.display_date }}</span>
      <span>&middot;</span>
      <span>{{ post.minutes }} min read</span>
      {% if post.tags %}<span>&middot;</span>{% for tag in post.tags %}<span class="tag">{{ tag }}</span>{% endfor %}{% endif %}
    </div>
  </div>
</header>

<article>
  <div class="post-body">
{{ post.body | safe }}
  </div>
  <div class="post-end">
    <a href="./">&larr; All posts</a>
    <a href="/#contact">Get in touch &rarr;</a>
  </div>
</article>
""" + _BLOG_FOOT


if __name__ == "__main__":
    if "--build" in sys.argv:
        build()
    else:
        app.run(debug=True)
