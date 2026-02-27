import urllib.parse
import re

def validate_target(target: str) -> bool:
    """
    Validates the target format.
    Authorized IPs and domains restriction was removed per user request.
    The user is responsible for testing only authorized infrastructure.
    """
    if not target:
        return False
        
    # Basic URL/IP validation
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme and parsed.netloc:
        return True
        
    # Simple IP/domain regex fallback
    domain_regex = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    ip_regex = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')
    
    if domain_regex.match(target) or ip_regex.match(target):
        return True
        
    return False
