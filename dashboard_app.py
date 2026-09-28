import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from gateway.ledger import fetch_usage
from gateway.reporting import summarize_optimization_savings, summarize_usage
from gateway.settings import ledger_path

PROJECT_ROOT = Path(__file__).resolve().parent
LOGO_PATH = PROJECT_ROOT / "app" / "assets" / "gateway_logo.svg"
LOGO_MARK_PATH = PROJECT_ROOT / "app" / "assets" / "gateway_mark.svg"
LOGO_ICON_PATH = PROJECT_ROOT / "app" / "assets" / "gateway_icon.svg"
AUTHOR_AVATAR_PATH = PROJECT_ROOT / "app" / "assets" / "author_avatar.png"
OWNER_NAME = "Ryan Johnson"
OWNER_EMAIL = "rmckayjohnson2021@gmail.com"
GITHUB_PROFILE_URL = "https://github.com/rmckayjohnson2021"
REPO_URL = "https://github.com/rmckayjohnson2021/llm-cost-eval-gateway"
COMPANION_REPO_URL = "https://github.com/rmckayjohnson2021/team-ai-incident-triage"


st.set_page_config(
    page_title="LLM cost gateway",
    page_icon=str(LOGO_ICON_PATH),
    layout="wide",
)


def apply_runbookops_style() -> None:
    st.html(
        """
        <style>
          .stApp {
            background:
              radial-gradient(circle at 24% 8%, rgba(0, 229, 255, 0.08), transparent 28rem),
              radial-gradient(circle at 82% 0%, rgba(0, 114, 255, 0.08), transparent 30rem),
              #0B0F17;
          }
          [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #080C12 0%, #0B111C 100%);
            border-right: 1px solid #1F2937;
          }
          [data-testid="stSidebar"] [data-testid="stMetric"] {
            background: #080C12;
          }
          [data-testid="stMetric"],
          [data-testid="stVerticalBlockBorderWrapper"] {
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
          }
          [data-testid="stMetricLabel"] p {
            color: #CBD5E1;
            font-weight: 650;
          }
          [data-testid="stMetricValue"] {
            color: #F8FAFC;
          }
          [data-testid="stBaseButton-primary"] {
            box-shadow: 0 0 28px rgba(0, 229, 255, 0.22);
          }
        </style>
        """
    )


@st.cache_data(ttl=5)
def load_usage(path: str) -> list[dict]:
    return fetch_usage(path)


def money(value: float) -> str:
    if abs(value) >= 1000:
        return f"${value:,.0f}"
    if abs(value) >= 10:
        return f"${value:,.2f}"
    return f"${value:.6f}"


