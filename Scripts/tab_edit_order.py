import streamlit as st
from datetime import datetime, date
import pandas as pd
from utils import get_sede_options
from data_manager import (
    init_database_session, search_orders, save_commission_order
)


def render_edit_order_tab():
    """Render the edit order tab with Supabase integration"""

    # Initialize database if not already done
    init_database_session()

    # Main title
    st.markdown('<h1 class="main-title">✏️ Editar una Orden</h1>', unsafe_allow_html=True)

    # Quick refresh button
    col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 2, 1])
    with col_refresh2:
        if st.button("🔄 Actualizar datos desde Supabase", key="refresh_edit_order", use_container_width=True):
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

    # Initialize edit state properly
    if 'edit_success_state' not in st.session_state:
        st.session_state.edit_success_state = {
            'show_success': False,
            'last_edited_order': None
        }

    # Show success message if edit was just completed
    if st.session_state.edit_success_state['show_success']:
        render_edit_success()
        return

    # Only show search and form if not in success state
    render_search_and_form()

    # Additional information
    st.markdown("---")
    st.markdown("**Nota:** Busque la orden que desea editar y corrija los campos con errores o typos.")


def render_edit_success():
    """Render success message with clear button"""
    success_state = st.session_state.edit_success_state

    st.markdown('<div class="success-section">', unsafe_allow_html=True)

    col_success1, col_success2 = st.columns([2, 1])

    with col_success1:
        st.success("¡Orden actualizada exitosamente en Supabase!")

        if success_state['last_edited_order']:
            st.write(f"**Orden editada:** #{success_state['last_edited_order']}")
            st.write("Los datos han sido actualizados en Supabase.")

    with col_success2:
        if st.button("✏️ Editar Otra Orden", key="new_edit_btn", use_container_width=True):
            # Reset success state
            st.session_state.edit_success_state = {
                'show_success': False,
                'last_edited_order': None
            }
            # Clear search and selection states
            if 'edit_search_results' in st.session_state:
                st.session_state.edit_search_results = []
            if 'edit_selected_record' in st.session_state:
                st.session_state.edit_selected_record = None
            if 'edit_selected_record_index' in st.session_state:
                st.session_state.edit_selected_record_index = None
            # Refresh data
            st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_search_and_form():
    """Render search functionality and edit form"""

    # Search section
    st.markdown('<div class="section-title">🔍 Búsqueda de Orden</div>', unsafe_allow_html=True)

    col_search1, col_search2 = st.columns([3, 1])

    with col_search1:
        search_term = st.text_input(
            "Buscar orden por número, sede, funcionario, etc.",
            help="Ingrese número de orden, sede o nombre del funcionario",
            key="edit_search_input"
        )

    with col_search2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🔍 Buscar", key="edit_search_btn", use_container_width=True)

    # Initialize search results in session state
    if 'edit_search_results' not in st.session_state:
        st.session_state.edit_search_results = []

    # Handle search
    if search_btn and search_term.strip():
        with st.spinner("Buscando órdenes en Supabase..."):
            results = search_orders(search_term.strip())
            if results:
                st.session_state.edit_search_results = results
                st.success(f"✅ Se encontraron {len(results)} orden(es)")
            else:
                st.warning("⚠️ No se encontraron órdenes que coincidan con la búsqueda")
                st.session_state.edit_search_results = []

    # Display search results
    if st.session_state.edit_search_results:
        st.markdown('<div class="section-title">📋 Resultados de Búsqueda</div>', unsafe_allow_html=True)

        # Create a table of results for selection
        results_data = []
        for idx, order in enumerate(st.session_state.edit_search_results):
            results_data.append({
                'Seleccionar': idx,
                'Número': order.get('numero_orden', 'N/A'),
                'Sede': order.get('sede', 'N/A'),
                'Funcionario': f"{order.get('primer_nombre', '')} {order.get('primer_apellido', '')}",
                'Fecha': order.get('fecha_elaboracion', 'N/A')
            })

        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, use_container_width=True, hide_index=True)

        # Select order to edit
        st.markdown('<div class="section-title">Seleccionar Orden para Editar</div>', unsafe_allow_html=True)

        selected_index = st.selectbox(
            "Seleccione una orden:",
            range(len(st.session_state.edit_search_results)),
            format_func=lambda i: f"#{st.session_state.edit_search_results[i].get('numero_orden', 'N/A')} - {st.session_state.edit_search_results[i].get('sede', 'N/A')}",
            key="edit_order_selector"
        )

        if selected_index is not None:
            st.session_state.edit_selected_record_index = selected_index
            st.session_state.edit_selected_record = st.session_state.edit_search_results[selected_index]

            st.markdown("---")
            render_edit_form(st.session_state.edit_selected_record)


