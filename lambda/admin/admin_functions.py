import json

import boto3

from shared.utils.lambda_utils import ENV_COGNITO
from shared.apiutils.router import path_pattern_matcher, BeaconError


cognito_client = boto3.client("cognito-idp")
USER_POOL_ID = ENV_COGNITO.COGNITO_USER_POOL_ID


def get_username_by_email(email):
    response = cognito_client.list_users(
        UserPoolId=USER_POOL_ID, Filter=f'email = "{email}"', Limit=1
    )

    if response.get("Users"):
        return response["Users"][0]["Username"]

    raise Exception(f"User with email {email} not found")


@path_pattern_matcher("users", "post")
def add_user(event):
    body_dict = json.loads(event.get("body"))
    email = body_dict.get("email")
    first_name = body_dict.get("first_name")
    last_name = body_dict.get("last_name")

    if not all([email, first_name, last_name]):
        raise BeaconError(
            error_code="BeaconAddUserMissingAttribute",
            error_message="Missing required attributes!",
        )

    cognito_client.admin_create_user(
        UserPoolId=USER_POOL_ID,
        Username=email,
        DesiredDeliveryMediums=["EMAIL"],
        UserAttributes=[
            {"Name": "email", "Value": email},
            {"Name": "given_name", "Value": first_name},
            {"Name": "family_name", "Value": last_name},
            {"Name": "email_verified", "Value": "true"},
        ],
    )
    print(f"User {email} created successfully!")
    return {"success": True}


@path_pattern_matcher("users", "get")
def get_users(event):
    pagination_token = (event.get("queryStringParameters") or dict()).get(
        "pagination_token", None
    )
    limit = int((event.get("queryStringParameters") or dict()).get("limit", 60))
    filterKey = (event.get("queryStringParameters") or dict()).get("key", None)
    filterValue = (event.get("queryStringParameters") or dict()).get("query", None)
    kwargs = {
        "UserPoolId": USER_POOL_ID,
        "Limit": limit,
    }
    if pagination_token:
        kwargs["PaginationToken"] = pagination_token
    if filterKey and filterValue:
        kwargs["Filter"] = f'{filterKey} ^= "{filterValue}"'

    response = cognito_client.list_users(**kwargs)
    # Extract users and next pagination token
    users = response.get("Users", [])
    next_pagination_token = response.get("PaginationToken", None)

    return {"users": users, "pagination_token": next_pagination_token}


@path_pattern_matcher("users/{email}", "delete")
def delete_user(event, email):
    username = get_username_by_email(email)
    cognito_client.admin_delete_user(UserPoolId=USER_POOL_ID, Username=username)

    print(f"User with email {email} removed successfully!")
    return {"success": True}


@path_pattern_matcher("users/{email}/groups", "get")
def user_groups(event, email):
    username = get_username_by_email(email)
    response = cognito_client.admin_list_groups_for_user(
        Username=username, UserPoolId=USER_POOL_ID
    )

    groups = response.get("Groups", [])
    print(f"User with email {email} has {len(groups)} groups")
    return {"groups": groups}


@path_pattern_matcher("users/{email}/groups", "post")
def update_user_groups(event, email):
    body_dict = json.loads(event.get("body"))
    chosen_groups = []
    removed_groups = []

    if body_dict["groups"]["admin"]:
        chosen_groups.append("admin-group")
    else:
        removed_groups.append("admin-group")
    if body_dict["groups"]["record"]:
        chosen_groups.append("record-access-user-group")
    else:
        removed_groups.append("record-access-user-group")
    if body_dict["groups"]["count"]:
        chosen_groups.append("count-access-user-group")
    else:
        removed_groups.append("count-access-user-group")
    if body_dict["groups"]["boolean"]:
        chosen_groups.append("boolean-access-user-group")
    else:
        removed_groups.append("boolean-access-user-group")

    username = get_username_by_email(email)
    for group_name in chosen_groups:
        cognito_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID, Username=username, GroupName=group_name
        )

    for group_name in removed_groups:
        cognito_client.admin_remove_user_from_group(
            UserPoolId=USER_POOL_ID, Username=username, GroupName=group_name
        )

    print(
        f"User with email {email} added to {len(chosen_groups)} and removed from {len(removed_groups)} groups"
    )
    return {"success": True}
