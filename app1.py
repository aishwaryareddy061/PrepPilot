import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import calendar
from datetime import date, datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
import requests


# ============================================================
# PREPPILOT
# AI-Powered Personalized Competitive Exam Preparation Assistant
# ============================================================

st.set_page_config(
    page_title="PrepPilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #f6f8ff, #eef2ff, #f8fafc);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827, #1e293b);
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.hero {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    padding: 30px;
    border-radius: 22px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 10px 30px rgba(79,70,229,0.20);
}

.hero h1 {
    margin: 0;
    font-size: 38px;
}

.hero p {
    margin-top: 8px;
    font-size: 17px;
    opacity: 0.9;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    margin-bottom: 18px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 5px 20px rgba(0,0,0,0.06);
}

.metric-card {
    background: white;
    padding: 18px;
    border-radius: 16px;
    text-align: center;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}

.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #4f46e5;
}

.metric-label {
    color: #64748b;
    font-size: 14px;
}

.plan-card {
    background: white;
    padding: 20px;
    border-radius: 18px;
    margin: 12px 0;
    border-left: 5px solid #4f46e5;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}

.ai-card {
    background: linear-gradient(135deg, #eef2ff, #f5f3ff);
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #c7d2fe;
}

.weak {
    background: #fff7ed;
    padding: 18px;
    border-radius: 15px;
    border-left: 5px solid #f97316;
}

.strong {
    background: #f0fdf4;
    padding: 18px;
    border-radius: 15px;
    border-left: 5px solid #22c55e;
}

.footer {
    text-align: center;
    color: #64748b;
    padding: 30px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "preppilot.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY,
            name TEXT,
            exam TEXT,
            paper TEXT,
            preparation_level TEXT,
            study_hours REAL,
            target_score REAL,
            exam_date TEXT,
            strong_subjects TEXT,
            weak_subjects TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            exam TEXT,
            paper TEXT,
            subject TEXT,
            score REAL,
            total_marks REAL,
            accuracy REAL,
            attempted REAL
        )
    """)

    # Upgrade older PrepPilot databases without deleting existing data.
    existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(mock_history)").fetchall()]
    if "paper" not in existing_columns:
        cursor.execute("ALTER TABLE mock_history ADD COLUMN paper TEXT")

    conn.commit()
    conn.close()


initialize_database()


# ============================================================
# EXAM DATA
# ============================================================

exam_data = {

    "GATE": {

        "AE - Aerospace Engineering": [
            "General Aptitude",
            "Engineering Mathematics",
            "Flight Mechanics",
            "Aerodynamics",
            "Structures",
            "Propulsion"
        ],

        "AG - Agricultural Engineering": [
            "General Aptitude",
            "Engineering Mathematics",
            "Farm Machinery",
            "Soil and Water Engineering",
            "Agricultural Processing"
        ],

        "AR - Architecture & Planning": [
            "General Aptitude",
            "Architecture",
            "Planning",
            "Building Construction",
            "Environmental Design"
        ],

        "BT - Biotechnology": [
            "General Aptitude",
            "Engineering Mathematics",
            "Biochemistry",
            "Microbiology",
            "Genetics",
            "Cell Biology",
            "Bioprocess Engineering"
        ],

        "CE - Civil Engineering": [
            "General Aptitude",
            "Engineering Mathematics",
            "Structural Engineering",
            "Geotechnical Engineering",
            "Water Resources Engineering",
            "Environmental Engineering",
            "Transportation Engineering"
        ],

        "CH - Chemical Engineering": [
            "General Aptitude",
            "Engineering Mathematics",
            "Chemical Engineering Thermodynamics",
            "Fluid Mechanics",
            "Heat Transfer",
            "Mass Transfer",
            "Reaction Engineering"
        ],

        "CS - Computer Science & IT": [
            "General Aptitude",
            "Engineering Mathematics",
            "Digital Logic",
            "Computer Organization",
            "Programming and Data Structures",
            "Algorithms",
            "Theory of Computation",
            "Compiler Design",
            "Operating Systems",
            "Databases",
            "Computer Networks"
        ],

        "CY - Chemistry": [
            "General Aptitude",
            "Physical Chemistry",
            "Organic Chemistry",
            "Inorganic Chemistry"
        ],

        "DA - Data Science & Artificial Intelligence": [
            "General Aptitude",
            "Probability and Statistics",
            "Linear Algebra",
            "Calculus and Optimization",
            "Programming",
            "Data Structures and Algorithms",
            "Database Management",
            "Machine Learning",
            "Artificial Intelligence"
        ],

        "EC - Electronics & Communication Engineering": [
            "General Aptitude",
            "Engineering Mathematics",
            "Networks",
            "Signals and Systems",
            "Electronic Devices",
            "Analog Circuits",
            "Digital Circuits",
            "Communication Systems",
            "Electromagnetics"
        ],

        "EE - Electrical Engineering": [
            "General Aptitude",
            "Engineering Mathematics",
            "Electric Circuits",
            "Electromagnetic Fields",
            "Signals and Systems",
            "Electrical Machines",
            "Power Systems",
            "Control Systems",
            "Power Electronics"
        ],

        "IN - Instrumentation Engineering": [
            "General Aptitude",
            "Engineering Mathematics",
            "Electrical Circuits",
            "Signals and Systems",
            "Control Systems",
            "Sensors",
            "Instrumentation"
        ],

        "MA - Mathematics": [
            "General Aptitude",
            "Linear Algebra",
            "Calculus",
            "Real Analysis",
            "Complex Analysis",
            "Differential Equations",
            "Numerical Analysis"
        ],

        "ME - Mechanical Engineering": [
            "General Aptitude",
            "Engineering Mathematics",
            "Engineering Mechanics",
            "Strength of Materials",
            "Theory of Machines",
            "Thermodynamics",
            "Fluid Mechanics",
            "Heat Transfer",
            "Manufacturing Engineering"
        ],

        "PH - Physics": [
            "General Aptitude",
            "Mathematical Physics",
            "Classical Mechanics",
            "Electromagnetism",
            "Quantum Mechanics",
            "Thermodynamics",
            "Solid State Physics"
        ],

        "ST - Statistics": [
            "General Aptitude",
            "Probability",
            "Statistical Inference",
            "Regression",
            "Multivariate Analysis",
            "Sampling Theory"
        ]
    },

    "JEE Main": {

        "Paper 1 - B.E. / B.Tech": [
            "Physics",
            "Chemistry",
            "Mathematics"
        ],

        "Paper 2A - B.Arch": [
            "Mathematics",
            "Aptitude Test",
            "Drawing Test"
        ],

        "Paper 2B - B.Planning": [
            "Mathematics",
            "Aptitude Test",
            "Planning Based Questions"
        ]
    },

    "NEET UG": {

        "NEET UG": [
            "Physics",
            "Chemistry",
            "Botany",
            "Zoology"
        ]
    },

    "UPSC Civil Services": {

        "Prelims - General Studies": [
            "History",
            "Geography",
            "Indian Polity",
            "Economy",
            "Environment",
            "Science and Technology",
            "Current Affairs"
        ],

        "Prelims - CSAT": [
            "Reading Comprehension",
            "Logical Reasoning",
            "Analytical Ability",
            "Basic Numeracy",
            "Data Interpretation"
        ],

        "Mains - General Studies": [
            "Indian Heritage and Culture",
            "History",
            "Geography",
            "Governance",
            "Constitution",
            "Social Issues",
            "Economy",
            "Environment",
            "Science and Technology",
            "International Relations",
            "Ethics"
        ]
    },

    "SSC CGL": {

        "Tier 1": [
            "General Intelligence and Reasoning",
            "General Awareness",
            "Quantitative Aptitude",
            "English Comprehension"
        ],

        "Tier 2 - Paper 1": [
            "Mathematical Abilities",
            "Reasoning and General Intelligence",
            "English Language",
            "General Awareness",
            "Computer Knowledge"
        ],

        "Tier 2 - Paper 2 Statistics": [
            "Statistics"
        ]
    },

    "CAT": {

        "CAT": [
            "Verbal Ability and Reading Comprehension",
            "Data Interpretation",
            "Logical Reasoning",
            "Quantitative Aptitude"
        ]
    },

    "Banking Exams": {

        "IBPS PO": [
            "English Language",
            "Quantitative Aptitude",
            "Reasoning Ability",
            "General Awareness",
            "Computer Aptitude"
        ],

        "SBI PO": [
            "English Language",
            "Quantitative Aptitude",
            "Reasoning Ability",
            "General Awareness",
            "Computer Aptitude"
        ],

        "IBPS Clerk": [
            "English Language",
            "Numerical Ability",
            "Reasoning Ability",
            "General Awareness"
        ],

        "SBI Clerk": [
            "English Language",
            "Numerical Ability",
            "Reasoning Ability",
            "General Awareness"
        ]
    }
}


# ============================================================
# DATABASE PROFILE FUNCTIONS
# ============================================================

def save_profile(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM profile")

    cursor.execute("""
        INSERT INTO profile (
            id,
            name,
            exam,
            paper,
            preparation_level,
            study_hours,
            target_score,
            exam_date,
            strong_subjects,
            weak_subjects
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        1,
        data["name"],
        data["exam"],
        data["paper"],
        data["preparation_level"],
        data["study_hours"],
        data["target_score"],
        data["exam_date"],
        ", ".join(data["strong_subjects"]),
        ", ".join(data["weak_subjects"])
    ))

    conn.commit()
    conn.close()


def load_profile():

    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM profile WHERE id = 1",
        conn
    )

    conn.close()

    if df.empty:
        return None

    return df.iloc[0].to_dict()


