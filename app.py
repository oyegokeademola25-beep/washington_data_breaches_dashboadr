from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Data breaches in Washington", layout="wide")

# A little styling: plain white cards for the headline numbers and softer filter tags.
st.markdown("""
<style>
.block-container { padding-top: 2.2rem; max-width: 1250px; }
div[data-testid="stMetric"] { background:#FFFFFF; border:1px solid #DDE2EA; border-radius:6px; padding:14px 18px; }
div[data-testid="stMetricLabel"] p { font-size:0.85rem; color:#5B6676; }
div[data-testid="stMetricValue"] { font-size:1.8rem; color:#14304F; }
span[data-baseweb="tag"] { background:#DCE6F2 !important; color:#1B2430 !important; }
h1 { color:#14304F; font-size:2.1rem; margin-bottom:0; }
.standfirst { color:#5B6676; font-size:1.05rem; margin:4px 0 18px 0; }
</style>
""", unsafe_allow_html=True)

# A small, restrained palette: blue for most charts, orange only where something needs attention.
BLUE, TEAL, ORANGE, GREY, RED = "#1F5FA8", "#2F8F83", "#D9822B", "#A3ADBA", "#B42318"


# Read the file once. Streamlit keeps the result ready when a filter changes.
@st.cache_data
def load_data():
    path = Path(__file__).parent / "washington_data_breaches_clean_imputed.csv"
    df = pd.read_csv(path, parse_dates=["DateSubmitted"])
    # Keep the columns we need and give them short, readable names.
    df = df.rename(columns={"Name": "Organisation", "ReportYear": "Year", "IndustryType": "Sector", "DataBreachCause": "Cause",
                            "CyberattackType": "Attack", "WashingtoniansAffected": "Residents",
                            "DaysElapsedBeforeNotification": "Days to notify", "NotifiedWithinDeadline": "On time"})
    df["Attack"] = df["Attack"].replace({"Not applicable (not a cyberattack)": "Not a cyberattack"})
    df["Year status"] = df["PartialYear"].map({True: "Incomplete year", False: "Complete year"})
    columns = ["Organisation", "DateSubmitted", "Year", "Year status", "Sector", "Cause", "Attack", "Residents", "SizeBand",
               "Days to notify", "On time", "IsCyberattack", "IsRansomware"]
    return df[columns]


