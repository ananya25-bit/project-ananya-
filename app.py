import sqlite3
from datetime import date
from pathlib import Path

import streamlit as st


# Keep the database next to this Python file, even if the app is started elsewhere.
DATABASE_PATH = Path(__file__).with_name("placements.db")

APPLICATION_STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]


def fetch_applications():
    """Return all applications, with the newest application dates first."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.execute(
            """
            SELECT application_id, company_name, job_role, application_date, status
            FROM applications
            ORDER BY application_date DESC, application_id DESC
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def fetch_status_counts():
    """Return a count for every status, including statuses with no applications."""
    counts = {status: 0 for status in APPLICATION_STATUSES}
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        rows = connection.execute(
            "SELECT status, COUNT(*) FROM applications GROUP BY status"
        ).fetchall()
    finally:
        connection.close()

    for status, count in rows:
        if status in counts:
            counts[status] = count
        elif status:
            counts[status] = count
    return counts


def add_application(company_name, job_role, application_date, status):
    """Insert one application into the database."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """
            INSERT INTO applications (company_name, job_role, application_date, status)
            VALUES (?, ?, ?, ?)
            """,
            (company_name, job_role, application_date, status),
        )
        connection.commit()
    finally:
        connection.close()


st.set_page_config(page_title="Placement Application Tracker", page_icon="📋", layout="wide")

st.title("📋 Placement Application Tracker")
st.write("Keep your job applications organized and see how your search is progressing.")

applications = fetch_applications()
total_applications = len(applications)

# Show the overall application count and the most frequently used job role.
role_counts = {}
for application in applications:
    job_role = application[2]
    role_counts[job_role] = role_counts.get(job_role, 0) + 1

if role_counts:
    most_applied_role = min(
        role_counts,
        key=lambda role: (-role_counts[role], role.casefold(), role),
    )
else:
    most_applied_role = None

metric_column, role_column = st.columns(2)
metric_column.metric("Total applications", total_applications)
if most_applied_role is None:
    role_column.metric("Most applied role", "No applications yet")
else:
    role_column.metric(
        "Most applied role",
        most_applied_role,
        help="If roles are tied, the name that comes first alphabetically is shown.",
    )

st.divider()

# Let the user enter and save an application.
st.header("Add an application")
with st.form("add_application_form", clear_on_submit=True):
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input("Application Date", value=date.today())
    status = st.selectbox("Status", APPLICATION_STATUSES)
    submitted = st.form_submit_button("Add Application")

if submitted:
    if not company_name.strip():
        st.error("Please enter a company name.")
    elif not job_role.strip():
        st.error("Please enter a job role.")
    else:
        add_application(
            company_name.strip(),
            job_role.strip(),
            application_date.isoformat(),
            status,
        )
        st.success(f"Application to {company_name.strip()} was added.")
        st.rerun()

st.divider()

# Display the saved applications in a table with all five database columns.
st.header("Your applications")
if applications:
    st.dataframe(
        [
            {
                "Application ID": row[0],
                "Company Name": row[1],
                "Job Role": row[2],
                "Application Date": row[3],
                "Status": row[4],
            }
            for row in applications
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No applications are recorded yet. Add your first application above.")

st.divider()

# Show the number of applications in each status and a simple bar chart.
st.header("Status-wise summary")
status_counts = fetch_status_counts()
summary_columns = st.columns(len(status_counts))
for column, (status_name, count) in zip(summary_columns, status_counts.items()):
    column.metric(status_name, count)

st.bar_chart({"Applications": status_counts}, y_label="Number of applications")