# ============================================================
# MOCK FUNCTIONS
# ============================================================

def save_mock(
    exam,
    paper,
    subject,
    score,
    total_marks,
    accuracy,
    attempted
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO mock_history
        (date, exam, paper, subject, score, total_marks, accuracy, attempted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        exam,
        paper,
        subject,
        score,
        total_marks,
        accuracy,
        attempted
    ))

    conn.commit()
    conn.close()


def load_mock_history(profile=None):
    """Load only mock results belonging to the active exam + paper."""
    if profile is None:
        profile = load_profile()

    if not profile:
        return pd.DataFrame()

    conn = get_connection()
    df = pd.read_sql_query(
        """SELECT * FROM mock_history
           WHERE exam = ? AND paper = ?
           ORDER BY id DESC""",
        conn,
        params=(profile["exam"], profile["paper"])
    )
    conn.close()
    return df


# ============================================================
# DATE FUNCTIONS
# ============================================================

def get_days_remaining(target_date):

    today = date.today()

    difference = (target_date - today).days

    # IMPORTANT:
    # This returns exactly 0 when target date is today.
    # It never converts 0 into 1.
    return max(0, difference)


def choose_target_date(existing_date=None):

    today = date.today()

    # --------------------------------------------------------
    # Default date
    # --------------------------------------------------------

    if existing_date is not None:

        try:
            if isinstance(existing_date, str):
                default_date = datetime.strptime(
                    existing_date,
                    "%Y-%m-%d"
                ).date()

            else:
                default_date = existing_date

        except:
            default_date = today + timedelta(days=90)

    else:

        default_date = today + timedelta(days=90)

    if default_date < today:
        default_date = today

    # --------------------------------------------------------
    # YEARS
    # --------------------------------------------------------

    start_year = today.year
    end_year = today.year + 5

    years = list(
        range(
            start_year,
            end_year + 1
        )
    )

    default_year = default_date.year

    if default_year not in years:
        default_year = start_year

    year = st.selectbox(
        "📅 Target Year",
        years,
        index=years.index(default_year),
        key="target_year"
    )

    # --------------------------------------------------------
    # MONTHS
    # --------------------------------------------------------

    months = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December"
    }

    default_month = default_date.month

    month_number = st.selectbox(
        "📅 Target Month",
        list(months.keys()),
        index=default_month - 1,
        format_func=lambda x: months[x],
        key="target_month"
    )

    # --------------------------------------------------------
    # DAYS
    # --------------------------------------------------------

    max_day = calendar.monthrange(
        year,
        month_number
    )[1]

    # If selected year/month is before today,
    # automatically move to today's month.
    if (
        year == today.year
        and month_number < today.month
    ):

        st.warning(
            "⚠️ That month has already passed. "
            "Please select a future month."
        )

        valid_days = list(
            range(
                today.day,
                max_day + 1
            )
        )

    elif (
        year == today.year
        and month_number == today.month
    ):

        valid_days = list(
            range(
                today.day,
                max_day + 1
            )
        )

    else:

        valid_days = list(
            range(
                1,
                max_day + 1
            )
        )

    default_day = default_date.day

    if default_day not in valid_days:
        default_day = valid_days[0]

    day = st.selectbox(
        "📅 Target Day",
        valid_days,
        index=valid_days.index(default_day),
        key="target_day"
    )

    selected_date = date(
        year,
        month_number,
        day
    )

    return selected_date


