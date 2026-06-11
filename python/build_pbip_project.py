"""Generate Power BI project (semantic model + report visuals)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POWERBI = ROOT / "powerbi"
PROJECT = POWERBI / "SalesPerformance"
REPORT = PROJECT / "SalesPerformance.Report"
SEMANTIC = PROJECT / "SalesPerformance.SemanticModel"
DATA_MODEL = ROOT / "data" / "model"

SCHEMA_VIS = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/visualContainer/2.7.0/schema.json"
)

VISUAL_CONTAINER_STYLE = {
    "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
    "border": [
        {
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "radius": {"expr": {"Literal": {"Value": "4D"}}},
            }
        }
    ],
    "title": [
        {
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
            }
        }
    ],
}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, obj: dict) -> None:
    write_text(path, json.dumps(obj, indent=2, ensure_ascii=False))


def vid() -> str:
    return uuid.uuid4().hex[:20]


def parse_field(field_ref: str) -> tuple[str, str, str]:
    table, col = field_ref.replace("]", "").split("[")
    return table, col, f"{table}.{col}"


def col_field(entity: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def meas_field(entity: str, prop: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def projection(field: dict, query_ref: str, active: bool = False) -> dict:
    p = {"field": field, "queryRef": query_ref}
    if active:
        p["active"] = True
    return p


def m_csv_source(filename: str, columns: int, types: list[tuple[str, str]]) -> str:
    m_path = str(DATA_MODEL / filename)
    type_lines = ", ".join(f'{{"{name}", {ptype}}}' for name, ptype in types)
    return f"""
