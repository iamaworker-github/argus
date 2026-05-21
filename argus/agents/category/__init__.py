from argus.agents.category.base import CategoryAgent
from argus.agents.category.web_agent import WebSecurityAgent
from argus.agents.category.network_agent import NetworkSecurityAgent
from argus.agents.category.cloud_agent import CloudSecurityAgent
from argus.agents.category.api_agent import APISecurityAgent
from argus.agents.category.identity_agent import IdentityAccessAgent
from argus.agents.category.code_agent import CodeAnalysisAgent
from argus.agents.category.recon_agent import ReconOSINTAgent

CATEGORY_MAP = {
    "web": WebSecurityAgent,
    "network": NetworkSecurityAgent,
    "cloud": CloudSecurityAgent,
    "api": APISecurityAgent,
    "identity": IdentityAccessAgent,
    "code": CodeAnalysisAgent,
    "recon": ReconOSINTAgent,
}
