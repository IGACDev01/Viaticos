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

def clean_dataframe_types(df):
    """Enhanced dataframe cleaning with comprehensive type handling"""
    df_clean = df.copy()
    
    # First, add missing columns that the app expects
    expected_columns = {
        'Número de Orden': 'int64',
        'Sede': 'object', 
        'Fecha de Elaboración': 'object',
        'Fecha Memorando': 'object',
        'Radicado del Memorando': 'object',
        'REC': 'int64',
        'ID del Rubro': 'object',
        'Fecha Inicial': 'object',
        'Fecha Final': 'object',
        'Número de Días': 'int64',  # This is missing in your Excel
        'Valor Viáticos Diario': 'float64',
        'Valor Viáticos Orden': 'float64',
        'Valor Gastos Orden': 'float64',
        'Número de Identificación': 'int64',
        'Primer Nombre': 'object',
        'Otros Nombres': 'object',
        'Primer Apellido': 'object',
        'Segundo Apellido': 'object',
        'Fecha de Registro': 'object',  # Missing in your Excel
        'Número de Legalización': 'object',  # Missing in your Excel
        'Días Legalizados': 'object',  # Missing in your Excel
        'Valor Viáticos Legalizado': 'object',  # Missing in your Excel
        'Valor Gastos Legalizado': 'object'  # Missing in your Excel
    }
    
    # Add missing columns with default values
    for col_name, col_type in expected_columns.items():
        if col_name not in df_clean.columns:
            if col_type == 'int64':
                df_clean[col_name] = 0
            elif col_type == 'float64':
                df_clean[col_name] = 0.0
            else:
                df_clean[col_name] = ""
            print(f"Added missing column: {col_name}")
    
    # Clean and convert existing columns
    
    # 1. String columns - ensure they're proper strings
    string_columns = ['Sede', 'Radicado del Memorando', 'ID del Rubro',
                     'Primer Nombre', 'Otros Nombres', 'Primer Apellido', 'Segundo Apellido']
    
    for col in string_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).replace('nan', '').replace('None', '').replace('0', '').str.strip().str.upper()
    
    # 2. Date columns - standardize to DD/MM/YYYY format
    date_columns = ['Fecha de Elaboración', 'Fecha Memorando', 'Fecha Inicial', 'Fecha Final', 'Fecha de Registro']
    
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(parse_date_flexible)
    
    # 3. Integer columns - clean and convert
    integer_columns = ['Número de Orden', 'REC', 'Número de Identificación']
    
    for col in integer_columns:
        if col in df_clean.columns:
            # Clean the values first
            df_clean[col] = df_clean[col].astype(str).str.replace(r'[^\d]', '', regex=True)
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype('int64')
    
    # 4. Currency columns - parse Colombian format and convert to float
    currency_columns = ['Valor Viáticos Diario', 'Valor Viáticos Orden', 'Valor Gastos Orden']
    
    for col in currency_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(parse_colombian_currency).astype('float64')
    
    # 5. Calculate missing 'Número de Días' if both date columns exist
    if 'Fecha Inicial' in df_clean.columns and 'Fecha Final' in df_clean.columns:
        def calc_days(row):
            if pd.notna(row['Fecha Inicial']) and pd.notna(row['Fecha Final']):
                return calculate_days_between_dates(row['Fecha Inicial'], row['Fecha Final'])
            return 0
        
        df_clean['Número de Días'] = df_clean.apply(calc_days, axis=1)
        print("Calculated 'Número de Días' from date range")
    
    # 6. Handle legalization columns (they might be empty initially)
    legalization_columns = ['Número de Legalización', 'Días Legalizados', 
                           'Valor Viáticos Legalizado', 'Valor Gastos Legalizado']
    
    for col in legalization_columns:
        if col in df_clean.columns:
            # Convert to string and clean
            df_clean[col] = df_clean[col].astype(str).replace('nan', '').replace('None', '').str.strip()
            # Replace '0' with empty string for these columns
            df_clean[col] = df_clean[col].replace('0', '')
    
    # 7. Add 'Fecha de Registro' with current timestamp if missing
    if df_clean['Fecha de Registro'].isna().all() or (df_clean['Fecha de Registro'] == '').all():
        df_clean['Fecha de Registro'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print("Added 'Fecha de Registro' with current timestamp")
    
    # 8. Ensure all object columns are strings to avoid Arrow issues
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            df_clean[col] = df_clean[col].astype(str)
    
    # 9. Reorder columns to match expected order
    column_order = [
        'Número de Orden', 'Sede', 'Fecha de Elaboración', 'Fecha Memorando',
        'Radicado del Memorando', 'REC', 'ID del Rubro', 'Fecha Inicial',
        'Fecha Final', 'Número de Días', 'Valor Viáticos Diario',
        'Valor Viáticos Orden', 'Valor Gastos Orden', 'Número de Identificación',
        'Primer Nombre', 'Otros Nombres', 'Primer Apellido', 'Segundo Apellido',
        'Fecha de Registro', 'Número de Legalización', 'Días Legalizados',
        'Valor Viáticos Legalizado', 'Valor Gastos Legalizado'
    ]
    
    # Add any remaining columns that weren't in the expected list
    remaining_cols = [col for col in df_clean.columns if col not in column_order]
    column_order.extend(remaining_cols)
    
    # Reorder, keeping only columns that exist
    existing_cols = [col for col in column_order if col in df_clean.columns]
    df_clean = df_clean[existing_cols]
    
    return df_clean

def load_excel_data(uploaded_file, sheet_name=None):
    """Load data from uploaded Excel file with enhanced type cleaning"""
    try:
        if sheet_name:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        else:
            df = pd.read_excel(uploaded_file)
        
        print(f"Loaded {len(df)} rows from Excel file")
        print(f"Original columns: {list(df.columns)}")
        
        # Clean data types
        df = clean_dataframe_types(df)
        
        print(f"Cleaned data: {len(df)} rows, {len(df.columns)} columns")
        print(f"Final columns: {list(df.columns)}")
        
        return df, None
    except Exception as e:
        return None, f"Error al leer el archivo Excel: {str(e)}"

def add_data_to_df(existing_df, new_data):
    """Add new row to existing DataFrame with proper data type handling"""
    # Create a copy of the existing dataframe to avoid modifying the original
    df_copy = existing_df.copy()
    
    # Create new row DataFrame
    new_df = pd.DataFrame([new_data])
    
    # Ensure consistent data types before concatenation
    for col in new_df.columns:
        if col in df_copy.columns:
            # Try to match the existing column type
            if df_copy[col].dtype == 'object':
                new_df[col] = new_df[col].astype(str)
            elif df_copy[col].dtype in ['int64', 'int32']:
                try:
                    new_df[col] = pd.to_numeric(new_df[col], errors='coerce').fillna(0).astype('int64')
                except:
                    new_df[col] = new_df[col].astype(str)
            elif df_copy[col].dtype in ['float64', 'float32']:
                try:
                    new_df[col] = pd.to_numeric(new_df[col], errors='coerce').fillna(0.0).astype('float64')
                except:
                    new_df[col] = new_df[col].astype(str)
    
    # Concatenate the dataframes
    updated_df = pd.concat([df_copy, new_df], ignore_index=True)
    
    # Ensure string columns that should be strings remain strings
    string_columns = ['Sede', 'Fecha de Elaboración', 
                     'Radicado del Memorando', 'Fecha Memorando', 'ID del Rubro',
                     'Fecha Inicial', 'Fecha Final', 'Primer Nombre', 'Otros Nombres',
                     'Primer Apellido', 'Segundo Apellido', 'Fecha de Registro']
    
    for col in string_columns:
        if col in updated_df.columns:
            updated_df[col] = updated_df[col].astype(str)
    
    return updated_df

def save_to_original_path(df, file_path, sheet_name):
    """Save the updated DataFrame back to the original file path"""
    try:
        # Create a backup of the original file
        backup_path = file_path.replace('.xlsx', '_backup.xlsx')
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_path)
        
        # Save the updated data to the original path
        df.to_excel(file_path, sheet_name=sheet_name, index=False)
        return True, f"Archivo guardado exitosamente en: {file_path}"
    except Exception as e:
        return False, f"Error al guardar el archivo: {str(e)}"

