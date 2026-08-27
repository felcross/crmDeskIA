"""
CSV Analysis Service — ported from financebot_br/analista.py.

Strips Streamlit dependencies; returns structured JSON for API consumption.
Uses pandas for CSV parsing, DuckDB for SQL execution, and LangChain Groq for LLM suggestions.
"""

import io
import json
import logging
import re

import duckdb
import pandas as pd
from langchain_groq import ChatGroq

from app.config import settings

log = logging.getLogger(__name__)

MAX_CATEGORIAS = 15


# ══════════════════════════════════════════════════════════════════════════════
# 1. CSV ANALYSIS — rich context generation
# ══════════════════════════════════════════════════════════════════════════════


def _detect_and_convert_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Try to convert text columns that look like dates.
    Formats tried: dd/mm/yyyy, yyyy-mm-dd, dd-mm-yyyy, mm/dd/yyyy, then inference.
    Only converts if >= 80% of sample values are valid dates.
    """
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]
    df = df.copy()

    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().head(20).astype(str)
        converted = False

        for fmt in formats:
            try:
                attempt = pd.to_datetime(sample, format=fmt, errors="coerce")
                if attempt.notna().mean() >= 0.8:
                    df[col] = pd.to_datetime(df[col], format=fmt, errors="coerce")
                    converted = True
                    log.info("Column '%s' converted to date with format '%s'", col, fmt)
                    break
            except Exception:
                continue

        if not converted:
            try:
                attempt = pd.to_datetime(sample, errors="coerce")
                if attempt.notna().mean() >= 0.8:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    log.info("Column '%s' converted via automatic inference", col)
            except Exception:
                pass

    return df


def _stats_numeric(series: pd.Series) -> dict:
    s = series.dropna()
    return {
        "min": round(float(s.min()), 4) if not s.empty else None,
        "max": round(float(s.max()), 4) if not s.empty else None,
        "mean": round(float(s.mean()), 4) if not s.empty else None,
        "nulls": int(series.isna().sum()),
    }


def _stats_categorical(series: pd.Series) -> dict:
    uniques = series.dropna().unique().tolist()
    return {
        "n_unique": len(uniques),
        "values": [str(v) for v in uniques[:MAX_CATEGORIAS]],
        "truncated": len(uniques) > MAX_CATEGORIAS,
        "nulls": int(series.isna().sum()),
    }


def _stats_date(series: pd.Series) -> dict:
    s = series.dropna()
    if s.empty:
        return {"min": None, "max": None, "nulls": int(series.isna().sum())}
    fmt = lambda v: str(v.date()) if hasattr(v, "date") else str(v)
    return {"min": fmt(s.min()), "max": fmt(s.max()), "nulls": int(series.isna().sum())}


def analyze_csv(df: pd.DataFrame) -> dict:
    """Analyze DataFrame and return structured context with types, stats, column groups."""
    df = _detect_and_convert_dates(df)

    ctx: dict = {
        "df_converted": df,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": {},
        "date_columns": [],
        "numeric_columns": [],
        "categorical_columns": [],
    }

    for col in df.columns:
        dtype = df[col].dtype

        if pd.api.types.is_datetime64_any_dtype(dtype):
            ctx["columns"][col] = {"type": "date", **_stats_date(df[col])}
            ctx["date_columns"].append(col)

        elif pd.api.types.is_numeric_dtype(dtype):
            ctx["columns"][col] = {"type": "numeric", **_stats_numeric(df[col])}
            ctx["numeric_columns"].append(col)

        else:
            stats = _stats_categorical(df[col])
            col_type = "categorical" if stats["n_unique"] <= MAX_CATEGORIAS else "text"
            ctx["columns"][col] = {"type": col_type, **stats}
            ctx["categorical_columns"].append(col)

    ctx["has_date"] = len(ctx["date_columns"]) > 0
    ctx["has_numeric"] = len(ctx["numeric_columns"]) > 0
    return ctx


# ══════════════════════════════════════════════════════════════════════════════
# 2. SCHEMA FOR LLM
# ══════════════════════════════════════════════════════════════════════════════


def build_schema_llm(context: dict) -> str:
    """Transform context into descriptive text for the LLM."""
    lines = [
        "You have access to a DuckDB table called 'dados':\n",
        f"  Rows    : {context['n_rows']:,}",
        f"  Columns : {context['n_cols']}\n",
        "  Columns:",
    ]

    for col, info in context["columns"].items():
        col_type = info["type"]
        if col_type == "date":
            lines.append(
                f"    - {col}  [DATE]  from {info['min']} to {info['max']}  |  {info['nulls']} nulls"
            )
        elif col_type == "numeric":
            lines.append(
                f"    - {col}  [NUMBER]  min={info['min']}  max={info['max']}  mean={info['mean']}  |  {info['nulls']} nulls"
            )
        elif col_type == "categorical":
            vals = ", ".join(f'"{v}"' for v in info["values"])
            extra = "  (+ others)" if info["truncated"] else ""
            lines.append(
                f"    - {col}  [CATEGORY]  {info['n_unique']} values: {vals}{extra}  |  {info['nulls']} nulls"
            )
        else:
            lines.append(
                f"    - {col}  [TEXT]  {info['n_unique']} unique values  |  {info['nulls']} nulls"
            )

    lines += [
        "",
        "  SQL Rules:",
        "    1. Table is exactly 'dados'.",
        "    2. Use column names exactly as listed.",
        "    3. CATEGORY values are case-sensitive — use exactly as listed.",
        "    4. For DATE use CAST(col AS DATE) if needed.",
        "    5. Return at most 50 rows. Use ORDER BY + LIMIT.",
        "    6. Never invent columns.",
    ]

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# 3. LLM SUGGESTION GENERATION
# ══════════════════════════════════════════════════════════════════════════════


def _get_llm() -> ChatGroq:
    return ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key)


def generate_suggestions(context: dict) -> list[dict]:
    """Call Groq and return 4 analysis suggestions as structured JSON."""
    llm = _get_llm()
    schema = build_schema_llm(context)
    df = context["df_converted"]
    sample = df.head(5).to_string(index=False)

    prompt = f"""You are a data analyst expert in SQL and DuckDB.