def show(fig):
    """Draw a chart with the same tidy layout everywhere."""
    fig.update_layout(template="plotly_white", margin=dict(t=50, b=10, l=10, r=10), legend_title_text="", title_x=0,
                      title_font_size=16, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")


st.title("Data breaches in Washington")
st.markdown('<div class="standfirst">Breach notifications filed with the Washington Attorney General: who was affected, '
            'how it happened and how quickly it was reported.</div>', unsafe_allow_html=True)
try:
    df = load_data()
except (OSError, ValueError) as error:
    st.error(f"Could not read the dataset: {error}")
    st.info("Keep washington_data_breaches_clean_imputed.csv in the same folder as app.py.")
    st.stop()

# Choose the rows to use throughout the dashboard.
st.sidebar.header("Filters")
years = st.sidebar.slider("Report years", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
sector_names = sorted(df["Sector"].unique())
cause_names = sorted(df["Cause"].unique())
sectors = st.sidebar.multiselect("Sectors", sector_names, default=sector_names)
causes = st.sidebar.multiselect("Causes", cause_names, default=cause_names)
st.sidebar.caption("Everything is selected at the start. Remove names to narrow the view.")

selected = df[
    df["Year"].between(years[0], years[1])
    & df["Sector"].isin(sectors)
    & df["Cause"].isin(causes)
].copy()

if selected.empty:
    st.warning("No breaches match these choices. Select at least one sector and one cause, or widen the years.")
    st.stop()

st.caption(f"Report years {years[0]}–{years[1]} · {len(selected):,} breaches selected. "
           "A report year runs from late July to late July, and the latest year is not finished yet.")

# The four headline numbers use the same selected rows as the charts.
cyber = selected[selected["IsCyberattack"]]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Breaches", f"{len(selected):,}")
c2.metric("Residents affected", f"{selected['Residents'].sum():,.0f}", help="A person can be counted in more than one breach.")
c3.metric("Median days to report", f"{selected['Days to notify'].median():.0f}", help="Days between the organisation finding out and telling the Attorney General.")
c4.metric("Ransomware share", f"{cyber['IsRansomware'].mean() * 100:.0f}%" if len(cyber) else "n/a", help="Share of cyberattacks that were ransomware.")

# Prepare the small tables that the charts will use.
per_year = selected.groupby(["Year", "Year status"], as_index=False).size().rename(columns={"size": "Breaches"})
per_sector = selected.groupby("Sector", as_index=False).agg(Breaches=("Organisation", "count"), Total=("Residents", "sum"), Typical=("Residents", "median"))

overview, affected, how, response, data_tab = st.tabs(["Overview", "Who is affected", "How it happened", "Response time", "Data and notes"])

with overview:
    st.subheader("How are breaches changing?")
    left, right = st.columns(2)
    with left:
        fig = px.bar(per_year, x="Year", y="Breaches", color="Year status", title="Breaches reported each year",
                     color_discrete_map={"Complete year": BLUE, "Incomplete year": GREY})
        fig.update_xaxes(dtick=1)
        show(fig)
    with right:
        fig = px.bar(per_sector.sort_values("Breaches"), x="Breaches", y="Sector", orientation="h", title="Breaches by sector",
                     color_discrete_sequence=[BLUE])
        show(fig)
    best_year = per_year.loc[per_year["Breaches"].idxmax()]
    best_sector = per_sector.loc[per_sector["Breaches"].idxmax()]
    biggest = selected.loc[selected["Residents"].idxmax()]
    st.subheader("What stands out")
    st.write(f"• Most breaches were reported in report year {int(best_year['Year'])} ({int(best_year['Breaches'])} breaches).")
    st.write(f"• {best_sector['Sector']} had the most breaches ({int(best_sector['Breaches'])}).")
    st.write(f"• The largest single breach affected {biggest['Residents']:,.0f} residents ({biggest['Organisation']}).")
    st.caption("These are observations from the selected records. The charts alone do not explain why numbers changed.")

with affected:
    st.subheader("How many residents are affected?")
    measure = st.radio("Show", ["Total residents", "Typical breach (median)"], horizontal=True)
    column = "Total" if measure == "Total residents" else "Typical"
    left, right = st.columns(2)
    with left:
        fig = px.bar(per_sector.sort_values(column), x=column, y="Sector", orientation="h", title=f"{measure} by sector",
                     labels={column: "Residents"}, color_discrete_sequence=[TEAL])
        show(fig)
    with right:
        order = ["Under 1k", "1k-9.9k", "10k-49.9k", "50k-999k", "1M+"]
        sizes = selected["SizeBand"].value_counts().reindex(order, fill_value=0).reset_index()
        sizes.columns = ["Size of breach", "Breaches"]
        fig = px.bar(sizes, x="Size of breach", y="Breaches", title="Breaches by size (residents affected)", color_discrete_sequence=[BLUE])
        show(fig)
    st.caption("Most breaches are small. A handful of very large breaches make up much of the total, so the median shows the typical case better than the total.")
    st.subheader("The ten largest breaches")
    top = selected.nlargest(10, "Residents")[["Organisation", "Year", "Sector", "Attack", "Residents"]]
    st.dataframe(top, hide_index=True, width="stretch", column_config={"Residents": st.column_config.NumberColumn(format="localized")})

with how:
    st.subheader("How do breaches happen?")
    left, right = st.columns(2)
    with left:
        causes_count = selected["Cause"].value_counts().reset_index()
        causes_count.columns = ["Cause", "Breaches"]
        fig = px.pie(causes_count, names="Cause", values="Breaches", hole=0.45, title="What caused the breaches", color_discrete_sequence=[BLUE, TEAL, GREY])
        show(fig)
    with right:
        if cyber.empty:
            st.info("No cyberattacks in this selection.")
        else:
            attacks = cyber["Attack"].value_counts().sort_values().reset_index()
            attacks.columns = ["Attack type", "Breaches"]
            fig = px.bar(attacks, x="Breaches", y="Attack type", orientation="h", title="Which kinds of cyberattack", color_discrete_sequence=[BLUE])
            show(fig)
    ransom = cyber[cyber["Year status"] == "Complete year"].groupby("Year")["IsRansomware"].mean().mul(100).reset_index(name="Ransomware %")
    if len(ransom) > 1:
        fig = px.line(ransom, x="Year", y="Ransomware %", markers=True, title="Ransomware as a share of cyberattacks (complete years only)", color_discrete_sequence=[ORANGE])
        fig.update_xaxes(dtick=1)
        show(fig)
    st.caption("Ransomware is software that locks an organisation's data until a ransom is paid. The data shows how often it was reported, not why it became more common.")

with response:
    st.subheader("How quickly do organisations report?")
    on_time = selected["On time"].mean() * 100
    a, b = st.columns(2)
    a.metric("Reported within the legal deadline", f"{on_time:.0f}%",
             help="The deadline was 45 days before 1 March 2020 and 30 days after. Treat this as an estimate.")
    b.metric("Slowest 10% took more than", f"{selected['Days to notify'].quantile(0.9):.0f} days")
    bins = st.slider("Histogram bins (approximate)", 5, 60, 30)
    fig = px.histogram(selected.assign(**{"Days to notify": selected["Days to notify"].clip(upper=180)}), x="Days to notify", nbins=bins,
                       title="Days from discovery to report (anything over 180 shown as 180)", color_discrete_sequence=[TEAL])
    fig.add_vline(x=30, line_dash="dash", line_color=RED, annotation_text="30-day deadline")
    fig.update_layout(yaxis_title="Number of breaches")
    show(fig)
    fig = px.box(selected, x="Sector", y="Days to notify", title="Days to report, by sector", color_discrete_sequence=[BLUE], points=False)
    fig.update_yaxes(range=[0, selected["Days to notify"].quantile(0.95)])
    show(fig)
    st.caption("Each box shows the middle half of breaches in a sector; the line inside is the median. Reasons for delay are not recorded in the data.")

with data_tab:
    st.subheader("Check the rows behind the charts")
    st.write("The table shows the selected breaches. Click a column heading to sort it.")
    columns = ["Organisation", "DateSubmitted", "Sector", "Cause", "Attack", "Residents", "Days to notify"]
    st.dataframe(selected[columns], hide_index=True, width="stretch", column_config={"DateSubmitted": st.column_config.DateColumn("Date reported"),
                                                                                     "Residents": st.column_config.NumberColumn(format="localized")})
    st.download_button("Download these rows as CSV", data=selected[columns].to_csv(index=False).encode("utf-8"), file_name="selected_breaches.csv", mime="text/csv")

    st.subheader("About this data")
    st.write("Source: Washington State Office of the Attorney General, Data Breach Notifications Affecting Washington Residents "
             "(data.wa.gov), snapshot 3 November 2026. Organisations must report breaches affecting more than 500 Washington residents.")
    st.write("The data was cleaned in the Colab notebook: formats fixed, impossible values corrected and some missing values estimated "
             "(about 19% of rows contain an estimate). Counts show reported breaches only and do not prove causes.")
    st.write("Residents affected is counted per breach, so a person can appear in more than one breach.")
