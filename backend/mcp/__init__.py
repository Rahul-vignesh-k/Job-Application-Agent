from backend.mcp.linkedin import LinkedInConnector
from backend.mcp.naukri import NaukriConnector
from backend.mcp.indeed import IndeedConnector
from backend.mcp.glassdoor import GlassdoorConnector

CONNECTORS = {
    "linkedin": LinkedInConnector,
    "naukri": NaukriConnector,
    "indeed": IndeedConnector,
    "glassdoor": GlassdoorConnector,
}
