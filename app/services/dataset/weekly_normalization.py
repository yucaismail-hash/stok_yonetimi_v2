"""Canonical YYYY-Www demand normalization for DATA1A."""
import re
from dataclasses import dataclass
from datetime import date

_PERIOD = re.compile(r"^(?P<year>\d{4})-W(?P<week>\d{2})$")

@dataclass(frozen=True)
class WeeklyPeriod:
    year: int
    week: int
    period: str

def parse_weekly_period(value):
    match = _PERIOD.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValueError("weekly period must use YYYY-Www")
    year, week = int(match['year']), int(match['week'])
    try: date.fromisocalendar(year, week, 1)
    except ValueError as exc: raise ValueError("invalid ISO weekly period") from exc
    return WeeklyPeriod(year, week, f"{year:04d}-W{week:02d}")

def weekly_columns(columns):
    return sorted((parse_weekly_period(column) for column in columns if isinstance(column, str) and _PERIOD.fullmatch(column)), key=lambda item:(item.year,item.week))

def _quantity(value):
    if value is None: return None
    if isinstance(value, bool) or not isinstance(value, (int,float)): raise ValueError("weekly quantity must be numeric or null")
    return float(value)

def normalize_wide_rows(rows, material_key='Ürün Kodu'):
    output=[]
    for row in rows:
        code=row.get(material_key)
        if not isinstance(code,str) or not code: raise ValueError("material code is required")
        for period in weekly_columns(row.keys()):
            quantity=_quantity(row.get(period.period))
            if quantity is not None: output.append({'material_code':code,'period':period.period,'quantity':quantity})
    return sorted(output,key=lambda item:(item['material_code'],parse_weekly_period(item['period']).year,parse_weekly_period(item['period']).week))

def normalize_long_rows(rows, material_key='Ürün Kodu', period_key='Dönem', quantity_key='Miktar'):
    output=[]
    for row in rows:
        code=row.get(material_key)
        if not isinstance(code,str) or not code: raise ValueError("material code is required")
        period=parse_weekly_period(row.get(period_key)); quantity=_quantity(row.get(quantity_key))
        if quantity is not None: output.append({'material_code':code,'period':period.period,'quantity':quantity})
    return sorted(output,key=lambda item:(item['material_code'],parse_weekly_period(item['period']).year,parse_weekly_period(item['period']).week))