def usage_dataframe(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def summary_dataframe(rows: list[dict], group_by: str) -> pd.DataFrame:
    return pd.DataFrame(summarize_usage(rows, group_by))


def filter_by_window(df: pd.DataFrame, window: str) -> pd.DataFrame:
    if df.empty or window == "All time" or "created_at" not in df.columns:
        return df

    created_at = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    start_by_window = {
        "Last hour": datetime.now(UTC) - timedelta(hours=1),
        "Last 24 hours": datetime.now(UTC) - timedelta(days=1),
        "Last 7 days": datetime.now(UTC) - timedelta(days=7),
        "Last 30 days": datetime.now(UTC) - timedelta(days=30),
    }
    return df.loc[created_at >= start_by_window[window]].copy()


def spend_trend(df: pd.DataFrame, window: str) -> pd.DataFrame:
    if df.empty or "created_at" not in df.columns:
        return pd.DataFrame(columns=["period", "estimated_cost_usd"])

    working = df.copy()
    working["created_at"] = pd.to_datetime(working["created_at"], errors="coerce", utc=True)
    working = working.dropna(subset=["created_at"])
    if working.empty:
        return pd.DataFrame(columns=["period", "estimated_cost_usd"])

    frequency = "h" if window in {"Last hour", "Last 24 hours"} else "D"
    working["period"] = working["created_at"].dt.floor(frequency)
    return working.groupby("period", as_index=False)["estimated_cost_usd"].sum().sort_values("period")


def observed_days(df: pd.DataFrame, window: str) -> float | None:
    if df.empty or "created_at" not in df.columns:
        return None
    if window == "Last hour":
        return 1 / 24
    if window == "Last 24 hours":
        return 1
    if window == "Last 7 days":
        return 7
    if window == "Last 30 days":
        return 30

    created_at = pd.to_datetime(df["created_at"], errors="coerce", utc=True).dropna()
    if created_at.empty:
        return None
    return max((created_at.max() - created_at.min()).total_seconds() / 86400, 1)


def run_rate(value: float, days: float | None, target_days: float) -> float:
    if not days:
        return 0.0
    return value / days * target_days


def top_cost_driver(summary: pd.DataFrame, label_column: str) -> str:
    if summary.empty:
        return "-"
    top = summary.sort_values("estimated_cost_usd", ascending=False).iloc[0]
    return f"{top[label_column]} ({money(float(top['estimated_cost_usd']))})"


def render_sidebar(total_rows: int, incident_summary: pd.DataFrame) -> None:
    with st.sidebar:
        st.image(str(LOGO_MARK_PATH), width=74)
        st.header("CostOps Gateway", icon=":material/account_tree:", help="Execution gateway for model routing and cost evaluation.")
        st.caption("LLM spend intelligence")

        st.subheader("System overview", icon=":material/monitoring:")
        left, right = st.columns(2)
        left.metric("Rows", total_rows, help="Usage ledger rows loaded by the dashboard.", icon=":material/database:", border=True)
        right.metric(
            "Types",
            len(incident_summary),
            help="Distinct incident types represented in the selected ledger.",
            icon=":material/category:",
            border=True,
        )
        left.metric(
            "Top cost",
            top_cost_driver(incident_summary, "incident_type"),
            help="Highest-cost incident type in the selected data.",
            icon=":material/paid:",
            border=True,
        )
        right.metric(
            "Coverage",
            "5/5" if len(incident_summary) >= 5 else f"{len(incident_summary)}/5",
            help="Demo coverage across the five RunbookOps incident categories.",
            icon=":material/hub:",
            border=True,
        )

        st.subheader("Controls", icon=":material/tune:")
        st.toggle("Authenticated API", value=True, disabled=True, help="The /v1 endpoints require X-Gateway-API-Key.")
        st.toggle("Usage ledger", value=True, disabled=True, help="Each request writes cost, route, status, model, and incident type.")
        st.toggle("Savings model", value=True, disabled=True, help="The dashboard estimates savings against a strong-only baseline.")

        st.subheader("Builder", icon=":material/person:")
        author_image, author_text = st.columns([0.34, 0.66], vertical_alignment="center")
        if AUTHOR_AVATAR_PATH.exists():
            author_image.image(str(AUTHOR_AVATAR_PATH), width=82)
        author_text.markdown(f"**{OWNER_NAME}**")
        author_text.caption("AI workflow builder")
        st.markdown(f"[GitHub]({GITHUB_PROFILE_URL})")
        st.markdown(f"[Repository]({REPO_URL})")


def render_header(row_count: int, spend_window: str) -> None:
    st.image(str(LOGO_PATH), width=360)
    st.title("CostOps Gateway", icon=":material/query_stats:")
    st.caption(f"Gateway dashboard | {row_count} ledger rows | Window: {spend_window}")
    st.space("small")


def render_empty_state(selected_ledger_path: str) -> None:
    with st.container(border=True):
        st.subheader("No usage rows yet", icon=":material/info:")
        st.write("Run the projected ledger seed script, demo, or API calls to populate the dashboard.")
        st.code(
            "C:\\Users\\rmcka\\.local\\bin\\uv.exe run python examples\\seed_projected_ledger.py",
            language="powershell",
        )
        st.caption(f"Ledger source: `{os.path.abspath(selected_ledger_path)}`")


def render_dashboard(filtered_df: pd.DataFrame, filtered_rows: list[dict], spend_window: str) -> None:
    savings = summarize_optimization_savings(filtered_rows)
    total_cost = float(filtered_df["estimated_cost_usd"].sum()) if not filtered_df.empty else 0.0
    total_calls = len(filtered_df)
    human_reviews = int((filtered_df["status"] == "human_review").sum()) if not filtered_df.empty else 0
    failed_or_blocked = int(filtered_df["status"].isin(["failed", "blocked"]).sum()) if not filtered_df.empty else 0
    days = observed_days(filtered_df, spend_window)
    monthly_savings = run_rate(float(savings["estimated_savings_usd"]), days, 30.4375)
    annual_savings = run_rate(float(savings["estimated_savings_usd"]), days, 365)

    route_summary = summary_dataframe(filtered_rows, "route")
    model_summary = summary_dataframe(filtered_rows, "model")
    incident_summary = summary_dataframe(filtered_rows, "incident_type")
    status_summary = summary_dataframe(filtered_rows, "status")

    with st.container(horizontal=True):
        st.metric("Calls", f"{total_calls}", border=True)
        st.metric("Estimated cost", money(total_cost), border=True)
        st.metric("Strong-only baseline", money(float(savings["strong_baseline_cost_usd"])), border=True)
        st.metric("Routing savings", money(float(savings["estimated_savings_usd"])), border=True)
        st.metric("Savings rate", f"{float(savings['savings_rate']):.1%}", border=True)
        st.metric("Monthly savings run rate", money(monthly_savings), border=True)
        st.metric("Annualized savings", money(annual_savings), border=True)
        st.metric("Human reviews", f"{human_reviews}", border=True)
        st.metric("Failed or blocked", f"{failed_or_blocked}", border=True)

    left, right = st.columns([0.6, 0.4], gap="large")
    with left, st.container(border=True):
        st.subheader("Spend trend", icon=":material/query_stats:")
        trend = spend_trend(filtered_df, spend_window)
        if trend.empty:
            st.caption("No timestamped spend rows in this window.")
        else:
            st.bar_chart(trend, x="period", y="estimated_cost_usd")

    with right, st.container(border=True):
        st.subheader("Cost by incident type", icon=":material/category:")
        if incident_summary.empty:
            st.caption("No incident type rows available.")
        else:
            chart_data = incident_summary.sort_values("estimated_cost_usd", ascending=False)
            st.bar_chart(chart_data, x="incident_type", y="estimated_cost_usd")

    left, right = st.columns(2, gap="large")
    with left, st.container(border=True):
        st.subheader("Calls by model", icon=":material/smart_toy:")
        st.bar_chart(model_summary, x="model", y="calls")

    with right, st.container(border=True):
        st.subheader("Calls by route", icon=":material/alt_route:")
        st.bar_chart(route_summary, x="route", y="calls")

    with st.container(border=True):
        st.subheader("Usage summaries", icon=":material/table_chart:")
        tabs = st.tabs(["By incident type", "By route", "By model", "By status"])
        for tab, summary in (
            (tabs[0], incident_summary),
            (tabs[1], route_summary),
            (tabs[2], model_summary),
            (tabs[3], status_summary),
        ):
            with tab:
                st.dataframe(
                    summary,
                    hide_index=True,
                    column_config={
                        "estimated_cost_usd": st.column_config.NumberColumn(
                            "Estimated cost",
                            format="$%.6f",
                        ),
                        "median_latency_ms": st.column_config.NumberColumn(
                            "Median latency",
                            format="%d ms",
                        ),
                    },
                )

    with st.container(border=True):
        st.subheader("Raw usage ledger", icon=":material/database:")
        st.dataframe(
            filtered_df,
            hide_index=True,
            column_config={
                "created_at": st.column_config.DatetimeColumn("Created", format="MMM DD, YYYY h:mm a"),
                "estimated_cost_usd": st.column_config.NumberColumn("Estimated cost", format="$%.6f"),
                "reserved_cost_usd": st.column_config.NumberColumn("Reserved cost", format="$%.6f"),
                "latency_ms": st.column_config.NumberColumn("Latency", format="%d ms"),
            },
        )


def render_footer() -> None:
    with st.container(border=True):
        left, right = st.columns([0.48, 0.52], gap="large", vertical_alignment="center")
        with left:
            st.caption("Project artifact")
            st.markdown(f"**{OWNER_NAME}** | [Email](mailto:{OWNER_EMAIL}) | [GitHub]({GITHUB_PROFILE_URL})")
        with right:
            st.caption(
                f"[Source repository]({REPO_URL}) | [Companion triage app]({COMPANION_REPO_URL})",
                text_alignment="right",
            )


apply_runbookops_style()

with st.sidebar:
    selected_ledger_path = st.text_input(
        "Ledger path",
        value=ledger_path(),
        help="SQLite usage ledger generated by the gateway executor, API, demo, or projected seed script.",
    )
    spend_window = st.selectbox(
        "Spend window",
        ["All time", "Last hour", "Last 24 hours", "Last 7 days", "Last 30 days"],
        index=4,
        help="Filter spend, savings, charts, and ledger rows to a recent time window.",
    )
    if st.button("Refresh data", icon=":material/refresh:", width="stretch"):
        load_usage.clear()
        st.toast("Dashboard data refreshed.", icon=":material/check_circle:")

rows = load_usage(selected_ledger_path)
df = usage_dataframe(rows)
filtered_df = filter_by_window(df, spend_window)
filtered_rows = filtered_df.to_dict("records")
incident_summary = summary_dataframe(filtered_rows, "incident_type")

render_sidebar(len(filtered_rows), incident_summary)
render_header(len(filtered_rows), spend_window)

if not rows:
    render_empty_state(selected_ledger_path)
else:
    render_dashboard(filtered_df, filtered_rows, spend_window)

render_footer()
st.caption(f"Ledger source: `{os.path.abspath(selected_ledger_path)}`")
