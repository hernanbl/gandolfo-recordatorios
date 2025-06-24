"""
Utilities for handling phone number normalization and validation.
"""

def strip_prefixes(number: str) -> tuple:
    """
    Helper function to strip all prefixes and get the base number.
    Returns (base_number, area_code)
    """
    area_code = '11'  # Default to Buenos Aires
    
    # Remove international prefix
    if number.startswith('+549'):
        base = number[4:]
    elif number.startswith('+54'):
        base = number[3:]
    elif number.startswith('549'):
        base = number[3:]
    elif number.startswith('54'):
        base = number[2:]
    else:
        base = number

    # Handle area codes
    if base.startswith('011'):
        base = base[3:]
    elif base.startswith('11'):
        base = base[2:]
    # Handle mobile prefix
    elif base.startswith('15'):
        base = base[2:]
    
    # If the remaining number is 10 digits, extract area code
    if len(base) >= 10:
        area_code = base[:2]
        base = base[2:]
    elif len(base) == 8:
        # 8 digits means it's a Buenos Aires number
        area_code = '11'
    
    return base, area_code

def normalize_argentine_phone(phone_number: str) -> str:
    """
    Normalizes Argentine phone numbers to canonical format: +549{area}{number}
    Examples:
    - +5491166686255 -> +5491166686255 (already correct)
    - +541166686255 -> +5491166686255 (adds 9)
    - 1166686255 -> +5491166686255 (adds +549)
    - whatsapp:+5491166686255 -> +5491166686255 (removes whatsapp:)
    - 011-1166686255 -> +5491166686255 (converts area code)
    - 15-6668-6255 -> +5491166686255 (handles mobile prefix)
    """
    # Remove whatsapp: prefix if present
    if phone_number.startswith('whatsapp:'):
        phone_number = phone_number[9:]
    
    # Remove any non-digit characters except +
    clean_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # If already in correct format, return as is
    if clean_number.startswith('+5491'):
        return clean_number
    
    # Strip all prefixes and get base number and area code
    base_number, area_code = strip_prefixes(clean_number.replace('+', ''))
    
    # Format the final number
    return f"+549{area_code}{base_number}"

def get_phone_variants(phone_number: str) -> list:
    """
    Gets standardized variants of a phone number for session lookup.
    Always returns the normalized number as the first variant.
    """
    normalized = normalize_argentine_phone(phone_number)
    variants = [normalized]
    
    # Add version without +
    if normalized.startswith('+'):
        variants.append(normalized[1:])
    
    # Add version with whatsapp: prefix if not present
    if not phone_number.startswith('whatsapp:'):
        variants.append(f"whatsapp:{normalized}")
    
    return variants