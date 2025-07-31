"""
FastMCP quickstart example.

cd to the `examples/snippets/clients` directory and run:
    uv run server fastmcp_quickstart stdio
"""

from mcp.server.fastmcp import FastMCP
from decorators import require_groups
from datasets import fetch_dataset, api, read_document, iter_document_filenames
import re
from dotenv import load_dotenv
import os

# Import authentication utilities
try:
    from auth_utils import get_user_token, get_user_info_and_token_simple
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    

# Create an MCP server
mcp = FastMCP("Demo")
API_NAME= "MEDICARE_API"
DOCUMENT_CATEGORY = "medicare"

load_dotenv()
AUTH_GROUPS = os.getenv("AUTH_GROUPS", "Unauthorized").split(",")

# Add an example from the medicare API
@mcp.resource("medicare://nursing-home-dataset")
@require_groups(AUTH_GROUPS)
def get_medicare_nursing_home_dataset() -> dict:
    """Fetch datasets from the Medicare API"""
    return fetch_dataset(API_NAME, "nursing_home_dataset")

@mcp.resource("medicare://deficit-reduction-dataset")
@require_groups(AUTH_GROUPS)
def get_deficit_reduction_dataset() -> dict:
    """Fetch datasets from the Medicare API. This example causes failure to demonstrate
    authentication and authorization failures."""
    return fetch_dataset(API_NAME, "deficit_reduction_dataset")

@mcp.resource("medicare://secure-data")
@require_groups(AUTH_GROUPS)
def get_secure_medicare_data() -> dict:
    """Fetch secure Medicare data. Requires specific group membership."""
    return {
        "message": "Access granted to secure Medicare data",
        "data": "This would contain sensitive Medicare information",
        "access_level": "group_restricted"
    }

@mcp.resource("medicare://admin-only-data")
@require_groups(AUTH_GROUPS)
def get_admin_only_data() -> dict:
    """Fetch admin-only Medicare data. Requires specific directory roles."""
    return {
        "message": "Access granted to administrative Medicare data",
        "data": "This would contain administrative Medicare information",
        "access_level": "admin_only"
    }


@mcp.resource("medicare://datasets")
def list_medicare_datasets() -> dict:
    """List available Medicare datasets from the datasets module."""
    return api[API_NAME]["datasets"]

@mcp.resource("documents://{filename}")
def get_document_resource(filename: str) -> str:
    """Expose Medicare documents as resources."""
    return read_document(DOCUMENT_CATEGORY, filename)

@mcp.tool()
def get_medicare_dataset_row_count(dataset_name: str) -> int:
    """Return the number of rows in a Medicare dataset by dataset name."""
    data = fetch_dataset(API_NAME, dataset_name)
    return len(data) if isinstance(data, list) else 0

@mcp.tool()
def get_medicare_document(filename: str) -> str:
    """Return the contents of a Medicare document from the documents/medicare folder."""
    return read_document(DOCUMENT_CATEGORY, filename)

@mcp.tool()
def answer_from_medicare_documents(question: str) -> str:
    """Answer a question using the contents of all Medicare documents in documents/medicare."""
    answers = []
    for fname in iter_document_filenames(DOCUMENT_CATEGORY):
        content = read_document(DOCUMENT_CATEGORY, fname)
        # Simple keyword match for now
        if re.search(re.escape(question), content, re.IGNORECASE):
            answers.append(f"From {fname}:\n{content}")
    if answers:
        return "\n\n".join(answers)
    # If no direct match, return a summary of all documents
    summary = []
    for fname in iter_document_filenames(DOCUMENT_CATEGORY):
        lines = read_document(DOCUMENT_CATEGORY, fname).splitlines()
        summary.append(f"From {fname}:\n{chr(10).join(lines[:5])}...")
    return "No direct answer found. Here are summaries:\n" + "\n\n".join(summary)

@mcp.tool()
def authenticate_user() -> dict:
    """
    Authenticate the current user and return their information and access token.
    This token can be used by the agent for further API calls to Microsoft services.
    """
    if not AUTH_AVAILABLE:
        return {
            "error": "Authentication not available. Install azure-identity and msgraph-sdk packages.",
            "status": "unavailable"
        }
    
    result = get_user_info_and_token_simple()
    
    if result["status"] == "success":
        return {
            "user": {
                "name": result["display_name"],
                "email": result["email"],
                "job_title": result["job_title"],
                "group_count": result["group_count"]
            },
            "authentication": {
                "status": "authenticated",
                "token_preview": result["access_token"][:20] + "...",
                "expires_on": result["token_expires_on"]
            }
            # Note: Full token is available internally but not exposed in responses
        }
    else:
        return {
            "error": result["error"],
            "status": "authentication_failed"
        }

@mcp.tool()
def get_user_access_token() -> dict:
    """
    Get just the access token for API calls to Microsoft Graph or other Azure services.
    Simplified version for when only the token is needed.
    """
    if not AUTH_AVAILABLE:
        return {
            "error": "Authentication not available. Install azure-identity and msgraph-sdk packages.",
            "status": "unavailable"
        }
    
    result = get_user_token()
    
    if result["status"] == "success":
        return {
            "access_token": result["access_token"],
            "expires_on": result["expires_on"],
            "status": "success"
        }
    else:
        return {
            "error": result["error"],
            "status": "failed"
        }

