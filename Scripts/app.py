import streamlit as st
from datetime import datetime, date
import pandas as pd
import os

# Import tab modules using Supabase
from tab_commission_form import render_commission_form_tab
from tab_legalization_form import render_additional_form_tab
from tab_edit_order import render_edit_order_tab
from tab_dashboard import render_dashboard_tab
from utils import initialize_session_state, get_colombian_datetime_now
from data_manager import render_database_status, init_database_session
from auth import initialize_auth_session, is_authenticated, render_login_page, render_user_info

# Page configuration
st.set_page_config(
    page_title="Sistema de Registro de Órdenes",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS - keeping original design
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #17becf);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 600;
    }

    .supabase-status {
        background: #f0f8ff;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 18px;
        font-weight: bold;
        color: #0066cc;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .stForm {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }

    .success-section {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        background-color: #f0f8f0;
    }

    .dashboard-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    }

    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 5px;
    }

    .metric-label {
        font-size: 1.1em;
        opacity: 0.9;
    }

    /* Footer styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #1f77b4;
        color: white;
        text-align: center;
        padding: 8px 0;
        font-size: 12px;
        z-index: 999;
        box-shadow: 0 -2px 4px rgba(0,0,0,0.1);
    }

    .footer a {
        color: #17becf;
        text-decoration: none;
    }

    .footer a:hover {
        text-decoration: underline;
    }

    /* Add padding to main container to prevent footer overlap */
    .main .block-container {
        padding-bottom: 60px;
    }

    /* Custom styling for segmented control */
    .stSelectbox > div > div {
        border-radius: 10px;
    }

    /* Connection status styling */
    .connection-info {
        background: #f0f8ff;
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 20px;
        font-size: 14px;
    }

    .stButton > button {
        width: 100%;
    }

    .stSpinner {
        text-align: center;
    }

    /* Supabase-specific styling */
    .supabase-info {
        background: #e8f5e8;
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin-bottom: 20px;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30, show_spinner=False)
def get_cached_database_status():
    """Get cached Supabase connection status and data info"""
    if st.session_state.get('database_connected') and st.session_state.get('excel_data') is not None:
        record_count = len(st.session_state.excel_data)
        return {
            'connected': True,
            'record_count': record_count,
            'last_update': get_colombian_datetime_now(),
            'db_type': 'Supabase Cloud Database'
        }
    elif st.session_state.get('database_connected'):
        return {
            'connected': True,
            'loading': True,
            'last_update': get_colombian_datetime_now()
        }
    return {'connected': False}


def main():
    # Initialize authentication session
    initialize_auth_session()

    # Check if user is authenticated
    if not is_authenticated():
        render_login_page()
        return

    # Initialize session state
    initialize_session_state()

    # Show user info in sidebar
    render_user_info()

    # Main title
    st.markdown("""
    <div class="main-header">
        <h1>🧭 Sistema de Registro de Órdenes</h1>
    </div>
    """, unsafe_allow_html=True)

    # Initialize Supabase and show status
    render_database_authentication()

    # Show cached connection status
    render_cached_database_status()

    # Create segmented control for navigation
    tab = st.segmented_control(
        "Navegación",
        ["📋 Órdenes de Comisión", "📝 Legalización", "✏️ Editar Orden", "📊 Dashboard", "⚙️ Administración"],
        selection_mode="single",
        default="📋 Órdenes de Comisión",
        label_visibility="collapsed",
    )

    # Add some spacing after the segmented control
    st.markdown("<br>", unsafe_allow_html=True)

    # Show content based on segmented control selection
    if tab == "📋 Órdenes de Comisión":
        render_commission_form_tab()

    elif tab == "📝 Legalización":
        render_additional_form_tab()

    elif tab == "✏️ Editar Orden":
        render_edit_order_tab()

    elif tab == "📊 Dashboard":
        render_dashboard_tab()

    elif tab == "⚙️ Administración":
        render_admin_tab()

    # Footer
    st.markdown("""
    <div class="footer">
        © 2025 Instituto Geográfico Agustín Codazzi (IGAC) - Todos los derechos reservados |
        Sistema de Registro de Órdenes de Comisión v3.0 (Supabase)
    </div>
    """, unsafe_allow_html=True)


