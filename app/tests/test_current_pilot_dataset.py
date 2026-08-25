from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.canonical_excel_ingestion import CanonicalExcelIngestionService


def _session_with_first(value):
    session = MagicMock()
    query = session.query.return_value
    query.join.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    query.first.return_value = value
    return session, query


def test_current_accepted_returns_none_when_company_has_no_dataset():
    session, _ = _session_with_first(None)
    assert CanonicalExcelIngestionService().get_current_accepted(session, uuid4()) is None


def test_current_accepted_maps_minimum_public_contract():
    dataset = SimpleNamespace(
        id=uuid4(), created_at='created', source_name='pilot.xlsx', record_count=12, sku_count=3,
    )
    event = SimpleNamespace(created_at='accepted')
    session, query = _session_with_first((dataset, event))

    result = CanonicalExcelIngestionService().get_current_accepted(session, uuid4())

    assert result == {
        'dataset_id': str(dataset.id), 'status': 'READY_FOR_WORKFLOW', 'accepted': True,
        'accepted_at': 'accepted', 'created_at': 'created', 'source_name': 'pilot.xlsx',
        'record_count': 12, 'material_count': 3,
    }
    query.order_by.assert_called_once()


def test_current_accepted_query_is_tenant_scoped_and_deterministic():
    company_id = uuid4()
    session, query = _session_with_first(None)

    CanonicalExcelIngestionService().get_current_accepted(session, company_id)

    filter_args = query.filter.call_args.args
    rendered_filters = ' '.join(str(item) for item in filter_args)
    assert 'datasets.company_id' in rendered_filters
    assert 'datasets.is_active' in rendered_filters
    assert 'datasets.is_deleted' in rendered_filters
    assert 'datasets.state' in rendered_filters
    order_args = query.order_by.call_args.args
    rendered_order = ' '.join(str(item) for item in order_args)
    assert 'dataset_events.created_at DESC' in rendered_order
    assert 'dataset_events.id DESC' in rendered_order