Analyze the schema and sample below and generate EXACTLY 4 relevant analysis suggestions.

{schema}

Sample (first 5 rows):
{sample}

Return ONLY a valid JSON array. No markdown, no text before or after.
Each object must have exactly these fields:
{{
  "titulo":    "short name",
  "descricao": "what this analysis reveals",
  "sql":       "SELECT ... FROM dados ... LIMIT 50",
  "grafico":   "line" | "bar" | "none",
  "x":         "column_x or null",
  "y":         "column_y or null"
}}

Critical rules:
- "line" ONLY if X is a DATE column and Y is numeric.
- "bar"  ONLY if X is CATEGORY and Y is numeric.
- "none" when in doubt — better "none" than a wrong chart.
- x and y must be EXACTLY the aliases/names that appear in the resulting SELECT.
- Vary analysis types: don't repeat the same grouping 4 times.
- SQL must work in DuckDB — no MySQL/PostgreSQL-only functions.

JSON:"""

    try:
        response = llm.invoke(prompt)
        text = response.content.strip()
        text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()

        suggestions = json.loads(text)

        required_fields = {"titulo", "descricao", "sql", "grafico", "x", "y"}
        valid = []
        for s in suggestions:
            if isinstance(s, dict) and required_fields.issubset(s.keys()):
                if s["grafico"] not in ("line", "bar", "none"):
                    s["grafico"] = "none"
                    s["x"] = None
                    s["y"] = None
                valid.append(s)

        log.info("Suggestions generated: %d", len(valid))
        return valid

    except json.JSONDecodeError as e:
        log.error("Invalid JSON from LLM: %s", e)
        return []
    except Exception as e:
        log.error("Error generating suggestions: %s", e)
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 4. SQL EXECUTION & CHART VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


def execute_suggestion(suggestion: dict, df: pd.DataFrame) -> tuple[pd.DataFrame | None, str | None]:
    """Execute suggestion SQL against DuckDB in-memory. CSV never touches persistent DB."""
    sql = suggestion.get("sql", "").strip()
    if not sql:
        return None, "Empty SQL in suggestion."
    try:
        con = duckdb.connect(":memory:")
        con.register("dados", df)
        result = con.execute(sql).df()
        con.close()
        return result, None
    except Exception as e:
        log.warning("Error executing '%s': %s", suggestion.get("titulo"), e)
        return None, str(e)


def _validate_chart(suggestion: dict, df: pd.DataFrame) -> tuple[bool, str]:
    """Check if chart is viable given actual result data."""
    chart_type = suggestion.get("grafico", "none")
    col_x = suggestion.get("x")
    col_y = suggestion.get("y")

    if chart_type == "none":
        return False, ""

    if df is None or df.empty:
        return False, "Not enough data for chart."

    cols = df.columns.tolist()

    if col_x and col_x not in cols:
        return False, f"Column '{col_x}' not found in result."

    if col_y and col_y not in cols:
        return False, f"Column '{col_y}' not found in result."

    if col_y and not pd.api.types.is_numeric_dtype(df[col_y]):
        return False, f"Column '{col_y}' is not numeric — cannot use as Y axis."

    if chart_type == "line" and len(df) < 3:
        return False, "Insufficient points for line chart (minimum 3)."

    if chart_type == "bar" and len(df) < 2:
        return False, "Insufficient categories for bar chart (minimum 2)."

    return True, ""


def _build_chart_config(suggestion: dict, df: pd.DataFrame) -> dict | None:
    """Build a chart configuration dict for frontend rendering."""
    viable, _ = _validate_chart(suggestion, df)
    if not viable:
        return None

    col_x = suggestion["x"]
    col_y = suggestion["y"]
    chart_type = suggestion["grafico"]

    x_values = df[col_x].astype(str).tolist()
    y_values = df[col_y].tolist()

    return {
        "type": chart_type,
        "title": suggestion.get("titulo", ""),
        "x_axis": col_x,
        "y_axis": col_y,
        "labels": x_values,
        "data": y_values,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. PUBLIC API — orchestrates full pipeline
# ══════════════════════════════════════════════════════════════════════════════


def parse_csv(file_bytes: bytes) -> pd.DataFrame:
    """Parse CSV bytes into a DataFrame."""
    return pd.read_csv(io.BytesIO(file_bytes))


def analyze_and_suggest(file_bytes: bytes) -> dict:
    """Full pipeline: parse CSV → analyze → generate suggestions → execute → build charts.

    Returns:
        {
            "suggestions": list[str],   # suggestion titles/descriptions
            "charts": list[dict],       # chart configs for frontend
            "summary": str              # text summary of the dataset
        }
    """
    df = parse_csv(file_bytes)
    context = analyze_csv(df)

    # Build summary
    summary_parts = [
        f"Dataset with {context['n_rows']:,} rows and {context['n_cols']} columns.",
    ]
    if context["date_columns"]:
        summary_parts.append(f"Date columns: {', '.join(context['date_columns'])}.")
    if context["numeric_columns"]:
        summary_parts.append(f"Numeric columns: {', '.join(context['numeric_columns'])}.")
    if context["categorical_columns"]:
        summary_parts.append(f"Categorical columns: {', '.join(context['categorical_columns'])}.")
    summary = " ".join(summary_parts)

    # Generate LLM suggestions
    raw_suggestions = generate_suggestions(context)

    suggestion_texts = []
    charts = []

    for s in raw_suggestions:
        title = s.get("titulo", "Untitled")
        desc = s.get("descricao", "")
        suggestion_texts.append(f"{title}: {desc}")

        result_df, error = execute_suggestion(s, context["df_converted"])
        if error:
            log.warning("Suggestion '%s' execution failed: %s", title, error)
            continue

        if result_df is not None and not result_df.empty:
            chart_config = _build_chart_config(s, result_df)
            if chart_config:
                charts.append(chart_config)

    return {
        "suggestions": suggestion_texts,
        "charts": charts,
        "summary": summary,
    }
