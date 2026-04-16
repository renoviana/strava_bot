from shared.user import get_user

MEMBROS = {
    "Joao": {"athlete_id": 1, "access_token": "t1", "refresh_token": "r1", "last_activity_date": None},
    "Maria": {"athlete_id": 2, "access_token": "t2", "refresh_token": "r2", "last_activity_date": None},
}


def test_get_user_by_id():
    result = get_user(MEMBROS, user_id=1)
    assert result == {"id": 1, "name": "Joao"}


def test_get_user_by_name():
    result = get_user(MEMBROS, user_name="Maria")
    assert result == {"id": 2, "name": "Maria"}


def test_get_user_id_not_found():
    result = get_user(MEMBROS, user_id=999)
    assert result == {}


def test_get_user_name_not_found():
    result = get_user(MEMBROS, user_name="Pedro")
    assert result == {}


def test_get_user_no_params():
    result = get_user(MEMBROS)
    assert result == {}


def test_get_user_empty_membros():
    result = get_user({}, user_id=1)
    assert result == {}
