import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
from utils import format_currency

def render_dashboard_tab():
    """Render the dashboard with data analytics"""
    st.markdown('<h1 class="main-title">📊 Dashboard - Análisis de Datos</h1>', unsafe_allow_html=True)

    # Quick refresh button
    col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 2, 1])
    with col_refresh2:
        if st.button("🔄 Actualizar datos desde Supabase", key="refresh_dashboard", use_container_width=True):
            with st.spinner("Actualizando datos desde Supabase..."):
                success, message = st.session_state.database_manager.refresh_data()
                if success:
                    st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    st.markdown("---")

    if st.session_state.excel_data is None:
        render_no_data_message()
        return

    df = st.session_state.excel_data.copy()
    
    # Process dates and prepare data
    df_processed = process_data_for_dashboard(df)
    
    if df_processed is None or len(df_processed) == 0:
        st.warning("⚠️ No se pudieron procesar las fechas en los datos.")
        return
    
    # Filters section
    df_filtered = render_filters_section(df_processed)

    st.markdown("---")
    
    # Alert dashboard section
    if st.session_state.excel_data is not None and 'Alerta' in st.session_state.excel_data.columns:
        st.markdown('<div class="section-title">🚨 Panel de Alertas de Legalización</div>', unsafe_allow_html=True)
        
        # Alert summary
        alert_counts = st.session_state.excel_data['Alerta'].value_counts()
        
        col_alert1, col_alert2, col_alert3 = st.columns(3)
        
        with col_alert1:
            plazo_vencido = alert_counts.get('Plazo Vencido', 0)
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);">
                <div class="metric-value">{plazo_vencido}</div>
                <div class="metric-label">Plazo Vencido</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_alert2:
            plazo_proximo = alert_counts.get('Plazo Próximo', 0)
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #ffa726 0%, #ff9800 100%);">
                <div class="metric-value">{plazo_proximo}</div>
                <div class="metric-label">Plazo Próximo</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_alert3:
            tiempo_suficiente = alert_counts.get('Tiempo Suficiente', 0)
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);">
                <div class="metric-value">{tiempo_suficiente}</div>
                <div class="metric-label">Tiempo Suficiente</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Show critical orders
        critical_orders = st.session_state.excel_data[
            st.session_state.excel_data['Alerta'].isin(['Plazo Vencido', 'Plazo Próximo'])
        ]
        
        if len(critical_orders) > 0:
            with st.expander(f"⚠️ Órdenes que Requieren Atención ({len(critical_orders)})", expanded=False):
                display_columns = [
                    'Número de Orden', 'Sede', 'Primer Nombre', 'Primer Apellido',
                    'Fecha Final', 'Fecha Límite Legalización', 'Plazo Restante Legalización', 'Alerta'
                ]
                available_columns = [col for col in display_columns if col in critical_orders.columns]
                st.dataframe(
                    critical_orders[available_columns].sort_values('Plazo Restante Legalización', na_position='last'),
                    use_container_width=True,
                    hide_index=True
                )

    # Overview metrics
    render_overview_metrics(df_filtered)
    
    # Charts section
    render_charts_section(df_filtered)
    
    # Data tables section
    render_data_tables(df_filtered)

