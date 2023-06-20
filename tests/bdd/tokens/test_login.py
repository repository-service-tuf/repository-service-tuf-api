# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
from pytest_bdd import given, scenario, then, when
from pytest_bdd.parsers import parse


@scenario("../features/tokens/login.feature", "Login using RSTUF API")
def test_login_using_rstuf_api():
    """Login using RSTUF API."""


@given(
    parse(
        "the API requester prepares 'data' with {username}, {password},"
        "{scope}, {expires}"
    ),
    target_fixture="data",
)
def the_api_requester_prepares_data(username, password, scope, expires):
    if expires == "None":
        expires = None
    else:
        expires = int(expires)

    return {
        "username": username,
        "password": password,
        "scope": scope,
        "expires": expires,
    }


@when(
    "the API requester sends a 'POST' method to '/api/v1/token' with 'data'",
    target_fixture="response",
)
def the_api_requester_sends_data(data, test_client):
    return test_client.post(url="/api/v1/token", data=data)


@then("the API requester should get status code '200'")
def the_api_requester_should_get_status_code_200(response):
    assert response.status_code == 200


@then("the API requester should get 'access_token' in response body")
def the_api_requester_should_get_access_token_in_response_body(response):
    assert response.json()["access_token"] is not None


@scenario(
    "../features/tokens/login.feature",
    "Login using RSTUF API gets Unauthorized",
)
def test_login_using_rstuf_api_gets_unauthorized():
    """Login using RSTUF API gets Unauthorized."""


@when(
    "the API requester sends a 'POST' method to '/api/v1/token' with invalid "
    "username/password in 'data'",
    target_fixture="unauthorized_response",
)
def the_api_requester_sends_data_unauthorized(data, test_client):
    return test_client.post(url="/api/v1/token", data=data)


@then("the API requester should get status code '401'")
def the_api_requester_should_get_status_code_401(unauthorized_response):
    assert unauthorized_response.status_code == 401


@then(
    "the API requester should get 'detail: Unauthorized' in the response body"
)
def the_api_requester_should_get_detail_unauthorized_in_the_response_body(
    unauthorized_response,
):
    assert unauthorized_response.json()["detail"] == "Unauthorized"


@scenario(
    "../features/tokens/login.feature",
    "Login using RSTUF API gets forbidden for invalid scopes",
)
def test_login_using_rstuf_api_gets_forbidden_for_invalid_scopes():
    """Login using RSTUF API gets forbidden for invalid scopes."""


@when(
    "the API requester sends a 'POST' method to '/api/v1/token' with invalid "
    "scopes in 'data'",
    target_fixture="invalid_scope_response",
)
def the_api_requester_sends_invalid_scopes_in_data(data, test_client):
    return test_client.post(url="/api/v1/token", data=data)


@then("the API requester should get status code '403'")
def the_api_requester_should_get_status_code_403(invalid_scope_response):
    assert invalid_scope_response.status_code == 403


@then("the API requester should get 'scope invalid' in the response body")
def the_api_requester_should_get_scope_invalid_in_the_response_body(
    invalid_scope_response,
):
    assert "forbidden" in invalid_scope_response.json()["detail"]["error"]
