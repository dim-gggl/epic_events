"""
Constants and common messages used throughout the Epic Events CRM application.
"""

# Common error messages
OPERATION_DENIED = "OPERATION DENIED"
INVALID_TOKEN = "Invalid access token"
NO_AUTH_TOKEN = "No authentication token available. Please login first."
NOT_AUTHORIZED = "You are not authorized to access this resource"
NOT_FOUND = "not found"
CANNOT_DELETE_WITH_ASSOCIATIONS = "Cannot delete with associated records"
CANNOT_DELETE_SELF = "You cannot delete your own account"
PASSWORDS_DO_NOT_MATCH = "Passwords do not match"
INVALID_EMAIL = "Invalid email address"
INVALID_USERNAME = "Invalid username"
INVALID_PASSWORD = "Invalid password"
INVALID_ROLE_ID = "Invalid role id"
INVALID_PHONE = "Invalid phone number. Please try again"
INVALID_DATE_FORMAT = "Invalid date. Expected format: dd/mm/yyyy"
INVALID_CHOICE = "Invalid choice"
INVALID_CLIENT_ID = "Client ID must be an integer"
INVALID_CONTRACT_ID = "Contract ID must be an integer"
INVALID_EVENT_ID = "Event ID must be an integer"
INVALID_USER_ID = "User ID must be an integer"
INVALID_COMMERCIAL_ID = "Commercial ID must be a positive integer"
INVALID_PARTICIPANT_COUNT = "Participant count must be a positive integer"
INVALID_TOTAL_AMOUNT = "Total amount must be a positive number"
INVALID_REMAINING_AMOUNT = "Remaining amount must be a positive number or 0"
INVALID_YES_NO = "Bad input, expected 'yes' or 'no'"
INVALID_END_DATE = "End date must be on or after start date"
INVALID_END_DATE_CHOICE = "Please choose 'e' for end date or 's' for start date"

# Success messages
LOGIN_SUCCESSFUL = "Login successful"
USER_CREATED = "User created successfully"
USER_UPDATED = "User updated successfully"
USER_DELETED = "User deleted successfully"
CLIENT_CREATED = "Client created successfully"
CLIENT_UPDATED = "Client updated successfully"
CLIENT_DELETED = "Client deleted successfully"
CONTRACT_CREATED = "Contract created successfully"
CONTRACT_UPDATED = "Contract updated successfully"
CONTRACT_DELETED = "Contract deleted successfully"
EVENT_CREATED = "Event created successfully"
EVENT_UPDATED = "Event updated successfully"
EVENT_DELETED = "Event deleted successfully"
EVENT_ASSIGNED = "Event assigned successfully"

# Permission messages
PERMISSION_DENIED = "You don't have permission to"
ONLY_MANAGEMENT = "This action is only available to management users"
ONLY_COMMERCIAL = "This action is only available to commercial users"
ONLY_SUPPORT = "This action is only available to support users"
ONLY_OWN_RECORDS = "You can only access your own records"
ONLY_ASSIGNED_RECORDS = "You can only access records assigned to you"

# Required field messages
REQUIRED_FIELD = "is required"
CANNOT_BE_EMPTY = "cannot be empty"
MUST_BE_INTEGER = "must be an integer"
MUST_BE_POSITIVE = "must be a positive number"

# Date format
DATE_FORMAT = "%d/%m/%Y"

# Role mappings
ROLE_NAMES = {
    1: "Management",
    2: "Commercial", 
    3: "Support"
}

# Common validation patterns
USERNAME_MIN_LENGTH = 5
USERNAME_MAX_LENGTH = 64
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
ROLE_MIN_ID = 1
ROLE_MAX_ID = 3

# Table styles
TABLE_STYLE_HEADER = "epic_style"
TABLE_STYLE_CONTENT = "grey100"
TABLE_STYLE_ID = "bold gold1"
PANEL_STYLE_SUCCESS = "bold bright_green"
PANEL_STYLE_ERROR = "bold bright_red"
PANEL_STYLE_WARNING = "bold bright_yellow"
PANEL_STYLE_INFO = "bold gold1"