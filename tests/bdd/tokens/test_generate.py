# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import ast

from pytest_bdd import given, scenario, then, when
from pytest_bdd.parsers import parse


@scenario(
    "../features/tokens/generate.feature",
    "Admin uses HTTP API to generate a token",
)
def test_admin_uses_http_api_to_generate_a_token():
    """Admin uses HTTP API to generate a token."""


@given("the admin has the admin password", target_fixture="admin_passwd")
def the_admin_has_the_admin_password(get_admin_pwd):
    return get_admin_pwd


@given(
    "the admin gets an 'access_token' by logging in to '/api/v1/token' with a "
    "'write:token' scope",
    target_fixture="access_token",
)
def the_admin_has_generated_an_access_token_with_write_token(access_token):
    return access_token


@given(
    parse("the admin adds Authorization Bearer {token} in the 'headers'"),
    target_fixture="headers",
)
def the_admin_adds_authorization_token_in_the_headers(access_token, token):
    if token == "'access_token'":
        header_token = f"Bearer {access_token}"
    else:
        header_token = f"Bearer {token}"
    headers = {"Authorization": header_token}
    return headers


@given(
    parse(
        "the admin adds JSON payload with scopes: {scopes} and "
        "expires: {expires}"
    ),
    target_fixture="payload",
)
def the_admin_adds_payload(scopes, expires):
    if scopes == "None":
        scopes = None
        payload = {"scopes": scopes, "expires": expires}
    else:
        # convert list string "['str', 'str']" to python list['str', 'str']
        payload = {"scopes": ast.literal_eval(scopes), "expires": expires}

    return payload


@when(
    "the admin sends a POST request to '/api/v1/token/new'",
    target_fixture="response",
)
def the_admin_sends_request(test_client, headers, payload):
    response = test_client.post(
        url="/api/v1/token/new", headers=headers, json=payload
    )
    return response


@then("the admin should get status code '200'")
def the_admin_gets_status_code_200(response):
    assert response.status_code == 200, response.text


@then("the admin should get 'access_token' with a new token")
def the_admin_gets_access_token(response):
    assert response.json()["access_token"] is not None


@scenario(
    "../features/tokens/generate.feature",
    "Admin cannot generate Token using HTTP API with an invalid expires",
)
def test_admin_cannot_generate_token_using_api_with_invalid_expires():
    """Admin cannot generate Token using HTTP API with an invalid expires"""


@when(
    "the admin sends a POST request to '/api/v1/token/new' with invalid "
    "'expires' in 'payload'",
    target_fixture="response",
)
def the_admin_sends_with_invalid_expires_in_payload(
    test_client, headers, payload
):
    response = test_client.post(
        url="/api/v1/token/new", headers=headers, json=payload
    )
    return response


@then("the admin should get status code '422'")
def the_admin_should_get_status_code_422_invalid_expires(response):
    assert response.status_code == 422, response.text


@scenario(
    "../features/tokens/generate.feature",
    "Admin cannot generate Token using HTTP API for certain scopes",
)
def test_admin_cannot_generate_token_using_http_rest_api_for_certain_scopes():
    """Admin cannot generate Token using HTTP API for certain scopes."""


@when(
    "the admin sends a POST request to '/api/v1/token/new' with not allowed "
    "'scopes' in 'payload'",
    target_fixture="response",
)
def the_admin_sends_request_with_invalid_scopes(test_client, headers, payload):
    response = test_client.post(
        url="/api/v1/token/new", headers=headers, json=payload
    )
    return response


@then("the admin should get status code '422'")
def the_admin_should_get_status_code_422_scopes(response):
    assert response.status_code == 422, response.text


@scenario(
    "../features/tokens/generate.feature",
    "Admin is Unauthorized to generate using HTTP API with an invalid token",
)
def test_admin_is_unauthorized_to_generate_invalid_token():
    """
    Admin is Unauthorized to generate using HTTP API with an invalid token.
    """


@when(
    "the admin sends a POST request to '/api/v1/token/new' with invalid "
    "'access_token' in the headers",
    target_fixture="response",
)
def the_admin_sends_a_invalid_access_token_in_headers(
    test_client, headers, payload
):
    response = test_client.post(
        url="/api/v1/token/new",
        headers=headers,
        json=payload,
    )
    return response


@then("the admin should get status code '401'")
def the_admin_should_get_status_code_401(response):
    assert response.status_code == 401, response.text


@then("the admin should get 'Failed to validate token' in the body")
def the_admin_should_get_failed_to_validate_token(response):
    assert response.json()["detail"]["error"] == "Failed to validate token"