def render_no_data_message():
    """Render message when no data is available"""
    st.warning("⚠️ No hay datos cargados. Por favor, carga un archivo Excel primero.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        ### 📋 Para usar el Dashboard:
        
        1. **Ve a la pestaña 'Órdenes de Comisión'**
        2. **Carga un archivo Excel** con datos existentes
        3. **Regresa aquí** para ver los análisis
        
        El dashboard mostrará:
        - 📈 Métricas generales
        - 🏢 Distribución por sede
        - 💰 Análisis de viáticos
        - 📅 Tendencias temporales
        """)

def process_data_for_dashboard(df):
    """Process data for dashboard analysis"""
    try:
        df_processed = df.copy()
        
        # FIXED: Look for the correct date column that exists in the data
        # Check which date columns are available
        available_date_columns = []
        potential_date_columns = [
            'Fecha de Registro', 'Fecha de Elaboración', 'Fecha Inicial', 
            'Fecha Final', 'Fecha Memorando', 'Fecha Legalización'
        ]
        
        for col in potential_date_columns:
            if col in df_processed.columns:
                available_date_columns.append(col)
        
        if not available_date_columns:
            st.warning("No se encontraron columnas de fecha válidas en los datos.")
            return None
        
        # Use the first available date column, preferring 'Fecha de Registro'
        date_column = 'Fecha de Registro' if 'Fecha de Registro' in available_date_columns else available_date_columns[0]
        
        st.info(f"📅 Usando columna de fecha: **{date_column}** para el análisis temporal")
        
        # Convert date column to datetime
        try:
            # Try different date formats
            date_formats = ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']
            
            for fmt in date_formats:
                try:
                    df_processed['Fecha_Analisis'] = pd.to_datetime(
                        df_processed[date_column], 
                        format=fmt, 
                        errors='raise'
                    )
                    break
                except (ValueError, TypeError):
                    continue
            else:
                # If no format works, try pandas automatic parsing
                df_processed['Fecha_Analisis'] = pd.to_datetime(
                    df_processed[date_column], 
                    errors='coerce',
                    dayfirst=True  # Assume day comes first (DD/MM/YYYY)
                )
        except Exception as e:
            st.error(f"Error al procesar fechas: {str(e)}")
            return None
        
        # Remove rows with invalid dates
        original_len = len(df_processed)
        df_processed = df_processed.dropna(subset=['Fecha_Analisis'])
        processed_len = len(df_processed)
        
        if processed_len == 0:
            st.warning("No se pudieron procesar ninguna fecha válida.")
            return None
        
        if processed_len < original_len:
            st.warning(f"Se procesaron {processed_len} de {original_len} registros (algunos registros tenían fechas inválidas)")
        
        # Extract year and month
        df_processed['Año'] = df_processed['Fecha_Analisis'].dt.year
        df_processed['Mes'] = df_processed['Fecha_Analisis'].dt.month
        df_processed['Mes_Nombre'] = df_processed['Fecha_Analisis'].dt.strftime('%B')
        
        # Create proper month labels for sorting and display
        df_processed['Año_Mes'] = df_processed['Fecha_Analisis'].dt.to_period('M')
        df_processed['Año_Mes_Str'] = df_processed['Año_Mes'].astype(str)
        
        # Create a more readable month format (MMM YYYY)
        df_processed['Mes_Año_Display'] = df_processed['Fecha_Analisis'].dt.strftime('%b %Y')
        
        # Create quarterly periods
        df_processed['Trimestre'] = df_processed['Fecha_Analisis'].dt.to_period('Q')
        df_processed['Trimestre_Str'] = df_processed['Trimestre'].astype(str)
        
        # Calculate total commission value (viaticos + gastos)
        viaticos_col = 'Valor Viáticos Orden' if 'Valor Viáticos Orden' in df_processed.columns else None
        gastos_col = 'Valor Gastos Orden' if 'Valor Gastos Orden' in df_processed.columns else None
        
        if viaticos_col and gastos_col:
            df_processed['Total_Comision'] = pd.to_numeric(df_processed[viaticos_col], errors='coerce').fillna(0) + pd.to_numeric(df_processed[gastos_col], errors='coerce').fillna(0)
        elif viaticos_col:
            df_processed['Total_Comision'] = pd.to_numeric(df_processed[viaticos_col], errors='coerce').fillna(0)
        elif gastos_col:
            df_processed['Total_Comision'] = pd.to_numeric(df_processed[gastos_col], errors='coerce').fillna(0)
        else:
            df_processed['Total_Comision'] = 0
        
        # Convert numeric columns to proper types
        numeric_columns = ['Valor Viáticos Orden', 'Valor Gastos Orden', 'Valor Viáticos Diario', 'Número de Días']
        for col in numeric_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
        
        return df_processed
        
    except Exception as e:
        st.error(f"Error procesando datos: {str(e)}")
        return None

def render_filters_section(df):
    """Render filters and return filtered dataframe"""
    st.markdown('<div class="section-title">🔧 Filtros</div>', unsafe_allow_html=True)
    
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        # Year filter
        available_years = sorted(df['Año'].unique())
        selected_years = st.multiselect(
            "Filtrar por Año:",
            available_years,
            default=available_years,
            key="year_filter"
        )
    
    with col_filter2:
        # Month filter
        month_names = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        available_months = sorted(df['Mes'].unique())
        selected_months = st.multiselect(
            "Filtrar por Mes:",
            available_months,
            default=available_months,
            format_func=lambda x: month_names.get(x, str(x)),
            key="month_filter"
        )
    
    with col_filter3:
        # Sede filter
        if 'Sede' in df.columns:
            available_sedes = sorted(df['Sede'].dropna().unique())
            selected_sedes = st.multiselect(
                "Filtrar por Sede:",
                available_sedes,
                default=available_sedes,
                key="sede_filter"
            )
        else:
            selected_sedes = []
    
    # Apply filters
    df_filtered = df.copy()
    
    if selected_years:
        df_filtered = df_filtered[df_filtered['Año'].isin(selected_years)]
    
    if selected_months:
        df_filtered = df_filtered[df_filtered['Mes'].isin(selected_months)]
    
    if selected_sedes and 'Sede' in df.columns:
        df_filtered = df_filtered[df_filtered['Sede'].isin(selected_sedes)]
    
    # Show filter results
    st.info(f"📊 Mostrando {len(df_filtered)} registros de {len(df)} totales")
    
    return df_filtered

def render_overview_metrics(df):
    """Render overview metrics cards"""
    st.markdown('<div class="section-title">📈 Métricas Generales</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_records = len(df)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_records:,}</div>
            <div class="metric-label">Total Registros</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        unique_employees = df['Número de Identificación'].nunique() if 'Número de Identificación' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{unique_employees:,}</div>
            <div class="metric-label">Funcionarios Únicos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_viaticos = df['Valor Viáticos Orden'].sum() if 'Valor Viáticos Orden' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${format_currency(total_viaticos)}</div>
            <div class="metric-label">Total Viáticos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_days = df['Número de Días'].mean() if 'Número de Días' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_days:.1f}</div>
            <div class="metric-label">Promedio Días</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

def render_charts_section(df):
    """Render charts section"""
    # Temporal Analysis
    render_temporal_analysis(df)
    
    # Monthly/Quarterly Line Chart
    render_period_line_chart(df)
    
    # Monthly/Quarterly Stacked Bar Chart by Sede
    render_period_stacked_bar_chart_by_sede(df)

def render_temporal_analysis(df):
    """Render updated temporal analysis with proper month display"""
    st.markdown('<div class="section-title">📅 Análisis Temporal Actualizado</div>', unsafe_allow_html=True)
    
    try:
        # Group by month for temporal analysis
        df_monthly_temp = df.groupby(['Año_Mes', 'Mes_Año_Display']).agg({
            'Número de Orden': 'count',
            'Total_Comision': 'sum',
            'Valor Viáticos Orden': 'sum',
            'Valor Gastos Orden': 'sum'
        }).reset_index()
        
        # Sort by the period to ensure proper ordering
        df_monthly_temp = df_monthly_temp.sort_values('Año_Mes')
        df_monthly_temp.columns = ['Año_Mes', 'Mes_Display', 'Cantidad_Registros', 'Total_Comision', 'Total_Viaticos', 'Total_Gastos']
        
        col_temp1, col_temp2 = st.columns(2)
        
        with col_temp1:
            # Monthly registrations with proper month display
            fig_monthly = px.line(
                df_monthly_temp, 
                x='Mes_Display', 
                y='Cantidad_Registros',
                title="Registros Mensuales",
                markers=True,
                color_discrete_sequence=["#1f77b4"]
            )
            fig_monthly.update_traces(
                hovertemplate='<b>%{x}</b><br>Registros: %{y}<extra></extra>'
            )
            fig_monthly.update_layout(
                height=400,
                xaxis_title="Mes",
                xaxis={'categoryorder': 'array', 'categoryarray': df_monthly_temp['Mes_Display'].tolist()}
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
            
            # Download button for monthly registrations
            if st.button("📥 Descargar Datos Registros Mensuales", key="download_monthly_reg"):
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_monthly_temp[['Mes_Display', 'Cantidad_Registros']].to_excel(writer, index=False, sheet_name='Registros_Mensuales')
                buffer.seek(0)
                st.download_button(
                    label="💾 Descargar Excel",
                    data=buffer.getvalue(),
                    file_name=f"registros_mensuales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col_temp2:
            # Monthly commission values with proper month display
            fig_monthly_values = px.line(
                df_monthly_temp, 
                x='Mes_Display', 
                y='Total_Comision',
                title="Valor Total Mensual de Comisiones",
                markers=True,
                color_discrete_sequence=["#2ca02c"]
            )
            fig_monthly_values.update_traces(
                hovertemplate='<b>%{x}</b><br>Total: $%{y:,.2f}<extra></extra>'
            )
            fig_monthly_values.update_layout(
                height=400,
                xaxis_title="Mes",
                xaxis={'categoryorder': 'array', 'categoryarray': df_monthly_temp['Mes_Display'].tolist()}
            )
            st.plotly_chart(fig_monthly_values, use_container_width=True)
            
            # Download button for monthly values
            if st.button("📥 Descargar Datos Valores Mensuales", key="download_monthly_val"):
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_monthly_temp[['Mes_Display', 'Total_Comision', 'Total_Viaticos', 'Total_Gastos']].to_excel(writer, index=False, sheet_name='Valores_Mensuales')
                buffer.seek(0)
                st.download_button(
                    label="💾 Descargar Excel",
                    data=buffer.getvalue(),
                    file_name=f"valores_mensuales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
    except Exception as e:
        st.warning(f"No se pudo generar análisis temporal: {str(e)}")

def render_period_line_chart(df):
    """Render period line chart with monthly/quarterly option and proper display"""
    st.markdown('<div class="section-title">📈 Tendencia Temporal - Valores</div>', unsafe_allow_html=True)
    
    # Period selector
    period_type = st.selectbox(
        "Seleccionar período:",
        ["Mensual", "Trimestral"],
        key="period_line_chart"
    )
    
    try:
        # Group by period
        if period_type == "Mensual":
            df_period = df.groupby(['Año_Mes', 'Mes_Año_Display']).agg({
                'Total_Comision': 'sum',
                'Valor Viáticos Orden': 'sum',
                'Valor Gastos Orden': 'sum'
            }).reset_index()
            df_period = df_period.sort_values('Año_Mes')
            x_col = 'Mes_Año_Display'
            x_order = df_period['Mes_Año_Display'].tolist()
        else:  # Trimestral
            df_period = df.groupby(['Trimestre', 'Trimestre_Str']).agg({
                'Total_Comision': 'sum',
                'Valor Viáticos Orden': 'sum',
                'Valor Gastos Orden': 'sum'
            }).reset_index()
            df_period = df_period.sort_values('Trimestre')
            x_col = 'Trimestre_Str'
            x_order = df_period['Trimestre_Str'].tolist()
        
        # Create line chart with multiple lines
        fig_period_lines = go.Figure()
        
        # Add line for total commissions
        fig_period_lines.add_trace(go.Scatter(
            x=df_period[x_col],
            y=df_period['Total_Comision'],
            mode='lines+markers',
            name='Total Comisiones',
            line=dict(color='#1f77b4', width=3),
            hovertemplate='<b>%{x}</b><br>Total Comisiones: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add line for viaticos
        fig_period_lines.add_trace(go.Scatter(
            x=df_period[x_col],
            y=df_period['Valor Viáticos Orden'],
            mode='lines+markers',
            name='Viáticos',
            line=dict(color='#2ca02c', width=3),
            hovertemplate='<b>%{x}</b><br>Viáticos: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add line for gastos
        fig_period_lines.add_trace(go.Scatter(
            x=df_period[x_col],
            y=df_period['Valor Gastos Orden'],
            mode='lines+markers',
            name='Gastos',
            line=dict(color='#ff7f0e', width=3),
            hovertemplate='<b>%{x}</b><br>Gastos: $%{y:,.2f}<extra></extra>'
        ))
        
        period_label = "Mes" if period_type == "Mensual" else "Trimestre"
        fig_period_lines.update_layout(
            title=f"Evolución {period_type} de Valores",
            xaxis_title=period_label,
            yaxis_title="Valor (COP)",
            height=500,
            hovermode='x unified',
            xaxis={'categoryorder': 'array', 'categoryarray': x_order}
        )
        
        st.plotly_chart(fig_period_lines, use_container_width=True)
        
        # Download button for period line chart data
        if st.button(f"📥 Descargar Datos Tendencia {period_type}", key=f"download_line_{period_type.lower()}"):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_period.to_excel(writer, index=False, sheet_name=f'Tendencia_{period_type}')
            buffer.seek(0)
            st.download_button(
                label="💾 Descargar Excel",
                data=buffer.getvalue(),
                file_name=f"tendencia_{period_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
    except Exception as e:
        st.warning(f"No se pudo generar gráfico de líneas: {str(e)}")

def render_period_stacked_bar_chart_by_sede(df):
    """Render stacked bar chart by sede and period with proper display"""
    st.markdown('<div class="section-title">📊 Análisis Temporal por Sede</div>', unsafe_allow_html=True)
    
    col_selector1, col_selector2 = st.columns(2)
    
    with col_selector1:
        # Period selector
        period_type = st.selectbox(
            "Seleccionar período:",
            ["Mensual", "Trimestral"],
            key="period_stacked_chart"
        )
    
    with col_selector2:
        # Value type selector
        chart_value_type = st.selectbox(
            "Seleccionar tipo de valor:",
            ["Total Comisiones", "Solo Viáticos", "Solo Gastos"],
            key="chart_value_stacked_filter"
        )
    
    try:
        # Map selection to column
        value_column_map = {
            "Total Comisiones": "Total_Comision",
            "Solo Viáticos": "Valor Viáticos Orden",
            "Solo Gastos": "Valor Gastos Orden"
        }
        value_column = value_column_map[chart_value_type]
        
        # Group by period and sede
        if period_type == "Mensual":
            df_period_sede = df.groupby(['Año_Mes', 'Mes_Año_Display', 'Sede']).agg({
                value_column: 'sum'
            }).reset_index()
            df_period_sede = df_period_sede.sort_values('Año_Mes')
            x_col = 'Mes_Año_Display'
            x_order = df_period_sede['Mes_Año_Display'].unique().tolist()
        else:  # Trimestral
            df_period_sede = df.groupby(['Trimestre', 'Trimestre_Str', 'Sede']).agg({
                value_column: 'sum'
            }).reset_index()
            df_period_sede = df_period_sede.sort_values('Trimestre')
            x_col = 'Trimestre_Str'
            x_order = df_period_sede['Trimestre_Str'].unique().tolist()
        
        # Create stacked bar chart
        fig_stacked_sede = px.bar(
            df_period_sede,
            x=x_col,
            y=value_column,
            color='Sede',
            title=f"Distribución {period_type} por Sede - {chart_value_type} (Barras Apiladas)",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        # Update to stacked bars
        fig_stacked_sede.update_layout(barmode='stack')
        
        fig_stacked_sede.update_traces(
            hovertemplate='<b>%{fullData.name}</b><br>%{x}<br>Valor: $%{y:,.2f}<extra></extra>'
        )
        
        period_label = "Mes" if period_type == "Mensual" else "Trimestre"
        fig_stacked_sede.update_layout(
            height=600,
            xaxis_title=period_label,
            yaxis_title=f"Valor {chart_value_type} (COP)",
            legend_title="Sede",
            xaxis={'categoryorder': 'array', 'categoryarray': x_order}
        )
        
        st.plotly_chart(fig_stacked_sede, use_container_width=True)
        
        # Download button for stacked chart data
        if st.button(f"📥 Descargar Datos {period_type} por Sede", key=f"download_stacked_{period_type.lower()}_{chart_value_type.lower()}"):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_period_sede.to_excel(writer, index=False, sheet_name=f'Datos_{period_type}_Sede')
            buffer.seek(0)
            st.download_button(
                label="💾 Descargar Excel",
                data=buffer.getvalue(),
                file_name=f"datos_sede_{period_type.lower()}_{chart_value_type.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Summary table for the chart
        with st.expander(f"📋 Tabla Resumen - {period_type}"):
            # Pivot table for better visualization
            pivot_table = df_period_sede.pivot(
                index='Sede', 
                columns=x_col, 
                values=value_column
            ).fillna(0)
            
            # Format currency in the table
            formatted_table = pivot_table.copy()
            for col in formatted_table.columns:
                formatted_table[col] = formatted_table[col].apply(lambda x: f"${format_currency(x)}")
            
            st.dataframe(formatted_table, use_container_width=True)
            
            # Download button for summary table
            if st.button(f"📥 Descargar Tabla Resumen {period_type}", key=f"download_table_{period_type.lower()}_{chart_value_type.lower()}"):
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    pivot_table.to_excel(writer, sheet_name=f'Resumen_{period_type}')
                buffer.seek(0)
                st.download_button(
                    label="💾 Descargar Excel",
                    data=buffer.getvalue(),
                    file_name=f"tabla_resumen_{period_type.lower()}_{chart_value_type.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
    except Exception as e:
        st.warning(f"No se pudo generar gráfico de barras apiladas: {str(e)}")


def render_data_tables(df):
    """Render data tables section with Excel exports"""
    st.markdown('<div class="section-title">📋 Exploración de Datos</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Registros Recientes", "🔍 Buscar Funcionario", "📈 Resumen por Sede"])
    
    with tab1:
        st.subheader("Últimos 10 Registros")
        recent_data = df.tail(10).copy()
        if len(recent_data) > 0:
            # Remove problematic columns for display
            display_columns = [col for col in recent_data.columns if 'Año_Mes' not in col and 'Trimestre' not in col and 'Fecha_Analisis' not in col]
            recent_display = recent_data[display_columns]
            
            # Format currency columns for display
            if 'Valor Viáticos Orden' in recent_display.columns:
                recent_display = recent_display.copy()
                recent_display['Valor Viáticos (Formatted)'] = recent_display['Valor Viáticos Orden'].apply(lambda x: f"${format_currency(x)}")
            
            st.dataframe(recent_display, use_container_width=True, height=400)
            
            # Download button for recent records (Excel format)
            if st.button("📥 Descargar Registros Recientes", key="download_recent"):
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    recent_display.to_excel(writer, index=False, sheet_name='Registros_Recientes')
                buffer.seek(0)
                st.download_button(
                    label="💾 Descargar Excel",
                    data=buffer.getvalue(),
                    file_name=f"registros_recientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("No hay datos para mostrar")
    
    with tab2:
        st.subheader("Buscar por Funcionario")
        if 'Primer Nombre' in df.columns and 'Primer Apellido' in df.columns:
            search_term = st.text_input("Ingrese nombre o apellido del funcionario:", "")
            
            if search_term:
                # Filter data based on search term
                mask = (
                    df['Primer Nombre'].str.contains(search_term, case=False, na=False) |
                    df['Primer Apellido'].str.contains(search_term, case=False, na=False)
                )
                
                if 'Otros Nombres' in df.columns:
                    mask |= df['Otros Nombres'].str.contains(search_term, case=False, na=False)
                
                if 'Segundo Apellido' in df.columns:
                    mask |= df['Segundo Apellido'].str.contains(search_term, case=False, na=False)
                
                filtered_df = df[mask]
                
                if len(filtered_df) > 0:
                    st.success(f"Se encontraron {len(filtered_df)} registros")
                    # Remove problematic columns for display
                    display_columns = [col for col in filtered_df.columns if 'Año_Mes' not in col and 'Trimestre' not in col and 'Fecha_Analisis' not in col]
                    search_results = filtered_df[display_columns]
                    st.dataframe(search_results, use_container_width=True)
                    
                    # Download button for search results (Excel format)
                    if st.button("📥 Descargar Resultados Búsqueda", key="download_search"):
                        buffer = BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            search_results.to_excel(writer, index=False, sheet_name='Resultados_Busqueda')
                        buffer.seek(0)
                        st.download_button(
                            label="💾 Descargar Excel",
                            data=buffer.getvalue(),
                            file_name=f"busqueda_funcionario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.warning("No se encontraron registros que coincidan con la búsqueda")
        else:
            st.warning("Columnas de nombres no disponibles para búsqueda")
    
    with tab3:
        st.subheader("Resumen Estadístico por Sede")
        if 'Sede' in df.columns and 'Valor Viáticos Orden' in df.columns:
            summary_stats = df.groupby('Sede').agg({
                'Número de Orden': 'count',
                'Total_Comision': ['sum', 'mean'],
                'Valor Viáticos Orden': ['sum', 'mean'],
                'Valor Gastos Orden': ['sum', 'mean'],
                'Número de Días': 'mean'
            }).round(2)
            
            # Flatten column names
            summary_stats.columns = [
                'Total_Ordenes', 'Total_Comision_Sum', 'Total_Comision_Mean',
                'Total_Viaticos_Sum', 'Total_Viaticos_Mean',
                'Total_Gastos_Sum', 'Total_Gastos_Mean', 'Promedio_Dias'
            ]
            summary_stats = summary_stats.reset_index()
            
            # Format currency columns
            currency_columns = [
                'Total_Comision_Sum', 'Total_Comision_Mean',
                'Total_Viaticos_Sum', 'Total_Viaticos_Mean',
                'Total_Gastos_Sum', 'Total_Gastos_Mean'
            ]
            
            for col in currency_columns:
                summary_stats[f'{col}_Formatted'] = summary_stats[col].apply(lambda x: f"${format_currency(x)}")
            
            st.dataframe(summary_stats, use_container_width=True)
            
            # Download button for summary by sede (Excel format)
            if st.button("📥 Descargar Resumen por Sede", key="download_sede_summary"):
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    summary_stats.to_excel(writer, index=False, sheet_name='Resumen_Por_Sede')
                buffer.seek(0)
                st.download_button(
                    label="💾 Descargar Excel",
                    data=buffer.getvalue(),
                    file_name=f"resumen_por_sede_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("Datos insuficientes para generar resumen por sede")