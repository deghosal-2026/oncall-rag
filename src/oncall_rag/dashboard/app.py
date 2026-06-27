from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path("data")
QUERIES_PATH = DATA_DIR / "queries.jsonl"
FEEDBACK_PATH = DATA_DIR / "feedback.jsonl"

st.set_page_config(page_title="Oncall RAG Dashboard", layout="wide")
st.title("Oncall RAG Dashboard")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


queries = load_jsonl(QUERIES_PATH)
feedback = load_jsonl(FEEDBACK_PATH)

tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Query Metrics", "Knowledge Gaps", "Feedback Analysis"]
)

with tab1:
    st.header("Overview")

    col1, col2, col3, col4 = st.columns(4)

    total_queries = len(queries)
    queries_today = sum(
        1
        for q in queries
        if q.get("timestamp", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    )
    total_feedback = len(feedback)
    up_count = sum(1 for f in feedback if f.get("rating") == "up")
    down_count = sum(1 for f in feedback if f.get("rating") == "down")
    feedback_ratio = f"{up_count / total_feedback:.0%}" if total_feedback else "N/A"

    col1.metric("Total Queries", total_queries)
    col2.metric("Queries Today", queries_today)
    col3.metric("Feedback Responses", total_feedback)
    col4.metric("Up Ratio", feedback_ratio)

    if queries:
        st.subheader("Recent Queries")
        df_queries = pd.DataFrame(queries)
        recent = df_queries.tail(10)[["timestamp", "question", "has_sources"]].iloc[::-1]
        st.dataframe(recent, use_container_width=True)

with tab2:
    st.header("Query Metrics")

    if queries:
        df = pd.DataFrame(queries)
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date

        st.subheader("Queries per Day")
        daily = df.groupby("date").size().reset_index(name="count")
        st.line_chart(daily.set_index("date"))

        st.subheader("Most Asked Questions")
        question_counts = Counter(q.get("question", "") for q in queries)
        top_questions = pd.DataFrame(
            question_counts.most_common(10),
            columns=["Question", "Count"],
        )
        st.bar_chart(top_questions.set_index("Question"))

        st.subheader("Sources Cited")
        source_counter: Counter = Counter()
        for q in queries:
            for src in q.get("sources", []):
                source_counter[src] += 1
        if source_counter:
            top_sources = pd.DataFrame(
                source_counter.most_common(10),
                columns=["Source", "Times Cited"],
            )
            st.bar_chart(top_sources.set_index("Source"))
    else:
        st.info("No queries recorded yet.")

with tab3:
    st.header("Knowledge Gaps")

    unanswered = [q for q in queries if not q.get("has_sources")]
    if unanswered:
        st.warning(f"{len(unanswered)} queries found no relevant runbook.")
        df_unanswered = pd.DataFrame(unanswered)
        st.dataframe(
            df_unanswered[["timestamp", "question"]],
            use_container_width=True,
        )
    else:
        st.success("All queries found relevant sources!")

    if feedback:
        st.subheader("Lowest-Rated Queries")
        downvoted = [f for f in feedback if f.get("rating") == "down"]
        if downvoted:
            df_down = pd.DataFrame(downvoted)
            st.dataframe(
                df_down[["timestamp", "question", "sources"]],
                use_container_width=True,
            )
        else:
            st.info("No downvotes recorded yet.")

with tab4:
    st.header("Feedback Analysis")

    if feedback:
        df_fb = pd.DataFrame(feedback)

        st.subheader("Source Quality Ranking")
        source_ratings: dict[str, list[int]] = defaultdict(list)
        for f in feedback:
            for src in f.get("sources", []):
                source_ratings[src].append(1 if f.get("rating") == "up" else -1)

        if source_ratings:
            rows = []
            for src, ratings in source_ratings.items():
                total = len(ratings)
                ups = sum(1 for r in ratings if r == 1)
                downs = total - ups
                score = (ups - downs) / total if total else 0
                rows.append(
                    {
                        "Source": src,
                        "Up": ups,
                        "Down": downs,
                        "Total": total,
                        "Score": f"{score:.2f}",
                    }
                )
            df_rank = pd.DataFrame(rows).sort_values("Score", ascending=False)
            st.dataframe(df_rank, use_container_width=True)

        st.subheader("Feedback Over Time")
        df_fb["date"] = pd.to_datetime(df_fb["timestamp"]).dt.date
        daily_fb = (
            df_fb.groupby(["date", "rating"])
            .size()
            .reset_index(name="count")
            .pivot(index="date", columns="rating", values="count")
            .fillna(0)
        )
        if not daily_fb.empty:
            st.line_chart(daily_fb)
    else:
        st.info("No feedback recorded yet.")
