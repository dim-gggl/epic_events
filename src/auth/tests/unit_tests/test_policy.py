import pytest

import src.auth.policy as policy


def test_enforce_any_or_own_allows_global(monkeypatch):
    monkeypatch.setattr(policy, 
                        "get_user_id_and_role_from_token", 
                        lambda tok: (10, 2))
    monkeypatch.setattr(policy, 
                        "get_effective_permissions", 
                        lambda rid: {"client:update"})

    # Should not raise
    policy.enforce_any_or_own("tok", "client", "update", owner_user_id=99)


def test_enforce_any_or_own_allows_own_when_owner(monkeypatch):
    monkeypatch.setattr(policy, 
                        "get_user_id_and_role_from_token", 
                        lambda tok: (7, 3))
    monkeypatch.setattr(policy, 
                        "get_effective_permissions", 
                        lambda rid: {"client:update:own"})

    # Owner matches -> allowed
    policy.enforce_any_or_own("tok", "client", "update", owner_user_id=7)

    # Owner mismatch -> denied
    with pytest.raises(PermissionError):
        policy.enforce_any_or_own("tok", "client", "update", owner_user_id=8)


def test_enforce_any_or_assigned(monkeypatch):
    monkeypatch.setattr(policy, 
                        "get_user_id_and_role_from_token", 
                        lambda tok: (4, 3))
    monkeypatch.setattr(policy, 
                        "get_effective_permissions", 
                        lambda rid: {"event:update:assigned"})

    # Assigned matches -> ok
    policy.enforce_any_or_assigned("tok", "event", "update", assigned_user_id=4)

    # Assigned mismatch -> denied
    with pytest.raises(PermissionError):
        policy.enforce_any_or_assigned("tok", "event", "update", assigned_user_id=9)


def test_can_create_event_for_contract(monkeypatch):
    # Global create allowed
    monkeypatch.setattr(policy, 
                        "get_user_id_and_role_from_token", 
                        lambda tok: (11, 1))
    monkeypatch.setattr(policy, 
                        "get_effective_permissions", 
                        lambda rid: {"event:create"})
    assert policy.can_create_event_for_contract("tok", 
                                                contract_commercial_id=99) is True

    # Only own_client, matching commercial -> allowed
    monkeypatch.setattr(policy, "get_user_id_and_role_from_token", lambda tok: (22, 2))
    monkeypatch.setattr(
        policy, "get_effective_permissions", lambda rid: {"event:create:own_client"}
    )
    assert policy.can_create_event_for_contract("tok", 
                                                contract_commercial_id=22) is True

    # Only own_client, mismatch -> denied
    assert policy.can_create_event_for_contract("tok", 
                                                contract_commercial_id=23) is False