def render_edit_form(order_data):
    """Render the edit form with current order data"""

    sede_options = get_sede_options()

    st.markdown('<div class="section-title">✏️ Editar Información de la Orden</div>', unsafe_allow_html=True)

    with st.form(f"edit_order_form_{order_data.get('numero_orden', 'unknown')}"):

        # Section 1: Commission Information
        st.markdown('<div class="section-title">1. Información de la Comisión</div>', unsafe_allow_html=True)

        # First row: Número de orden, sede y fecha de elaboración
        col1, col2, col3 = st.columns(3)

        with col1:
            num_orden = st.number_input(
                "Número de Orden",
                value=int(order_data.get('numero_orden', 0)) if order_data.get('numero_orden') else 0,
                min_value=1,
                step=1,
                format="%d",
                key="edit_num_orden",
                disabled=True,  # Don't allow changing the order number
                help="No se puede cambiar el número de orden"
            )

        with col2:
            sede = st.selectbox(
                "Sede",
                options=sede_options,
                index=sede_options.index(order_data.get('sede', sede_options[0])) if order_data.get('sede') in sede_options else 0,
                key="edit_sede"
            )

        with col3:
            # Parse the date string to date object
            fecha_elaboracion_str = order_data.get('fecha_elaboracion', '')
            try:
                fecha_elaboracion = pd.to_datetime(fecha_elaboracion_str).date() if fecha_elaboracion_str else date.today()
            except:
                fecha_elaboracion = date.today()

            fecha_elaboracion = st.date_input(
                "Fecha Elaboración",
                value=fecha_elaboracion,
                key="edit_fecha_elaboracion"
            )

        # Second row: Radicado, Fecha Memorando, REC, ID Rubro
        col4, col5, col6, col7 = st.columns(4)

        with col4:
            radicado = st.text_input(
                "Radicado del Memorando",
                value=order_data.get('radicado_memorando', ''),
                key="edit_radicado"
            )

        with col5:
            fecha_memorando_str = order_data.get('fecha_memorando', '')
            try:
                fecha_memorando = pd.to_datetime(fecha_memorando_str).date() if fecha_memorando_str else date.today()
            except:
                fecha_memorando = date.today()

            fecha_memorando = st.date_input(
                "Fecha Memorando",
                value=fecha_memorando,
                key="edit_fecha_memorando"
            )

        with col6:
            rec = st.number_input(
                "REC",
                value=int(order_data.get('rec', 0)) if order_data.get('rec') else 0,
                min_value=1,
                step=1,
                format="%d",
                key="edit_rec"
            )

        with col7:
            id_rubro = st.text_input(
                "ID del Rubro",
                value=order_data.get('id_rubro', ''),
                key="edit_id_rubro"
            )

        # Third row: Fecha Inicial, Fecha Final
        col8, col9 = st.columns(2)

        with col8:
            fecha_inicial_str = order_data.get('fecha_inicial', '')
            try:
                fecha_inicial = pd.to_datetime(fecha_inicial_str).date() if fecha_inicial_str else date.today()
            except:
                fecha_inicial = date.today()

            fecha_inicial = st.date_input(
                "Fecha Inicial",
                value=fecha_inicial,
                key="edit_fecha_inicial"
            )

        with col9:
            fecha_final_str = order_data.get('fecha_final', '')
            try:
                fecha_final = pd.to_datetime(fecha_final_str).date() if fecha_final_str else date.today()
            except:
                fecha_final = date.today()

            fecha_final = st.date_input(
                "Fecha Final",
                value=max(fecha_inicial, fecha_final) if fecha_final_str else fecha_inicial,
                min_value=fecha_inicial,
                key="edit_fecha_final"
            )

        # Fourth row: Número de Días, Valor Viáticos Diario, Valor Viáticos Orden, Valor Gastos Orden
        col10, col11, col12, col13 = st.columns(4)

        with col10:
            num_dias = st.number_input(
                "Número de Días",
                value=int(order_data.get('numero_dias', 0)) if order_data.get('numero_dias') else 0,
                min_value=0,
                step=1,
                format="%d",
                key="edit_num_dias"
            )

        with col11:
            viaticos_diarios = st.number_input(
                "Valor Viáticos Diario",
                value=float(order_data.get('valor_viaticos_diario', 0)) if order_data.get('valor_viaticos_diario') else 0.0,
                min_value=0.0,
                format="%.2f",
                key="edit_viaticos_diarios"
            )

        with col12:
            viaticos_orden = st.number_input(
                "Valor Viáticos Orden",
                value=float(order_data.get('valor_viaticos_orden', 0)) if order_data.get('valor_viaticos_orden') else 0.0,
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="edit_viaticos_orden"
            )

        with col13:
            gastos_orden = st.number_input(
                "Valor Gastos Orden",
                value=float(order_data.get('valor_gastos_orden', 0)) if order_data.get('valor_gastos_orden') else 0.0,
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="edit_gastos_orden"
            )

        # Add spacing
        st.markdown("<br>", unsafe_allow_html=True)

        # Section 2: Employee Information
        st.markdown('<div class="section-title">2. Información del Funcionario</div>', unsafe_allow_html=True)

        # Employee ID field
        num_identificacion = st.text_input(
            "Número de Identificación",
            value=str(order_data.get('numero_identificacion', '')),
            key="edit_num_identificacion",
            disabled=True,
            help="No se puede cambiar el número de identificación"
        )

        col_info1, col_info2 = st.columns(2)

        with col_info1:
            primer_nombre = st.text_input(
                "Primer Nombre",
                value=order_data.get('primer_nombre', ''),
                key="edit_primer_nombre"
            )

            otros_nombres = st.text_input(
                "Otros Nombres",
                value=order_data.get('otros_nombres', '') or '',
                key="edit_otros_nombres"
            )

        with col_info2:
            primer_apellido = st.text_input(
                "Primer Apellido",
                value=order_data.get('primer_apellido', ''),
                key="edit_primer_apellido"
            )

            segundo_apellido = st.text_input(
                "Segundo Apellido",
                value=order_data.get('segundo_apellido', '') or '',
                key="edit_segundo_apellido"
            )

        # Add spacing
        st.markdown("<br>", unsafe_allow_html=True)

        # Submit button
        col_center = st.columns([1, 2, 1])
        with col_center[1]:
            submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)

        # Form validation and processing
        if submitted:
            process_edit_submission(
                num_orden, sede, fecha_elaboracion, radicado, fecha_memorando, rec, id_rubro,
                fecha_inicial, fecha_final, num_dias, viaticos_diarios, viaticos_orden, gastos_orden,
                num_identificacion, primer_nombre, otros_nombres, primer_apellido, segundo_apellido
            )


