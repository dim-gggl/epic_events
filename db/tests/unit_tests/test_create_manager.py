"""
Unit tests for db.create_manager
"""
import sys
import os
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

import db.create_manager as cm


def test_ensure_root_posix_denied(monkeypatch, capsys):
    if os.name == 'nt':
        return
    with patch('os.geteuid', return_value=1000):
        try:
            cm._ensure_root()
        except SystemExit:
            pass
        out = capsys.readouterr().err
        assert 'sudo' in out


def test_init_manager_happy_path(monkeypatch):
    # Bypass root check
    with patch('db.create_manager._ensure_root'), \
         patch('db.create_manager.input', side_effect=['jdoe', 'John Doe', 'y', 'j@d.com']), \
         patch('db.create_manager.is_valid_username', return_value=True), \
         patch('db.create_manager.is_valid_email', return_value=True), \
         patch('db.create_manager._prompt_password', return_value='Passw0rd!'), \
         patch('db.create_manager.hash_password', return_value='HASH'), \
         patch('db.create_manager.Session') as MockSession, \
         patch('db.create_manager.select') as mock_select:
        # Configure context-managed Session
        session = Mock()
        cm_obj = Mock()
        cm_obj.__enter__ = Mock(return_value=session)
        cm_obj.__exit__ = Mock(return_value=False)
        MockSession.return_value = cm_obj

        # Role missing first, then user email missing
        session.scalar.side_effect = [None, None]

        # Execute
        cm.init_manager()
        assert session.add.called
        assert session.commit.called



