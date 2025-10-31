import streamlit as st
from datetime import datetime, date
import pandas as pd
from utils import format_currency
from data_manager import (
    init_database_session, search_orders, update_legalization
)


def render_additional_form_tab():
    """Render the legalization form tab with Supabase integration"""

    # Initialize database if not already done
    init_database_session()

    # Main title
    st.markdown('<h1 class="main-title">📝 Seguimiento y Legalización de Órdenes</h1>', unsafe_allow_html=True)

    # Quick refresh button
    col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 2, 1])
    with col_refresh2:
        if st.button("🔄 Actualizar datos desde Supabase", key="refresh_legalization_form", use_container_width=True):
            with st.spinner("Actualizando datos desde Supabase..."):
                success, message = st.session_state.database_manager.refresh_data()
                if success:
                    st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    st.markdown("---")

    # Show connection status
    st.success("✅ Conectado a Supabase")

    # Initialize legalization state properly
    if 'legalization_success_state' not in st.session_state:
        st.session_state.legalization_success_state = {
            'show_success': False,
            'last_legalized_order': None
        }

    # Show success message if legalization was just completed
    if st.session_state.legalization_success_state['show_success']:
        render_legalization_success()
        return

    # Only show search and form if not in success state
    render_search_and_form()

    # Additional information
    st.markdown("---")
    st.markdown("**Nota:** Busque la orden de comisión que desea legalizar y complete los campos correspondientes.")