def process_edit_submission(num_orden, sede, fecha_elaboracion, radicado, fecha_memorando, rec, id_rubro,
                            fecha_inicial, fecha_final, num_dias, viaticos_diarios, viaticos_orden, gastos_orden,
                            num_identificacion, primer_nombre, otros_nombres, primer_apellido, segundo_apellido):
    """Process edit form submission"""

    # Validate required fields
    errors = []

    if num_orden <= 0:
        errors.append("• Número de Orden debe ser mayor que 0")

    if rec <= 0:
        errors.append("• REC debe ser mayor que 0")

    if fecha_final < fecha_inicial:
        errors.append("• La Fecha Final debe ser posterior a la Fecha Inicial")

    if num_dias < 0:
        errors.append("• Número de Días no puede ser negativo")

    if not primer_nombre.strip():
        errors.append("• Primer Nombre es obligatorio")

    if not primer_apellido.strip():
        errors.append("• Primer Apellido es obligatorio")

    if errors:
        st.error("Por favor corrija los siguientes errores:")
        for error in errors:
            st.error(error)
    else:
        with st.spinner("Actualizando orden en Supabase..."):

            # Prepare data for update
            commission_data = {
                "numero_orden": num_orden,
                "sede": sede.upper() if sede else "",
                "fecha_elaboracion": fecha_elaboracion.strftime("%d/%m/%Y"),
                "fecha_memorando": fecha_memorando.strftime("%d/%m/%Y"),
                "radicado_memorando": radicado.upper() if radicado else "",
                "rec": rec,
                "id_rubro": id_rubro.upper() if id_rubro else "",
                "fecha_inicial": fecha_inicial.strftime("%d/%m/%Y"),
                "fecha_final": fecha_final.strftime("%d/%m/%Y"),
                "numero_dias": num_dias,
                "valor_viaticos_diario": viaticos_diarios,
                "valor_viaticos_orden": viaticos_orden,
                "valor_gastos_orden": gastos_orden,
                "numero_identificacion": int(num_identificacion) if num_identificacion else 0,
                "primer_nombre": primer_nombre.upper() if primer_nombre else "",
                "otros_nombres": otros_nombres.upper() if otros_nombres else "",
                "primer_apellido": primer_apellido.upper() if primer_apellido else "",
                "segundo_apellido": segundo_apellido.upper() if segundo_apellido else ""
            }

            # Get the database manager
            db_manager = st.session_state.database_manager

            # Get the current order to preserve legalization data
            current_order = db_manager.get_order_by_number(num_orden)

            if current_order:
                # Add legalization fields from current order (don't overwrite)
                commission_data['fecha_legalizacion'] = current_order.get('fecha_legalizacion', '')
                commission_data['numero_legalizacion'] = current_order.get('numero_legalizacion', '')
                commission_data['dias_legalizados'] = current_order.get('dias_legalizados', '')
                commission_data['valor_viaticos_legalizado'] = current_order.get('valor_viaticos_legalizado', '')
                commission_data['valor_gastos_legalizado'] = current_order.get('valor_gastos_legalizado', '')

                # Delete the old order and insert the updated one
                try:
                    db_manager.client.table('ordenes').delete().eq('numero_orden', num_orden).execute()

                    # Save as new order (which recalculates formulated fields)
                    save_success, save_message = save_commission_order(commission_data)

                    if save_success:
                        # Update session state DataFrame for display purposes
                        st.session_state.excel_data = db_manager.get_all_orders_df()

                        # Set success state
                        st.session_state.edit_success_state = {
                            'show_success': True,
                            'last_edited_order': num_orden
                        }

                        # Show immediate success message
                        st.success(f"✅ Orden #{num_orden} actualizada exitosamente")
                        st.rerun()
                    else:
                        st.error(f"❌ {save_message}")
                        st.warning("No se pudo actualizar la orden en Supabase.")

                except Exception as e:
                    st.error(f"❌ Error actualizando orden: {str(e)}")
            else:
                st.error(f"❌ No se encontró la orden #{num_orden}")