# ============================================================
# ML MODEL
# ============================================================

def train_model():

    data = pd.DataFrame({

        "study_hours": [
            1, 2, 2, 3, 3, 4, 4, 5,
            5, 6, 6, 7, 7, 8, 8, 9,
            9, 10, 10, 11, 11, 12
        ],

        "mock_score": [
            25, 30, 35, 38, 42, 45, 48, 52,
            55, 58, 60, 63, 65, 68, 72, 75,
            78, 82, 85, 88, 92, 95
        ],

        "accuracy": [
            35, 40, 43, 45, 48, 50, 52, 55,
            58, 60, 62, 65, 67, 70, 73, 76,
            78, 82, 85, 88, 92, 95
        ],

        "attempt_rate": [
            35, 40, 45, 48, 50, 53, 55, 58,
            60, 62, 65, 68, 70, 73, 76, 78,
            80, 84, 87, 90, 94, 97
        ],

        "level": [
            "Needs Improvement",
            "Needs Improvement",
            "Needs Improvement",
            "Needs Improvement",
            "Needs Improvement",
            "Needs Improvement",
            "Needs Improvement",
            "Average",
            "Average",
            "Average",
            "Average",
            "Average",
            "Average",
            "Average",
            "Average",
            "Strong",
            "Strong",
            "Strong",
            "Strong",
            "Strong",
            "Strong",
            "Strong"
        ]
    })

    X = data[
        [
            "study_hours",
            "mock_score",
            "accuracy",
            "attempt_rate"
        ]
    ]

    y = data["level"]

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )

    model.fit(X, y)

    return model


model = train_model()


# ============================================================
# ML PREDICTION
# ============================================================

def get_prediction(
    study_hours,
    mock_score,
    accuracy,
    attempted
):

    features = pd.DataFrame([{
        "study_hours": study_hours,
        "mock_score": mock_score,
        "accuracy": accuracy,
        "attempt_rate": attempted
    }])

    prediction = model.predict(features)[0]

    probabilities = model.predict_proba(features)[0]

    confidence = max(probabilities) * 100

    return prediction, confidence


# ============================================================
# SUBJECT ANALYSIS
# ============================================================

def analyze_subjects(history):

    if history.empty:
        return [], []

    grouped = history.groupby(
        "subject"
    ).agg({
        "score": "mean",
        "accuracy": "mean"
    }).reset_index()

    weak = grouped[
        grouped["accuracy"] < 60
    ]["subject"].tolist()

    strong = grouped[
        grouped["accuracy"] >= 75
    ]["subject"].tolist()

    return weak, strong


# ============================================================
# PLAN GENERATOR
# ============================================================

def generate_plan(
    subjects,
    weak_subjects,
    study_hours,
    target_date
):

    days_remaining = get_days_remaining(
        target_date
    )

    # ========================================================
    # VERY IMPORTANT:
    # If 0 days remain, return ZERO DAYS.
    # ========================================================

    if days_remaining == 0:

        return [], 0

    # --------------------------------------------------------
    # Create EXACT number of remaining days.
    # --------------------------------------------------------

    plan = []

    normal_subjects = [
        subject
        for subject in subjects
        if subject not in weak_subjects
    ]

    if not normal_subjects:
        normal_subjects = subjects

    for i in range(days_remaining):

        current_date = date.today() + timedelta(
            days=i
        )

        # ----------------------------------------------------
        # Weak subject priority
        # ----------------------------------------------------

        if weak_subjects:

            weak_subject = weak_subjects[
                i % len(weak_subjects)
            ]

            if study_hours >= 6:

                normal_subject = normal_subjects[
                    i % len(normal_subjects)
                ]

                tasks = [
                    f"Deep study: {weak_subject}",
                    f"Practice questions: {weak_subject}",
                    f"Revision: {normal_subject}"
                ]

            elif study_hours >= 3:

                normal_subject = normal_subjects[
                    i % len(normal_subjects)
                ]

                tasks = [
                    f"Study: {weak_subject}",
                    f"Practice questions: {weak_subject}",
                    f"Quick revision: {normal_subject}"
                ]

            else:

                tasks = [
                    f"Study: {weak_subject}",
                    f"Practice questions: {weak_subject}",
                    "Quick revision"
                ]

        else:

            subject = subjects[
                i % len(subjects)
            ]

            tasks = [
                f"Study: {subject}",
                f"Practice questions: {subject}",
                "Revision and self-test"
            ]

        plan.append({
            "day": i + 1,
            "date": current_date.strftime(
                "%d %B %Y"
            ),
            "tasks": tasks
        })

    return plan, days_remaining