def render_legalization_success():
    """Render success message with clear button"""
    success_state = st.session_state.legalization_success_state

    st.markdown('<div class="success-section">', unsafe_allow_html=True)

    col_success1, col_success2 = st.columns([2, 1])

    with col_success1:
        st.success("¡Legalización actualizada exitosamente en Supabase!")

        if success_state['last_legalized_order']:
            st.write(f"**Orden legalizada:** #{success_state['last_legalized_order']}")
            st.write("Los datos han sido guardados en Supabase.")

    with col_success2:
        if st.button("📝 Legalizar Otra Orden", key="new_legalization_btn", use_container_width=True):
            # Reset success state
            st.session_state.legalization_success_state = {
                'show_success': False,
                'last_legalized_order': None
            }
            # Clear search and selection states
            if 'search_results' in st.session_state:
                st.session_state.search_results = []
            if 'selected_record' in st.session_state:
                st.session_state.selected_record = None
            if 'selected_record_index' in st.session_state:
                st.session_state.selected_record_index = None
            # Refresh data
            st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_search_and_form():
    """Render search functionality and legalization form"""

    # Search section
    st.markdown('<div class="section-title">🔍 Buscar Orden de Comisión en Supabase</div>', unsafe_allow_html=True)

    col_search1, col_search2 = st.columns([3, 1])

    with col_search1:
        search_term = st.text_input(
            "Buscar por:",
            placeholder="Número de orden, identificación, nombre, apellido, sede, radicado...",
            help="Puede buscar por cualquier campo relevante de la orden de comisión",
            key="search_order"
        )

    with col_search2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🔍 Buscar en Supabase", key="search_btn", use_container_width=True)

    # Initialize search results
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

    if 'selected_record' not in st.session_state:
        st.session_state.selected_record = None

    if 'selected_record_index' not in st.session_state:
        st.session_state.selected_record_index = None

    # Perform search using Supabase
    if search_btn and search_term.strip():
        with st.spinner("Buscando en Supabase..."):
            search_results = search_orders(search_term)
            st.session_state.search_results = search_results
            st.session_state.selected_record = None
            st.session_state.selected_record_index = None

    # Display search results
    if st.session_state.search_results:
        st.markdown('<div class="section-title">📋 Resultados de Búsqueda</div>', unsafe_allow_html=True)

        # Show number of results
        num_results = len(st.session_state.search_results)
        st.info(f"Se encontraron {num_results} orden(es) de comisión en Supabase")

        # Display results in an interactive table
        for idx, row in enumerate(st.session_state.search_results):
            with st.expander(
                    f"Orden #{row.get('numero_orden', 'N/A')} - {row.get('primer_nombre', '')} {row.get('primer_apellido', '')} - {row.get('sede', '')}",
                    expanded=False):

                # Show record summary
                col_summary1, col_summary2, col_summary3 = st.columns(3)

                with col_summary1:
                    st.write("**Información Básica:**")
                    st.write(f"• Orden: {row.get('numero_orden', 'N/A')}")
                    st.write(f"• Sede: {row.get('sede', 'N/A')}")
                    st.write(f"• REC: {row.get('rec', 'N/A')}")
                    st.write(f"• Radicado: {row.get('radicado_memorando', 'N/A')}")

                with col_summary2:
                    st.write("**Funcionario:**")
                    st.write(f"• ID: {row.get('numero_identificacion', 'N/A')}")
                    st.write(f"• Nombre: {row.get('primer_nombre', '')} {row.get('otros_nombres', '')}")
                    st.write(f"• Apellidos: {row.get('primer_apellido', '')} {row.get('segundo_apellido', '')}")

                with col_summary3:
                    st.write("**Información Financiera:**")
                    st.write(f"• Días: {row.get('numero_dias', 'N/A')}")
                    viaticos_diario = row.get('valor_viaticos_diario', 0)
                    viaticos_orden = row.get('valor_viaticos_orden', 0)
                    gastos_orden = row.get('valor_gastos_orden', 0)

                    try:
                        st.write(f"• Viáticos Diario: ${format_currency(float(viaticos_diario))}")
                        st.write(f"• Total Viáticos: ${format_currency(float(viaticos_orden))}")
                        st.write(f"• Total Gastos: ${format_currency(float(gastos_orden))}")
                    except (ValueError, TypeError):
                        st.write(f"• Viáticos Diario: {viaticos_diario}")
                        st.write(f"• Total Viáticos: {viaticos_orden}")
                        st.write(f"• Total Gastos: {gastos_orden}")

                # Show legalization status
                st.write("**Estado de Legalización:**")
                legalization_status = []

                # Check legalization fields
                num_legalizacion = row.get('numero_legalizacion')
                dias_legalizados = row.get('dias_legalizados')
                viaticos_legalizado = row.get('valor_viaticos_legalizado')
                gastos_legalizado = row.get('valor_gastos_legalizado')

                if num_legalizacion and str(num_legalizacion).strip() and str(num_legalizacion) != 'None':
                    legalization_status.append(f"✅ Número de Legalización: {num_legalizacion}")
                else:
                    legalization_status.append("❌ Sin número de legalización")

                if dias_legalizados and str(dias_legalizados).strip() and str(dias_legalizados) != 'None':
                    legalization_status.append(f"✅ Días Legalizados: {dias_legalizados}")
                else:
                    legalization_status.append("❌ Sin días legalizados")

                if viaticos_legalizado and str(viaticos_legalizado).strip() and str(viaticos_legalizado) != 'None':
                    try:
                        legalization_status.append(
                            f"✅ Viáticos Legalizado: ${format_currency(float(viaticos_legalizado))}")
                    except (ValueError, TypeError):
                        legalization_status.append(f"✅ Viáticos Legalizado: {viaticos_legalizado}")
                else:
                    legalization_status.append("❌ Sin viáticos legalizados")

                if gastos_legalizado and str(gastos_legalizado).strip() and str(gastos_legalizado) != 'None':
                    try:
                        legalization_status.append(f"✅ Gastos Legalizado: ${format_currency(float(gastos_legalizado))}")
                    except (ValueError, TypeError):
                        legalization_status.append(f"✅ Gastos Legalizado: {gastos_legalizado}")
                else:
                    legalization_status.append("❌ Sin gastos legalizados")

                for status in legalization_status:
                    st.write(f"• {status}")

                # Select button
                if st.button(f"✏️ Seleccionar para Legalizar", key=f"select_{idx}", use_container_width=True):
                    st.session_state.selected_record = row
                    st.session_state.selected_record_index = row.get('numero_orden')
                    st.rerun()

    elif search_term.strip() and search_btn:
        st.warning("No se encontraron resultados para la búsqueda realizada en Supabase.")

    # Show legalization form if a record is selected
    if st.session_state.selected_record is not None:
        render_legalization_form()


