import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
import re
import locale
from typing import Optional

# Colombian date/time formatting functions
def format_colombian_date(date_value) -> str:
    """
    Format date to Colombian format: DD/MM/YYYY (without time)
    Accepts: datetime objects, date objects, or date strings in various formats
    Returns: String in DD/MM/YYYY format
    """
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return ""

    try:
        # If it's already a string
        if isinstance(date_value, str):
            # Check if it already looks like DD/MM/YYYY
            if len(date_value) == 10 and date_value[2] == '/' and date_value[5] == '/':
                # Already in correct format
                return date_value.strip()

            # Try to parse the string
            date_obj = pd.to_datetime(date_value)
        else:
            # Convert to datetime if it's not already
            date_obj = pd.to_datetime(date_value)

        # Return in DD/MM/YYYY format
        return date_obj.strftime('%d/%m/%Y')
    except:
        return str(date_value).strip()


def format_colombian_datetime(datetime_value) -> str:
    """
    Format datetime to Colombian format: DD/MM/YYYY HH:MM:SS
    Accepts: datetime objects or datetime strings
    Returns: String in DD/MM/YYYY HH:MM:SS format
    """
    if pd.isna(datetime_value) or datetime_value == "" or datetime_value is None:
        return ""

    try:
        if isinstance(datetime_value, str):
            datetime_obj = pd.to_datetime(datetime_value)
        else:
            datetime_obj = pd.to_datetime(datetime_value)

        return datetime_obj.strftime('%d/%m/%Y %H:%M:%S')
    except:
        return str(datetime_value).strip()


def get_colombian_date_now() -> str:
    """
    Get current date in Colombian format: DD/MM/YYYY
    Returns: String in DD/MM/YYYY format
    """
    return datetime.now().strftime('%d/%m/%Y')


def get_colombian_datetime_now() -> str:
    """
    Get current datetime in Colombian format: DD/MM/YYYY HH:MM:SS
    Returns: String in DD/MM/YYYY HH:MM:SS format
    """
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


def parse_colombian_date(date_str: str) -> Optional[str]:
    """
    Parse Colombian format date (DD/MM/YYYY) and return as ISO format (YYYY-MM-DD) for database storage
    This ensures compatibility with Supabase date storage

    Args:
        date_str: Date string in various formats

    Returns:
        ISO format date string (YYYY-MM-DD) or None if cannot parse
    """
    if pd.isna(date_str) or date_str == "" or date_str is None:
        return None

    try:
        date_obj = pd.to_datetime(date_str, dayfirst=True)
        # Return as ISO format for database storage
        return date_obj.strftime('%Y-%m-%d')
    except:
        return None


def parse_date_for_database(date_value) -> Optional[str]:
    """
    Parse any date format and return as ISO format (YYYY-MM-DD) for database storage
    This ensures compatibility with Supabase date fields

    Args:
        date_value: Date in any format (string, datetime object, etc.)

    Returns:
        ISO format date string (YYYY-MM-DD) or None
    """
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return None

    try:
        # Parse the date with day-first preference
        date_obj = pd.to_datetime(date_value, dayfirst=True)
        # Return as ISO format for database
        return date_obj.strftime('%Y-%m-%d')
    except:
        return None


def colombian_day_names():
    """Get Colombian Spanish day names"""
    return ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def colombian_month_names():
    """Get Colombian Spanish month names"""
    return ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


def format_colombian_date_verbose(date_value) -> str:
    """
    Format date to verbose Colombian format: Lunes, 30 de Enero de 2025

    Args:
        date_value: Date in any format

    Returns:
        Verbose formatted date string in Colombian Spanish
    """
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return ""

    try:
        date_obj = pd.to_datetime(date_value)
        day_name = colombian_day_names()[date_obj.weekday()]
        month_name = colombian_month_names()[date_obj.month]
        return f"{day_name}, {date_obj.day} de {month_name} de {date_obj.year}"
    except:
        return str(date_value).strip()


def format_currency(value):
    """Format currency with Colombian format: 1.234.567,89"""
    if value == 0 or value == 0.0:
        return "0,00"
    
    # Convert to string with 2 decimal places
    formatted = f"{value:,.2f}"
    
    # Replace comma with temporary placeholder
    formatted = formatted.replace(',', 'TEMP')
    
    # Replace dot with comma (for decimals)
    formatted = formatted.replace('.', ',')
    
    # Replace temporary placeholder with dot (for thousands)
    formatted = formatted.replace('TEMP', '.')
    
    return formatted

def parse_colombian_currency(value):
    """Parse Colombian currency format to float"""
    if pd.isna(value) or value == "" or value is None:
        return 0.0
    
    # Convert to string and clean
    value_str = str(value).strip()
    
    # Remove currency symbols and extra spaces
    value_str = re.sub(r'[₡$\s]', '', value_str)
    
    # If empty after cleaning, return 0
    if not value_str:
        return 0.0
    
    # Handle Colombian format: 1.234.567,89
    # Replace dots (thousands separators) with empty string
    # Replace comma (decimal separator) with dot
    if ',' in value_str:
        # Split by comma
        parts = value_str.split(',')
        if len(parts) == 2:
            # Remove dots from integer part
            integer_part = parts[0].replace('.', '')
            decimal_part = parts[1]
            value_str = f"{integer_part}.{decimal_part}"
        else:
            # Just remove dots if no decimal part
            value_str = value_str.replace('.', '').replace(',', '')
    else:
        # No comma, just remove dots
        value_str = value_str.replace('.', '')
    
    try:
        return float(value_str)
    except ValueError:
        return 0.0

def parse_date_flexible(date_value):
    """
    Parse date with multiple format support and return in DD/MM/YYYY format
    Uses the format_colombian_date function to ensure consistency
    """
    if pd.isna(date_value) or date_value == "" or date_value is None:
        return None

    # Convert to string
    date_str = str(date_value).strip()

    if not date_str or date_str.lower() in ['nan', 'none', '0']:
        return None

    # Use the Colombian date formatter for consistency
    try:
        formatted = format_colombian_date(date_str)
        return formatted if formatted else None
    except:
        return None

def calculate_days_between_dates(start_date_str, end_date_str):
    """Calculate number of days between two date strings"""
    try:
        # Parse dates
        start_date = pd.to_datetime(start_date_str, dayfirst=True)
        end_date = pd.to_datetime(end_date_str, dayfirst=True)
        
        # Calculate difference
        delta = end_date - start_date
        return max(0, delta.days + 1)  # +1 to include both start and end dates
    except:
        return 0


def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'excel_data': None,
        'file_name': None,
        'sheet_name': "Data",  # Changed default to "Data"
        'show_download': False,
        'file_loaded_from_path': False,
        'auto_load_attempted': False,
        'show_success_message': False,
        'last_saved_data': None,
        'show_success_message_2': False,
        'last_saved_data_2': None,
        'funcionario_saved_message': None  # Added for funcionario save messages
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_sede_options():
    """Get predefined sede options"""
    return [
        "Sede Central", "Atlántico", "Bolívar", "Boyacá", "Caquetá", "Caldas",
        "Casanare", "Cauca", "Cordoba", "Cesar", "Cundinamarca", "Magdalena",
        "Guajira", "Huila", "Norte de Santander", "Meta", "Nariño", "Quindio",
        "Risaralda", "Sucre", "Santander", "Tolima", "Valle del Cauca"
    ]