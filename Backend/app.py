import html
from textwrap import dedent

import streamlit as st
from model.recommendation_model import recommend_skills


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Smart SkillPath",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CAREER-WISE SKILLS
# =========================================================

CAREER_SKILLS = {
    "Data Scientist": [
        "Python", "SQL", "Excel", "Machine Learning", "Statistics",
        "Pandas", "NumPy", "Data Visualization", "Scikit-learn",
        "TensorFlow", "PyTorch", "Deep Learning", "Data Mining",
        "Data Wrangling", "R", "Spark", "Hadoop"
    ],

    "Data Analyst": [
        "Python", "SQL", "Excel", "Power BI", "Tableau", "Statistics",
        "Pandas", "NumPy", "Data Visualization", "Data Cleaning",
        "Data Analysis", "MySQL", "Microsoft Excel", "DAX"
    ],

    "Machine Learning Engineer": [
        "Python", "SQL", "Machine Learning", "Deep Learning",
        "Scikit-learn", "TensorFlow", "PyTorch", "Pandas", "NumPy",
        "Statistics", "Data Structures", "Algorithms", "Git", "Docker",
        "MLOps", "AWS", "Azure"
    ],

    "Software Engineer": [
        "Python", "Java", "C", "C++", "JavaScript", "Data Structures",
        "Algorithms", "OOP", "Git", "GitHub", "SQL", "MySQL",
        "Software Development", "Testing", "Debugging", "REST API"
    ],

    "Web Developer": [
        "HTML", "CSS", "JavaScript", "PHP", "Python", "React", "Node.js",
        "MySQL", "MongoDB", "Git", "GitHub", "REST API", "Bootstrap",
        "Responsive Design"
    ],

    "Backend Developer": [
        "Python", "Java", "PHP", "Node.js", "SQL", "MySQL", "MongoDB",
        "REST API", "Django", "Flask", "Git", "Docker", "Linux",
        "Database Management"
    ],

    "Frontend Developer": [
        "HTML", "CSS", "JavaScript", "React", "Bootstrap", "TypeScript",
        "Git", "GitHub", "Responsive Design", "UI/UX", "Figma", "REST API"
    ],

    "DevOps Engineer": [
        "Linux", "Git", "GitHub", "Docker", "Kubernetes", "AWS", "Azure",
        "CI/CD", "Jenkins", "Python", "Bash", "Terraform",
        "Cloud Computing", "Networking"
    ],

    "Cloud Engineer": [
        "AWS", "Microsoft Azure", "Google Cloud", "Cloud Computing",
        "Linux", "Networking", "Docker", "Kubernetes", "Python",
        "Terraform", "Security", "Virtualization"
    ],

    "Cybersecurity Analyst": [
        "Cybersecurity", "Network Security", "Linux", "Python",
        "Ethical Hacking", "Cryptography", "Firewalls", "SIEM",
        "Penetration Testing", "Networking", "Risk Management",
        "Incident Response"
    ],

    "Database Administrator": [
        "SQL", "MySQL", "Oracle", "MongoDB", "Database Management",
        "Database Security", "Backup and Recovery", "Python", "Linux",
        "Data Modeling", "PL/SQL"
    ],

    "Business Intelligence Analyst": [
        "SQL", "Power BI", "Tableau", "Excel", "DAX", "Data Analysis",
        "Data Visualization", "Statistics", "MySQL", "Data Cleaning",
        "Business Intelligence"
    ]
}


# =========================================================
# SESSION STATE
# =========================================================

if "recommendation_result" not in st.session_state:
    st.session_state.recommendation_result = None

if "last_career" not in st.session_state:
    st.session_state.last_career = None

if "last_skills" not in st.session_state:
    st.session_state.last_skills = []


# =========================================================
# HELPERS
# =========================================================

def safe(value):
    return html.escape(str(value))


def render_html(content):
    """
    Streamlit's st.html() is used instead of st.markdown()
    so custom HTML is rendered as HTML rather than displayed
    as raw text.
    """
    st.html(dedent(content))