def render_legalization_form():
    """Render the legalization form"""

    record = st.session_state.selected_record
    record_order_number = st.session_state.selected_record_index

    st.markdown('<div class="section-title">📝 Formulario de Legalización</div>', unsafe_allow_html=True)

    # Show selected record summary
    st.success(
        f"✅ Orden seleccionada: #{record.get('numero_orden', 'N/A')} - {record.get('primer_nombre', '')} {record.get('primer_apellido', '')}")

    # Show current legalization values if they exist
    current_values = {}

    # Get current legalization values
    num_legalizacion = record.get('numero_legalizacion')
    if num_legalizacion and str(num_legalizacion).strip() and str(num_legalizacion) != 'None':
        try:
            current_values['Número de Legalización'] = int(float(num_legalizacion))
        except (ValueError, TypeError):
            pass

    dias_legalizados = record.get('dias_legalizados')
    if dias_legalizados and str(dias_legalizados).strip() and str(dias_legalizados) != 'None':
        try:
            current_values['Días Legalizados'] = int(float(dias_legalizados))
        except (ValueError, TypeError):
            pass

    viaticos_legalizado = record.get('valor_viaticos_legalizado')
    if viaticos_legalizado and str(viaticos_legalizado).strip() and str(viaticos_legalizado) != 'None':
        try:
            current_values['Valor Viáticos Legalizado'] = float(viaticos_legalizado)
        except (ValueError, TypeError):
            pass

    gastos_legalizado = record.get('valor_gastos_legalizado')
    if gastos_legalizado and str(gastos_legalizado).strip() and str(gastos_legalizado) != 'None':
        try:
            current_values['Valor Gastos Legalizado'] = float(gastos_legalizado)
        except (ValueError, TypeError):
            pass

    if current_values:
        with st.expander("📋 Valores Actuales de Legalización", expanded=False):
            for key, value in current_values.items():
                if 'Valor' in key:
                    st.write(f"• **{key}**: ${format_currency(value)}")
                else:
                    st.write(f"• **{key}**: {value}")

    # Legalization form
    with st.form("legalization_form"):

        st.markdown('<div class="section-title">💰 Información de Legalización</div>', unsafe_allow_html=True)

        col_leg1, col_leg2 = st.columns(2)

        with col_leg1:
            num_legalizacion = st.number_input(
                "Número de Legalización",
                min_value=1,
                step=1,
                format="%d",
                value=current_values.get('Número de Legalización', 1),
                help="Ingrese el número de legalización",
                key="num_legalizacion"
            )

            valor_viaticos_legalizado = st.number_input(
                "Valor Viáticos Legalizado",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=current_values.get('Valor Viáticos Legalizado', 0.0),
                help="Ingrese el valor de viáticos legalizado",
                key="valor_viaticos_legalizado"
            )

        with col_leg2:
            dias_legalizados = st.number_input(
                "Días Legalizados",
                min_value=0,
                step=1,
                format="%d",
                value=current_values.get('Días Legalizados', 0),
                help="Ingrese los días legalizados",
                key="dias_legalizados"
            )

            valor_gastos_legalizado = st.number_input(
                "Valor Gastos Legalizado",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=current_values.get('Valor Gastos Legalizado', 0.0),
                help="Ingrese el valor de gastos legalizado",
                key="valor_gastos_legalizado"
            )

        # Show comparison with original values
        st.markdown('<div class="section-title">📊 Comparación con Valores Originales</div>', unsafe_allow_html=True)

        col_comp1, col_comp2, col_comp3, col_comp4 = st.columns(4)

        with col_comp1:
            st.write("**Días Totales:**")
            try:
                original_dias = int(float(record.get('numero_dias', 0)))
            except (ValueError, TypeError):
                original_dias = 0
            st.write(f"• Original: {original_dias}")
            st.write(f"• Legalizado: {dias_legalizados}")
            if dias_legalizados > original_dias:
                st.warning("⚠️ Días legalizados > días originales")

        with col_comp2:
            st.write("**Días Hábiles:**")
            try:
                dias_habiles = int(float(record.get('dias_habiles', 0)))
            except (ValueError, TypeError):
                dias_habiles = 0
            st.write(f"• Calculados: {dias_habiles}")
            st.write(f"• Legalizado: {dias_legalizados}")
            if dias_legalizados > dias_habiles:
                st.warning("⚠️ Días legalizados > días hábiles")

        with col_comp3:
            st.write("**Viáticos:**")
            try:
                original_viaticos = float(record.get('valor_viaticos_orden', 0))
                viaticos_habiles = float(record.get('valor_viaticos_habiles', 0))
            except (ValueError, TypeError):
                original_viaticos = 0
                viaticos_habiles = 0
            st.write(f"• Original: ${format_currency(original_viaticos)}")
            if viaticos_habiles > 0:
                st.write(f"• Por Días Hábiles: ${format_currency(viaticos_habiles)}")
            st.write(f"• Legalizado: ${format_currency(valor_viaticos_legalizado)}")
            if valor_viaticos_legalizado > original_viaticos:
                st.warning("⚠️ Viáticos legalizados > viáticos originales")

        with col_comp4:
            st.write("**Gastos:**")
            try:
                original_gastos = float(record.get('valor_gastos_orden', 0))
            except (ValueError, TypeError):
                original_gastos = 0
            st.write(f"• Original: ${format_currency(original_gastos)}")
            st.write(f"• Legalizado: ${format_currency(valor_gastos_legalizado)}")
            if valor_gastos_legalizado > original_gastos:
                st.warning("⚠️ Gastos legalizados > gastos originales")

        # Add spacing
        st.markdown("<br>", unsafe_allow_html=True)

        # Submit button
        col_center = st.columns([1, 2, 1])
        with col_center[1]:
            submitted = st.form_submit_button("💾 Guardar Legalización en Supabase", use_container_width=True)

        # Form processing
        if submitted:
            process_legalization_submission(
                record, record_order_number, num_legalizacion, dias_legalizados,
                valor_viaticos_legalizado, valor_gastos_legalizado
            )

    # Clear selection button
    if st.button("🔄 Seleccionar Otra Orden", key="clear_selection"):
        st.session_state.selected_record = None
        st.session_state.selected_record_index = None
        st.rerun()