@mcp.tool()
def list_medicare_documents() -> list:
    """List all Medicare documents available."""
    return iter_document_filenames(DOCUMENT_CATEGORY)

@mcp.tool()
def get_medicare_dataset_columns(dataset_name: str) -> list:
    """Return the column names/fields for a given Medicare dataset (if available)."""
    data = fetch_dataset(API_NAME, dataset_name)
    if isinstance(data, list) and data:
        return list(data[0].keys())
    return []

@mcp.tool()
def summarize_medicare_dataset_column(dataset_name: str, column: str) -> dict:
    """Provide min, max, and average for a numeric column in a Medicare dataset."""
    data = fetch_dataset(API_NAME, dataset_name)
    values = [row.get(column) for row in data if isinstance(row.get(column), (int, float))]
    if not values:
        return {"error": "No numeric data found for column."}
    return {
        "min": min(values),
        "max": max(values),
        "average": sum(values) / len(values)
    }

@mcp.prompt()
def explain_nursing_home_dataset() -> str:
    """Generate an explanation of the nursing home dataset and how to use it."""
    return (
        "The nursing home dataset contains facility-level information about "
        "active residents currently in nursing homes. You can use this data to "
        "analyze trends, compare facilities, or answer questions about nursing "
        "home populations. If you need help interpreting specific fields, ask for "
        "details about the column names or data structure. "
        "Do not share any personally identifiable information. "
        "If asked for sensitive data, politely refuse."
    )

@mcp.prompt()
def explain_deficit_reduction_dataset() -> str:
    """Explain the Deficit Reduction Act Hospital-Acquired Condition dataset 
    and its use."""
    return (
        "The Deficit Reduction Act Hospital-Acquired Condition dataset provides "
        "hospital-level measures for four conditions included in the DRA HAC payment "
        "provision. Use this data to analyze hospital performance, compare rates of "
        "hospital-acquired conditions, or answer questions about compliance and "
        "quality. "
        "If you need help with specific fields, ask for details about the column names "
        "or data structure."
    )

@mcp.prompt()
def explain_medicare_document_access() -> str:
    """Explain how to access and use the Medicare documents."""
    return (
        "You can access Medicare documents using the get_medicare_document tool or the documents:// resource. "
        "Use list_medicare_documents to see available files. For example, to read a document, use "
        "get_medicare_document('nursing_home_overview.txt') or access documents://nursing_home_overview.txt."
    )

@mcp.prompt()
def explain_available_tools() -> str:
    """Summarize what tools are available and what they do."""
    base_tools = (
        "Available tools include: get_medicare_dataset_row_count (count rows in a dataset), "
        "get_medicare_document (read a document), answer_from_medicare_documents (answer questions from documents), "
        "list_medicare_documents (list all documents), get_medicare_dataset_columns (list dataset columns), and "
        "summarize_medicare_dataset_column (summarize a numeric column)."
    )
    
    if AUTH_AVAILABLE:
        auth_tools = (
            " Authentication tools: authenticate_user (get user info and token), "
            "get_user_access_token (get just the access token for API calls)."
        )
        return base_tools + auth_tools
    else:
        return base_tools + " Authentication tools are not currently available."

@mcp.prompt()
def explain_tool_resource_flow() -> str:
    """Explain to the agent how the different tools and resources work together."""
    return (
        "To answer user questions, first use the list_medicare_datasets resource to discover available datasets. "
        "For questions about the data, use get_medicare_dataset_columns to see available fields, and get_medicare_dataset_row_count "
        "to find out how many records are present. If the user asks for specific data, fetch it using the appropriate resource, such as "
        "medicare://nursing-home-dataset/{user_role}. For document-based questions, use list_medicare_documents to see available files, "
        "get_medicare_document to read a file, and answer_from_medicare_documents to search all documents for relevant information. "
        "Summarize or analyze data using summarize_medicare_dataset_column. Use the explanation prompts for guidance on each dataset or tool."
    )

@mcp.prompt()
def explain_authentication() -> str:
    """Explain how authentication works in this MCP server."""
    if AUTH_AVAILABLE:
        return (
            "This MCP server supports user authentication through Microsoft Entra ID. "
            "Use the 'authenticate_user' tool to sign in and get user information plus an access token. "
            "The token can be used for subsequent API calls to Microsoft Graph or other Azure services. "
            "Use 'get_user_access_token' for a simplified token-only response. "
            "Authentication is handled automatically through your browser or existing Windows credentials."
        )
    else:
        return (
            "Authentication is not currently available. To enable user authentication, "
            "install the required packages: azure-identity and msgraph-sdk. "
            "Once installed, you can use authenticate_user and get_user_access_token tools."
        )

@mcp.prompt()
def explain_role_escalation_policy() -> str:
    """Explain the agent's role escalation policy for authorization."""
    return (
        "By default, you should perform all operations as a 'guest'. If you encounter an authorization error, "
        "ask the user if they would like to proceed as an 'admin'. If the user agrees, retry the operation as 'admin' "
        "and remember this role for the rest of the session. Always use the least privileged role unless escalation is required. "
        "If authentication is enabled, you can also use the authenticate_user tool to get proper user credentials."
    )

@mcp.prompt()
def notify_user_processing(task_description: str) -> str:
    """Notify the user that their request is being processed, reiterating the task."""
    return (
        f"Thank you for your request. I am now processing the following task: {task_description}. "
        "Please hold on while I complete this for you."
    )
