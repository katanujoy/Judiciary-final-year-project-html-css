import re
from datetime import datetime

def validate_email_domain(email: str) -> bool:
    """
    Validate that the email belongs to the judiciary domain.

    Args:
        email (str): Email address to validate.

    Returns:
        bool: True if email domain is allowed, False otherwise.
    """
    if not email or '@' not in email:
        return False
    
    allowed_domains = {'judiciary.go.ke', 'judiciary.ke'}
    domain = email.split('@')[-1].lower()
    return domain in allowed_domains


def validate_file_type(filename: str) -> bool:
    """
    Validate uploaded file type.

    Args:
        filename (str): Name of the file.

    Returns:
        bool: True if file extension is allowed, False otherwise.
    """
    if not filename or '.' not in filename:
        return False
    
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions


def validate_case_number(case_number: str) -> bool:
    """
    Validate case number format: e.g., CR-2024-001

    Format: PREFIX-YYYY-NUMBER (PREFIX: 1-4 uppercase letters, NUMBER: 3-5 digits)

    Args:
        case_number (str): Case number string.

    Returns:
        bool: True if format matches, False otherwise.
    """
    if not case_number:
        return False
    pattern = r'^[A-Z]{1,4}-\d{4}-\d{3,5}$'
    return bool(re.match(pattern, case_number))


def validate_date_format(date_string: str) -> bool:
    """
    Validate date format YYYY-MM-DD.

    Args:
        date_string (str): Date string.

    Returns:
        bool: True if valid date format, False otherwise.
    """
    if not date_string:
        return False
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False