def render_database_authentication():
    """Initialize Supabase database and show connection status"""
    if 'database_connected' not in st.session_state:
        with st.spinner("Conectando a Supabase..."):
            init_database_session()


def render_cached_database_status():
    """Render Supabase connection status using cached data"""
    try:
        cached_status = get_cached_database_status()

        if cached_status.get('connected') and not cached_status.get('loading'):
            st.markdown(f"""
            <div class="supabase-info">
                ✅ <strong>Supabase Conectado</strong> | 
                📊 {cached_status['record_count']} registros cargados | 
                ☁️ Tipo: {cached_status.get('db_type', 'Supabase')} |
                🕒 Actualizado: {cached_status['last_update']}
            </div>
            """, unsafe_allow_html=True)
        elif cached_status.get('connected') and cached_status.get('loading'):
            st.markdown("""
            <div class="supabase-info">
                🔄 <strong>Supabase Conectado</strong> - Cargando datos...
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="connection-info">
                🔄 <strong>Conectando a Supabase...</strong>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown("""
        <div class="connection-info">
            ⚠️ <strong>Error con Supabase...</strong>
        </div>
        """, unsafe_allow_html=True)


def render_admin_tab():
    """Render administration tab for database management with Supabase"""
    st.markdown('<h1 class="main-title">⚙️ Administración de Base de Datos</h1>', unsafe_allow_html=True)

    if 'database_manager' not in st.session_state:
        st.error("Base de datos no inicializada")
        return

    # Database information section
    st.markdown('<div class="section-title">📊 Información de la Base de Datos</div>', unsafe_allow_html=True)

    col_info1, col_info2, col_info3, col_info4 = st.columns(4)

    with col_info1:
        # Orders count
        orders_count = len(st.session_state.excel_data) if st.session_state.excel_data is not None else 0
        st.metric("Total Órdenes", orders_count)

    with col_info2:
        # Unique funcionarios count
        if st.session_state.excel_data is not None and 'Número de Identificación' in st.session_state.excel_data.columns:
            unique_funcionarios = st.session_state.excel_data['Número de Identificación'].nunique()
        else:
            unique_funcionarios = 0
        st.metric("Funcionarios Únicos", unique_funcionarios)

    with col_info3:
        # Database type
        st.metric("Tipo BD", "Supabase")

    with col_info4:
        # Orders with alerts
        if st.session_state.excel_data is not None and 'Alerta' in st.session_state.excel_data.columns:
            alerts_count = len(st.session_state.excel_data[
                                   st.session_state.excel_data['Alerta'].isin(['Plazo Vencido', 'Plazo Próximo'])
                               ])
        else:
            alerts_count = 0
        st.metric("Órdenes con Alertas", alerts_count)

    st.markdown("---")

    # Import/Export section
    st.markdown('<div class="section-title">📁 Importar/Exportar Datos</div>', unsafe_allow_html=True)

    col_export1, col_export2 = st.columns(2)

    with col_export1:
        st.subheader("📤 Exportar Datos")
        st.write("Exportar todos los datos de Supabase a un archivo Excel en la carpeta Data")

        # Custom filename option
        custom_filename = st.text_input(
            "Nombre personalizado (opcional):",
            placeholder="ej: data_enero.xlsx",
            help="Si no se especifica, se usará un nombre con fecha y hora"
        )

        if st.button("💾 Exportar a Excel", key="export_excel", use_container_width=True):
            with st.spinner("Exportando datos desde Supabase..."):
                filename = st.session_state.database_manager.export_to_excel(
                    custom_filename if custom_filename.strip() else None)
                if filename:
                    st.success(f"✅ Datos exportados exitosamente desde Supabase")
                    st.info(f"📁 Archivo generado: {filename}")

                    # Read the file for download
                    try:
                        with open(filename, 'rb') as file:
                            st.download_button(
                                label="⬇️ Descargar Archivo Excel",
                                data=file.read(),
                                file_name=os.path.basename(filename),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    except Exception as e:
                        st.warning(f"Archivo creado pero no se puede descargar: {str(e)}")
                else:
                    st.error("❌ Error al exportar datos")

    with col_export2:
        st.subheader("📥 Importar Datos")
        st.write("Importar órdenes desde un archivo Excel existente a Supabase")

        uploaded_file = st.file_uploader(
            "Seleccionar archivo Excel",
            type=['xlsx', 'xls'],
            help="Sube un archivo Excel con órdenes de comisión para importar"
        )

        if uploaded_file is not None:
            # Get sheet names
            try:
                excel_file = pd.ExcelFile(uploaded_file)
                sheet_names = excel_file.sheet_names

                selected_sheet = st.selectbox(
                    "Seleccionar Hoja:",
                    sheet_names,
                    index=0 if 'Data' not in sheet_names else sheet_names.index('Data'),
                    key="import_sheet_selector"
                )

                if st.button("📁 Importar Datos", key="import_excel", use_container_width=True):
                    with st.spinner("Importando datos a Supabase..."):
                        success, message = st.session_state.database_manager.import_from_excel(uploaded_file,
                                                                                               selected_sheet)

                        if success:
                            st.success("✅ Importación completada")
                            st.info(message)
                            # Refresh data
                            st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()
                            st.rerun()
                        else:
                            st.error(f"❌ Error en importación: {message}")

            except Exception as e:
                st.error(f"Error leyendo archivo: {str(e)}")

    st.markdown("---")

    # Quick refresh section
    st.markdown('<div class="section-title">🔄 Actualizar Datos</div>', unsafe_allow_html=True)

    col_refresh1, col_refresh2, col_refresh3 = st.columns([2, 2, 2])

    with col_refresh1:
        if st.button("🔄 Actualizar datos desde Supabase", key="refresh_data_btn", use_container_width=True):
            with st.spinner("Actualizando datos desde Supabase..."):
                success, message = st.session_state.database_manager.refresh_data()
                if success:
                    st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    st.markdown("---")

    # Database maintenance section
    st.markdown('<div class="section-title">🔧 Mantenimiento de Base de Datos</div>', unsafe_allow_html=True)

    col_maint1, col_maint2 = st.columns(2)

    with col_maint1:
        st.subheader("🔄 Actualizar Campos Calculados")
        st.write("Recalcular todos los campos automáticos en Supabase")

        st.info("""
        **Campos que se recalcularán:**
        • Fecha Reintegro
        • Fecha Límite Legalización  
        • Plazo Restante Legalización
        • Alerta
        • Estado Legalización
        • Valor Orden Legalizado
        """)

        if st.button("🔄 Recalcular Todos los Campos", key="recalculate_fields", use_container_width=True):
            with st.spinner("Recalculando campos en Supabase..."):
                success, message = st.session_state.database_manager.recalculate_all_formulated_fields()
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

    with col_maint2:
        st.subheader("📋 Información Técnica")
        st.write("**Tipo de BD:** Supabase (PostgreSQL)")
        st.write("**Conexión:** Nube")
        st.write("**Tablas:** ordenes, funcionarios, festivos, sedes")
        st.write("**Ventajas Supabase:**")
        st.write("• Acceso en tiempo real")
        st.write("• Escalabilidad automática")
        st.write("• Respaldos automáticos")
        st.write("• API REST automática")
        st.write("• Sincronización en tiempo real")
        st.write("• Seguridad avanzada")

        # Show recent database operations
        st.write("**Campos Calculados Automáticamente:**")
        st.write("• Fecha Reintegro (WORKDAY + 1 día)")
        st.write("• Fecha Límite Legalización (WORKDAY + 5 días)")
        st.write("• Plazo Restante (días hábiles restantes)")
        st.write("• Alerta (estado según plazo)")
        st.write("• Estado Legalización (a tiempo/atrasado)")
        st.write("**Festivos 2025:** 19 días festivos colombianos configurados")

    st.markdown("---")

    # Recent activity section
    st.markdown('<div class="section-title">📈 Actividad Reciente</div>', unsafe_allow_html=True)

    if st.session_state.excel_data is not None and len(st.session_state.excel_data) > 0:
        # Show last 5 orders
        display_columns = [
            'Número de Orden', 'Sede', 'Primer Nombre', 'Primer Apellido',
            'Fecha Límite Legalización', 'Alerta', 'Estado Legalización'
        ]
        available_columns = [col for col in display_columns if col in st.session_state.excel_data.columns]
        recent_orders = st.session_state.excel_data[available_columns].tail(5)

        st.write("**Últimas 5 Órdenes Registradas:**")
        st.dataframe(recent_orders, use_container_width=True, hide_index=True)

        # Summary statistics
        col_stats1, col_stats2, col_stats3 = st.columns(3)

        with col_stats1:
            if 'Estado Legalización' in st.session_state.excel_data.columns:
                a_tiempo = len(
                    st.session_state.excel_data[st.session_state.excel_data['Estado Legalización'] == 'A tiempo'])
                st.write(f"**Órdenes a Tiempo:** {a_tiempo}")

        with col_stats2:
            if 'Estado Legalización' in st.session_state.excel_data.columns:
                atrasado = len(
                    st.session_state.excel_data[st.session_state.excel_data['Estado Legalización'] == 'Atrasado'])
                st.write(f"**Órdenes Atrasadas:** {atrasado}")

        with col_stats3:
            if 'Fecha Legalización' in st.session_state.excel_data.columns:
                legalizadas = len(
                    st.session_state.excel_data[st.session_state.excel_data['Fecha Legalización'].notna()])
                st.write(f"**Órdenes Legalizadas:** {legalizadas}")
    else:
        st.info("No hay órdenes registradas aún")

    # Database connection info
    st.markdown("---")
    st.markdown('<div class="section-title">🔗 Información de Conexión</div>', unsafe_allow_html=True)

    col_conn1, col_conn2 = st.columns(2)

    with col_conn1:
        if st.session_state.get('database_connected'):
            st.success("✅ Conectado a Supabase")
            st.write("**Estado:** Activo")
            st.write("**Última actualización:** " + get_colombian_datetime_now())
        else:
            st.error("❌ No conectado a Supabase")
            st.write("**Estado:** Desconectado")

    with col_conn2:
        st.write("**Configuración:**")
        # Safely display URL without exposing full credentials
        try:
            supabase_url = st.secrets.get("SUPABASE_URL", "No configurada")
            if supabase_url and supabase_url != "No configurada":
                # Show only domain part for security
                url_display = supabase_url.split("//")[1].split("/")[0] if "//" in supabase_url else "Configurada"
                st.write(f"• URL: {url_display}")
            else:
                st.write("• URL: No configurada")

            supabase_key = st.secrets.get("SUPABASE_KEY", None)
            st.write("• API Key: " + ("Configurada ✅" if supabase_key else "No configurada ❌"))
        except Exception:
            # Fallback for local development
            supabase_url = os.getenv("SUPABASE_URL", "No configurada")
            url_display = supabase_url.split("//")[1].split("/")[
                0] if supabase_url and "//" in supabase_url else "Local/Env"
            st.write(f"• URL: {url_display}")
            st.write("• API Key: " + ("Configurada ✅" if os.getenv("SUPABASE_KEY") else "No configurada ❌"))

        st.write("• Timeout: 30 segundos")
        st.write("• SSL: Habilitado")

    # Footer note
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
        <strong>Nota:</strong> Supabase proporciona una base de datos PostgreSQL en la nube con 
        sincronización en tiempo real, respaldos automáticos y escalabilidad automática. 
        Los campos calculados se actualizan automáticamente según los festivos colombianos configurados.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()