# ============================================================
# MISSED DAY RECOVERY
# ============================================================
def build_recovery_plan(subjects, weak_subjects, study_hours, target_date, missed_days, mode, available_today):
    """Create a catch-up plan without pushing all missed work into one day."""
    today = date.today()
    days_remaining = get_days_remaining(target_date)

    if days_remaining <= 0:
        return [], 0, 0.0

    missed_hours = missed_days * float(study_hours)

    # We never add more than 50% extra study time to a normal day.
    max_extra_per_day = float(study_hours) * 0.5

    if mode == "Light / Less-Time Recovery":
        # Only recover about half of the missed workload and protect today's workload.
        recover_hours = missed_hours * 0.5
        daily_extra_cap = min(max_extra_per_day, 1.0)
    else:
        recover_hours = missed_hours
        daily_extra_cap = max_extra_per_day

    future_days = max(0, days_remaining - 1)
    recovery_days = min(max(1, future_days), max(1, missed_days + 2))

    # Today may have less time because the student is busy. Use the
    # student's available hours today instead of pretending they have
    # their normal study time. The missed work is spread over future days.
    today_hours = min(float(available_today), float(study_hours))
    missed_recovery_after_today = max(0.0, recover_hours - max(0.0, today_hours - float(study_hours)))

    extra_per_day = 0.0
    if recovery_days > 0:
        extra_per_day = min(
            daily_extra_cap,
            missed_recovery_after_today / recovery_days
        )

    recoverable_hours = max(0.0, today_hours - float(study_hours)) + (extra_per_day * recovery_days)

    if not subjects:
        subjects = ["General Revision"]

    priority_subjects = []
    for subject in weak_subjects + subjects:
        if subject not in priority_subjects:
            priority_subjects.append(subject)

    plan = []

    # Add TODAY only when the student has some study time available.
    today_subject = priority_subjects[0]
    today_next_subject = priority_subjects[1 % len(priority_subjects)]
    plan.append({
        "day": 1,
        "date": today.strftime("%d %B %Y"),
        "normal_hours": float(study_hours),
        "extra_hours": 0.0,
        "total_hours": round(today_hours, 1),
        "tasks": [
            f"Recovery priority: {today_subject}",
            f"Short practice: {today_subject}",
            f"If time remains: {today_next_subject}"
        ]
    })

    for i in range(recovery_days):
        current_date = today + timedelta(days=i + 1)
        subject = priority_subjects[(i + 1) % len(priority_subjects)]
        next_subject = priority_subjects[(i + 2) % len(priority_subjects)]

        if mode == "Light / Less-Time Recovery":
            tasks = [
                f"Priority recovery: {subject}",
                f"Quick practice: {subject}",
                f"Maintain normal plan: {next_subject}"
            ]
        else:
            tasks = [
                f"Recover missed work: {subject}",
                f"Practice questions: {subject}",
                f"Continue normal plan: {next_subject}"
            ]

        plan.append({
            "day": i + 2,
            "date": current_date.strftime("%d %B %Y"),
            "normal_hours": float(study_hours),
            "extra_hours": round(extra_per_day, 1),
            "total_hours": round(float(study_hours) + extra_per_day, 1),
            "tasks": tasks
        })

    return plan, len(plan), recoverable_hours


# ============================================================
# LOCAL AI ASSISTANT — OLLAMA
# ============================================================

def ask_ollama(prompt, context):
    """Fast local AI response using Ollama."""
    system_prompt = f"""You are PrepPilot, a concise exam study assistant.
Use the student's context below. Do not invent scores, subjects, or exam rules.
Give practical answers in simple language. Prefer short bullet points.

STUDENT CONTEXT:
{context}

QUESTION:
{prompt}
"""

    payload = {
        "model": "llama3.2",
        "prompt": system_prompt,
        "stream": False,
        "keep_alive": "5m",
        "options": {
            "temperature": 0.2,
            "num_ctx": 2048,
            "num_predict": 220,
            "top_p": 0.9
        }
    }

    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=90
    )
    response.raise_for_status()
    data = response.json()
    answer = data.get("response", "I could not generate a response right now.").strip()
    return answer


