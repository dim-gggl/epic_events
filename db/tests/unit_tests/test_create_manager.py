"""
Unit tests for db.create_manager
"""
import sys
import os
import pytest
from unittest.mock import patch, Mock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

import db.create_manager as cm


class TestEnsureRoot:
    """Test the root privilege checking functionality."""
    
    def test_ensure_root_posix_success(self):
        """Test that _ensure_root passes when running as root on POSIX."""
        if os.name == 'nt':
            pytest.skip("Windows test")
        
        with patch('os.geteuid', return_value=0):
            # Should not raise SystemExit when running as root
            try:
                cm._ensure_root()
            except SystemExit:
                pytest.fail("_ensure_root() raised SystemExit when running as root")
    
    def test_ensure_root_posix_denied(self, capsys):
        """Test that _ensure_root exits when not running as root on POSIX."""
        if os.name == 'nt':
            pytest.skip("Windows test")
        
        with patch('os.geteuid', return_value=1000):
            with pytest.raises(SystemExit):
                cm._ensure_root()
            
            captured = capsys.readouterr()
            assert "root privileges" in captured.err
    
    def test_ensure_root_windows_success(self):
        """Test that _ensure_root passes when running as admin on Windows."""
        if os.name != 'nt':
            pytest.skip("Windows test")
        
        with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=1):
            try:
                cm._ensure_root()
            except SystemExit:
                pytest.fail("_ensure_root() raised SystemExit when running as admin")
    
    def test_ensure_root_windows_denied(self, capsys):
        """Test that _ensure_root exits when not running as admin on Windows."""
        if os.name != 'nt':
            pytest.skip("Windows test")
        
        with patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=0):
            with pytest.raises(SystemExit):
                cm._ensure_root()
            
            captured = capsys.readouterr()
            assert "root" in captured.err


class TestInitManager:
    """Test the manager initialization functionality."""
    
    def test_init_manager_with_valid_inputs(self, capsys):
        """Test successful manager creation with valid inputs."""
        # Mock the root check
        with patch('db.create_manager._ensure_root'), \
             patch('db.create_manager.Session') as mock_session_class, \
             patch('db.create_manager.hash_password', return_value='hashed_password'):
            
            # Setup session mock
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            
            # Mock role exists
            mock_role = Mock()
            mock_role.id = 1
            mock_session.scalar.return_value = mock_role  # Role exists, no existing user
            
            # Call with valid inputs
            cm.init_manager(
                username="testmanager",
                full_name="Test Manager", 
                email="test@example.com"
            )
            
            # Verify user was created with correct data
            mock_session.add.assert_called_once()
            created_user = mock_session.add.call_args[0][0]
            assert created_user.username == "testmanager"
            assert created_user.full_name == "Test Manager"
            assert created_user.email == "test@example.com"
            assert created_user.password_hash == "hashed_password"
            assert created_user.role_id == 1
            
            # Verify session was committed
            mock_session.commit.assert_called_once()
            
            # Verify success message
            captured = capsys.readouterr()
            assert "Management user 'testmanager' created with success" in captured.out
    
    def test_init_manager_creates_role_if_missing(self):
        """Test that management role is created if it doesn't exist."""
        with patch('db.create_manager._ensure_root'), \
             patch('db.create_manager.Session') as mock_session_class, \
             patch('db.create_manager.hash_password', return_value='hashed_password'):
            
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            
            # Mock role doesn't exist initially, then no existing user
            mock_session.scalar.side_effect = [None, None]  # No role, no existing user
            
            cm.init_manager(
                username="testmanager",
                full_name="Test Manager",
                email="test@example.com"
            )
            
            # Verify role was created
            assert mock_session.add.call_count == 2  # Role + User
            mock_session.flush.assert_called_once()
            mock_session.commit.assert_called_once()
    
    def test_init_manager_exits_on_duplicate_email(self, capsys):
        """Test that init_manager exits when email already exists."""
        with patch('db.create_manager._ensure_root'), \
             patch('db.create_manager.Session') as mock_session_class, \
             patch('db.create_manager.hash_password', return_value='hashed_password'):
            
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            
            # Mock role exists, but user with email exists
            mock_role = Mock()
            mock_role.id = 1
            existing_user = Mock()  # User with same email exists
            mock_session.scalar.side_effect = [mock_role, existing_user]
            
            with pytest.raises(SystemExit):
                cm.init_manager(
                    username="testmanager",
                    full_name="Test Manager",
                    email="existing@example.com"
                )
            
            captured = capsys.readouterr()
            assert "Email already exists" in captured.out