let
    Source = Csv.Document(
        File.Contents("{m_path}"),
        [Delimiter = ",", Columns = {columns}, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {{{type_lines}}})
in
    ChangedTypes"""


def tmdl_column(name: str, dtype: str, summarize: str = "none", hidden: bool = False) -> str:
    lines = [
        f"\tcolumn {name}",
        f"\t\tdataType: {dtype}",
        f"\t\tsourceColumn: {name}",
        f"\t\tsummarizeBy: {summarize}",
    ]
    if hidden:
        lines.append("\t\tisHidden")
    return "\n".join(lines)


def write_platform(path: Path, item_type: str, display_name: str) -> None:
    write_json(
        path,
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/platform/platformProperties/2.0.0/schema.json",
            "version": "2.0",
            "metadata": {"type": item_type, "displayName": display_name},
            "config": {"logicalId": str(uuid.uuid4())},
        },
    )


def build_semantic_model() -> None:
    def_dir = SEMANTIC / "definition"
    tables_dir = def_dir / "tables"

    write_platform(SEMANTIC / ".platform", "SemanticModel", "Sales Performance")
    write_json(
        SEMANTIC / "diagramLayout.json",
        {"version": "1.0.0", "diagrams": [{"name": "All tables", "nodes": [], "zoomValue": 100}]},
    )
    write_json(
        SEMANTIC / "definition.pbism",
        {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/item/"
                "semanticModel/definitionProperties/1.0.0/schema.json"
            ),
            "version": "4.0",
            "settings": {},
        },
    )

    write_text(def_dir / "database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
    write_text(
        def_dir / "model.tmdl",
        """model Model
\tculture: en-US
\tdefaultPowerBIDataSourceVersion: powerBI_V3
\tannotation __PBI_TimeIntelligenceEnabled = 1

annotation PBI_QueryOrder = ["Fact_Sales", "Dim_Date", "Dim_Customer", "Dim_Product", "Dim_Geography"]

ref table Fact_Sales
ref table Dim_Date
ref table Dim_Customer
ref table Dim_Product
ref table Dim_Geography
""",
    )

    write_text(
        def_dir / "cultures" / "en-US.tmdl",
        "cultureInfo en-US\n\tlinguisticMetadata =\n\t\t\t{\n\t\t\t  \"Version\": \"1.0.0\"\n\t\t\t}\n",
    )

    write_text(
        def_dir / "relationships.tmdl",
        """relationship rel_date
\tfromColumn: Fact_Sales.Order_Date
\ttoColumn: Dim_Date.Date

relationship rel_customer
\tfromColumn: Fact_Sales.Customer_ID
\ttoColumn: Dim_Customer.Customer_ID

relationship rel_product
\tfromColumn: Fact_Sales.Product_Name
\ttoColumn: Dim_Product.Product_Name

relationship rel_geography
\tfromColumn: Fact_Sales.GeographyKey
\ttoColumn: Dim_Geography.GeographyKey
""",
    )

    fact_cols = [
        ("Order_ID", "string"),
        ("Order_Date", "dateTime"),
        ("Customer_ID", "string"),
        ("Product_Name", "string"),
        ("GeographyKey", "string"),
        ("Sales", "double"),
        ("Quantity", "int64"),
        ("Discount", "double"),
        ("Profit", "double"),
    ]
    fact_types = [
        ("Order_ID", "type text"),
        ("Order_Date", "type date"),
        ("Customer_ID", "type text"),
        ("Product_Name", "type text"),
        ("GeographyKey", "type text"),
        ("Sales", "type number"),
        ("Quantity", "Int64.Type"),
        ("Discount", "type number"),
        ("Profit", "type number"),
    ]
    fact_body = "\n".join(tmdl_column(n, t) for n, t in fact_cols)
    measure_defs = [
        ("Total Revenue", "SUM ( Fact_Sales[Sales] )", "$#,0.00", "_ KPIs"),
        ("Total Profit", "SUM ( Fact_Sales[Profit] )", "$#,0.00", "_ KPIs"),
        ("Total Orders", "DISTINCTCOUNT ( Fact_Sales[Order_ID] )", "#,0", "_ KPIs"),
        ("Average Order Value", "DIVIDE ( [Total Revenue], [Total Orders] )", "$#,0.00", "_ KPIs"),
        ("Profit Margin %", "DIVIDE ( [Total Profit], [Total Revenue] )", "0.00%", "_ KPIs"),
        ("Total Quantity", "SUM ( Fact_Sales[Quantity] )", "#,0", "_ KPIs"),
        ("Revenue YTD", "TOTALYTD ( [Total Revenue], Dim_Date[Date] )", "$#,0.00", "_ Time Intelligence"),
        ("Revenue PY", "CALCULATE ( [Total Revenue], SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )", "$#,0.00", "_ Time Intelligence"),
        ("Revenue YoY Growth %", "DIVIDE ( [Total Revenue] - [Revenue PY], [Revenue PY] )", "0.00%", "_ Time Intelligence"),
        ("Customer Count", "DISTINCTCOUNT ( Fact_Sales[Customer_ID] )", "#,0", "_ Customer"),
        ("Product Count", "DISTINCTCOUNT ( Fact_Sales[Product_Name] )", "#,0", "_ Product"),
        ("Customer Contribution %", "DIVIDE ( [Total Revenue], CALCULATE ( [Total Revenue], ALL ( Dim_Customer ) ) )", "0.00%", "_ Customer"),
        ("Customers in Band", "DISTINCTCOUNT ( Dim_Customer[Customer_ID] )", "#,0", "_ Customer"),
    ]
    measure_blocks = [
        f"\tmeasure '{name}' = {expr}\n\t\tformatString: {fmt}\n\t\tdisplayFolder: \"{folder}\""
        for name, expr, fmt, folder in measure_defs
    ]

    write_text(
        tables_dir / "Fact_Sales.tmdl",
        f"""table Fact_Sales
\tlineageTag: {uuid.uuid4()}

{fact_body}

{chr(10).join(measure_blocks)}

\tpartition Fact_Sales = m
\t\tmode: import
\t\tsource ={m_csv_source("Fact_Sales.csv", 9, fact_types)}
""",
    )

    date_cols = [
        ("Date", "dateTime"),
        ("Year", "int64"),
        ("Month", "int64"),
        ("MonthName", "string"),
        ("Quarter", "int64"),
        ("QuarterLabel", "string"),
        ("YearMonth", "string"),
    ]
    date_types = [
        ("Date", "type date"),
        ("Year", "Int64.Type"),
        ("Month", "Int64.Type"),
        ("MonthName", "type text"),
        ("Quarter", "Int64.Type"),
        ("QuarterLabel", "type text"),
        ("YearMonth", "type text"),
    ]
    write_text(
        tables_dir / "Dim_Date.tmdl",
        f"""table Dim_Date
\tlineageTag: {uuid.uuid4()}
\tdataCategory: Time

\tannotation __PBI_DateTable = true

{chr(10).join(tmdl_column(n, t) for n, t in date_cols)}

\tpartition Dim_Date = m
\t\tmode: import
\t\tsource ={m_csv_source("Dim_Date.csv", 7, date_types)}
""",
    )

    cust_cols = [
        ("Customer_ID", "string"),
        ("Customer_Name", "string"),
        ("Segment", "string"),
        ("Customer_Total_Revenue", "double"),
        ("Revenue_Band", "string"),
        ("Revenue_Band_Sort", "int64"),
    ]
    cust_types = [
        ("Customer_ID", "type text"),
        ("Customer_Name", "type text"),
        ("Segment", "type text"),
        ("Customer_Total_Revenue", "type number"),
        ("Revenue_Band", "type text"),
        ("Revenue_Band_Sort", "Int64.Type"),
    ]
    write_text(
        tables_dir / "Dim_Customer.tmdl",
        f"""table Dim_Customer
\tlineageTag: {uuid.uuid4()}

{chr(10).join(tmdl_column(n, t) for n, t in cust_cols)}

\tpartition Dim_Customer = m
\t\tmode: import
\t\tsource ={m_csv_source("Dim_Customer.csv", 6, cust_types)}
""",
    )

    prod_cols = [("Product_Name", "string"), ("Category", "string"), ("Sub_Category", "string")]
    prod_types = [
        ("Product_Name", "type text"),
        ("Category", "type text"),
        ("Sub_Category", "type text"),
    ]
    write_text(
        tables_dir / "Dim_Product.tmdl",
        f"""table Dim_Product
\tlineageTag: {uuid.uuid4()}

{chr(10).join(tmdl_column(n, t) for n, t in prod_cols)}

\tpartition Dim_Product = m
\t\tmode: import
\t\tsource ={m_csv_source("Dim_Product.csv", 3, prod_types)}
""",
    )

    geo_cols = [
        ("GeographyKey", "string"),
        ("Region", "string"),
        ("State", "string"),
        ("City", "string"),
    ]
    geo_types = [
        ("GeographyKey", "type text"),
        ("Region", "type text"),
        ("State", "type text"),
        ("City", "type text"),
    ]
    write_text(
        tables_dir / "Dim_Geography.tmdl",
        f"""table Dim_Geography
\tlineageTag: {uuid.uuid4()}

{chr(10).join(tmdl_column(n, t, hidden=(n == "GeographyKey")) for n, t in geo_cols)}

\tpartition Dim_Geography = m
\t\tmode: import
\t\tsource ={m_csv_source("Dim_Geography.csv", 4, geo_types)}
""",
    )


def make_visual(
    visual_type: str,
    pos: dict,
    query_state: dict,
    title: str,
    sort_def: dict | None = None,
    extra_objects: dict | None = None,
) -> dict:
    objects = extra_objects or {}
    visual = {
        "visualType": visual_type,
        "query": {"queryState": query_state},
        "objects": objects,
        "visualContainerObjects": {
            **VISUAL_CONTAINER_STYLE,
            "title": [
                {
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                        "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
                    }
                }
            ],
        },
    }
    if sort_def:
        visual["query"]["sortDefinition"] = sort_def
    return {
        "$schema": SCHEMA_VIS,
        "name": vid(),
        "position": {
            "x": pos["x"],
            "y": pos["y"],
            "z": pos.get("z", 0),
            "height": pos["h"],
            "width": pos["w"],
            "tabOrder": pos.get("tab", 0),
        },
        "visual": visual,
    }


def card_visual(measure: str, pos: dict, title: str) -> dict:
    table, col, qref = parse_field(measure)
    return make_visual(
        "card",
        pos,
        {"Values": {"projections": [projection(meas_field(table, col), qref, True)]}},
        title,
    )


def bar_visual(axis: str, measure: str, pos: dict, title: str, horizontal: bool = True) -> dict:
    t_axis, c_axis, q_axis = parse_field(axis)
    t_meas, c_meas, q_meas = parse_field(measure)
    vtype = "clusteredBarChart" if horizontal else "clusteredColumnChart"
    return make_visual(
        vtype,
        pos,
        {
            "Category": {"projections": [projection(col_field(t_axis, c_axis), q_axis, True)]},
            "Y": {"projections": [projection(meas_field(t_meas, c_meas), q_meas)]},
        },
        title,
        sort_def={
            "sort": [{"field": meas_field(t_meas, c_meas), "direction": "Descending"}],
            "isDefaultSort": True,
        },
        extra_objects={
            "categoryAxis": [
                {
                    "properties": {
                        "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}},
                    }
                }
            ],
            "valueAxis": [
                {
                    "properties": {
                        "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}},
                    }
                }
            ],
        },
    )


def line_visual(axis: str, measure: str, pos: dict, title: str) -> dict:
    t_axis, c_axis, q_axis = parse_field(axis)
    t_meas, c_meas, q_meas = parse_field(measure)
    return make_visual(
        "lineChart",
        pos,
        {
            "Category": {"projections": [projection(col_field(t_axis, c_axis), q_axis, True)]},
            "Y": {"projections": [projection(meas_field(t_meas, c_meas), q_meas)]},
        },
        title,
        extra_objects={
            "lineStyles": [
                {
                    "properties": {
                        "strokeWidth": {"expr": {"Literal": {"Value": "2D"}}},
                        "areaShow": {"expr": {"Literal": {"Value": "true"}}},
                    }
                }
            ],
        },
    )


def donut_visual(legend: str, measure: str, pos: dict, title: str) -> dict:
    t_leg, c_leg, q_leg = parse_field(legend)
    t_meas, c_meas, q_meas = parse_field(measure)
    return make_visual(
        "donutChart",
        pos,
        {
            "Category": {"projections": [projection(col_field(t_leg, c_leg), q_leg, True)]},
            "Y": {"projections": [projection(meas_field(t_meas, c_meas), q_meas)]},
        },
        title,
    )


def slicer_visual(field: str, pos: dict, title: str) -> dict:
    table, col, qref = parse_field(field)
    return make_visual(
        "slicer",
        pos,
        {"Values": {"projections": [projection(col_field(table, col), qref, True)]}},
        title,
    )


def table_visual(columns: list[str], pos: dict, title: str) -> dict:
    projections = []
    for col_ref in columns:
        table, col, qref = parse_field(col_ref)
        if col_ref.startswith("Fact_Sales["):
            projections.append(projection(meas_field(table, col), qref))
        else:
            projections.append(projection(col_field(table, col), qref))
    return make_visual("tableEx", pos, {"Values": {"projections": projections}}, title)


def treemap_visual(group: str, details: str, measure: str, pos: dict, title: str) -> dict:
    tg, cg, qg = parse_field(group)
    td, cd, qd = parse_field(details)
    tm, cm, qm = parse_field(measure)
    return make_visual(
        "treemap",
        pos,
        {
            "Group": {"projections": [projection(col_field(tg, cg), qg, True)]},
            "Details": {"projections": [projection(col_field(td, cd), qd)]},
            "Values": {"projections": [projection(meas_field(tm, cm), qm)]},
        },
        title,
    )


def waterfall_visual(category: str, measure: str, pos: dict, title: str) -> dict:
    tc, cc, qc = parse_field(category)
    tm, cm, qm = parse_field(measure)
    return make_visual(
        "waterfallChart",
        pos,
        {
            "Category": {"projections": [projection(col_field(tc, cc), qc, True)]},
            "Y": {"projections": [projection(meas_field(tm, cm), qm)]},
        },
        title,
    )


def build_report() -> None:
    def_dir = REPORT / "definition"
    pages_dir = def_dir / "pages"
    theme_dst = REPORT / "StaticResources" / "RegisteredResources" / "SalesPerformanceTheme.json"
    theme_dst.parent.mkdir(parents=True, exist_ok=True)
    theme_src = POWERBI / "PowerBI_Theme.json"
    if theme_src.exists():
        theme_dst.write_text(theme_src.read_text(encoding="utf-8"), encoding="utf-8")

    base_theme_dir = REPORT / "StaticResources" / "SharedResources" / "BaseThemes"
    base_theme_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        base_theme_dir / "CY24SU10.json",
        {"name": "CY24SU10", "dataColors": ["#118DFF", "#12239E", "#E66C37"], "background": "#FFFFFF", "foreground": "#252423", "tableAccent": "#118DFF"},
    )

    write_platform(REPORT / ".platform", "Report", "Sales Performance Dashboard")

    write_json(
        REPORT / "definition.pbir",
        {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                "definitionProperties/2.0.0/schema.json"
            ),
            "version": "4.0",
            "datasetReference": {"byPath": {"path": "../SalesPerformance.SemanticModel"}},
        },
    )

    write_json(
        def_dir / "version.json",
        {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                "definition/versionMetadata/1.0.0/schema.json"
            ),
            "version": "2.0.0",
        },
    )

    write_json(
        def_dir / "report.json",
        {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                "definition/report/1.0.0/schema.json"
            ),
            "themeCollection": {
                "baseTheme": {
                    "name": "CY24SU10",
                    "reportVersionAtImport": {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"},
                    "type": "SharedResources",
                },
                "customTheme": {
                    "name": "SalesPerformanceTheme",
                    "reportVersionAtImport": {"visual": "2.6.0", "report": "3.1.0", "page": "2.3.0"},
                    "type": "RegisteredResources",
                },
            },
            "resourcePackages": [
                {
                    "name": "SharedResources",
                    "type": "SharedResources",
                    "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}],
                },
                {
                    "name": "RegisteredResources",
                    "type": "RegisteredResources",
                    "items": [
                        {"name": "SalesPerformanceTheme", "path": "SalesPerformanceTheme.json", "type": "CustomTheme"}
                    ],
                },
            ],
            "settings": {
                "useStylableVisualContainerHeader": True,
                "exportDataMode": "AllowSummarizedAndUnderlying",
                "defaultDrillFilterOtherVisuals": True,
            },
        },
    )

    pages = [
        {
            "id": "ExecutiveOverview",
            "name": "Executive Overview",
            "width": 1280,
            "height": 720,
            "visuals": [
                ("card", "Fact_Sales[Total Revenue]", {"x": 16, "y": 16, "w": 240, "h": 100}, "Total Revenue"),
                ("card", "Fact_Sales[Total Profit]", {"x": 272, "y": 16, "w": 240, "h": 100}, "Total Profit"),
                ("card", "Fact_Sales[Total Orders]", {"x": 528, "y": 16, "w": 240, "h": 100}, "Total Orders"),
                ("card", "Fact_Sales[Average Order Value]", {"x": 784, "y": 16, "w": 240, "h": 100}, "Average Order Value"),
                ("card", "Fact_Sales[Profit Margin %]", {"x": 1040, "y": 16, "w": 224, "h": 100}, "Profit Margin %"),
                ("line", "Dim_Date[YearMonth]", "Fact_Sales[Total Revenue]", {"x": 16, "y": 132, "w": 960, "h": 260}, "Monthly Revenue Trend"),
                ("donut", "Dim_Customer[Segment]", "Fact_Sales[Total Revenue]", {"x": 992, "y": 132, "w": 272, "h": 260}, "Revenue by Segment"),
                ("bar", "Dim_Geography[Region]", "Fact_Sales[Total Revenue]", {"x": 16, "y": 408, "w": 470, "h": 296}, "Revenue by Region"),
                ("col", "Dim_Product[Category]", "Fact_Sales[Total Profit]", {"x": 502, "y": 408, "w": 474, "h": 296}, "Profit by Category"),
                ("slicer", "Dim_Geography[Region]", {"x": 992, "y": 408, "w": 272, "h": 96}, "Region"),
                ("slicer", "Dim_Product[Category]", {"x": 992, "y": 512, "w": 272, "h": 96}, "Category"),
                ("slicer", "Dim_Date[Year]", {"x": 992, "y": 616, "w": 272, "h": 88}, "Year"),
            ],
        },
        {
            "id": "ProductAnalysis",
            "name": "Product Analysis",
            "width": 1280,
            "height": 900,
            "visuals": [
                ("bar", "Dim_Product[Product_Name]", "Fact_Sales[Total Revenue]", {"x": 16, "y": 16, "w": 624, "h": 280}, "Top 10 Products by Revenue"),
                ("bar", "Dim_Product[Product_Name]", "Fact_Sales[Total Profit]", {"x": 656, "y": 16, "w": 608, "h": 280}, "Top 10 Products by Profit"),
                ("col", "Dim_Product[Category]", "Fact_Sales[Total Revenue]", {"x": 16, "y": 312, "w": 624, "h": 280}, "Revenue by Category"),
                ("treemap", ("Dim_Product[Sub_Category]", "Dim_Product[Product_Name]", "Fact_Sales[Total Revenue]"), {"x": 656, "y": 312, "w": 608, "h": 280}, "Revenue by Subcategory"),
                ("bar", "Dim_Product[Product_Name]", "Fact_Sales[Total Quantity]", {"x": 16, "y": 608, "w": 1248, "h": 276}, "Quantity Sold by Product"),
            ],
        },
        {
            "id": "CustomerAnalysis",
            "name": "Customer Analysis",
            "width": 1280,
            "height": 900,
            "visuals": [
                (
                    "table",
                    [
                        "Dim_Customer[Customer_Name]",
                        "Fact_Sales[Total Revenue]",
                        "Fact_Sales[Total Profit]",
                        "Fact_Sales[Total Orders]",
                        "Fact_Sales[Average Order Value]",
                    ],
                    {"x": 16, "y": 16, "w": 624, "h": 320},
                    "Top Customers",
                ),
                ("col", "Dim_Customer[Segment]", "Fact_Sales[Total Revenue]", {"x": 656, "y": 16, "w": 608, "h": 320}, "Revenue by Segment"),
                ("waterfall", "Dim_Customer[Customer_Name]", "Fact_Sales[Total Revenue]", {"x": 16, "y": 352, "w": 624, "h": 280}, "Customer Contribution"),
                ("bar", "Dim_Customer[Customer_Name]", "Fact_Sales[Total Orders]", {"x": 656, "y": 352, "w": 608, "h": 280}, "Orders by Customer"),
                ("col", "Dim_Customer[Revenue_Band]", "Fact_Sales[Customers in Band]", {"x": 16, "y": 648, "w": 1248, "h": 236}, "Revenue Distribution"),
            ],
        },
    ]

    for page in pages:
        page_id = page["id"]
        page_dir = pages_dir / page_id
        visual_entries = []

        for idx, spec in enumerate(page["visuals"]):
            kind = spec[0]
            pos = {**spec[-2], "tab": (idx + 1) * 1000}
            title = spec[-1]

            if kind == "card":
                v = card_visual(spec[1], pos, title)
            elif kind == "line":
                v = line_visual(spec[1], spec[2], pos, title)
            elif kind == "bar":
                v = bar_visual(spec[1], spec[2], pos, title, horizontal=True)
            elif kind == "col":
                v = bar_visual(spec[1], spec[2], pos, title, horizontal=False)
            elif kind == "donut":
                v = donut_visual(spec[1], spec[2], pos, title)
            elif kind == "slicer":
                v = slicer_visual(spec[1], pos, title)
            elif kind == "table":
                v = table_visual(spec[1], pos, title)
            elif kind == "waterfall":
                v = waterfall_visual(spec[1], spec[2], pos, title)
            elif kind == "treemap":
                group, details, measure = spec[1]
                v = treemap_visual(group, details, measure, pos, title)
            else:
                continue

            vdir = page_dir / "visuals" / v["name"]
            write_json(vdir / "visual.json", v)
            visual_entries.append(v["name"])

        write_json(
            page_dir / "page.json",
            {
                "$schema": (
                    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                    "definition/page/1.0.0/schema.json"
                ),
                "name": page_id,
                "displayName": page["name"],
                "displayOption": "FitToPage",
                "height": page["height"],
                "width": page["width"],
                "objects": {
                    "background": [
                        {
                            "properties": {
                                "color": {
                                    "solid": {
                                        "color": {"expr": {"Literal": {"Value": "'#F5F7FA'"}}}
                                    }
                                },
                                "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                            }
                        }
                    ]
                },
            },
        )
    write_json(
        pages_dir / "pages.json",
        {
            "$schema": (
                "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                "definition/pagesMetadata/1.0.0/schema.json"
            ),
            "pageOrder": [p["id"] for p in pages],
            "activePageName": pages[0]["id"],
        },
    )


def build_pbip_root() -> None:
    write_json(
        POWERBI / "SalesPerformance.pbip",
        {
            "version": "1.0",
            "artifacts": [
                {"report": {"path": "SalesPerformance/SalesPerformance.Report"}},
                {"dataset": {"path": "SalesPerformance/SalesPerformance.SemanticModel"}},
            ],
            "settings": {"enableAutoRecovery": True},
        },
    )


def main() -> None:
    if not DATA_MODEL.exists():
        raise SystemExit("Run python python/build_powerbi_model.py first.")
    build_semantic_model()
    build_report()
    build_pbip_root()
    print(f"Power BI project created: {POWERBI / 'SalesPerformance.pbip'}")
    print("Open in Power BI Desktop -> enable PBIP preview if prompted.")


if __name__ == "__main__":
    main()
