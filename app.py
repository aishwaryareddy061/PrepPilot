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
.stApp { background: linear-gradient(135deg, #f6f8ff, #eef2ff, #f8fafc); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #111827, #1e293b); }
[data-testid="stSidebar"] * { color: white !important; }
.hero { background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 30px; border-radius: 22px;
        color: white; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(79,70,229,0.20); }
.hero h1 { margin: 0; font-size: 38px; }
.hero p { margin-top: 8px; font-size: 17px; opacity: 0.9; }
.card { background: white; padding: 22px; border-radius: 18px; margin-bottom: 18px;
        border: 1px solid #e5e7eb; box-shadow: 0 5px 20px rgba(0,0,0,0.06); }
.metric-card { background: white; padding: 18px; border-radius: 16px; text-align: center;
               border: 1px solid #e5e7eb; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
.metric-value { font-size: 28px; font-weight: 700; color: #4f46e5; }
.metric-label { color: #64748b; font-size: 14px; }
.plan-card { background: white; padding: 20px; border-radius: 18px; margin: 12px 0;
             border-left: 5px solid #4f46e5; box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
.ai-card { background: linear-gradient(135deg, #eef2ff, #f5f3ff); padding: 22px; border-radius: 18px;
           border: 1px solid #c7d2fe; }
.weak { background: #fff7ed; padding: 18px; border-radius: 15px; border-left: 5px solid #f97316; }
.strong { background: #f0fdf4; padding: 18px; border-radius: 15px; border-left: 5px solid #22c55e; }
.footer { text-align: center; color: #64748b; padding: 30px; }
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            profile_id INTEGER,
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

    # Upgrade an older PrepPilot database safely.
    mock_columns = [r[1] for r in cursor.execute("PRAGMA table_info(mock_history)").fetchall()]
    if "profile_id" not in mock_columns:
        cursor.execute("ALTER TABLE mock_history ADD COLUMN profile_id INTEGER")
        cursor.execute("UPDATE mock_history SET profile_id = 1 WHERE profile_id IS NULL")

    conn.commit()
    conn.close()


initialize_database()

# ============================================================
# EXAM DATA
# ============================================================

exam_data = {
    "GATE": {
        "AE - Aerospace Engineering": ["General Aptitude", "Engineering Mathematics", "Flight Mechanics", "Aerodynamics", "Structures", "Propulsion"],
        "AG - Agricultural Engineering": ["General Aptitude", "Engineering Mathematics", "Farm Machinery", "Soil and Water Engineering", "Agricultural Processing"],
        "AR - Architecture & Planning": ["General Aptitude", "Architecture", "Planning", "Building Construction", "Environmental Design"],
        "BT - Biotechnology": ["General Aptitude", "Engineering Mathematics", "Biochemistry", "Microbiology", "Genetics", "Cell Biology", "Bioprocess Engineering"],
        "CE - Civil Engineering": ["General Aptitude", "Engineering Mathematics", "Structural Engineering", "Geotechnical Engineering", "Water Resources Engineering", "Environmental Engineering", "Transportation Engineering"],
        "CH - Chemical Engineering": ["General Aptitude", "Engineering Mathematics", "Chemical Engineering Thermodynamics", "Fluid Mechanics", "Heat Transfer", "Mass Transfer", "Reaction Engineering"],
        "CS - Computer Science & IT": ["General Aptitude", "Engineering Mathematics", "Digital Logic", "Computer Organization", "Programming and Data Structures", "Algorithms", "Theory of Computation", "Compiler Design", "Operating Systems", "Databases", "Computer Networks"],
        "CY - Chemistry": ["General Aptitude", "Physical Chemistry", "Organic Chemistry", "Inorganic Chemistry"],
        "DA - Data Science & Artificial Intelligence": ["General Aptitude", "Probability and Statistics", "Linear Algebra", "Calculus and Optimization", "Programming", "Data Structures and Algorithms", "Database Management", "Machine Learning", "Artificial Intelligence"],
        "EC - Electronics & Communication Engineering": ["General Aptitude", "Engineering Mathematics", "Networks", "Signals and Systems", "Electronic Devices", "Analog Circuits", "Digital Circuits", "Communication Systems", "Electromagnetics"],
        "EE - Electrical Engineering": ["General Aptitude", "Engineering Mathematics", "Electric Circuits", "Electromagnetic Fields", "Signals and Systems", "Electrical Machines", "Power Systems", "Control Systems", "Power Electronics"],
        "IN - Instrumentation Engineering": ["General Aptitude", "Engineering Mathematics", "Electrical Circuits", "Signals and Systems", "Control Systems", "Sensors", "Instrumentation"],
        "MA - Mathematics": ["General Aptitude", "Linear Algebra", "Calculus", "Real Analysis", "Complex Analysis", "Differential Equations", "Numerical Analysis"],
        "ME - Mechanical Engineering": ["General Aptitude", "Engineering Mathematics", "Engineering Mechanics", "Strength of Materials", "Theory of Machines", "Thermodynamics", "Fluid Mechanics", "Heat Transfer", "Manufacturing Engineering"],
        "PH - Physics": ["General Aptitude", "Mathematical Physics", "Classical Mechanics", "Electromagnetism", "Quantum Mechanics", "Thermodynamics", "Solid State Physics"],
        "ST - Statistics": ["General Aptitude", "Probability", "Statistical Inference", "Regression", "Multivariate Analysis", "Sampling Theory"]
    },
    "JEE Main": {
        "Paper 1 - B.E. / B.Tech": ["Physics", "Chemistry", "Mathematics"],
        "Paper 2A - B.Arch": ["Mathematics", "Aptitude Test", "Drawing Test"],
        "Paper 2B - B.Planning": ["Mathematics", "Aptitude Test", "Planning Based Questions"]
    },
    "NEET UG": {
        "NEET UG": ["Physics", "Chemistry", "Botany", "Zoology"]
    },
    "UPSC Civil Services": {
        "Prelims - General Studies": ["History", "Geography", "Indian Polity", "Economy", "Environment", "Science and Technology", "Current Affairs"],
        "Prelims - CSAT": ["Reading Comprehension", "Logical Reasoning", "Analytical Ability", "Basic Numeracy", "Data Interpretation"],
        "Mains - General Studies": ["Indian Heritage and Culture", "History", "Geography", "Governance", "Constitution", "Social Issues", "Economy", "Environment", "Science and Technology", "International Relations", "Ethics"]
    },
    "SSC CGL": {
        "Tier 1": ["General Intelligence and Reasoning", "General Awareness", "Quantitative Aptitude", "English Comprehension"],
        "Tier 2 - Paper 1": ["Mathematical Abilities", "Reasoning and General Intelligence", "English Language", "General Awareness", "Computer Knowledge"],
        "Tier 2 - Paper 2 Statistics": ["Statistics"]
    },
    "JEE": {
        "JEE Main": ["Physics", "Chemistry", "Mathematics"],
        "JEE Advanced": ["Physics", "Chemistry", "Mathematics"]
    },
    "UPSC": {
        "Civil Services Prelims": ["General Studies Paper I", "Current Affairs", "History", "Geography", "Indian Polity", "Economy", "Environment and Ecology", "General Science"],
        "Civil Services Mains - GS": ["Essay", "General Studies I", "General Studies II", "General Studies III", "General Studies IV", "Optional Subject"]
    },
    "CAT": {
        "CAT": ["Verbal Ability and Reading Comprehension", "Data Interpretation", "Logical Reasoning", "Quantitative Aptitude"]
    },
    "Banking Exams": {
        "IBPS PO": ["English Language", "Quantitative Aptitude", "Reasoning Ability", "General Awareness", "Computer Aptitude"],
        "SBI PO": ["English Language", "Quantitative Aptitude", "Reasoning Ability", "General Awareness", "Computer Aptitude"],
        "IBPS Clerk": ["English Language", "Numerical Ability", "Reasoning Ability", "General Awareness"],
        "SBI Clerk": ["English Language", "Numerical Ability", "Reasoning Ability", "General Awareness"]
    }
}

# ============================================================
# PROFILE FUNCTIONS (MULTI-PROFILE)
# ============================================================


def split_subjects(text):
    return [x.strip() for x in str(text or "").split(",") if x.strip()]


def load_profiles():
    """Return all saved PrepPilot profiles."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM profile ORDER BY id", conn)
    conn.close()
    return df


def save_profile(data, profile_id=None):
    """Create a new profile (profile_id=None) or update an existing one."""
    conn = get_connection()
    cursor = conn.cursor()

    values = (
        data["name"], data["exam"], data["paper"],
        data["preparation_level"], data["study_hours"],
        data["target_score"], data["exam_date"],
        ", ".join(data["strong_subjects"]),
        ", ".join(data["weak_subjects"])
    )

    if profile_id is None:
        cursor.execute("""
            INSERT INTO profile (
                name, exam, paper, preparation_level, study_hours,
                target_score, exam_date, strong_subjects, weak_subjects
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        new_id = cursor.lastrowid
    else:
        cursor.execute("""
            UPDATE profile SET
                name=?, exam=?, paper=?, preparation_level=?, study_hours=?,
                target_score=?, exam_date=?, strong_subjects=?, weak_subjects=?
            WHERE id=?
        """, values + (profile_id,))
        new_id = profile_id

    conn.commit()
    conn.close()

    # The sidebar selectbox is already drawn in this run, so we cannot change
    # its value directly. We leave a "pending" note; the sidebar applies it
    # at the start of the next run (before the selectbox is created).
    st.session_state["active_profile_id"] = int(new_id)
    st.session_state["pending_profile_id"] = int(new_id)
    return int(new_id)


def load_profile():
    """Load the currently selected profile."""
    profiles = load_profiles()
    if profiles.empty:
        return None

    ids = profiles["id"].astype(int).tolist()
    active_id = st.session_state.get("active_profile_id")
    if active_id not in ids:
        active_id = ids[-1]
        st.session_state["active_profile_id"] = int(active_id)

    row = profiles[profiles["id"] == int(active_id)]
    if row.empty:
        return None
    return row.iloc[0].to_dict()

# ============================================================
# MOCK FUNCTIONS
# ============================================================


def save_mock(profile_id, exam, paper, subject, score, total_marks, accuracy, attempted):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mock_history
        (profile_id, date, exam, paper, subject, score, total_marks, accuracy, attempted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        profile_id, datetime.now().strftime("%Y-%m-%d %H:%M"), exam, paper,
        subject, score, total_marks, accuracy, attempted
    ))
    conn.commit()
    conn.close()


def load_mock_history(profile=None):
    """Load mock results only for the active profile."""
    if profile is None:
        profile = load_profile()
    if not profile:
        return pd.DataFrame()

    conn = get_connection()
    df = pd.read_sql_query(
        """SELECT * FROM mock_history
           WHERE profile_id = ? AND exam = ? AND paper = ?
           ORDER BY id DESC""",
        conn, params=(int(profile["id"]), profile["exam"], profile["paper"])
    )
    conn.close()
    return df

# ============================================================
# DATE FUNCTIONS
# ============================================================


def get_days_remaining(target_date):
    # Returns exactly 0 when the target date is today (never converted to 1).
    return max(0, (target_date - date.today()).days)


def choose_target_date(existing_date=None, key_prefix="target"):
    today = date.today()

    if existing_date is not None:
        try:
            if isinstance(existing_date, str):
                default_date = datetime.strptime(existing_date, "%Y-%m-%d").date()
            else:
                default_date = existing_date
        except Exception:
            default_date = today + timedelta(days=90)
    else:
        default_date = today + timedelta(days=90)

    if default_date < today:
        default_date = today

    years = list(range(today.year, today.year + 6))
    default_year = default_date.year if default_date.year in years else today.year

    year = st.selectbox(
        "📅 Target Year", years,
        index=years.index(default_year),
        key=f"{key_prefix}_year"
    )

    months = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    month_number = st.selectbox(
        "📅 Target Month", list(months.keys()),
        index=default_date.month - 1,
        format_func=lambda x: months[x],
        key=f"{key_prefix}_month"
    )

    max_day = calendar.monthrange(year, month_number)[1]

    if year == today.year and month_number < today.month:
        st.warning("⚠️ That month has already passed. Please select a future month.")
        valid_days = list(range(today.day, max_day + 1))
    elif year == today.year and month_number == today.month:
        valid_days = list(range(today.day, max_day + 1))
    else:
        valid_days = list(range(1, max_day + 1))

    if not valid_days:
        valid_days = [max_day]

    default_day = default_date.day if default_date.day in valid_days else valid_days[0]

    day = st.selectbox(
        "📅 Target Day", valid_days,
        index=valid_days.index(default_day),
        key=f"{key_prefix}_day"
    )

    return date(year, month_number, day)

# ============================================================
# ML MODEL
# ============================================================


def train_model():
    data = pd.DataFrame({
        "study_hours": [1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12],
        "mock_score": [25, 30, 35, 38, 42, 45, 48, 52, 55, 58, 60, 63, 65, 68, 72, 75, 78, 82, 85, 88, 92, 95],
        "accuracy": [35, 40, 43, 45, 48, 50, 52, 55, 58, 60, 62, 65, 67, 70, 73, 76, 78, 82, 85, 88, 92, 95],
        "attempt_rate": [35, 40, 45, 48, 50, 53, 55, 58, 60, 62, 65, 68, 70, 73, 76, 78, 80, 84, 87, 90, 94, 97],
        "level": (["Needs Improvement"] * 7) + (["Average"] * 8) + (["Strong"] * 7)
    })

    X = data[["study_hours", "mock_score", "accuracy", "attempt_rate"]]
    y = data["level"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model


model = train_model()


def get_prediction(study_hours, mock_score, accuracy, attempted):
    features = pd.DataFrame([{
        "study_hours": study_hours,
        "mock_score": mock_score,
        "accuracy": accuracy,
        "attempt_rate": attempted
    }])
    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    return prediction, max(probabilities) * 100

# ============================================================
# SUBJECT ANALYSIS
# ============================================================


def analyze_subjects(history):
    if history.empty:
        return [], []

    grouped = history.groupby("subject").agg({"score": "mean", "accuracy": "mean"}).reset_index()
    weak = grouped[grouped["accuracy"] < 60]["subject"].tolist()
    strong = grouped[grouped["accuracy"] >= 75]["subject"].tolist()
    return weak, strong

# ============================================================
# PLAN GENERATOR (FIXED: covers weak + normal + strong subjects)
# ============================================================

# Relative share of study days. Weak gets the most, strong the least,
# but strong/normal subjects are NEVER dropped.
CATEGORY_WEIGHTS = {"weak": 3.0, "normal": 2.0, "strong": 1.0}
CATEGORY_RANK = {"weak": 0, "normal": 1, "strong": 2}


def allocate_days(all_subjects, category_of, total_days):
    """Decide how many days each subject gets.

    1. If there are enough days, EVERY subject gets at least 1 day.
    2. Remaining days are shared by weight (weak 3 : normal 2 : strong 1)
       using the largest-remainder method so the total is exactly total_days.
    3. If there are fewer days than subjects, subjects are picked in
       priority order (weak, normal, strong) - one day each.
    """
    n = len(all_subjects)
    quotas = {s: 0 for s in all_subjects}

    if total_days <= 0 or n == 0:
        return quotas

    if total_days < n:
        ordered = sorted(all_subjects, key=lambda s: (CATEGORY_RANK[category_of[s]], all_subjects.index(s)))
        for s in ordered[:total_days]:
            quotas[s] = 1
        return quotas

    for s in all_subjects:
        quotas[s] = 1

    remaining = total_days - n
    if remaining == 0:
        return quotas

    total_weight = sum(CATEGORY_WEIGHTS[category_of[s]] for s in all_subjects)
    raw = {s: remaining * CATEGORY_WEIGHTS[category_of[s]] / total_weight for s in all_subjects}

    for s in all_subjects:
        quotas[s] += int(raw[s])

    leftover = total_days - sum(quotas.values())
    by_fraction = sorted(
        all_subjects,
        key=lambda s: (-(raw[s] - int(raw[s])), CATEGORY_RANK[category_of[s]])
    )
    for s in by_fraction[:leftover]:
        quotas[s] += 1

    return quotas


def spread_schedule(all_subjects, category_of, quotas, total_days):
    """Place each subject's days evenly across the timeline (no clumping)."""
    slots = []
    for s in all_subjects:
        q = quotas[s]
        for k in range(q):
            position = (k + 0.5) * total_days / q
            slots.append((position, CATEGORY_RANK[category_of[s]], all_subjects.index(s), s))
    slots.sort()
    return [s for _, _, _, s in slots]


def generate_plan(subjects, weak_subjects, strong_subjects, study_hours, target_date, history=None):
    """Generate a balanced timetable with FULL syllabus coverage.

    Weak   = most days
    Normal = regular days
    Strong = fewer days (maintenance), but never skipped
    """
    days_remaining = get_days_remaining(target_date)
    if days_remaining <= 0 or not subjects:
        return [], max(0, days_remaining)

    all_subjects = list(dict.fromkeys(str(s).strip() for s in subjects if str(s).strip()))
    weak = list(dict.fromkeys(s for s in weak_subjects if s in all_subjects))
    strong = list(dict.fromkeys(s for s in strong_subjects if s in all_subjects and s not in weak))

    # Use mock performance as an additional signal.
    performance = {}
    if history is not None and not history.empty and "total_marks" in history.columns:
        temp = history.copy()
        temp["score_pct"] = (temp["score"] / temp["total_marks"] * 100).replace([np.inf, -np.inf], np.nan)
        grouped = temp.groupby("subject").agg(
            score_pct=("score_pct", "mean"),
            accuracy=("accuracy", "mean")
        )
        for subject, row in grouped.iterrows():
            performance[subject] = {"score": float(row["score_pct"]), "accuracy": float(row["accuracy"])}

    for subject, perf in performance.items():
        if subject not in all_subjects:
            continue
        if perf["accuracy"] < 60 or perf["score"] < 60:
            if subject not in weak:
                weak.append(subject)
            if subject in strong:
                strong.remove(subject)
        elif perf["accuracy"] >= 75 and perf["score"] >= 75:
            if subject not in weak and subject not in strong:
                strong.append(subject)

    normal = [s for s in all_subjects if s not in weak and s not in strong]
    category_of = {}
    for s in weak:
        category_of[s] = "weak"
    for s in strong:
        category_of[s] = "strong"
    for s in normal:
        category_of[s] = "normal"

    quotas = allocate_days(all_subjects, category_of, days_remaining)
    order = spread_schedule(all_subjects, category_of, quotas, days_remaining)

    plan = []
    for i, focus in enumerate(order):
        day_number = i + 1
        category = category_of[focus]

        if category == "weak":
            label = "🔴 Weak-subject priority"
        elif category == "strong":
            label = "🟢 Strong-subject maintenance"
        else:
            label = "🟡 Full-syllabus coverage"

        perf = performance.get(focus)
        if perf:
            score = perf["score"]
            accuracy = perf["accuracy"]
            if accuracy < 60 or score < 60:
                task1 = f"Concept study: {focus}"
                task2 = f"Practice questions + mistake review: {focus}"
                note = f"Mock: {score:.0f}% score / {accuracy:.0f}% accuracy — high priority"
            elif accuracy < 75 or score < 75:
                task1 = f"Study + practice: {focus}"
                task2 = f"Review previous mistakes: {focus}"
                note = f"Mock: {score:.0f}% score / {accuracy:.0f}% accuracy — needs practice"
            else:
                task1 = f"Timed practice: {focus}"
                task2 = f"PYQs + quick revision: {focus}"
                note = f"Mock: {score:.0f}% score / {accuracy:.0f}% accuracy — maintain performance"
        elif category == "strong":
            task1 = f"Quick revision: {focus}"
            task2 = f"Practice/PYQs: {focus}"
            note = "Strong subject — maintenance study; not skipped"
        elif category == "weak":
            task1 = f"Learn/revise concepts: {focus}"
            task2 = f"Focused practice + mistake review: {focus}"
            note = "Weak subject — extra practice priority"
        else:
            task1 = f"Study concepts: {focus}"
            task2 = f"Practice questions: {focus}"
            note = "Regular syllabus coverage"

        # Secondary short revision slot from a different category when possible.
        if category == "weak":
            secondary_candidates = strong + normal
        elif category == "strong":
            secondary_candidates = weak + normal
        else:
            secondary_candidates = weak + strong
        secondary_candidates = [s for s in secondary_candidates if s != focus]
        if not secondary_candidates:
            secondary_candidates = [s for s in all_subjects if s != focus]
        secondary = secondary_candidates[i % len(secondary_candidates)] if secondary_candidates else focus

        if float(study_hours) >= 6:
            task3 = f"Revision / PYQs: {secondary}"
        elif float(study_hours) >= 3:
            task3 = f"Quick revision: {secondary}"
        else:
            task3 = f"Short revision: {secondary}"

        if day_number % 7 == 0:
            task2 = "Weekly mock / timed test"
            task3 = f"Analyze mistakes and revise: {focus}"
            label += " + 📝 Weekly checkpoint"

        plan.append({
            "day": day_number,
            "date": (date.today() + timedelta(days=i)).strftime("%d %B %Y"),
            "subject": focus,
            "category": category,
            "tasks": [task1, task2, task3],
            "focus": label,
            "performance": note
        })

    return plan, days_remaining


def plan_summary_table(plan, subjects):
    """Show how many days each subject receives in the plan."""
    counts = {}
    cats = {}
    for item in plan:
        counts[item["subject"]] = counts.get(item["subject"], 0) + 1
        cats[item["subject"]] = item["category"]

    label = {"weak": "🔴 Weak", "normal": "🟡 Normal", "strong": "🟢 Strong"}
    rows = []
    for s in subjects:
        rows.append({
            "Subject": s,
            "Type": label.get(cats.get(s), "—"),
            "Study Days": counts.get(s, 0)
        })
    df = pd.DataFrame(rows)
    return df.sort_values("Study Days", ascending=False).reset_index(drop=True)

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
    max_extra_per_day = float(study_hours) * 0.5

    if mode == "Light / Less-Time Recovery":
        recover_hours = missed_hours * 0.5
        daily_extra_cap = min(max_extra_per_day, 1.0)
    else:
        recover_hours = missed_hours
        daily_extra_cap = max_extra_per_day

    future_days = max(0, days_remaining - 1)
    recovery_days = min(max(1, future_days), max(1, missed_days + 2))

    today_hours = min(float(available_today), float(study_hours))
    missed_recovery_after_today = max(0.0, recover_hours - max(0.0, today_hours - float(study_hours)))

    extra_per_day = 0.0
    if recovery_days > 0:
        extra_per_day = min(daily_extra_cap, missed_recovery_after_today / recovery_days)

    recoverable_hours = max(0.0, today_hours - float(study_hours)) + (extra_per_day * recovery_days)

    if not subjects:
        subjects = ["General Revision"]

    priority_subjects = []
    for subject in weak_subjects + subjects:
        if subject not in priority_subjects:
            priority_subjects.append(subject)

    plan = []

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
            tasks = [f"Priority recovery: {subject}", f"Quick practice: {subject}", f"Maintain normal plan: {next_subject}"]
        else:
            tasks = [f"Recover missed work: {subject}", f"Practice questions: {subject}", f"Continue normal plan: {next_subject}"]

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
        "options": {"temperature": 0.2, "num_ctx": 2048, "num_predict": 220, "top_p": 0.9}
    }
    response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=90)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "I could not generate a response right now.").strip()


def build_ai_context(profile, history):
    if not profile:
        return "No preparation profile has been created yet."

    target_date = datetime.strptime(profile["exam_date"], "%Y-%m-%d").date()
    days = get_days_remaining(target_date)
    weak = split_subjects(profile.get("weak_subjects", ""))
    strong = split_subjects(profile.get("strong_subjects", ""))

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
# SIDEBAR / PROFILE SWITCHER (FIXED)
# ============================================================

st.session_state.setdefault("new_form_id", 0)
st.session_state.setdefault("create_new_profile", False)


def on_profile_change():
    """Runs when the user picks a different profile in the sidebar."""
    st.session_state["active_profile_id"] = int(st.session_state["profile_selector"])
    st.session_state["create_new_profile"] = False


st.sidebar.markdown("""
<h2 style="text-align:center;">🚀 PrepPilot</h2>
<p style="text-align:center;">Smart Exam Preparation</p>
""", unsafe_allow_html=True)

profiles_df = load_profiles()
profile_ids = profiles_df["id"].astype(int).tolist() if not profiles_df.empty else []

# Apply a newly saved/created profile BEFORE the selectbox is created.
if "pending_profile_id" in st.session_state:
    st.session_state["profile_selector"] = st.session_state.pop("pending_profile_id")

if profile_ids:
    if st.session_state.get("profile_selector") not in profile_ids:
        fallback = st.session_state.get("active_profile_id")
        st.session_state["profile_selector"] = fallback if fallback in profile_ids else profile_ids[-1]

    profile_labels = {
        int(r["id"]): f"{int(r['id'])}. {r['name']} — {r['exam']} / {r['paper']}"
        for _, r in profiles_df.iterrows()
    }

    st.sidebar.markdown("### 👤 Profiles")
    st.sidebar.selectbox(
        "Switch profile",
        profile_ids,
        format_func=lambda i: profile_labels.get(i, str(i)),
        key="profile_selector",
        on_change=on_profile_change
    )
    st.session_state["active_profile_id"] = int(st.session_state["profile_selector"])

    active_row = profiles_df[profiles_df["id"] == st.session_state["active_profile_id"]].iloc[0]
    st.sidebar.caption(f"Active: {active_row['exam']} — {active_row['paper']}")
else:
    st.sidebar.info("No profiles yet. Create your first profile below.")

if st.sidebar.button("➕ Create New Profile", use_container_width=True):
    st.session_state["create_new_profile"] = True
    st.session_state["new_form_id"] += 1   # fresh blank form every time
    st.session_state["page"] = "📚 Exam & Profile"
    st.rerun()

if st.sidebar.button("✏️ Edit Current Profile", use_container_width=True, disabled=profiles_df.empty):
    st.session_state["create_new_profile"] = False
    st.session_state["page"] = "📚 Exam & Profile"
    st.rerun()

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
    ],
    key="page"
)

st.sidebar.markdown("---")
st.sidebar.caption("AI-powered personalized competitive exam preparation")

# ============================================================
# HERO
# ============================================================

st.markdown("""
<div class="hero">
<h1>🚀 PrepPilot</h1>
<p>Your AI-powered personalized competitive exam preparation assistant.</p>
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
        target_date = datetime.strptime(profile["exam_date"], "%Y-%m-%d").date()
        days = get_days_remaining(target_date)

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown("""
            <div class="metric-card">
            <div class="metric-value">🎓</div>
            <div class="metric-label">Exam</div>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"{profile['exam']} — {profile['paper']}")

        with c2:
            st.markdown(f"""
            <div class="metric-card">
            <div class="metric-value">{days}</div>
            <div class="metric-label">Days Remaining</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-card">
            <div class="metric-value">{len(history)}</div>
            <div class="metric-label">Mock Tests</div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="metric-card">
            <div class="metric-value">{profile["study_hours"]}</div>
            <div class="metric-label">Study Hours/Day</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if days == 0:
            st.error("⏰ Your target date is TODAY. There are no preparation days remaining.")
        else:
            st.success(f"📅 You have {days} preparation days remaining.")

        st.markdown("""
        <div class="ai-card">
        <h3>🤖 PrepPilot Status</h3>
        <p>
        Your profiles are permanently saved. You can keep several exams (for example GATE and UPSC)
        and switch between them from the sidebar. Mock-test performance is tracked per profile.
        </p>
        </div>
        """, unsafe_allow_html=True)

        if len(profile_ids) > 1:
            st.markdown("### 👤 All your profiles")
            overview = profiles_df[["id", "name", "exam", "paper", "exam_date", "study_hours"]].copy()
            overview.columns = ["ID", "Name", "Exam", "Paper", "Exam Date", "Hours/Day"]
            st.dataframe(overview, use_container_width=True, hide_index=True)
    else:
        st.info("👋 Welcome! Go to **Exam & Profile** to create your preparation profile.")

# ============================================================
# EXAM & PROFILE
# ============================================================

elif page == "📚 Exam & Profile":

    st.subheader("📚 Exam & Preparation Profile")

    creating_new = st.session_state.get("create_new_profile", False) or profiles_df.empty
    existing = None if creating_new else load_profile()

    if creating_new and not profiles_df.empty:
        st.info("🆕 Creating a new profile. Your existing profiles will remain saved.")
        if st.button("↩️ Cancel and return to current profile"):
            st.session_state["create_new_profile"] = False
            st.rerun()

    if existing:
        default_name = existing["name"]
        default_exam = existing["exam"]
        default_paper = existing["paper"]
        default_level = existing["preparation_level"]
        default_hours = float(existing["study_hours"])
        default_score = float(existing["target_score"])
        existing_date = existing["exam_date"]
    else:
        default_name = ""
        default_exam = "GATE"
        default_paper = list(exam_data["GATE"].keys())[0]
        default_level = "Beginner"
        default_hours = 4.0
        default_score = 70.0
        existing_date = None

    if creating_new:
        form_key = f"new_{st.session_state['new_form_id']}"
    else:
        form_key = "profile_" + str(int(existing["id"]))

    name = st.text_input("Your Name", value=default_name, placeholder="Enter your name", key=f"{form_key}_name")

    exam_options = list(exam_data.keys())
    exam_index = exam_options.index(default_exam) if default_exam in exam_options else 0

    exam = st.selectbox("Select Competitive Exam", exam_options, index=exam_index, key=f"{form_key}_exam")

    papers = list(exam_data[exam].keys())
    paper_index = papers.index(default_paper) if default_paper in papers else 0

    paper = st.selectbox("Select Paper / Stage / Branch", papers, index=paper_index, key=f"{form_key}_paper_{exam}")

    subjects = exam_data[exam][paper]

    st.markdown("### 📚 Subjects")
    st.write(", ".join(subjects))

    levels = ["Beginner", "Intermediate", "Advanced"]
    preparation_level = st.selectbox(
        "Current Preparation Level", levels,
        index=levels.index(default_level) if default_level in levels else 0,
        key=f"{form_key}_level"
    )

    study_hours = st.number_input(
        "Daily Study Hours", min_value=1.0, max_value=16.0,
        value=default_hours, step=0.5, key=f"{form_key}_hours"
    )

    target_score = st.number_input(
        "Target Score (%)", min_value=1.0, max_value=100.0,
        value=default_score, step=1.0, key=f"{form_key}_score"
    )

    st.markdown("### 📅 Target Exam Date")
    st.caption("Choose any future year, month, and day.")

    exam_date = choose_target_date(existing_date, key_prefix=f"{form_key}_date")

    st.info(f"Selected target date: **{exam_date.strftime('%d %B %Y')}**")

    days_remaining = get_days_remaining(exam_date)

    if days_remaining == 0:
        st.error("⏰ 0 days remaining — your target date is today.")
    else:
        st.success(f"📅 {days_remaining} days remaining.")

    existing_strong = split_subjects(existing.get("strong_subjects", "")) if existing else []
    existing_weak = split_subjects(existing.get("weak_subjects", "")) if existing else []

    # Keys include exam + paper so the lists reset when the exam changes.
    subject_key = f"{form_key}_{exam}_{paper}"

    st.markdown("### 💪 Strong Subjects")
    strong_subjects = st.multiselect(
        "Select subjects you are comfortable with", subjects,
        default=[x for x in existing_strong if x in subjects],
        key=f"{subject_key}_strong"
    )

    st.markdown("### ⚠️ Weak Subjects")
    weak_subjects = st.multiselect(
        "Select subjects that need more attention", subjects,
        default=[x for x in existing_weak if x in subjects],
        key=f"{subject_key}_weak"
    )

    if st.button("💾 Save Profile", use_container_width=True):

        overlap = set(strong_subjects) & set(weak_subjects)

        if not name.strip():
            st.error("Please enter your name.")
        elif not weak_subjects:
            st.warning("Select at least one weak subject.")
        elif overlap:
            st.error(f"A subject can't be both strong and weak: {', '.join(sorted(overlap))}")
        else:
            profile_data = {
                "name": name.strip(),
                "exam": exam,
                "paper": paper,
                "preparation_level": preparation_level,
                "study_hours": study_hours,
                "target_score": target_score,
                "exam_date": exam_date.strftime("%Y-%m-%d"),
                "strong_subjects": strong_subjects,
                "weak_subjects": weak_subjects
            }
            current_profile_id = None if creating_new else int(existing["id"])
            save_profile(profile_data, current_profile_id)
            st.session_state["create_new_profile"] = False

            st.success("✅ New profile created and selected!" if current_profile_id is None
                       else "✅ Current profile updated successfully!")
            st.rerun()

# ============================================================
# PERFORMANCE ANALYSIS
# ============================================================

elif page == "🧠 Performance Analysis":

    st.subheader("🧠 Performance Analysis")
    st.caption("A simple view of what you should focus on.")

    history = load_mock_history()

    if history.empty:
        st.info("Take a mock test first to see your performance.")
    else:
        weak, strong = analyze_subjects(history)

        grouped = history.groupby("subject").agg({"score": "mean", "accuracy": "mean"}).reset_index()

        grouped["status"] = grouped["accuracy"].apply(
            lambda x: "🔴 Weak" if x < 60 else ("🟡 Needs Practice" if x < 75 else "🟢 Strong")
        )
        grouped["action"] = grouped["accuracy"].apply(
            lambda x: "Focus first" if x < 60 else ("Practice more" if x < 75 else "Maintain")
        )

        st.markdown("### 📋 Subject Performance")
        st.dataframe(
            grouped[["subject", "accuracy", "status", "action"]].rename(columns={
                "subject": "Subject", "accuracy": "Accuracy (%)",
                "status": "Status", "action": "What to do"
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

    st.subheader("📅 Personalized Study Timetable")
    profile = load_profile()

    if not profile:
        st.warning("Please create your profile first.")
    else:
        target_date = datetime.strptime(profile["exam_date"], "%Y-%m-%d").date()
        subjects = exam_data[profile["exam"]][profile["paper"]]
        history = load_mock_history()

        profile_weak = split_subjects(profile.get("weak_subjects", ""))
        profile_strong = split_subjects(profile.get("strong_subjects", ""))
        detected_weak, detected_strong = analyze_subjects(history)

        weak_subjects = list(dict.fromkeys(profile_weak + detected_weak))
        strong_subjects = list(dict.fromkeys(profile_strong + detected_strong))
        strong_subjects = [s for s in strong_subjects if s not in weak_subjects]

        plan, days_remaining = generate_plan(
            subjects, weak_subjects, strong_subjects,
            float(profile["study_hours"]), target_date, history
        )

        if days_remaining <= 0:
            st.error("⏰ Your target date is today. No future preparation days remain.")
        else:
            st.success(f"📅 Your timetable contains exactly **{days_remaining} preparation days**.")

            if days_remaining < len(subjects):
                st.warning(
                    f"You have only {days_remaining} days for {len(subjects)} subjects, "
                    "so weak subjects were scheduled first and some strong subjects "
                    "could not fit. Use the daily revision slot to touch them."
                )

            normal_count = len([s for s in subjects if s not in weak_subjects and s not in strong_subjects])

            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric("🔴 Weak", len([s for s in weak_subjects if s in subjects]))
            with c2:
                st.metric("🟡 Normal", normal_count)
            with c3:
                st.metric("🟢 Strong", len([s for s in strong_subjects if s in subjects]))
            with c4:
                st.metric("📚 Total Subjects", len(subjects))
            with c5:
                st.metric("📝 Mock Tests", len(history))

            st.markdown("### 🎯 How this timetable is personalized")
            st.info(
                "Every subject is included. Weak subjects get the most days, normal subjects "
                "get regular days, and strong subjects get fewer maintenance days (about a "
                "3 : 2 : 1 ratio). Days are spread evenly so no subject disappears for weeks. "
                "Mock-test scores change the type of work: low performance → concepts + mistakes, "
                "medium → practice, high → timed practice/PYQs."
            )

            st.markdown("### 📊 Days allocated per subject")
            st.dataframe(plan_summary_table(plan, subjects), use_container_width=True, hide_index=True)

            st.markdown("### 📅 Day-by-day plan")
            for item in plan:
                st.markdown(
                    f"""
                    <div class="plan-card">
                        <h3>Day {item["day"]} — {item["date"]} · {item["subject"]}</h3>
                        <p>⏱️ Daily study time: <b>{float(profile["study_hours"]):.1f} hours</b></p>
                        <p>🎯 <b>{item["focus"]}</b></p>
                        <ul>
                            <li>{item["tasks"][0]}</li>
                            <li>{item["tasks"][1]}</li>
                            <li>{item["tasks"][2]}</li>
                        </ul>
                        <p>📊 {item["performance"]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# ============================================================
# MOCK TEST
# ============================================================

elif page == "📝 Mock Test":

    st.subheader("📝 Mock Test Performance")
    profile = load_profile()

    if not profile:
        st.warning("Please create your profile first.")
    else:
        st.caption(f"Saving results for: {profile['name']} — {profile['exam']} / {profile['paper']}")

        subjects = exam_data[profile["exam"]][profile["paper"]]

        subject = st.selectbox("Select Subject", subjects)

        total_marks = st.number_input("Total Marks", min_value=1.0, max_value=500.0, value=100.0, step=1.0)

        score = st.number_input("Score Obtained", min_value=0.0, max_value=float(total_marks), value=0.0, step=1.0)

        total_questions = st.number_input("Total Questions", min_value=1, max_value=300, value=50, step=1)

        attempted = st.number_input(
            "Questions Attempted", min_value=0, max_value=int(total_questions),
            value=min(40, int(total_questions)), step=1
        )

        correct = st.number_input("Correct Answers", min_value=0, max_value=int(attempted), value=0, step=1)

        if attempted > 0:
            accuracy = (correct / attempted) * 100
            attempt_rate = (attempted / total_questions) * 100
        else:
            accuracy = 0
            attempt_rate = 0

        st.metric("Current Accuracy", f"{accuracy:.1f}%")

        if st.button("💾 Save Mock Result", use_container_width=True):
            save_mock(
                int(profile["id"]), profile["exam"], profile["paper"],
                subject, score, total_marks, accuracy, attempt_rate
            )
            st.success("✅ Mock result saved permanently!")

# ============================================================
# ML ANALYSIS
# ============================================================

elif page == "🤖 ML Analysis":

    st.subheader("🤖 Machine Learning Analysis")

    history = load_mock_history()
    profile = load_profile()

    if not profile:
        st.warning("Please create your profile first.")
    elif history.empty:
        st.info("Take at least one mock test first.")
    else:
        average_score = (history["score"] / history["total_marks"] * 100).mean()
        average_accuracy = history["accuracy"].mean()
        average_attempt = history["attempted"].mean()

        prediction, confidence = get_prediction(
            float(profile["study_hours"]), average_score, average_accuracy, average_attempt
        )

        st.markdown(f"""
        <div class="ai-card">
        <h2>🤖 ML Prediction</h2>
        <h1>{prediction}</h1>
        <p>Model confidence: <b>{confidence:.1f}%</b></p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Average Score", f"{average_score:.1f}%")
        with c2:
            st.metric("Average Accuracy", f"{average_accuracy:.1f}%")
        with c3:
            st.metric("Average Attempt Rate", f"{average_attempt:.1f}%")

        st.markdown("### How PrepPilot's ML works")
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
        ordered = history.sort_values("id")
        latest = ordered.iloc[-1]["percentage"]
        previous = ordered.iloc[-2]["percentage"] if len(history) > 1 else None

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
                st.metric("Latest Score", f"{latest:.1f}%", f"{latest - previous:+.1f}%")

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
            display_history.style.format({"Accuracy (%)": "{:.1f}%", "Score (%)": "{:.1f}%"}),
            use_container_width=True,
            hide_index=True
        )

        csv = history.to_csv(index=False)
        st.download_button("⬇️ Download Progress", csv, "preppilot_progress.csv", "text/csv")

# ============================================================
# ADAPTIVE PLAN
# ============================================================

elif page == "🔄 Adaptive Plan":

    st.subheader("🔄 Adaptive Study Plan")
    profile = load_profile()
    history = load_mock_history()

    if not profile:
        st.warning("Please create your profile first.")
    else:
        target_date = datetime.strptime(profile["exam_date"], "%Y-%m-%d").date()
        subjects = exam_data[profile["exam"]][profile["paper"]]

        profile_weak = split_subjects(profile.get("weak_subjects", ""))
        profile_strong = split_subjects(profile.get("strong_subjects", ""))
        detected_weak, detected_strong = analyze_subjects(history)

        weak_subjects = list(dict.fromkeys(profile_weak + detected_weak))
        strong_subjects = list(dict.fromkeys(profile_strong + detected_strong))
        strong_subjects = [s for s in strong_subjects if s not in weak_subjects]

        plan, days_remaining = generate_plan(
            subjects, weak_subjects, strong_subjects,
            float(profile["study_hours"]), target_date, history
        )

        if days_remaining <= 0:
            st.error("⏰ Your target date is today. There are no future preparation days for an adaptive plan.")
        else:
            weak_text = ", ".join(weak_subjects) if weak_subjects else "None detected"
            strong_text = ", ".join(strong_subjects) if strong_subjects else "None detected"

            st.markdown(f"""
            <div class="ai-card">
                <h3>🤖 Adaptive Recommendation</h3>
                <p><b>Weak subjects:</b> {weak_text}</p>
                <p><b>Strong subjects:</b> {strong_text}</p>
                <p><b>Mock tests used:</b> {len(history)}</p>
                <p>PrepPilot rotates the full syllabus while giving extra attention to weak areas and using mock performance to decide the study activity.</p>
            </div>
            """, unsafe_allow_html=True)

            st.success(f"📅 Adaptive plan contains exactly **{days_remaining} day(s)**.")

            st.markdown("### 📊 Days allocated per subject")
            st.dataframe(plan_summary_table(plan, subjects), use_container_width=True, hide_index=True)

            for item in plan:
                st.markdown(
                    f"""
                    <div class="plan-card">
                        <h3>Day {item["day"]} — {item["date"]} · {item["subject"]}</h3>
                        <p>🎯 <b>{item["focus"]}</b></p>
                        <ul>
                            <li>{item["tasks"][0]}</li>
                            <li>{item["tasks"][1]}</li>
                            <li>{item["tasks"][2]}</li>
                        </ul>
                        <p>📊 {item["performance"]}</p>
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
            weak_subjects = split_subjects(profile.get("weak_subjects", ""))

            st.markdown("### 1️⃣ Tell PrepPilot what happened")
            missed_days = st.number_input(
                "How many study days did you miss?",
                min_value=1, max_value=max(1, min(30, days_remaining)), value=1, step=1
            )

            available_today = st.number_input(
                "How many hours can you study today?",
                min_value=0.5, max_value=16.0,
                value=min(2.0, float(profile["study_hours"])), step=0.5
            )

            mode = st.radio(
                "Choose recovery method",
                ["Balanced Catch-up", "Light / Less-Time Recovery"],
                help="Balanced recovery spreads the missed work. Light recovery intentionally recovers less so your schedule stays comfortable."
            )

            st.markdown("### 2️⃣ Your recovery strategy")
            normal_hours = float(profile["study_hours"])
            missed_hours = missed_days * normal_hours

            if mode == "Balanced Catch-up":
                st.info(f"You missed about **{missed_hours:.1f} hours**. PrepPilot will spread the catch-up work instead of putting all of it on one day.")
            else:
                st.info(f"You missed about **{missed_hours:.1f} hours**. PrepPilot will recover only part of it and protect you from an overloaded schedule.")

            if st.button("🔄 Create Recovery Plan", use_container_width=True):
                recovery_plan, recovery_days, recoverable_hours = build_recovery_plan(
                    subjects, weak_subjects, normal_hours, target_date,
                    int(missed_days), mode, float(available_today)
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
        weak = split_subjects(profile.get("weak_subjects", ""))

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

        # Keep a separate chat per profile so GATE and UPSC chats don't mix.
        chat_key = f"ai_chat_{int(profile['id'])}"

        if chat_key not in st.session_state:
            st.session_state[chat_key] = [{
                "role": "assistant",
                "content": "Hi! 👋 I'm your PrepPilot AI Study Assistant. Ask me about your study plan, weak subjects, mock performance, revision, or missed days."
            }]

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

        for message in st.session_state[chat_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        pending = st.session_state.pop("ai_pending", None)
        user_prompt = st.chat_input("Ask PrepPilot anything about your preparation...")
        prompt = user_prompt or pending

        if prompt:
            st.session_state[chat_key].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            context = build_ai_context(profile, history)
            with st.chat_message("assistant"):
                with st.spinner("PrepPilot is thinking..."):
                    try:
                        answer = ask_ollama(prompt, context)
                        st.markdown(answer)
                    except requests.exceptions.ConnectionError:
                        answer = "Ollama is not running. Open a terminal and run `ollama run llama3.2`, then return to PrepPilot."
                        st.error(answer)
                    except requests.exceptions.Timeout:
                        answer = "The local AI took too long to respond. Please try a shorter question."
                        st.error(answer)
                    except Exception as e:
                        answer = f"I couldn't get a response from Ollama: {e}"
                        st.error(answer)
                    st.session_state[chat_key].append({"role": "assistant", "content": answer})

        if st.button("🗑️ Clear Chat"):
            st.session_state[chat_key] = [{
                "role": "assistant",
                "content": "Chat cleared. What would you like to study?"
            }]
            st.rerun()

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
<hr>
🚀 <b>PrepPilot</b> — AI-Powered Personalized Exam Preparation Assistant
<br><br>
Built with Python • Streamlit • Pandas • Scikit-learn • SQLite
</div>
""", unsafe_allow_html=True)