def card(title, value, number):
    return f"""
    <div class="summary-card">
        <div class="summary-number">{safe(number)}</div>
        <div class="summary-title">{safe(title)}</div>
        <div class="summary-value">{safe(value)}</div>
    </div>
    """


def skill_card(skill, symbol=""):
    return f"""
    <div class="skill-card">
        <span class="skill-icon">{safe(symbol)}</span>
        <span class="skill-text">{safe(skill)}</span>
    </div>
    """


def info_card(title, text):
    return f"""
    <div class="info-card">
        <div class="info-title">
            <span class="info-mark">i</span>
            {safe(title)}
        </div>

        <div class="info-text">
            {safe(text)}
        </div>
    </div>
    """


def role_card(role_name, score):
    return f"""
    <div class="role-card">

        <div class="role-top">

            <div class="role-name">
                <span class="role-symbol">R</span>
                {safe(role_name)}
            </div>

            <div class="score-badge">
                {score:.2f}%
            </div>

        </div>

        <div class="role-label">
            Skill profile match
        </div>

    </div>
    """


def certification_card(number, certification):
    return f"""
    <div class="cert-card">

        <div class="cert-number">
            {safe(number)}
        </div>

        <div class="cert-content">

            <div class="cert-title">
                <span class="cert-check">✓</span>
                {safe(certification)}
            </div>

            <div class="cert-subtitle">
                Relevant to your selected career path
            </div>

        </div>

    </div>
    """


# =========================================================
# CUSTOM CSS
# =========================================================

