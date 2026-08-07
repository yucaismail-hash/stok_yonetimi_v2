"""Pure DATA1B import-policy validation; no persistence or API behavior."""
from enum import Enum
from app.services.dataset.weekly_normalization import parse_weekly_period

class DemandType(str, Enum):
    SALES='sales'; SHIPMENT='shipment'; ORDER='order'; CONSUMPTION='consumption'; OTHER='other'

SHEETS={'Temel_Veriler': {'required': True, 'fields': ('Ürün Kodu','Ürün Grubu')}, 'Malzeme_Tedarikciler': {'required': False, 'fields': ('Ürün Kodu','Tedarikçi Kodu')}, 'Tedarikciler': {'required': False, 'fields': ('Tedarikçi Kodu',)}, 'Events': {'required': False, 'fields': ()}}
EVENT_TYPES={'campaign','price_change','launch','fair_event','operational_shutdown','special_customer_demand','other'}
DATA_REQUIREMENTS={'events':'OPTIONAL','demand_type':'WIZARD','service_level':'WIZARD','official_calendar':'AUTOMATIC','event_effect':'CALCULATED','supplier_enrichment':'OPTIONAL'}

def validate_demand_type(value):
    if value is None: return None
    try: return DemandType(value).value
    except (TypeError, ValueError) as exc: raise ValueError('invalid demand_type') from exc

def validate_import_sheets(sheets, demand_type=None):
    validate_demand_type(demand_type)
    errors=[]
    for name, policy in SHEETS.items():
        rows=sheets.get(name)
        if rows is None:
            if policy['required']: errors.append(f'{name} is required')
            continue
        if not isinstance(rows,list): errors.append(f'{name} must contain rows'); continue
        for index,row in enumerate(rows):
            if not isinstance(row,dict) or any(not row.get(field) for field in policy['fields']): errors.append(f'{name}[{index}] missing required identity field')
    base=sheets.get('Temel_Veriler')
    if base:
        for index,row in enumerate(base):
            if not row.get('Ürün Kodu') or not row.get('Ürün Grubu'): errors.append(f'Temel_Veriler[{index}] missing product hierarchy identity')
    mapping=sheets.get('Malzeme_Tedarikciler'); suppliers=sheets.get('Tedarikciler'); metrics=('Sipariş Karşılama Oranı (%)','Terminden Önce Teslim (%)','Termininde Teslim (%)','Terminden Sonra Teslim (%)','Ortalama Teslim Süresi (Gün)','Teslim Süresi Std. Sapması')
    availability={'core_data':'available' if base and not errors else 'unavailable','supplier_mapping':'available' if mapping else 'unavailable','supplier_performance':('unavailable' if not suppliers else ('full' if all(all(field in row and row[field] not in (None,'') for field in metrics) for row in suppliers) else 'partial')),'events':'available' if sheets.get('Events') is not None else 'unavailable','demand_type':'configured' if demand_type is not None else 'missing'}
    return {'valid':not errors,'errors':errors,'availability':availability}

def validate_events(rows, products):
    errors=[]
    groups={row.get('Ürün Grubu'):set() for row in products if row.get('Ürün Grubu')}
    for row in products:
        if row.get('Ürün Grubu') and row.get('Ürün Sınıfı'): groups[row['Ürün Grubu']].add(row['Ürün Sınıfı'])
    for index,row in enumerate(rows or []):
        group=row.get('Ürün Grubu'); product_class=row.get('Ürün Sınıfı'); event_type=row.get('Event Tipi')
        try:
            year=int(row.get('Yıl')); start=int(row.get('Başlangıç Hafta')); end=int(row.get('Bitiş Hafta')); parse_weekly_period(f'{year:04d}-W{start:02d}'); parse_weekly_period(f'{year:04d}-W{end:02d}')
            if start>end: raise ValueError('start_week must not exceed end_week')
        except (TypeError,ValueError): errors.append(f'Events[{index}] invalid weekly range')
        if not group: errors.append(f'Events[{index}] group is required')
        elif group not in groups: errors.append(f'Events[{index}] unknown group')
        elif product_class and product_class not in groups[group]: errors.append(f'Events[{index}] class is not in group')
        if event_type not in EVENT_TYPES: errors.append(f'Events[{index}] invalid event type')
    return {'valid':not errors,'errors':errors,'availability':'available' if rows is not None and not errors else ('unavailable' if rows is None else 'invalid')}

def validate_service_level(value):
    if not isinstance(value,dict) or value.get('mode') not in ('automatic','manual'): raise ValueError('invalid service level mode')
    if value['mode']=='automatic': return {'mode':'automatic'}
    level=value.get('value')
    if isinstance(level,bool) or not isinstance(level,(int,float)) or not 0<level<1: raise ValueError('manual service level must be between 0 and 1')
    return {'mode':'manual','value':float(level)}
