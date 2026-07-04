"""CONCEPT:OK-OS.governance.okta Unified Okta Management API facade.

Composes the domain clients (users, groups, apps, policies, system) over the
shared httpx base so one authenticated ``Api`` instance serves every tool.
"""

from okta_agent.api.api_client_apps import Api as AppsApi
from okta_agent.api.api_client_groups import Api as GroupsApi
from okta_agent.api.api_client_policies import Api as PoliciesApi
from okta_agent.api.api_client_system import Api as SystemApi
from okta_agent.api.api_client_users import Api as UsersApi

__version__ = "0.1.0"


class Api(UsersApi, GroupsApi, AppsApi, PoliciesApi, SystemApi):
    """All Okta Management API domains behind one client."""
