# Data breaches in Washington: simple dashboard

A one-file Streamlit dashboard (app.py, about 190 lines) in the same style as the sample you were given:
sidebar filters, four headline numbers, five tabs, plain-English captions, a table with a download button.

Run it:
    pip install -r requirements.txt
    python -m streamlit run app.py

Keep washington_data_breaches_clean_imputed.csv in the same folder as app.py.

Tabs: Overview, Who is affected, How it happened, Response time, Data and notes.
Filters: report years, sectors, causes.

Data: Washington State Office of the Attorney General, Data Breach Notifications Affecting Washington Residents (data.wa.gov), snapshot 3 November 2026.
https://data.wa.gov/Consumer-Protection/Data-Breach-Notifications-Affecting-Washington-Res/sb4j-ca4h

Reminder: your brief asks for Task 1 in one Colab notebook, and says AI help must be rewritten into your own work and acknowledged.
Read every line of app.py until you can explain it; every step is commented.
