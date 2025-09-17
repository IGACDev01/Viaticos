import streamlit as st
from datetime import datetime, date
import pandas as pd
from utils import get_sede_options
from data_manager import (
    init_database_session, get_funcionario, save_commission_order
)


def render_commission_form_tab():
    """Render the main commission form tab with Supabase integration"""

    # Initialize database if not already done
    init_database_session()

    # Main title
    st.markdown('<h1 class="main-title">📋 Registro de Órdenes de Comisión</h1>', unsafe_allow_html=True)

    # Render the form
    render_commission_form()

    # Additional information
    st.markdown("---")
    st.markdown("**Nota:** Todos los campos marcados son obligatorios excepto 'Otros Nombres' y 'Segundo Apellido'.")


def render_commission_form():
    """Render the commission form with Supabase integration"""

    # Initialize form success state
    if 'form_success_state' not in st.session_state:
        st.session_state.form_success_state = {
            'show_success': False,
            'last_saved_order': None,
            'funcionario_message': None
        }

    # Check for success message
    if st.session_state.form_success_state['show_success']:
        render_success_message()
        return

    # Render the actual form
    render_form_fields("1", "")


def render_success_message():
    """Render success message"""
    success_state = st.session_state.form_success_state

    st.markdown('<div class="success-section">', unsafe_allow_html=True)

    col_success1, col_success2 = st.columns([2, 1])

    with col_success1:
        st.success("¡Registro guardado exitosamente en Supabase!")

        # Show saved data summary
        if success_state['last_saved_order']:
            st.write("**Datos guardados:**")
            st.write(f"• **Orden:** {success_state['last_saved_order'].get('numero_orden', 'N/A')}")
            st.write(f"• **Sede:** {success_state['last_saved_order'].get('sede', 'N/A')}")
            st.write(
                f"• **Funcionario:** {success_state['last_saved_order'].get('primer_nombre', '')} {success_state['last_saved_order'].get('primer_apellido', '')}")
            st.write(f"• **Fecha:** {success_state['last_saved_order'].get('fecha_elaboracion', 'N/A')}")

        # Show funcionario save message if it was a new one
        if success_state['funcionario_message']:
            st.info(success_state['funcionario_message'])

    with col_success2:
        if st.button("➕ Adicionar otro registro", key="add_another_btn", use_container_width=True):
            # Reset success state
            st.session_state.form_success_state = {
                'show_success': False,
                'last_saved_order': None,
                'funcionario_message': None
            }
            # Clear funcionario info
            if 'funcionario_info' in st.session_state:
                st.session_state['funcionario_info'] = None
            # Clear form fields
            keys_to_delete = [k for k in st.session_state.keys() if k.startswith('form_')]
            for key in keys_to_delete:
                del st.session_state[key]
            # Refresh data
            st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_form_fields(form_id, form_prefix):
    """Render the form fields with Supabase integration"""

    sede_options = get_sede_options()

    # Employee lookup section
    st.markdown('<div class="section-title">🔍 Búsqueda de Funcionario (Opcional)</div>', unsafe_allow_html=True)

    col_lookup1, col_lookup2 = st.columns([2, 1])

    with col_lookup1:
        lookup_id = st.text_input(
            "Número de Identificación para Búsqueda",
            help="Ingrese el número de identificación para buscar en Supabase",
            key=f"{form_prefix}lookup_id"
        )

    with col_lookup2:
        st.markdown("<br>", unsafe_allow_html=True)
        lookup_btn = st.button("🔍 Buscar Funcionario", key=f"{form_prefix}lookup_btn")

    # Initialize employee info in session state
    funcionario_key = f"{form_prefix}funcionario_info"
    if funcionario_key not in st.session_state:
        st.session_state[funcionario_key] = None

    # Handle employee lookup
    if lookup_btn and lookup_id.strip():
        with st.spinner("Buscando funcionario en Supabase..."):
            funcionario_info = get_funcionario(lookup_id.strip())
            if funcionario_info:
                st.success("✅ Funcionario encontrado en Supabase")
                st.session_state[funcionario_key] = funcionario_info
            else:
                st.warning(
                    "⚠️ Funcionario no encontrado. Complete la información manualmente y se guardará para futuras comisiones.")
                st.session_state[funcionario_key] = None

    # Create the main form
    with st.form(f"commission_form_{form_id}"):

        # Section 1: Commission Information
        st.markdown('<div class="section-title">1. Información de la Comisión</div>', unsafe_allow_html=True)

        # First row: Número de orden, sede y fecha de elaboración
        col1, col2, col3 = st.columns(3)

        with col1:
            num_orden = st.number_input(
                "Número de Orden", min_value=1, step=1, format="%d",
                help="Ingrese solo números", key=f"{form_prefix}num_orden"
            )

        with col2:
            sede = st.selectbox(
                "Sede", options=sede_options,
                help="Seleccione una sede de la lista", key=f"{form_prefix}sede"
            )

        with col3:
            fecha_elaboracion = st.date_input(
                "Fecha Elaboración", value=date.today(),
                help="Seleccione la fecha de elaboración", key=f"{form_prefix}fecha_elaboracion"
            )

        # Second row: Radicado, Fecha Memorando, REC, ID Rubro
        col4, col5, col6, col7 = st.columns(4)

        with col4:
            radicado = st.text_input(
                "Radicado del Memorando",
                help="Ingrese el ID del radicado", key=f"{form_prefix}radicado"
            )

        with col5:
            fecha_memorando = st.date_input(
                "Fecha Memorando", value=date.today(),
                help="Seleccione la fecha del memorando", key=f"{form_prefix}fecha_memorando"
            )

        with col6:
            rec = st.number_input(
                "REC", min_value=1, step=1, format="%d",
                help="Ingrese solo números", key=f"{form_prefix}rec"
            )

        with col7:
            id_rubro = st.text_input(
                "ID del Rubro",
                help="Ingrese el ID del rubro", key=f"{form_prefix}id_rubro"
            )

        # Third row: Fecha Inicial, Fecha Final
        col8, col9 = st.columns(2)

        with col8:
            fecha_inicial = st.date_input(
                "Fecha Inicial", value=date.today(),
                help="Seleccione la fecha inicial", key=f"{form_prefix}fecha_inicial"
            )

        with col9:
            # Only restriction is that fecha_final must be after fecha_inicial
            min_fecha_final = fecha_inicial if fecha_inicial else date.today()

            fecha_final = st.date_input(
                "Fecha Final", value=date.today(), min_value=fecha_inicial,
                help="Debe ser posterior o igual a la fecha inicial", key=f"{form_prefix}fecha_final"
            )

        # Fourth row: Número de Días, Valor Viáticos Diario, Valor Viáticos Orden, Valor Gastos Orden
        col10, col11, col12, col13 = st.columns(4)

        with col10:
            num_dias = st.number_input(
                "Número de Días", min_value=0, step=1, format="%d",
                help="Ingrese el número de días", key=f"{form_prefix}num_dias"
            )

        with col11:
            viaticos_diarios = st.number_input(
                "Valor Viáticos Diario", min_value=0.0, format="%.2f",
                help="Ingrese el valor con decimales", key=f"{form_prefix}viaticos_diarios"
            )

        with col12:
            viaticos_orden = st.number_input(
                "Valor Viáticos Orden", min_value=0.0, step=0.01, format="%.2f",
                help="Ingrese el valor con decimales", key=f"{form_prefix}viaticos_orden"
            )

        with col13:
            gastos_orden = st.number_input(
                "Valor Gastos Orden", min_value=0.0, step=0.01, format="%.2f",
                help="Ingrese el valor con decimales", key=f"{form_prefix}gastos_orden"
            )

        # Add spacing
        st.markdown("<br>", unsafe_allow_html=True)

        # Section 2: Employee Information
        st.markdown('<div class="section-title">2. Información del Funcionario</div>', unsafe_allow_html=True)

        # Get funcionario info from session state
        funcionario_info = st.session_state.get(funcionario_key)

        # Employee ID field
        num_identificacion = st.text_input(
            "Número de Identificación",
            value=lookup_id if lookup_id else "",
            help="Ingrese el número de identificación",
            key=f"{form_prefix}num_identificacion"
        )

        # Display employee information fields
        if funcionario_info:
            # Show pre-filled information with default values
            st.info("💡 La información del funcionario se cargó automáticamente desde Supabase.")

            col_info1, col_info2 = st.columns(2)

            with col_info1:

                primer_nombre = st.text_input(
                    "Primer Nombre",
                    value=funcionario_info['primer_nombre'],
                    help="Información cargada automáticamente",
                    key=f"{form_prefix}primer_nombre"
                )

                otros_nombres = st.text_input(
                    "Otros Nombres",
                    value=funcionario_info['otros_nombres'],
                    help="Información cargada automáticamente (opcional)",
                    key=f"{form_prefix}otros_nombres"
                )

            with col_info2:

                primer_apellido = st.text_input(
                    "Primer Apellido",
                    value=funcionario_info['primer_apellido'],
                    help="Información cargada automáticamente",
                    key=f"{form_prefix}primer_apellido"
                )

                segundo_apellido = st.text_input(
                    "Segundo Apellido",
                    value=funcionario_info['segundo_apellido'],
                    help="Información cargada automáticamente (opcional)",
                    key=f"{form_prefix}segundo_apellido"
                )

        else:
            # Manual entry fields
            col14, col15 = st.columns(2)

            with col14:
                primer_nombre = st.text_input(
                    "Primer Nombre",
                    help="Ingrese el primer nombre", key=f"{form_prefix}primer_nombre"
                )

                otros_nombres = st.text_input(
                    "Otros Nombres",
                    help="Ingrese otros nombres (opcional)", key=f"{form_prefix}otros_nombres"
                )

            with col15:
                primer_apellido = st.text_input(
                    "Primer Apellido",
                    help="Ingrese el primer apellido", key=f"{form_prefix}primer_apellido"
                )
                segundo_apellido = st.text_input(
                    "Segundo Apellido",
                    help="Ingrese el segundo apellido (opcional)", key=f"{form_prefix}segundo_apellido"
                )

        # Add spacing
        st.markdown("<br>", unsafe_allow_html=True)

        # Submit button
        col_center = st.columns([1, 2, 1])
        with col_center[1]:
            submitted = st.form_submit_button("💾 Registrar en Supabase", use_container_width=True)

        # Form validation and processing
        if submitted:
            process_form_submission(
                num_orden, sede, fecha_elaboracion, radicado, fecha_memorando, rec, id_rubro,
                fecha_inicial, fecha_final, num_dias, viaticos_diarios, viaticos_orden, gastos_orden,
                num_identificacion, primer_nombre, otros_nombres, primer_apellido, segundo_apellido,
                form_id, form_prefix
            )