def build_ai_context(profile, history):
    if not profile:
        return "No preparation profile has been created yet."

    target_date = datetime.strptime(profile["exam_date"], "%Y-%m-%d").date()
    days = get_days_remaining(target_date)
    weak = [x.strip() for x in str(profile.get("weak_subjects", "")).split(",") if x.strip()]
    strong = [x.strip() for x in str(profile.get("strong_subjects", "")).split(",") if x.strip()]

    lines = [
        f"Exam: {profile['exam']} | Paper: {profile['paper']}",
        f"Level: {profile['preparation_level']} | Daily hours: {float(profile['study_hours']):.1f}",
        f"Target: {float(profile['target_score']):.1f}% | Days remaining: {days}",
        f"Weak: {', '.join(weak) if weak else 'None'}",
        f"Strong: {', '.join(strong) if strong else 'None'}"
    ]

    if history is not None and not history.empty:
        lines.append("Recent mocks:")
        for _, row in history.head(3).iterrows():
            lines.append(f"- {row['subject']}: {row['score']}/{row['total_marks']}, accuracy {row['accuracy']:.0f}%")
    else:
        lines.append("Recent mocks: None")

    return "\n".join(lines)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("""
<h2 style="text-align:center;">🚀 PrepPilot</h2>
<p style="text-align:center;">Smart Exam Preparation</p>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📚 Exam & Profile",
        "🧠 Performance Analysis",
        "📅 Study Timetable",
        "📝 Mock Test",
        "🤖 ML Analysis",
        "📊 Progress",
        "🔄 Adaptive Plan",
        "⏰ Missed Day Recovery",
        "🤖 AI Study Assistant"
    ]
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "AI-powered personalized exam preparation"
)


# ============================================================
# HERO
# ============================================================

st.markdown("""
<div class="hero">

<h1>🚀 PrepPilot</h1>

<p>
Your AI-powered personalized competitive exam preparation assistant.
</p>

</div>
""", unsafe_allow_html=True)


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    profile = load_profile()

    history = load_mock_history()

    st.subheader("Welcome to PrepPilot 👋")

    if profile:

        target_date = datetime.strptime(
            profile["exam_date"],
            "%Y-%m-%d"
        ).date()

        days = get_days_remaining(
            target_date
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.markdown("""
            <div class="metric-card">

            <div class="metric-value">🎓</div>

            <div class="metric-label">
            Exam
            </div>

            </div>
            """, unsafe_allow_html=True)

            st.write(profile["exam"])

        with c2:

            st.markdown(
                f"""
                <div class="metric-card">

                <div class="metric-value">
                {days}
                </div>

                <div class="metric-label">
                Days Remaining
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:

            st.markdown(
                f"""
                <div class="metric-card">

                <div class="metric-value">
                {len(history)}
                </div>

                <div class="metric-label">
                Mock Tests
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        with c4:

            st.markdown(
                f"""
                <div class="metric-card">

                <div class="metric-value">
                {profile["study_hours"]}
                </div>

                <div class="metric-label">
                Study Hours/Day
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if days == 0:

            st.error(
                "⏰ Your target date is TODAY. "
                "There are no preparation days remaining."
            )

        else:

            st.success(
                f"📅 You have {days} preparation days remaining."
            )

        st.markdown(
            f"""
            <div class="ai-card">

            <h3>🤖 PrepPilot Status</h3>

            <p>
            Your profile is permanently saved.
            Mock-test performance is tracked automatically.
            Study plans use your actual remaining preparation time.
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.info(
            "👋 Welcome! Go to **Exam & Profile** "
            "to create your preparation profile."
        )


# ============================================================
# EXAM & PROFILE
# ============================================================

elif page == "📚 Exam & Profile":

    st.subheader("📚 Exam & Preparation Profile")

    existing = load_profile()

    if existing:

        default_name = existing["name"]
        default_exam = existing["exam"]
        default_paper = existing["paper"]
        default_level = existing["preparation_level"]
        default_hours = float(
            existing["study_hours"]
        )
        default_score = float(
            existing["target_score"]
        )
        existing_date = existing["exam_date"]

    else:

        default_name = ""
        default_exam = "GATE"
        default_paper = list(
            exam_data["GATE"].keys()
        )[0]

        default_level = "Beginner"
        default_hours = 4.0
        default_score = 70.0
        existing_date = None

    name = st.text_input(
        "Your Name",
        value=default_name,
        placeholder="Enter your name"
    )

    exam_options = list(
        exam_data.keys()
    )

    exam_index = (
        exam_options.index(default_exam)
        if default_exam in exam_options
        else 0
    )

    exam = st.selectbox(
        "Select Competitive Exam",
        exam_options,
        index=exam_index
    )

    papers = list(
        exam_data[exam].keys()
    )

    paper_index = (
        papers.index(default_paper)
        if default_paper in papers
        else 0
    )

    paper = st.selectbox(
        "Select Paper / Stage / Branch",
        papers,
        index=paper_index
    )

    subjects = exam_data[
        exam
    ][
        paper
    ]

    st.markdown(
        "### 📚 Subjects"
    )

    st.write(
        ", ".join(subjects)
    )

    preparation_level = st.selectbox(
        "Current Preparation Level",
        [
            "Beginner",
            "Intermediate",
            "Advanced"
        ],
        index=[
            "Beginner",
            "Intermediate",
            "Advanced"
        ].index(default_level)
    )

    study_hours = st.number_input(
        "Daily Study Hours",
        min_value=1.0,
        max_value=16.0,
        value=default_hours,
        step=0.5
    )

    target_score = st.number_input(
        "Target Score (%)",
        min_value=1.0,
        max_value=100.0,
        value=default_score,
        step=1.0
    )

    # ========================================================
    # NEW DATE SELECTOR
    # ========================================================

    st.markdown(
        "### 📅 Target Exam Date"
    )

    st.caption(
        "Choose any future year, month, and day."
    )

    exam_date = choose_target_date(
        existing_date
    )

    st.info(
        f"Selected target date: "
        f"**{exam_date.strftime('%d %B %Y')}**"
    )

    days_remaining = get_days_remaining(
        exam_date
    )

    if days_remaining == 0:

        st.error(
            "⏰ 0 days remaining — your target date is today."
        )

    else:

        st.success(
            f"📅 {days_remaining} days remaining."
        )

    # ========================================================
    # SUBJECT SELECTION
    # ========================================================

    st.markdown(
        "### 💪 Strong Subjects"
    )

    existing_strong = [x.strip() for x in str(existing.get("strong_subjects", "")).split(",") if x.strip()] if existing else []
    existing_weak = [x.strip() for x in str(existing.get("weak_subjects", "")).split(",") if x.strip()] if existing else []

    strong_subjects = st.multiselect(
        "Select subjects you are comfortable with",
        subjects,
        default=[x for x in existing_strong if x in subjects]
    )

    st.markdown(
        "### ⚠️ Weak Subjects"
    )

    weak_subjects = st.multiselect(
        "Select subjects that need more attention",
        subjects,
        default=[x for x in existing_weak if x in subjects]
    )

    if st.button(
        "💾 Save Profile",
        use_container_width=True
    ):

        if not name.strip():

            st.error(
                "Please enter your name."
            )

        elif not weak_subjects:

            st.warning(
                "Select at least one weak subject."
            )

        else:

            profile_data = {

                "name": name,

                "exam": exam,

                "paper": paper,

                "preparation_level":
                    preparation_level,

                "study_hours":
                    study_hours,

                "target_score":
                    target_score,

                "exam_date":
                    exam_date.strftime(
                        "%Y-%m-%d"
                    ),

                "strong_subjects":
                    strong_subjects,

                "weak_subjects":
                    weak_subjects
            }

            save_profile(
                profile_data
            )

            st.success(
                "✅ Profile saved successfully!"
            )

            st.rerun()


# ============================================================
# PERFORMANCE ANALYSIS
# ============================================================

elif page == "🧠 Performance Analysis":

    st.subheader("🧠 Performance Analysis")
    st.caption("A simple view of what you should focus on. No confusing hover graphs.")

    history = load_mock_history()

    if history.empty:
        st.info("Take a mock test first to see your performance.")
    else:
        weak, strong = analyze_subjects(history)

        grouped = history.groupby("subject").agg({
            "score": "mean",
            "accuracy": "mean"
        }).reset_index()

        grouped["status"] = grouped["accuracy"].apply(
            lambda x: "🔴 Weak" if x < 60 else ("🟡 Needs Practice" if x < 75 else "🟢 Strong")
        )
        grouped["action"] = grouped["accuracy"].apply(
            lambda x: "Focus first" if x < 60 else ("Practice more" if x < 75 else "Maintain")
        )

        st.markdown("### 📋 Subject Performance")
        st.dataframe(
            grouped[["subject", "accuracy", "status", "action"]].rename(columns={
                "subject": "Subject",
                "accuracy": "Accuracy (%)",
                "status": "Status",
                "action": "What to do"
            }).style.format({"Accuracy (%)": "{:.1f}%"}),
            use_container_width=True,
            hide_index=True
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🔴 Weak", len(weak))
        with c2:
            st.metric("🟡 Needs Practice", len(grouped[(grouped["accuracy"] >= 60) & (grouped["accuracy"] < 75)]))
        with c3:
            st.metric("🟢 Strong", len(strong))

        st.markdown("### 🎯 What this means")
        st.info(
            "🔴 Below 60% → give this subject more study time.\n\n"
            "🟡 60–74.9% → practice questions and revise mistakes.\n\n"
            "🟢 75% or above → maintain it with regular revision."
        )


# ============================================================
# STUDY TIMETABLE
# ============================================================

elif page == "📅 Study Timetable":

    st.subheader(
        "📅 Personalized Study Timetable"
    )

    profile = load_profile()

    if not profile:

        st.warning(
            "Please create your profile first."
        )

    else:

        target_date = datetime.strptime(
            profile["exam_date"],
            "%Y-%m-%d"
        ).date()

        subjects = exam_data[
            profile["exam"]
        ][
            profile["paper"]
        ]

        weak_subjects = [

            x.strip()

            for x in
            profile["weak_subjects"].split(",")

            if x.strip()
        ]

        plan, days_remaining = generate_plan(
            subjects,
            weak_subjects,
            float(profile["study_hours"]),
            target_date
        )

        # ====================================================
        # ZERO-DAY CASE
        # ====================================================

        if days_remaining == 0:

            st.error(
                "⏰ Your target date is TODAY."
            )

            st.warning(
                "There are **0 preparation days remaining**, "
                "so PrepPilot will not generate a study timetable."
            )

        else:

            st.success(
                f"📅 Your timetable contains exactly "
                f"**{days_remaining} preparation days**."
            )

            # ------------------------------------------------
            # Display full plan
            # ------------------------------------------------

            for item in plan:

                st.markdown(
                    f"""
                    <div class="plan-card">

                    <h3>
                    Day {item["day"]} — {item["date"]}
                    </h3>

                    <p>
                    ⏱️ Study time:
                    <b>{profile["study_hours"]} hours</b>
                    </p>

                    <ul>

                    <li>
                    {item["tasks"][0]}
                    </li>

                    <li>
                    {item["tasks"][1]}
                    </li>

                    <li>
                    {item["tasks"][2]}
                    </li>

                    </ul>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ============================================================
# MOCK TEST
# ============================================================

elif page == "📝 Mock Test":

    st.subheader(
        "📝 Mock Test Performance"
    )

    profile = load_profile()

    if not profile:

        st.warning(
            "Please create your profile first."
        )

    else:

        subjects = exam_data[
            profile["exam"]
        ][
            profile["paper"]
        ]

        subject = st.selectbox(
            "Select Subject",
            subjects
        )

        total_marks = st.number_input(
            "Total Marks",
            min_value=1.0,
            max_value=500.0,
            value=100.0,
            step=1.0
        )

        score = st.number_input(
            "Score Obtained",
            min_value=0.0,
            max_value=float(
                total_marks
            ),
            value=0.0,
            step=1.0
        )

        total_questions = st.number_input(
            "Total Questions",
            min_value=1,
            max_value=300,
            value=50,
            step=1
        )

        attempted = st.number_input(
            "Questions Attempted",
            min_value=0,
            max_value=int(
                total_questions
            ),
            value=min(
                40,
                int(total_questions)
            ),
            step=1
        )

        correct = st.number_input(
            "Correct Answers",
            min_value=0,
            max_value=int(
                attempted
            ),
            value=0,
            step=1
        )

        if attempted > 0:

            accuracy = (
                correct /
                attempted
            ) * 100

            attempt_rate = (
                attempted /
                total_questions
            ) * 100

        else:

            accuracy = 0

            attempt_rate = 0

        st.metric(
            "Current Accuracy",
            f"{accuracy:.1f}%"
        )

        if st.button(
            "💾 Save Mock Result",
            use_container_width=True
        ):

            save_mock(
                profile["exam"],
                profile["paper"],
                subject,
                score,
                total_marks,
                accuracy,
                attempt_rate
            )

            st.success(
                "✅ Mock result saved permanently!"
            )


# ============================================================
# ML ANALYSIS
# ============================================================

elif page == "🤖 ML Analysis":

    st.subheader(
        "🤖 Machine Learning Analysis"
    )

    history = load_mock_history()

    profile = load_profile()

    if not profile:

        st.warning(
            "Please create your profile first."
        )

    elif history.empty:

        st.info(
            "Take at least one mock test first."
        )

    else:

        average_score = (
            history["score"] /
            history["total_marks"] *
            100
        ).mean()

        average_accuracy = (
            history["accuracy"].mean()
        )

        average_attempt = (
            history["attempted"].mean()
        )

        prediction, confidence = get_prediction(
            float(profile["study_hours"]),
            average_score,
            average_accuracy,
            average_attempt
        )

        st.markdown(
            f"""
            <div class="ai-card">

            <h2>🤖 ML Prediction</h2>

            <h1>{prediction}</h1>

            <p>
            Model confidence:
            <b>{confidence:.1f}%</b>
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Average Score",
                f"{average_score:.1f}%"
            )

        with c2:

            st.metric(
                "Average Accuracy",
                f"{average_accuracy:.1f}%"
            )

        with c3:

            st.metric(
                "Average Attempt Rate",
                f"{average_attempt:.1f}%"
            )

        st.markdown(
            "### How PrepPilot's ML works"
        )

        st.write("""
PrepPilot uses a Random Forest classification model.

It considers:

• Daily study hours
• Mock-test score
• Accuracy
• Attempt rate

The model predicts:

• Needs Improvement
• Average
• Strong
        """)

        st.caption(
            "The initial Random Forest model uses sample training data. "
            "Your mock history is used for your performance analysis."
        )


# ============================================================
# PROGRESS
# ============================================================

elif page == "📊 Progress":

    st.subheader("📊 Your Progress")
    st.caption("Simple progress tracking — no hover graph needed.")

    history = load_mock_history()

    if history.empty:
        st.info("No mock-test history available.")
    else:
        history["percentage"] = (history["score"] / history["total_marks"]) * 100

        average = history["percentage"].mean()
        best = history["percentage"].max()
        latest = history.sort_values("id").iloc[-1]["percentage"]

        previous = None
        if len(history) > 1:
            previous = history.sort_values("id").iloc[-2]["percentage"]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Mocks", len(history))
        with c2:
            st.metric("Average Score", f"{average:.1f}%")
        with c3:
            st.metric("Best Score", f"{best:.1f}%")
        with c4:
            if previous is None:
                st.metric("Latest Score", f"{latest:.1f}%")
            else:
                change = latest - previous
                st.metric("Latest Score", f"{latest:.1f}%", f"{change:+.1f}%")

        st.markdown("### 📈 Easy-to-read progress")
        if previous is None:
            st.info(f"Your first recorded mock score is **{latest:.1f}%**. Take another mock to see whether you improve.")
        elif latest > previous:
            st.success(f"📈 Your latest score improved by **{latest - previous:.1f} percentage points** compared with your previous mock.")
        elif latest < previous:
            st.warning(f"📉 Your latest score dropped by **{previous - latest:.1f} percentage points**. Review the mistakes before your next mock.")
        else:
            st.info("➡️ Your latest score is the same as your previous mock. Focus on weak subjects to move it higher.")

        st.markdown("### 📋 Mock History")
        display_history = history[["date", "subject", "score", "total_marks", "accuracy", "percentage"]].copy()
        display_history.columns = ["Date", "Subject", "Score", "Total Marks", "Accuracy (%)", "Score (%)"]
        st.dataframe(
            display_history.style.format({
                "Accuracy (%)": "{:.1f}%",
                "Score (%)": "{:.1f}%"
            }),
            use_container_width=True,
            hide_index=True
        )

        csv = history.to_csv(index=False)
        st.download_button(
            "⬇️ Download Progress",
            csv,
            "preppilot_progress.csv",
            "text/csv"
        )


# ============================================================
# ADAPTIVE PLAN
# ============================================================

elif page == "🔄 Adaptive Plan":

    st.subheader(
        "🔄 Adaptive Study Plan"
    )

    profile = load_profile()

    history = load_mock_history()

    if not profile:

        st.warning(
            "Please create your profile first."
        )

    else:

        target_date = datetime.strptime(
            profile["exam_date"],
            "%Y-%m-%d"
        ).date()

        subjects = exam_data[
            profile["exam"]
        ][
            profile["paper"]
        ]

        profile_weak = [

            x.strip()

            for x in
            profile["weak_subjects"].split(",")

            if x.strip()
        ]

        detected_weak, detected_strong = (
            analyze_subjects(history)
        )

        weak_subjects = list(
            dict.fromkeys(
                profile_weak +
                detected_weak
            )
        )

        plan, days_remaining = generate_plan(
            subjects,
            weak_subjects,
            float(profile["study_hours"]),
            target_date
        )

        # ====================================================
        # ZERO-DAY CASE
        # ====================================================

        if days_remaining == 0:

            st.error(
                "⏰ Your target date is TODAY."
            )

            st.warning(
                "There are **0 preparation days remaining**. "
                "No adaptive timetable has been generated."
            )

        else:

            st.markdown(
                f"""
                <div class="ai-card">

                <h3>
                🤖 Adaptive Recommendation
                </h3>

                <p>
                PrepPilot is giving additional study
                attention to:
                </p>

                <b>
                {
                    ", ".join(weak_subjects)
                    if weak_subjects
                    else
                    "No major weak subjects detected"
                }
                </b>

                </div>
                """,
                unsafe_allow_html=True
            )

            st.success(
                f"📅 Adaptive plan contains "
                f"exactly {days_remaining} day(s)."
            )

            for item in plan:

                st.markdown(
                    f"""
                    <div class="plan-card">

                    <h3>
                    Day {item["day"]} —
                    {item["date"]}
                    </h3>

                    <p>
                    🎯 Priority:
                    Weak-subject focused
                    </p>

                    <ul>

                    <li>
                    {item["tasks"][0]}
                    </li>

                    <li>
                    {item["tasks"][1]}
                    </li>

                    <li>
                    {item["tasks"][2]}
                    </li>

                    </ul>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ============================================================
# MISSED DAY RECOVERY PAGE
# ============================================================

elif page == "⏰ Missed Day Recovery":

    st.subheader("⏰ Missed Day Recovery")
    st.write("Busy schedule? Missed one or more study days? PrepPilot can redistribute the unfinished work.")

    profile = load_profile()

    if not profile:
        st.warning("Please create your profile first.")
    else:
        target_date = datetime.strptime(profile["exam_date"], "%Y-%m-%d").date()
        days_remaining = get_days_remaining(target_date)

        if days_remaining == 0:
            st.error("⏰ Your target date is today. There are no future preparation days available for recovery.")
        else:
            subjects = exam_data[profile["exam"]][profile["paper"]]
            weak_subjects = [x.strip() for x in profile["weak_subjects"].split(",") if x.strip()]

            st.markdown("### 1️⃣ Tell PrepPilot what happened")
            missed_days = st.number_input(
                "How many study days did you miss?",
                min_value=1,
                max_value=max(1, min(30, days_remaining)),
                value=1,
                step=1
            )

            available_today = st.number_input(
                "How many hours can you study today?",
                min_value=0.5,
                max_value=16.0,
                value=min(2.0, float(profile["study_hours"])),
                step=0.5
            )

            mode = st.radio(
                "Choose recovery method",
                [
                    "Balanced Catch-up",
                    "Light / Less-Time Recovery"
                ],
                help="Balanced recovery spreads the missed work. Light recovery intentionally recovers less so your schedule stays comfortable."
            )

            st.markdown("### 2️⃣ Your recovery strategy")
            normal_hours = float(profile["study_hours"])
            missed_hours = missed_days * normal_hours

            if mode == "Balanced Catch-up":
                st.info(
                    f"You missed about **{missed_hours:.1f} hours**. PrepPilot will spread the catch-up work instead of putting all of it on one day."
                )
            else:
                st.info(
                    f"You missed about **{missed_hours:.1f} hours**. PrepPilot will recover only part of it and protect you from an overloaded schedule."
                )

            if st.button("🔄 Create Recovery Plan", use_container_width=True):
                recovery_plan, recovery_days, recoverable_hours = build_recovery_plan(
                    subjects,
                    weak_subjects,
                    normal_hours,
                    target_date,
                    int(missed_days),
                    mode,
                    float(available_today)
                )

                st.markdown("### 3️⃣ Your adjusted plan")
                st.success(
                    f"PrepPilot adjusted the next **{recovery_days} day(s)**. "
                    f"Today you have **{available_today:.1f} hours** available. "
                    f"The recovery plan adds only a small amount of extra work per day."
                )

                if recoverable_hours < missed_hours and mode == "Balanced Catch-up":
                    st.warning(
                        f"Because the exam date is fixed, only about **{recoverable_hours:.1f} hours** can be safely redistributed without overloading your days. "
                        "The remaining work should be treated as lower priority."
                    )

                for item in recovery_plan:
                    st.markdown(
                        f"""
                        <div class="plan-card">
                        <h3>Day {item["day"]} — {item["date"]}</h3>
                        <p>⏱️ Normal: <b>{item["normal_hours"]:.1f} h</b> &nbsp; + &nbsp; Recovery: <b>{item["extra_hours"]:.1f} h</b> &nbsp; = &nbsp; Total: <b>{item["total_hours"]:.1f} h</b></p>
                        <ul>
                        <li>{item["tasks"][0]}</li>
                        <li>{item["tasks"][1]}</li>
                        <li>{item["tasks"][2]}</li>
                        </ul>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown("### 💡 Important")
                st.write(
                    "Missing one day does not mean you should study double the next day. "
                    "PrepPilot keeps the target date fixed and distributes the missed work across several days."
                )


# ============================================================
# AI STUDY ASSISTANT
# ============================================================

elif page == "🤖 AI Study Assistant":

    st.subheader("🤖 AI Study Assistant")
    st.caption("Free local AI powered by Ollama — no OpenAI credits or API key required.")

    profile = load_profile()
    history = load_mock_history()

    if not profile:
        st.warning("Please create your Exam & Profile first.")
    else:
        target_date = datetime.strptime(profile["exam_date"], "%Y-%m-%d").date()
        days = get_days_remaining(target_date)
        weak = [x.strip() for x in str(profile.get("weak_subjects", "")).split(",") if x.strip()]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Exam", profile["exam"])
        with c2:
            st.metric("Days Remaining", days)
        with c3:
            st.metric("Daily Hours", f"{float(profile['study_hours']):.1f} h")

        st.markdown(
            f"**Paper:** {profile['paper']}  \n"
            f"**Weak subjects:** {', '.join(weak) if weak else 'None specified'}"
        )

        if "ai_chat" not in st.session_state:
            st.session_state.ai_chat = [
                {
                    "role": "assistant",
                    "content": "Hi! 👋 I'm your PrepPilot AI Study Assistant. Ask me about your study plan, weak subjects, mock performance, revision, or missed days."
                }
            ]

        st.markdown("### 💡 Try asking")
        suggestions = [
            "What should I study today?",
            "How can I improve my weak subjects?",
            "I missed yesterday. What should I do?",
            "Give me a study plan for today."
        ]

        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, key=f"ai_suggestion_{i}", use_container_width=True):
                    st.session_state.ai_pending = suggestion

        for message in st.session_state.ai_chat:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        pending = st.session_state.pop("ai_pending", None)
        user_prompt = st.chat_input("Ask PrepPilot anything about your preparation...")
        prompt = user_prompt or pending

        if prompt:
            st.session_state.ai_chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            context = build_ai_context(profile, history)
            with st.chat_message("assistant"):
                with st.spinner("PrepPilot is thinking..."):
                    try:
                        answer = ask_ollama(prompt, context)
                        st.markdown(answer)
                        st.session_state.ai_chat.append({"role": "assistant", "content": answer})
                    except requests.exceptions.ConnectionError:
                        answer = "Ollama is not running. Open a terminal and run `ollama run llama3.2`, then return to PrepPilot."
                        st.error(answer)
                        st.session_state.ai_chat.append({"role": "assistant", "content": answer})
                    except requests.exceptions.Timeout:
                        answer = "The local AI took too long to respond. Please try a shorter question."
                        st.error(answer)
                        st.session_state.ai_chat.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        answer = f"I couldn't get a response from Ollama: {e}"
                        st.error(answer)
                        st.session_state.ai_chat.append({"role": "assistant", "content": answer})

        if st.button("🗑️ Clear Chat"):
            st.session_state.ai_chat = [
                {
                    "role": "assistant",
                    "content": "Chat cleared. What would you like to study?"
                }
            ]
            st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">

<hr>

🚀 <b>PrepPilot</b>
— AI-Powered Personalized Exam Preparation Assistant

<br><br>

Built with Python • Streamlit • Pandas • Scikit-learn • SQLite

</div>
""", unsafe_allow_html=True)