def process_legalization_submission(record, record_order_number, num_legalizacion, dias_legalizados,
                                    valor_viaticos_legalizado, valor_gastos_legalizado):
    """Process legalization form submission with Supabase integration"""

    # Validate required fields
    errors = []

    if num_legalizacion <= 0:
        errors.append("• Número de Legalización debe ser mayor que 0")

    if dias_legalizados < 0:
        errors.append("• Días Legalizados no puede ser negativo")

    if valor_viaticos_legalizado < 0:
        errors.append("• Valor Viáticos Legalizado no puede ser negativo")

    if valor_gastos_legalizado < 0:
        errors.append("• Valor Gastos Legalizado no puede ser negativo")

    # Compare with original values and add validation errors
    try:
        original_dias = int(float(record.get('numero_dias', 0)))
        if dias_legalizados > original_dias:
            errors.append(
                f"• Días Legalizados ({dias_legalizados}) no puede ser mayor que los días originales ({original_dias})")
    except (ValueError, TypeError):
        pass

    try:
        original_viaticos = float(record.get('valor_viaticos_orden', 0))
        if valor_viaticos_legalizado > original_viaticos:
            errors.append(
                f"• Valor Viáticos Legalizado (${format_currency(valor_viaticos_legalizado)}) no puede ser mayor que el valor original (${format_currency(original_viaticos)})")
    except (ValueError, TypeError):
        pass

    try:
        original_gastos = float(record.get('valor_gastos_orden', 0))
        if valor_gastos_legalizado > original_gastos:
            errors.append(
                f"• Valor Gastos Legalizado (${format_currency(valor_gastos_legalizado)}) no puede ser mayor que el valor original (${format_currency(original_gastos)})")
    except (ValueError, TypeError):
        pass

    if errors:
        st.error("Por favor corrija los siguientes errores:")
        for error in errors:
            st.error(error)
    else:
        with st.spinner("Actualizando legalización en Supabase..."):

            legalization_data = {
                "numero_legalizacion": num_legalizacion,
                "dias_legalizados": dias_legalizados,
                "valor_viaticos_legalizado": valor_viaticos_legalizado,
                "valor_gastos_legalizado": valor_gastos_legalizado
            }

            save_success, save_message = update_legalization(
                record_order_number, legalization_data
            )

            if save_success:
                # Update local session state
                st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()

                # Set success state
                st.session_state.legalization_success_state = {
                    'show_success': True,
                    'last_legalized_order': record.get('numero_orden', 'N/A')
                }

                # Clear selection state
                st.session_state.selected_record = None
                st.session_state.selected_record_index = None

                # Show immediate success message
                st.success(f"✅ {save_message}")
                st.info("💡 Los datos han sido actualizados en Supabase.")

                # Show success animation
                st.balloons()

                st.rerun()
            else:
                st.error(f"❌ {save_message}")
                st.warning("No se pudieron guardar los cambios en Supabase.")