def process_form_submission(num_orden, sede, fecha_elaboracion, radicado, fecha_memorando, rec, id_rubro,
                            fecha_inicial, fecha_final, num_dias, viaticos_diarios, viaticos_orden, gastos_orden,
                            num_identificacion, primer_nombre, otros_nombres, primer_apellido, segundo_apellido,
                            form_id, form_prefix):
    """Process form submission with Supabase integration"""

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

    if not num_identificacion.strip():
        errors.append("• Número de Identificación es obligatorio")

    if not primer_nombre.strip():
        errors.append("• Primer Nombre es obligatorio")

    if not primer_apellido.strip():
        errors.append("• Primer Apellido es obligatorio")

    if errors:
        st.error("Por favor corrija los siguientes errores:")
        for error in errors:
            st.error(error)
    else:
        with st.spinner("Guardando registro en Supabase..."):

            # Prepare data for Supabase
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

            # Save to Supabase
            save_success, save_message = save_commission_order(commission_data)

            if save_success:
                # Get calculated fields from the saved order
                saved_order = st.session_state.database_manager.get_order_by_number(num_orden)

                # Update session state DataFrame for display purposes
                st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()

                # Check if funcionario was new
                funcionario_saved_message = ""
                existing_funcionario = get_funcionario(num_identificacion.strip())
                if existing_funcionario:
                    funcionario_saved_message = f"✅ Funcionario guardado en Supabase para futuras comisiones."

                # Set success state
                st.session_state.form_success_state = {
                    'show_success': True,
                    'last_saved_order': saved_order,
                    'funcionario_message': funcionario_saved_message
                }

                # Show immediate success message
                st.success(f"✅ {save_message}")
                if funcionario_saved_message:
                    st.info(funcionario_saved_message)

                st.rerun()
            else:
                st.error(f"❌ {save_message}")
                st.warning("No se pudo guardar el registro en Supabase.")