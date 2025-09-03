"""
Unit tests for db.create_tables
"""
import sys
import os
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from db.create_tables import init_db


def test_init_db_creates_and_seeds():
    with patch('db.create_tables.Session') as MockSession, \
         patch('db.create_tables.metadata') as mock_meta, \
         patch('db.create_tables.engine') as mock_engine, \
         patch('db.create_tables._seed_roles') as seed:
        session = Mock()
        MockSession.return_value = session
        init_db()
        mock_meta.create_all.assert_called_once_with(mock_engine)
        seed.assert_called_once_with(session)
        session.commit.assert_called_once()
        session.close.assert_called_once()