def reset_form_fields(form_prefix=""):
    """Reset all form-related session state variables"""
    form_keys = [
        f'{form_prefix}num_orden', f'{form_prefix}sede', f'{form_prefix}fecha_elaboracion', 
        f'{form_prefix}radicado', f'{form_prefix}fecha_memorando', f'{form_prefix}rec', 
        f'{form_prefix}id_rubro', f'{form_prefix}fecha_inicial', f'{form_prefix}fecha_final', 
        f'{form_prefix}num_dias', f'{form_prefix}viaticos_diarios', f'{form_prefix}viaticos_orden', 
        f'{form_prefix}gastos_orden', f'{form_prefix}num_identificacion', f'{form_prefix}primer_nombre', 
        f'{form_prefix}otros_nombres', f'{form_prefix}primer_apellido', f'{form_prefix}segundo_apellido',
        f'{form_prefix}lookup_id', f'{form_prefix}funcionario_info'  # Added lookup-related keys
    ]
    
    for key in form_keys:
        if key in st.session_state:
            del st.session_state[key]

def load_file_from_path(path, sheet_name="Data"):  # Changed default to "Data"
    """Try to load Excel file from specified path with enhanced type cleaning"""
    if not path or not path.strip():
        return None, "No se especificó una ruta"
    
    try:
        if not os.path.exists(path):
            return None, f"El archivo no existe en la ruta: {os.path.basename(path)}"
        
        if not path.lower().endswith(('.xlsx', '.xls')):
            return None, "El archivo debe ser un archivo Excel (.xlsx o .xls)"
        
        # Try to get sheet names first
        excel_file = pd.ExcelFile(path)
        sheet_names = excel_file.sheet_names
        
        # Load with specified sheet or first sheet
        if sheet_name in sheet_names:
            df = pd.read_excel(path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(path, sheet_name=sheet_names[0])
            sheet_name = sheet_names[0]
        
        print(f"Loaded {len(df)} rows from {sheet_name} sheet")
        
        # Clean data types
        df = clean_dataframe_types(df)
        
        file_name = os.path.basename(path)
        return (df, file_name, sheet_name, sheet_names), None
        
    except Exception as e:
        return None, f"Error al cargar el archivo: {str(e)}"

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

def render_file_configuration():
    """Render file configuration section"""
    st.markdown('<div class="section-title">⚙️ Configuración de Archivo</div>', unsafe_allow_html=True)

    with st.expander("🔧 Configurar Ruta del Archivo", expanded=True):
        col_config1, col_config2 = st.columns([3, 1])
        
        with col_config1:
            file_path = st.text_input(
                "Ruta del archivo Excel:",
                value="",
                placeholder="Ej: C:/Users/Usuario/Documents/ordenes_comision.xlsx",
                help="Ingresa la ruta completa al archivo Excel que quieres usar"
            )
        
        with col_config2:
            load_from_path_btn = st.button("📂 Cargar desde Ruta", key="load_path_btn")

    # Handle loading from path
    if load_from_path_btn and file_path.strip():
        result, error = load_file_from_path(file_path.strip(), "Data")  # Default to "Data" sheet
        
        if not error:
            df, file_name, sheet_name, sheet_names = result
            st.session_state.excel_data = df
            st.session_state.file_name = file_name
            st.session_state.sheet_name = sheet_name
            st.session_state.file_loaded_from_path = True
            st.success(f"✅ Archivo cargado exitosamente desde: {file_name}")
            st.rerun()
        else:
            st.error(f"❌ {error}")

    # Auto-load status
    if st.session_state.excel_data is not None:
        st.success(f"✅ Archivo cargado: **{st.session_state.file_name}** (Hoja: {st.session_state.sheet_name})")
        st.info(f"📊 Registros existentes: {len(st.session_state.excel_data)}")
        
        # Show preview of existing data
        with st.expander("👀 Vista previa de los datos cargados", expanded=False):
            st.dataframe(st.session_state.excel_data.tail(5), use_container_width=True)
    else:
        st.warning("⚠️ No se pudo cargar el archivo por defecto")
        st.info("👇 Por favor, sube el archivo manualmente")

def render_file_upload():
    """Render file upload section for manual file loading"""
    st.markdown('<div class="section-title">📂 Cargar Archivo Excel Manualmente</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        col_upload1, col_upload2 = st.columns([3, 1])
        
        with col_upload1:
            uploaded_file = st.file_uploader(
                "Selecciona tu archivo Excel existente",
                type=['xlsx', 'xls'],
                help="Sube el archivo Excel donde quieres agregar los nuevos registros"
            )
        
        with col_upload2:
            if uploaded_file is not None:
                # Get sheet names
                try:
                    excel_file = pd.ExcelFile(uploaded_file)
                    sheet_names = excel_file.sheet_names
                    
                    # Default to "Data" sheet if it exists, otherwise first sheet
                    default_sheet = "Data" if "Data" in sheet_names else sheet_names[0]
                    
                    selected_sheet = st.selectbox(
                        "Seleccionar Hoja:",
                        sheet_names,
                        index=sheet_names.index(default_sheet) if default_sheet in sheet_names else 0,
                        key="sheet_selector"
                    )
                    st.session_state.sheet_name = selected_sheet
                except:
                    st.error("Error al leer las hojas del archivo")
        
        if uploaded_file is not None:
            # Load the Excel data
            df, error = load_excel_data(uploaded_file, st.session_state.sheet_name)
            
            if error:
                st.error(error)
            else:
                st.session_state.excel_data = df
                st.session_state.file_name = uploaded_file.name
                st.session_state.file_loaded_from_path = False
                
                st.success(f"✅ Archivo cargado: **{uploaded_file.name}** (Hoja: {st.session_state.sheet_name})")
                st.info(f"📊 Registros existentes: {len(df)}")
                
                # Show preview of existing data
                with st.expander("👀 Vista previa de los datos existentes", expanded=False):
                    st.dataframe(df.tail(5), use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)