st.html(
    """
    <style>

    /* =====================================================
       COLOR SYSTEM
       ===================================================== */

    :root {
        --navy: #172A3A;
        --deep-navy: #102333;

        --teal: #2A9D8F;
        --dark-teal: #217A70;

        --orange: #D9824B;
        --dark-orange: #A85D2D;

        --cream: #F7F3EA;
        --white: #FFFFFF;

        --text: #304452;
        --muted: #667580;

        --border: #DDE5E3;

        --soft-teal: #EAF6F4;
        --soft-orange: #FBEEE5;
    }


    /* =====================================================
       MAIN APP
       ===================================================== */

    .stApp {
        background: var(--cream);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1,
    h2,
    h3 {
        color: var(--navy) !important;
    }


    /* =====================================================
       HERO
       ===================================================== */

    .hero {
        background:
            radial-gradient(
                circle at 90% 15%,
                rgba(217,130,75,.16),
                transparent 28%
            ),
            linear-gradient(
                135deg,
                #EAF6F4 0%,
                #FFFFFF 65%,
                #FBEEE5 100%
            );

        border: 1px solid #D6E8E5;
        border-radius: 24px;

        padding: 42px 38px;
        margin-bottom: 30px;

        text-align: center;

        box-shadow:
            0 8px 30px rgba(23,42,58,.06);
    }


    .hero-kicker {
        display: inline-block;

        background: var(--navy);
        color: white;

        padding: 7px 15px;

        border-radius: 999px;

        font-size: 11px;
        font-weight: 800;

        letter-spacing: 1px;

        margin-bottom: 15px;
    }


    .hero-title {
        font-size: 43px;
        line-height: 1.15;

        font-weight: 850;

        color: var(--navy);

        margin-bottom: 10px;
    }


    .hero-subtitle {
        font-size: 18px;

        font-weight: 650;

        color: var(--dark-teal);

        margin-bottom: 10px;
    }


    .hero-description {
        max-width: 760px;

        margin: auto;

        color: var(--muted);

        font-size: 15px;

        line-height: 1.7;
    }


    /* =====================================================
       SECTION HEADINGS
       ===================================================== */

    .section-heading {
        font-size: 25px;

        font-weight: 820;

        color: var(--navy);

        margin: 24px 0 5px 0;
    }


    .section-subheading {
        color: var(--muted);

        font-size: 14px;

        margin-bottom: 18px;
    }


    /* =====================================================
       STEP HEADERS
       ===================================================== */

    .step-header {
        display: flex;

        align-items: center;

        gap: 14px;

        margin: 22px 0 10px 0;
    }


    .step-number {
        min-width: 36px;
        height: 36px;

        border-radius: 50%;

        background: var(--teal);

        color: white;

        display: flex;

        align-items: center;
        justify-content: center;

        font-weight: 850;
        font-size: 13px;

        box-shadow:
            0 4px 10px rgba(42,157,143,.22);
    }


    .step-title {
        font-size: 18px;

        font-weight: 750;

        color: var(--navy);
    }


    .step-description {
        color: var(--muted);

        font-size: 13px;

        margin: -3px 0 12px 50px;
    }


    /* =====================================================
       SELECT / MULTISELECT
       ===================================================== */

    div[data-baseweb="select"] > div {
        background: white !important;

        border: 1px solid var(--border) !important;

        border-radius: 13px !important;

        min-height: 48px;
    }


    div[data-baseweb="select"] > div:hover {
        border-color: var(--teal) !important;
    }


    div[data-baseweb="select"] input {
        color: var(--navy) !important;
    }


    span[data-baseweb="tag"] {
        background: var(--soft-teal) !important;

        color: var(--dark-teal) !important;

        border: 1px solid #C8E6E1 !important;

        border-radius: 999px !important;
    }


    span[data-baseweb="tag"] svg {
        color: var(--dark-teal) !important;
    }


    /* =====================================================
       BUTTONS
       ===================================================== */

    div[data-testid="stButton"] > button {
        border-radius: 12px !important;

        min-height: 48px;

        font-weight: 750 !important;

        transition: all .2s ease;
    }


    div[data-testid="stButton"] > button[kind="primary"] {
        background: var(--teal) !important;

        border-color: var(--teal) !important;

        color: white !important;
    }


    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: var(--dark-teal) !important;

        border-color: var(--dark-teal) !important;

        transform: translateY(-1px);
    }


    /* =====================================================
       SUMMARY CARDS
       ===================================================== */

    .summary-card {
        position: relative;

        overflow: hidden;

        background: var(--white);

        border: 1px solid var(--border);

        border-radius: 18px;

        padding: 20px;

        min-height: 145px;

        box-shadow:
            0 4px 14px rgba(23,42,58,.05);
    }


    .summary-card::after {
        content: "";

        position: absolute;

        width: 70px;
        height: 70px;

        right: -22px;
        bottom: -22px;

        border-radius: 50%;

        background: var(--soft-orange);
    }


    .summary-number {
        display: inline-flex;

        align-items: center;
        justify-content: center;

        width: 34px;
        height: 34px;

        border-radius: 10px;

        background: var(--soft-teal);

        color: var(--teal);

        font-size: 11px;

        font-weight: 850;

        margin-bottom: 12px;
    }


    .summary-title {
        font-size: 12px;

        color: var(--muted);

        font-weight: 650;

        margin-bottom: 6px;
    }


    .summary-value {
        font-size: 21px;

        color: var(--navy);

        font-weight: 800;

        line-height: 1.3;
    }


    /* =====================================================
       SKILL CARDS
       ===================================================== */

    .skill-card {
        display: flex;

        align-items: center;

        gap: 11px;

        background: var(--white);

        border: 1px solid var(--border);

        border-left: 4px solid var(--teal);

        border-radius: 13px;

        padding: 13px 15px;

        margin-bottom: 9px;

        min-height: 48px;

        box-shadow:
            0 2px 8px rgba(23,42,58,.035);
    }


    .skill-icon {
        color: var(--teal);

        font-weight: 900;

        min-width: 17px;

        text-align: center;
    }


    .skill-text {
        color: var(--navy);

        font-weight: 650;

        font-size: 14px;
    }


    /* =====================================================
       INFO CARD
       ===================================================== */

    .info-card {
        background: white;

        border: 1px solid var(--border);

        border-radius: 16px;

        padding: 18px;

        margin-bottom: 12px;
    }


    .info-title {
        color: var(--navy);

        font-size: 16px;

        font-weight: 750;

        margin-bottom: 7px;
    }


    .info-mark {
        display: inline-flex;

        align-items: center;
        justify-content: center;

        width: 25px;
        height: 25px;

        border-radius: 8px;

        background: var(--soft-orange);

        color: var(--orange);

        margin-right: 8px;

        font-size: 12px;

        font-weight: 850;
    }


    .info-text {
        color: var(--muted);

        font-size: 13px;

        line-height: 1.5;
    }


    /* =====================================================
       CERTIFICATION CARDS
       ===================================================== */

    .cert-card {
        display: flex;

        align-items: center;

        gap: 15px;

        background: white;

        border: 1px solid var(--border);

        border-radius: 16px;

        padding: 16px 18px;

        margin-bottom: 10px;

        box-shadow:
            0 3px 10px rgba(23,42,58,.035);
    }


    .cert-number {
        width: 36px;
        height: 36px;

        min-width: 36px;

        border-radius: 11px;

        background: var(--soft-orange);

        color: var(--orange);

        display: flex;

        align-items: center;
        justify-content: center;

        font-weight: 850;
    }


    .cert-title {
        color: var(--navy);

        font-weight: 750;

        font-size: 14px;
    }


    .cert-check {
        display: inline-flex;

        align-items: center;
        justify-content: center;

        width: 20px;
        height: 20px;

        border-radius: 50%;

        background: var(--orange);

        color: white;

        font-size: 11px;

        margin-right: 8px;
    }


    .cert-subtitle {
        color: #87959C;

        font-size: 12px;

        margin-top: 3px;
    }


    /* =====================================================
       JOB ROLE CARDS
       ===================================================== */

    .role-card {
        background: white;

        border: 1px solid var(--border);

        border-radius: 16px;

        padding: 17px 18px 12px 18px;

        margin-bottom: 7px;

        box-shadow:
            0 3px 10px rgba(23,42,58,.035);
    }


    .role-top {
        display: flex;

        align-items: center;

        justify-content: space-between;

        gap: 15px;
    }


    .role-name {
        color: var(--navy);

        font-size: 15px;

        font-weight: 750;
    }


    .role-symbol {
        display: inline-flex;

        align-items: center;
        justify-content: center;

        width: 25px;
        height: 25px;

        border-radius: 8px;

        background: var(--soft-teal);

        color: var(--teal);

        margin-right: 7px;

        font-weight: 900;

        font-size: 10px;
    }


    .score-badge {
        background: var(--soft-orange);

        color: var(--dark-orange);

        border: 1px solid #F0D3C0;

        border-radius: 999px;

        padding: 5px 10px;

        font-size: 12px;

        font-weight: 800;

        white-space: nowrap;
    }


    .role-label {
        color: #94A0A5;

        font-size: 12px;

        margin-top: 6px;
    }


    /* Progress bar */

    div[data-testid="stProgress"] > div > div > div {
        background: var(--teal) !important;
    }


    /* =====================================================
       RESULT BANNER
       ===================================================== */

    .result-banner {
        background:
            radial-gradient(
                circle at 92% 20%,
                rgba(217,130,75,.25),
                transparent 24%
            ),
            linear-gradient(
                135deg,
                var(--deep-navy),
                var(--navy)
            );

        color: white;

        border-radius: 20px;

        padding: 24px 26px;

        margin: 28px 0 20px 0;

        box-shadow:
            0 8px 24px rgba(16,35,51,.14);
    }


    .result-banner-title {
        font-size: 22px;

        font-weight: 800;
    }


    .result-banner-text {
        color: #C8D6DC;

        font-size: 13px;

        margin-top: 5px;
    }


    /* =====================================================
       TABS
       ===================================================== */

    button[data-baseweb="tab"] {
        color: var(--muted) !important;

        font-weight: 700 !important;
    }


    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--teal) !important;
    }


    div[data-baseweb="tab-highlight"] {
        background: var(--teal) !important;
    }


    /* =====================================================
       SIDEBAR
       ===================================================== */

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                var(--deep-navy) 0%,
                var(--navy) 100%
            );

        border-right: none;
    }


    [data-testid="stSidebar"] > div:first-child {
        padding: 1.5rem 1rem;
    }


    .sidebar-brand {
        display: flex;

        align-items: center;

        gap: 11px;

        padding: 8px 6px 18px 6px;
    }


    .sidebar-logo {
        width: 42px;
        height: 42px;

        border-radius: 13px;

        background: var(--teal);

        display: flex;

        align-items: center;
        justify-content: center;

        color: white;

        font-size: 14px;

        font-weight: 900;

        box-shadow:
            0 5px 14px rgba(42,157,143,.25);
    }


    .sidebar-logo::before {
        content: "S";
    }


    .sidebar-brand-name {
        font-size: 19px;

        font-weight: 800;

        color: white;
    }


    .sidebar-brand-sub {
        color: #B8C7CE;

        font-size: 11px;

        margin-top: 2px;
    }


    .sidebar-intro {
        background: rgba(42,157,143,.13);

        border: 1px solid rgba(42,157,143,.25);

        border-radius: 16px;

        padding: 16px;

        margin: 4px 0 22px 0;
    }


    .sidebar-intro-title {
        color: white;

        font-size: 15px;

        font-weight: 750;

        margin-bottom: 6px;
    }


    .sidebar-intro-text {
        color: #C8D4D8;

        font-size: 12px;

        line-height: 1.55;
    }


    .sidebar-menu-title {
        color: #91A9B3;

        font-size: 10px;

        font-weight: 800;

        letter-spacing: 1.3px;

        margin: 0 6px 10px 6px;
    }


    .sidebar-item {
        display: flex;

        align-items: center;

        gap: 11px;

        padding: 12px 10px;

        border-radius: 13px;

        margin-bottom: 7px;
    }


    .sidebar-item.active {
        background: rgba(42,157,143,.18);

        border: 1px solid rgba(42,157,143,.18);
    }


    .sidebar-item-icon {
        width: 34px;
        height: 34px;

        min-width: 34px;

        border-radius: 10px;

        background: rgba(255,255,255,.08);

        display: flex;

        align-items: center;
        justify-content: center;

        color: white;

        font-size: 9px;

        font-weight: 850;
    }


    .sidebar-item-01::before {
        content: "01";
    }


    .sidebar-item-02::before {
        content: "02";
    }


    .sidebar-item-03::before {
        content: "03";
    }


    .sidebar-item-04::before {
        content: "04";
    }


    .sidebar-item b {
        display: block;

        color: white;

        font-size: 13px;
    }


    .sidebar-item small {
        display: block;

        color: #AEBEC3;

        font-size: 10px;

        margin-top: 2px;
    }


    .sidebar-divider {
        height: 1px;

        background: rgba(255,255,255,.12);

        margin: 20px 5px;
    }


    .sidebar-tip {
        display: flex;

        gap: 10px;

        background: rgba(217,130,75,.11);

        border: 1px solid rgba(217,130,75,.16);

        border-radius: 14px;

        padding: 13px;
    }


    .sidebar-tip-icon {
        color: var(--orange);

        font-size: 16px;

        font-weight: 800;
    }


    .sidebar-tip b {
        font-size: 12px;

        color: white;
    }


    .sidebar-tip p {
        color: #B8C7CE;

        font-size: 10px;

        line-height: 1.5;

        margin: 4px 0 0 0;
    }


    [data-testid="stSidebar"] button {
        background: var(--teal) !important;

        color: white !important;

        border: 1px solid var(--teal) !important;
    }


    [data-testid="stSidebar"] button:hover {
        background: var(--dark-teal) !important;

        border-color: var(--dark-teal) !important;
    }


    /* =====================================================
       ALERTS
       ===================================================== */

    [data-testid="stAlert"] {
        border-radius: 13px !important;
    }


    /* =====================================================
       FOOTER
       ===================================================== */

    .footer {
        text-align: center;

        color: #7C8B91;

        font-size: 12px;

        padding: 35px 0 10px 0;
    }


    .footer-accent {
        color: var(--teal);

        font-weight: 800;
    }


    /* =====================================================
       MOBILE
       ===================================================== */

    @media (max-width: 768px) {

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .hero {
            padding: 28px 18px;
        }

        .hero-title {
            font-size: 31px;
        }

        .hero-subtitle {
            font-size: 16px;
        }

        .summary-card {
            margin-bottom: 12px;
        }
    }

    </style>
    """
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    render_html(
        """
        <div class="sidebar-brand">

            <div class="sidebar-logo"></div>

            <div>
                <div class="sidebar-brand-name">
                    Smart SkillPath
                </div>

                <div class="sidebar-brand-sub">
                    Career Assistant
                </div>
            </div>

        </div>


        <div class="sidebar-intro">

            <div class="sidebar-intro-title">
                Find your next step
            </div>

            <div class="sidebar-intro-text">
                Discover the skills, certifications and roles
                connected to your career goal.
            </div>

        </div>


        <div class="sidebar-menu-title">
            YOUR JOURNEY
        </div>


        <div class="sidebar-item active">

            <span class="sidebar-item-icon sidebar-item-01"></span>

            <div>
                <b>Career Goal</b>
                <small>Choose your target role</small>
            </div>

        </div>


        <div class="sidebar-item">

            <span class="sidebar-item-icon sidebar-item-02"></span>

            <div>
                <b>Your Skills</b>
                <small>Tell us what you know</small>
            </div>

        </div>


        <div class="sidebar-item">

            <span class="sidebar-item-icon sidebar-item-03"></span>

            <div>
                <b>SkillPath</b>
                <small>Get your recommendations</small>
            </div>

        </div>


        <div class="sidebar-item">

            <span class="sidebar-item-icon sidebar-item-04"></span>

            <div>
                <b>Career Options</b>
                <small>Explore roles & certifications</small>
            </div>

        </div>


        <div class="sidebar-divider"></div>


        <div class="sidebar-tip">

            <div class="sidebar-tip-icon">
                •
            </div>

            <div>
                <b>Quick tip</b>

                <p>
                    Select only the skills you are comfortable
                    with for more meaningful recommendations.
                </p>
            </div>

        </div>
        """
    )


    if st.session_state.recommendation_result is not None:

        st.markdown("")

        if st.button(
            "Start a New Path",
            use_container_width=True
        ):

            st.session_state.recommendation_result = None
            st.session_state.last_career = None
            st.session_state.last_skills = []

            st.rerun()


# =========================================================
# HERO
# =========================================================

render_html(
    """
    <div class="hero">

        <div class="hero-kicker">
            ML CAREER RECOMMENDATION SYSTEM
        </div>

        <div class="hero-title">
            Smart SkillPath
        </div>

        <div class="hero-subtitle">
            Build a clearer path toward your IT career.
        </div>

        <div class="hero-description">
            Select your target career and the skills you already have.
            Smart SkillPath will identify relevant skills,
            certifications and job roles using your recommendation model.
        </div>

    </div>
    """
)


# =========================================================
# INPUT AREA
# =========================================================

render_html(
    """
    <div class="section-heading">
        Build Your SkillPath
    </div>

    <div class="section-subheading">
        Complete the two simple steps below.
        You can change your choices before generating your results.
    </div>
    """
)


# =========================================================
# STEP 1
# =========================================================

render_html(
    """
    <div class="step-header">

        <div class="step-number">
            1
        </div>

        <div class="step-title">
            Choose your career goal
        </div>

    </div>

    <div class="step-description">
        Which IT career are you preparing for?
    </div>
    """
)


career = st.selectbox(
    "Target career",
    list(CAREER_SKILLS.keys()),
    label_visibility="collapsed"
)


st.markdown("")


# =========================================================
# STEP 2
# =========================================================

render_html(
    """
    <div class="step-header">

        <div class="step-number">
            2
        </div>

        <div class="step-title">
            Tell us about your current skills
        </div>

    </div>

    <div class="step-description">
        Select the skills you already know. You can choose more than one.
    </div>
    """
)


selected_skills = st.multiselect(
    "Current skills",
    CAREER_SKILLS.get(career, []),
    placeholder="Select the skills you already know...",
    label_visibility="collapsed"
)


st.markdown("")


# =========================================================
# GENERATE BUTTON
# =========================================================

submitted = st.button(
    "Generate My Personalized SkillPath",
    use_container_width=True,
    type="primary"
)


# =========================================================
# FORM SUBMISSION
# =========================================================

if submitted:

    if not selected_skills:

        st.warning(
            "Please select at least one current skill before continuing."
        )

    else:

        with st.spinner(
            "Analyzing your skills and building your personalized path..."
        ):

            try:

                current_skills = ", ".join(selected_skills)

                result = recommend_skills(
                    current_skills,
                    career
                )

                st.session_state.recommendation_result = result
                st.session_state.last_career = career
                st.session_state.last_skills = selected_skills

            except Exception:

                st.error(
                    "We couldn't generate your SkillPath right now. "
                    "Please try again with a different skill selection."
                )


# =========================================================
# RESULTS
# =========================================================

result = st.session_state.recommendation_result


if result is not None:

    career = st.session_state.last_career
    selected_skills = st.session_state.last_skills


    # =====================================================
    # GET MODEL RESULTS
    # =====================================================

    skill_gap = list(
        dict.fromkeys(
            result.get(
                "skill_gap",
                []
            )
        )
    )


    recommended_skills = list(
        dict.fromkeys(
            result.get(
                "recommended_skills",
                []
            )
        )
    )


    certifications = list(
        dict.fromkeys(
            result.get(
                "certifications",
                []
            )
        )
    )


    matching_roles = result.get(
        "matching_roles",
        []
    )


    # =====================================================
    # REMOVE ALREADY KNOWN SKILLS
    # =====================================================

    selected_lower = {
        str(skill).strip().lower()
        for skill in selected_skills
    }


    recommended_skills = [
        skill
        for skill in recommended_skills
        if str(skill).strip().lower()
        not in selected_lower
    ]


    skill_gap = [
        skill
        for skill in skill_gap
        if str(skill).strip().lower()
        not in selected_lower
    ]


    # =====================================================
    # RESULT BANNER
    # =====================================================

    render_html(
        f"""
        <div class="result-banner">

            <div class="result-banner-title">
                Your Personalized SkillPath
            </div>

            <div class="result-banner-text">
                Career goal: {safe(career)}
                &nbsp; • &nbsp;
                {len(selected_skills)} current skill(s) selected
            </div>

        </div>
        """
    )


    # =====================================================
    # OVERVIEW CARDS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.html(
            card(
                "Career Goal",
                career,
                "01"
            )
        )


    with c2:

        st.html(
            card(
                "Current Skills",
                str(len(selected_skills)),
                "02"
            )
        )


    with c3:

        st.html(
            card(
                "Skills to Focus On",
                str(len(skill_gap)),
                "03"
            )
        )


    with c4:

        st.html(
            card(
                "Certifications",
                str(len(certifications)),
                "04"
            )
        )


    # =====================================================
    # RESULT TABS
    # =====================================================

    st.markdown("")


    tab1, tab2, tab3 = st.tabs(
        [
            "Skills",
            "Certifications",
            "Job Roles"
        ]
    )


    # =====================================================
    # TAB 1 — SKILLS
    # =====================================================

    with tab1:

        render_html(
            """
            <div class="section-heading">
                Your Current Skills
            </div>

            <div class="section-subheading">
                These are the skills you told us you already have.
            </div>
            """
        )


        if selected_skills:

            cols = st.columns(3)

            for i, skill in enumerate(selected_skills):

                with cols[i % 3]:

                    st.html(
                        skill_card(
                            skill,
                            "✓"
                        )
                    )

        else:

            st.info(
                "No current skills selected."
            )


        st.markdown("---")


        # =================================================
        # SKILLS TO FOCUS ON
        # =================================================

        render_html(
            """
            <div class="section-heading">
                Skills to Focus On
            </div>

            <div class="section-subheading">
                These are the skills returned by the recommendation
                model as areas to focus on next.
            </div>
            """
        )


        if skill_gap:

            cols = st.columns(2)

            for i, skill in enumerate(skill_gap):

                with cols[i % 2]:

                    st.html(
                        skill_card(
                            skill,
                            "→"
                        )
                    )

        else:

            st.success(
                "No additional skill gap was returned by the model."
            )


        st.markdown("---")


        # =================================================
        # RECOMMENDED SKILLS
        # =================================================

        render_html(
            """
            <div class="section-heading">
                Recommended Skills
            </div>

            <div class="section-subheading">
                Prioritized skills from the ML recommendation model.
            </div>
            """
        )


        if recommended_skills:

            cols = st.columns(2)

            for i, skill in enumerate(recommended_skills):

                with cols[i % 2]:

                    st.html(
                        skill_card(
                            skill,
                            "+"
                        )
                    )

        else:

            st.info(
                "No additional skills were recommended."
            )


    # =====================================================
    # TAB 2 — CERTIFICATIONS
    # =====================================================

    with tab2:

        render_html(
            """
            <div class="section-heading">
                Recommended Certifications
            </div>

            <div class="section-subheading">
                Certifications associated with the relevant job profiles
                identified by the model.
            </div>
            """
        )


        if certifications:

            for i, certification in enumerate(
                certifications,
                start=1
            ):

                st.html(
                    certification_card(
                        i,
                        certification
                    )
                )

        else:

            st.info(
                "No certification recommendations were returned for this profile."
            )


        st.markdown("")


        st.html(
            info_card(
                "How to use these results",
                "Choose certifications that match the skills you want to develop next. "
                "The recommendations shown here come from the project's existing dataset and model."
            )
        )


    # =====================================================
    # TAB 3 — JOB ROLES
    # =====================================================

    with tab3:

        render_html(
            """
            <div class="section-heading">
                Matching Job Roles
            </div>

            <div class="section-subheading">
                The model compares your selected skills with relevant
                job-role skill profiles.
            </div>
            """
        )


        if matching_roles:

            for role in matching_roles:

                if isinstance(role, dict):

                    role_name = role.get(
                        "role",
                        role.get(
                            "job_title",
                            "Unknown Role"
                        )
                    )


                    raw_score = role.get(
                        "similarity",
                        role.get(
                            "score",
                            0
                        )
                    )


                    try:

                        score = float(raw_score)

                    except (
                        ValueError,
                        TypeError
                    ):

                        score = 0.0


                    score = min(
                        max(
                            score,
                            0.0
                        ),
                        100.0
                    )


                    st.html(
                        role_card(
                            role_name,
                            score
                        )
                    )


                    st.progress(
                        score / 100
                    )


                else:

                    st.html(
                        skill_card(
                            role,
                            "R"
                        )
                    )


        else:

            st.info(
                "No matching job roles were returned by the model."
            )


    # =====================================================
    # COMPLETION MESSAGE
    # =====================================================

    st.markdown("---")


    st.success(
        "Your SkillPath is ready. Review the results above and use them "
        "to plan your next learning steps."
    )


# =========================================================
# FOOTER
# =========================================================

render_html(
    """
    <div class="footer">

        <span class="footer-accent">
            Smart SkillPath
        </span>

        <br>

        ML-Based Career & Skill Recommendation System

    </div>
    """
)