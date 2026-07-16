"""
╔══════════════════════════════════════════════════════════════════╗
║          Retail Warehouse Analytics Dashboard                    ║
║          DEPI Graduation Project – Interactive Data App          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Path Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Dataset")

COLORS = {
    "bg":      "#0d1117",
    "card":    "#161b22",
    "border":  "#30363d",
    "accent1": "#7c3aed",
    "accent2": "#06b6d4",
    "accent3": "#f59e0b",
    "accent4": "#10b981",
    "accent5": "#f43f5e",
    "text":    "#e6edf3",
    "muted":   "#8b949e",
}

CHART_TPL = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e6edf3", family="Inter, system-ui, sans-serif"),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
    margin=dict(t=40, b=40, l=40, r=20),
    colorway=["#7c3aed","#06b6d4","#f59e0b","#10b981","#f43f5e"],
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)

print("Loading datasets...")
orders      = pd.read_csv(os.path.join(DATA_DIR,"orders.csv"))
order_items = pd.read_csv(os.path.join(DATA_DIR,"order_items.csv"))
payments    = pd.read_csv(os.path.join(DATA_DIR,"payments.csv"))
customers   = pd.read_csv(os.path.join(DATA_DIR,"customers.csv"))
products    = pd.read_csv(os.path.join(DATA_DIR,"products.csv"))
categories  = pd.read_csv(os.path.join(DATA_DIR,"categories.csv"))
stores      = pd.read_csv(os.path.join(DATA_DIR,"stores.csv"))
employees   = pd.read_csv(os.path.join(DATA_DIR,"employees.csv"))
shipments   = pd.read_csv(os.path.join(DATA_DIR,"shipments.csv"))
returns     = pd.read_csv(os.path.join(DATA_DIR,"returns.csv"))
suppliers   = pd.read_csv(os.path.join(DATA_DIR,"suppliers.csv"))
promotions  = pd.read_csv(os.path.join(DATA_DIR,"promotions.csv"))

orders["order_date"] = pd.to_datetime(orders["order_date"], format="mixed")
orders["year"]       = orders["order_date"].dt.year
orders["month"]      = orders["order_date"].dt.to_period("M").astype(str)
orders["dow"]        = orders["order_date"].dt.day_name()
customers["signup_date"] = pd.to_datetime(customers["signup_date"], format="mixed")

print("Computing aggregations...")
total_revenue   = payments["amount"].sum()
total_orders    = orders["order_id"].nunique()
total_customers = customers["customer_id"].nunique()
total_returns   = returns["return_id"].count()
return_rate     = total_returns / order_items["order_item_id"].count() * 100
avg_order_val   = total_revenue / total_orders

monthly_rev = orders.merge(payments,on="order_id")[["month","amount"]].groupby("month",as_index=False).sum().sort_values("month")
city_rev    = orders.merge(stores,on="store_id").merge(payments,on="order_id").groupby("city",as_index=False)["amount"].sum().sort_values("amount",ascending=False)
ship_status = shipments["status"].value_counts().reset_index(); ship_status.columns=["status","count"]
items_cat   = order_items.merge(products,on="product_id").merge(categories,on="category_id")
cat_rev     = items_cat.merge(orders[["order_id"]],on="order_id").merge(payments,on="order_id").groupby("category_name",as_index=False)["amount"].sum().sort_values("amount",ascending=False).head(15)
customers["month_signup"] = customers["signup_date"].dt.to_period("M").astype(str)
signups_m   = customers.groupby("month_signup").size().reset_index(name="new_customers").sort_values("month_signup")
cust_city   = customers["city"].value_counts().reset_index(); cust_city.columns=["city","count"]
emp_stores  = employees.merge(stores,on="store_id")
salary_city = emp_stores.groupby("city")["salary"].mean().reset_index(); salary_city.columns=["city","avg_salary"]
sup_country = suppliers["country"].value_counts().reset_index(); sup_country.columns=["country","count"]
scatter_s   = order_items.sample(min(3000,len(order_items)),random_state=42)
yearly_rev  = orders.merge(payments,on="order_id").groupby("year",as_index=False)["amount"].sum()
dow_orders  = orders.groupby("dow").size().reset_index(name="orders")
dow_full    = dow_orders.set_index("dow").reindex(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]).fillna(0).reset_index()
print("Done. Starting app...")

def kpi_card(icon,title,value,subtitle,color):
    return  html.Div([
        html.Div([
            html.Div(icon,style={"fontSize":"1.8rem","background":f"linear-gradient(135deg,{color},{color}88)","borderRadius":"12px","width":"52px","height":"52px","display":"flex","alignItems":"center","justifyContent":"center","boxShadow":f"0 4px 20px {color}44","flexShrink":"0"}),
            html.Div([
                html.P(title,style={"color":"#8b949e","fontSize":"0.75rem","fontWeight":"600","margin":"0","textTransform":"uppercase","letterSpacing":"0.08em"}),
                html.H3(value,style={"color":"#e6edf3","margin":"4px 0 2px","fontWeight":"700","fontSize":"1.5rem"}),
                html.P(subtitle,style={"color":"#8b949e","margin":"0","fontSize":"0.75rem"}),
            ]),
        ],style={"display":"flex","gap":"14px","alignItems":"center"}),
    ],className="kpi-card",style={"background":"#161b22","border":"1px solid #30363d","borderRadius":"16px","padding":"20px 22px","boxShadow":"0 4px 24px rgba(0,0,0,0.4)","flex":"1","minWidth":"190px","cursor":"default","transition":"transform 0.2s ease,box-shadow 0.2s ease"})

def chart_card(children,span=1):
    return html.Div(children,style={"background":"#161b22","border":"1px solid #30363d","borderRadius":"16px","padding":"20px","flex":str(span),"minWidth":"300px","boxShadow":"0 4px 24px rgba(0,0,0,0.4)"})

def section_hdr(title,sub=""):
    return html.Div([html.H5(title,style={"color":"#e6edf3","fontWeight":"700","margin":"0","fontSize":"1rem"}),html.P(sub,style={"color":"#8b949e","margin":"0","fontSize":"0.78rem"})],style={"marginBottom":"12px"})

def stat_pill(label,value,color):
    return html.Div([html.P(label,style={"margin":"0","fontSize":"0.72rem","color":"#8b949e","textTransform":"uppercase","letterSpacing":"0.06em"}),html.H5(value,style={"margin":"4px 0 0","color":color,"fontWeight":"700"})],style={"background":"#161b22","border":f"1px solid #30363d","borderLeft":f"3px solid {color}","borderRadius":"10px","padding":"12px 16px","flex":"1","minWidth":"130px"})

def fig_monthly():
    f=go.Figure(go.Scatter(x=monthly_rev["month"],y=monthly_rev["amount"],mode="lines+markers",name="Revenue",line=dict(color="#7c3aed",width=2.5),marker=dict(size=6,color="#7c3aed"),fill="tozeroy",fillcolor="rgba(124,58,237,0.13)"))
    f.update_layout(**CHART_TPL,title="Monthly Revenue Trend"); return f

def fig_city():
    f=px.bar(city_rev,x="city",y="amount",color="city",color_discrete_sequence=["#7c3aed","#06b6d4","#f59e0b","#10b981"],labels={"amount":"Revenue","city":"City"},title="Revenue by City")
    f.update_layout(**CHART_TPL); f.update_traces(marker_line_width=0); return f

def fig_ship():
    sc={"delivered":"#10b981","shipped":"#06b6d4","late":"#f43f5e"}
    colors=[sc.get(s,"#f59e0b") for s in ship_status["status"]]
    f=go.Figure(go.Pie(labels=ship_status["status"],values=ship_status["count"],hole=0.55,marker=dict(colors=colors,line=dict(width=2,color="#0d1117")),textfont=dict(color="#e6edf3",size=12),textinfo="label+percent"))
    f.update_layout(**CHART_TPL,title="Shipment Status",showlegend=False); return f

def fig_cats():
    f=px.bar(cat_rev.sort_values("amount"),x="amount",y="category_name",orientation="h",color="amount",color_continuous_scale=["#7c3aed","#06b6d4"],labels={"amount":"Revenue","category_name":"Category"},title="Top 15 Categories by Revenue")
    f.update_layout(**CHART_TPL,coloraxis_showscale=False); f.update_traces(marker_line_width=0); return f

def fig_signups():
    f=go.Figure(go.Bar(x=signups_m["month_signup"],y=signups_m["new_customers"],marker=dict(color="#06b6d4",opacity=0.85,line=dict(width=0))))
    f.update_layout(**CHART_TPL,title="New Customer Signups per Month"); return f

def fig_cust_city():
    f=go.Figure(go.Pie(labels=cust_city["city"],values=cust_city["count"],hole=0.45,marker=dict(colors=["#7c3aed","#06b6d4","#f59e0b","#10b981"],line=dict(width=2,color="#0d1117")),textfont=dict(color="#e6edf3"),textinfo="label+percent"))
    f.update_layout(**CHART_TPL,title="Customers by City",showlegend=False); return f

def fig_salary():
    f=px.bar(salary_city,x="city",y="avg_salary",color="city",color_discrete_sequence=["#7c3aed","#06b6d4","#10b981","#f59e0b"],title="Avg Employee Salary by City",labels={"avg_salary":"Avg Salary (INR)","city":"City"})
    f.update_layout(**CHART_TPL); f.update_traces(marker_line_width=0); return f

def fig_supplier():
    f=go.Figure(go.Pie(labels=sup_country["country"],values=sup_country["count"],hole=0.5,marker=dict(colors=["#f59e0b","#7c3aed","#06b6d4"],line=dict(width=2,color="#0d1117")),textfont=dict(color="#e6edf3"),textinfo="label+percent"))
    f.update_layout(**CHART_TPL,title="Suppliers by Country",showlegend=False); return f

def fig_price_hist():
    f=go.Figure(go.Histogram(x=products["price"],nbinsx=40,marker=dict(color="#7c3aed",opacity=0.85,line=dict(width=0))))
    f.update_layout(**CHART_TPL,title="Product Price Distribution",xaxis_title="Price (INR)",yaxis_title="Count"); return f

def fig_refund_hist():
    f=go.Figure(go.Histogram(x=returns["refund"],nbinsx=35,marker=dict(color="#f43f5e",opacity=0.85,line=dict(width=0))))
    f.update_layout(**CHART_TPL,title="Return Refund Distribution",xaxis_title="Refund (INR)",yaxis_title="Count"); return f

def fig_scatter():
    f=px.scatter(scatter_s,x="qty",y="price",opacity=0.45,color_discrete_sequence=["#06b6d4"],title="Qty vs Unit Price (sample 3k)",labels={"qty":"Quantity","price":"Price (INR)"})
    f.update_traces(marker=dict(size=5)); f.update_layout(**CHART_TPL); return f

def fig_dow():
    f=px.bar(dow_full,x="dow",y="orders",color="orders",color_continuous_scale=["#7c3aed","#06b6d4"],title="Orders by Day of Week",labels={"dow":"Day","orders":"Order Count"})
    f.update_layout(**CHART_TPL,coloraxis_showscale=False); f.update_traces(marker_line_width=0); return f

def fig_yearly():
    f=px.bar(yearly_rev,x="year",y="amount",color="year",color_discrete_sequence=["#7c3aed","#06b6d4","#10b981","#f59e0b"],title="Revenue by Year",labels={"amount":"Revenue (INR)","year":"Year"},text_auto=".2s")
    f.update_traces(textfont_color="#e6edf3",marker_line_width=0); f.update_layout(**CHART_TPL,showlegend=False); return f

def fig_promo():
    disc_b=pd.cut(promotions["discount"],bins=[0,10,20,30,40],labels=["0-10%","11-20%","21-30%","31-40%"])
    dc=disc_b.value_counts().sort_index().reset_index(); dc.columns=["range","count"]
    f=px.bar(dc,x="range",y="count",color="range",color_discrete_sequence=["#10b981","#06b6d4","#f59e0b","#f43f5e"],title="Promotion Discount Ranges",labels={"range":"Discount Range","count":"# Promotions"})
    f.update_layout(**CHART_TPL,showlegend=False); f.update_traces(marker_line_width=0); return f

def fig_emp_salary_hist():
    f=go.Figure(go.Histogram(x=employees["salary"],nbinsx=30,marker=dict(color="#f59e0b",opacity=0.85,line=dict(width=0))))
    f.update_layout(**CHART_TPL,title="Employee Salary Distribution",xaxis_title="Salary (INR)",yaxis_title="Count"); return f

def fig_emp_city():
    ec=emp_stores["city"].value_counts().reset_index(); ec.columns=["city","count"]
    f=go.Figure(go.Pie(labels=ec["city"],values=ec["count"],hole=0.5,marker=dict(colors=["#7c3aed","#06b6d4","#10b981","#f59e0b"],line=dict(width=2,color="#0d1117")),textfont=dict(color="#e6edf3"),textinfo="label+percent"))
    f.update_layout(**CHART_TPL,title="Employees by City",showlegend=False); return f

app=dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP,"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"],title="Retail Analytics – DEPI")

TAB_IDS=["tab-overview","tab-sales","tab-customers","tab-products","tab-logistics","tab-employees","tab-suppliers"]
TAB_LABELS=[("📊","Overview"),("💰","Sales"),("👥","Customers"),("📦","Products"),("🚚","Logistics"),("👔","Employees"),("🏭","Suppliers")]

def nav_item(icon,label,tid,active=False):
    return html.Div([html.Span(icon,style={"fontSize":"1.1rem"}),html.Span(label)],id=tid,style={"display":"flex","gap":"10px","alignItems":"center","padding":"10px 14px","borderRadius":"10px","cursor":"pointer","fontSize":"0.88rem","fontWeight":"500","marginBottom":"4px","color":"#e6edf3" if active else "#8b949e","background":"rgba(124,58,237,0.18)" if active else "transparent","border":"1px solid rgba(124,58,237,0.4)" if active else "1px solid transparent","transition":"all 0.2s ease"},n_clicks=0)

sidebar=html.Div([
    html.Div([html.Div("🛒",style={"fontSize":"2rem"}),html.Div([html.H6("Retail Analytics",style={"margin":"0","fontWeight":"700","color":"#e6edf3","fontSize":"1rem"}),html.P("DEPI Project",style={"margin":"0","fontSize":"0.7rem","color":"#8b949e"})])],style={"display":"flex","gap":"12px","alignItems":"center","marginBottom":"28px","paddingBottom":"18px","borderBottom":"1px solid #30363d"}),
    html.Div([nav_item(i,l,t,k==0) for k,(t,(i,l)) in enumerate(zip(TAB_IDS,TAB_LABELS))],id="sidebar-nav"),
    html.Div("Retail Warehouse v1.0",style={"marginTop":"auto","color":"#8b949e","fontSize":"0.7rem","textAlign":"center","paddingTop":"20px","borderTop":"1px solid #30363d"}),
],style={"width":"210px","minWidth":"210px","height":"100vh","position":"fixed","top":"0","left":"0","background":"#161b22","borderRight":"1px solid #30363d","padding":"22px 14px","display":"flex","flexDirection":"column","overflowY":"auto","zIndex":"100"})

topbar=html.Div([
    html.Div([html.H4("Dashboard",id="page-title-text",style={"margin":"0","fontWeight":"700","color":"#e6edf3","fontSize":"1.3rem"}),html.P("Retail Warehouse · All Time",style={"margin":"0","color":"#8b949e","fontSize":"0.8rem"})]),
    html.Div("🟢 Live Data",style={"background":"rgba(16,185,129,0.12)","color":"#10b981","borderRadius":"20px","padding":"4px 14px","fontSize":"0.75rem","fontWeight":"600","border":"1px solid rgba(16,185,129,0.3)"}),
],style={"display":"flex","justifyContent":"space-between","alignItems":"center","marginBottom":"26px","paddingBottom":"18px","borderBottom":"1px solid #30363d"})

app.layout=html.Div([
    dcc.Store(id="active-tab",data="tab-overview"),
    sidebar,
    html.Div([topbar,html.Div(id="tab-content")],style={"marginLeft":"210px","padding":"26px 30px","minHeight":"100vh","background":"#0d1117"}),
],style={"background":"#0d1117","minHeight":"100vh","fontFamily":"Inter, system-ui, sans-serif"})

app.index_string='''<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}<style>*,*::before,*::after{box-sizing:border-box}html,body{margin:0;padding:0;background:#0d1117}::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:#0d1117}::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}.kpi-card:hover{transform:translateY(-3px)!important;box-shadow:0 8px 32px rgba(124,58,237,0.25)!important}#sidebar-nav>div:hover{background:rgba(124,58,237,0.12)!important;color:#e6edf3!important}</style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>'''

@app.callback(Output("active-tab","data"),[Input(t,"n_clicks") for t in TAB_IDS],prevent_initial_call=True)
def set_tab(*_):
    ctx=dash.callback_context
    return ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else "tab-overview"

@app.callback(Output("tab-content","children"),Input("active-tab","data"))
def render(tab):
    C=COLORS
    if tab=="tab-overview":
        return html.Div([
            html.Div([
                kpi_card("💰","Total Revenue",f"INR {total_revenue/1e7:.2f} Cr","All payments",C["accent1"]),
                kpi_card("📦","Total Orders",f"{total_orders:,}","All-time",C["accent2"]),
                kpi_card("👥","Customers",f"{total_customers:,}","Registered",C["accent4"]),
                kpi_card("↩️","Return Rate",f"{return_rate:.1f}%","Of all items",C["accent5"]),
                kpi_card("🧾","Avg Order",f"INR {avg_order_val:,.0f}","Per order",C["accent3"]),
            ],style={"display":"flex","gap":"14px","flexWrap":"wrap","marginBottom":"24px"}),
            html.Div([
                chart_card([section_hdr("Revenue Trend","Monthly totals"),dcc.Graph(figure=fig_monthly(),config={"displayModeBar":False},style={"height":"270px"})],span=2),
                chart_card([section_hdr("Revenue by City"),dcc.Graph(figure=fig_city(),config={"displayModeBar":False},style={"height":"270px"})]),
            ],style={"display":"flex","gap":"14px","marginBottom":"14px","flexWrap":"wrap"}),
            html.Div([
                chart_card([section_hdr("Revenue by Year"),dcc.Graph(figure=fig_yearly(),config={"displayModeBar":False},style={"height":"250px"})]),
                chart_card([section_hdr("Shipment Status"),dcc.Graph(figure=fig_ship(),config={"displayModeBar":False},style={"height":"250px"})]),
                chart_card([section_hdr("Orders by Day"),dcc.Graph(figure=fig_dow(),config={"displayModeBar":False},style={"height":"250px"})]),
            ],style={"display":"flex","gap":"14px","flexWrap":"wrap"}),
        ])
    elif tab=="tab-sales":
        return html.Div([
            html.Div([
                chart_card([section_hdr("Monthly Revenue"),dcc.Graph(figure=fig_monthly(),config={"displayModeBar":False},style={"height":"320px"})],span=2),
                chart_card([section_hdr("Yearly Revenue"),dcc.Graph(figure=fig_yearly(),config={"displayModeBar":False},style={"height":"320px"})]),
            ],style={"display":"flex","gap":"14px","marginBottom":"14px","flexWrap":"wrap"}),
            html.Div([
                chart_card([section_hdr("Top 15 Categories by Revenue"),dcc.Graph(figure=fig_cats(),config={"displayModeBar":False},style={"height":"380px"})],span=2),
                chart_card([section_hdr("Promotion Discounts"),dcc.Graph(figure=fig_promo(),config={"displayModeBar":False},style={"height":"380px"})]),
            ],style={"display":"flex","gap":"14px","flexWrap":"wrap"}),
        ])
    elif tab=="tab-customers":
        return html.Div([
            html.Div([
                chart_card([section_hdr("Monthly Signups","New customer registrations"),dcc.Graph(figure=fig_signups(),config={"displayModeBar":False},style={"height":"300px"})],span=2),
                chart_card([section_hdr("Customers by City"),dcc.Graph(figure=fig_cust_city(),config={"displayModeBar":False},style={"height":"300px"})]),
            ],style={"display":"flex","gap":"14px","flexWrap":"wrap"}),
        ])
    elif tab=="tab-products":
        return html.Div([
            html.Div([
                chart_card([section_hdr("Product Price Distribution"),dcc.Graph(figure=fig_price_hist(),config={"displayModeBar":False},style={"height":"280px"})]),
                chart_card([section_hdr("Qty vs Price Scatter"),dcc.Graph(figure=fig_scatter(),config={"displayModeBar":False},style={"height":"280px"})]),
                chart_card([section_hdr("Return Refund Distribution"),dcc.Graph(figure=fig_refund_hist(),config={"displayModeBar":False},style={"height":"280px"})]),
            ],style={"display":"flex","gap":"14px","marginBottom":"14px","flexWrap":"wrap"}),
            html.Div([
                chart_card([section_hdr("Top Categories by Revenue"),dcc.Graph(figure=fig_cats(),config={"displayModeBar":False},style={"height":"380px"})],span=3),
            ],style={"display":"flex","gap":"14px","flexWrap":"wrap"}),
        ])
    elif tab=="tab-logistics":
        return html.Div([
            html.Div([
                chart_card([section_hdr("Shipment Status"),dcc.Graph(figure=fig_ship(),config={"displayModeBar":False},style={"height":"330px"})]),
                chart_card([section_hdr("Return Refund Distribution"),dcc.Graph(figure=fig_refund_hist(),config={"displayModeBar":False},style={"height":"330px"})],span=2),
            ],style={"display":"flex","gap":"14px","marginBottom":"14px","flexWrap":"wrap"}),
            html.Div([
                stat_pill("📬 Total Shipments",f"{shipments.shape[0]:,}",C["accent2"]),
                stat_pill("✅ Delivered",f"{(shipments['status']=='delivered').sum():,}",C["accent4"]),
                stat_pill("🚚 Shipped",f"{(shipments['status']=='shipped').sum():,}",C["accent3"]),
                stat_pill("⚠️ Late",f"{(shipments['status']=='late').sum():,}",C["accent5"]),
                stat_pill("↩️ Total Returns",f"{returns.shape[0]:,}",C["accent1"]),
            ],style={"display":"flex","gap":"12px","flexWrap":"wrap"}),
        ])
    elif tab=="tab-employees":
        return html.Div([
            html.Div([
                chart_card([section_hdr("Avg Salary by City"),dcc.Graph(figure=fig_salary(),config={"displayModeBar":False},style={"height":"300px"})],span=2),
                chart_card([section_hdr("Employees by City"),dcc.Graph(figure=fig_emp_city(),config={"displayModeBar":False},style={"height":"300px"})]),
            ],style={"display":"flex","gap":"14px","marginBottom":"14px","flexWrap":"wrap"}),
            html.Div([
                chart_card([section_hdr("Salary Distribution"),dcc.Graph(figure=fig_emp_salary_hist(),config={"displayModeBar":False},style={"height":"270px"})],span=3),
            ],style={"display":"flex","gap":"14px","flexWrap":"wrap"}),
        ])
    elif tab=="tab-suppliers":
        return html.Div([
            html.Div([
                chart_card([section_hdr("Suppliers by Country (Pie)"),dcc.Graph(figure=fig_supplier(),config={"displayModeBar":False},style={"height":"340px"})]),
                chart_card([section_hdr("Suppliers by Country (Bar)"),dcc.Graph(figure=px.bar(sup_country,x="country",y="count",color="country",color_discrete_sequence=["#f59e0b","#7c3aed","#06b6d4"],title="Supplier Count per Country",labels={"count":"# Suppliers","country":"Country"}).update_layout(**CHART_TPL,showlegend=False),config={"displayModeBar":False},style={"height":"340px"})],span=2),
            ],style={"display":"flex","gap":"14px","flexWrap":"wrap"}),
        ])
    return html.Div("Select a tab")

if __name__=="__main__":
    app.run(debug=False,host="127.0.0.1",port=8050)
