from app import create_app, db
from app.services.performance_import_service import import_performance
app = create_app()
with app.app_context():
    result = import_performance('''JULY  31ST, 2026
MIKINDANI UREMBO COLLECTIONS,
Dear Partner,
PARTNER PERFORMANCE REPORT AS AT 31ST JULY 2026
We appreciate your continued partnership and for signing up to the Partner Model.
As communicated earlier, you are entitled to a back margin commission of 3.75%, which is earned based on performance against the three key KPIs outlined below.
To earn 3.75% Back Margin, you will be required to do the following.
*              2,000+ Gross Adds,
*              2,000+ SIM Billing,
*              100% Active AM Agents (Mapped agents with 5 CICO Transactions & Ksh 1,000 Value)
Signed Contract Status: WITH LEGAL
KPI
MTD
Back Margin Rate
Partner Gross Adds
934
0.0075
Sim Kits Billing
2000
0.0075
% Active Agents
0.7800
0.0075
Back Margin Rate
0.0225
0.0225
Primaries Purchased
244999.99999260603
Agent Led Airtime (Direct)
408908
Retailer Influenced Self Recharges
111532
''')
    print(result)

