import os
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st
from supabase import create_client, Client

class SupabaseDBManager:
    """Supabase database manager for commission orders system"""

    def __init__(self):
        self.supabase_url = st.secrets["SUPABASE_URL"]
        self.supabase_key = self.st.secrets["SUPABASE_KEY"]

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def calculate_business_days(self, start_date: str, end_date: str) -> int:
        """Calculate business days between two dates excluding holidays"""
        try:
            # Get holidays from database
            response = self.client.table('festivos').select('fecha').execute()
            holidays_data = response.data

            # Convert holidays to datetime objects
            holidays = []
            for holiday in holidays_data:
                try:
                    holiday_date = holiday['fecha']
                    if '-' in holiday_date:
                        holidays.append(datetime.strptime(holiday_date, '%Y-%m-%d').date())
                    else:
                        holidays.append(datetime.strptime(holiday_date, '%d/%m/%Y').date())
                except:
                    continue

            # Convert string dates to datetime objects
            if '/' in start_date:
                start = datetime.strptime(start_date, '%d/%m/%Y').date()
                end = datetime.strptime(end_date, '%d/%m/%Y').date()
            else:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()

            business_days = 0
            current = start

            while current <= end:
                if (current.weekday() < 5 and current not in holidays):
                    business_days += 1
                current += timedelta(days=1)

            return business_days

        except Exception as e:
            print(f"Error calculating business days: {str(e)}")
            return 0

    def calculate_workday(self, start_date: str, days: int) -> str:
        """Calculate workday (WORKDAY.INTL equivalent) excluding weekends and holidays"""
        try:
            # Get holidays from database
            response = self.client.table('festivos').select('fecha').execute()
            holidays_data = response.data

            # Convert holidays to datetime objects
            holidays = []
            for holiday in holidays_data:
                try:
                    holiday_date = holiday['fecha']
                    if '-' in holiday_date:
                        holidays.append(datetime.strptime(holiday_date, '%Y-%m-%d').date())
                    else:
                        holidays.append(datetime.strptime(holiday_date, '%d/%m/%Y').date())
                except:
                    continue

            # Convert start date
            if '/' in start_date:
                start = datetime.strptime(start_date, '%d/%m/%Y').date()
            else:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()

            current = start
            days_added = 0

            while days_added < days:
                current += timedelta(days=1)
                if current.weekday() < 5 and current not in holidays:
                    days_added += 1

            return current.strftime('%d/%m/%Y')

        except Exception as e:
            print(f"Error calculating workday: {str(e)}")
            return ""

    def calculate_formulated_fields(self, order_data: Dict) -> Dict:
        """Calculate the Excel formulated fields"""
        formulated = {}

        try:
            fecha_final = order_data.get('fecha_final', '')
            fecha_inicial = order_data.get('fecha_inicial', '')
            fecha_legalizacion = order_data.get('fecha_legalizacion', '')

            # Fecha Reintegro: WORKDAY.INTL(fecha_final, 1, 1, holidays)
            if fecha_final and fecha_final != 'ANULADA':
                formulated['fecha_reintegro'] = self.calculate_workday(fecha_final, 1)
            else:
                formulated['fecha_reintegro'] = ''

            # Fecha Límite Legalización: WORKDAY.INTL(fecha_final, 5, 1, holidays)
            if fecha_final and fecha_final != 'ANULADA' and fecha_inicial != 'ANULADA':
                formulated['fecha_limite_legalizacion'] = self.calculate_workday(fecha_final, 5)
            else:
                formulated['fecha_limite_legalizacion'] = ''

            # Plazo Restante Legalización
            if fecha_legalizacion or not formulated['fecha_limite_legalizacion']:
                formulated['plazo_restante_legalizacion'] = None
            else:
                try:
                    today = datetime.now().strftime('%d/%m/%Y')
                    total_days = self.calculate_business_days(fecha_inicial, formulated['fecha_limite_legalizacion'])
                    elapsed_days = self.calculate_business_days(fecha_inicial, today)
                    formulated['plazo_restante_legalizacion'] = total_days - elapsed_days
                except:
                    formulated['plazo_restante_legalizacion'] = None

            # Alerta
            plazo = formulated.get('plazo_restante_legalizacion')
            if plazo is None:
                formulated['alerta'] = ''
            elif plazo < 0:
                formulated['alerta'] = 'Plazo Vencido'
            elif plazo <= 2:
                formulated['alerta'] = 'Plazo Próximo'
            else:
                formulated['alerta'] = 'Tiempo Suficiente'

            # Estado Legalización
            if fecha_legalizacion:
                try:
                    if formulated['fecha_limite_legalizacion']:
                        legalizacion_date = datetime.strptime(fecha_legalizacion, '%d/%m/%Y').date()
                        limite_date = datetime.strptime(formulated['fecha_limite_legalizacion'], '%d/%m/%Y').date()
                        formulated[
                            'estado_legalizacion'] = 'A tiempo' if legalizacion_date <= limite_date else 'Atrasado'
                    else:
                        formulated['estado_legalizacion'] = 'A tiempo'
                except:
                    formulated['estado_legalizacion'] = 'A tiempo'
            else:
                try:
                    if formulated['fecha_limite_legalizacion']:
                        today = datetime.now().date()
                        limite_date = datetime.strptime(formulated['fecha_limite_legalizacion'], '%d/%m/%Y').date()
                        formulated['estado_legalizacion'] = 'Atrasado' if today > limite_date else 'A tiempo'
                    else:
                        formulated['estado_legalizacion'] = 'A tiempo'
                except:
                    formulated['estado_legalizacion'] = 'A tiempo'

            # Valor Orden Legalizado
            viaticos_leg = order_data.get('valor_viaticos_legalizado', 0) or 0
            gastos_leg = order_data.get('valor_gastos_legalizado', 0) or 0
            if viaticos_leg or gastos_leg:
                formulated['valor_orden_legalizado'] = float(viaticos_leg) + float(gastos_leg)
            else:
                formulated['valor_orden_legalizado'] = None

        except Exception as e:
            print(f"Error calculating formulated fields: {str(e)}")
            formulated = {
                'fecha_reintegro': '',
                'fecha_limite_legalizacion': '',
                'plazo_restante_legalizacion': None,
                'alerta': '',
                'estado_legalizacion': 'A tiempo',
                'valor_orden_legalizado': None
            }

        return formulated

    def get_funcionario(self, numero_identificacion: int) -> Optional[Dict]:
        """Get funcionario by identification number"""
        try:
            response = self.client.table('funcionarios').select('*').eq('numero_identificacion',
                                                                        numero_identificacion).execute()

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            print(f"Error getting funcionario: {str(e)}")
            return None

    def save_funcionario(self, numero_identificacion: int, primer_nombre: str,
                         otros_nombres: str, primer_apellido: str,
                         segundo_apellido: str) -> Tuple[bool, str]:
        """Save or update funcionario"""
        try:
            funcionario_data = {
                'numero_identificacion': numero_identificacion,
                'primer_nombre': primer_nombre.upper(),
                'otros_nombres': otros_nombres.upper(),
                'primer_apellido': primer_apellido.upper(),
                'segundo_apellido': segundo_apellido.upper()
            }

            # Try to insert, if conflict then update
            response = self.client.table('funcionarios').upsert(funcionario_data).execute()

            if response.data:
                return True, "Funcionario guardado exitosamente"
            else:
                return False, "Error guardando funcionario"

        except Exception as e:
            return False, f"Error guardando funcionario: {str(e)}"

    def save_commission_order(self, commission_data: Dict) -> Tuple[bool, str]:
        """Save commission order with automatic field calculations"""
        try:
            # Calculate formulated fields
            formulated = self.calculate_formulated_fields(commission_data)

            # Check if funcionario exists, if not create it
            funcionario_exists = self.get_funcionario(commission_data['numero_identificacion'])
            if not funcionario_exists:
                self.save_funcionario(
                    commission_data['numero_identificacion'],
                    commission_data['primer_nombre'],
                    commission_data['otros_nombres'],
                    commission_data['primer_apellido'],
                    commission_data['segundo_apellido']
                )

            # Prepare order data
            order_data = {
                'numero_orden': commission_data['numero_orden'],
                'sede': commission_data['sede'],
                'fecha_elaboracion': commission_data['fecha_elaboracion'],
                'fecha_memorando': commission_data['fecha_memorando'],
                'radicado_memorando': commission_data.get('radicado_memorando', ''),
                'rec': commission_data['rec'],
                'id_rubro': commission_data.get('id_rubro', ''),
                'fecha_inicial': commission_data['fecha_inicial'],
                'fecha_final': commission_data['fecha_final'],
                'numero_dias': commission_data['numero_dias'],
                'valor_viaticos_diario': commission_data['valor_viaticos_diario'],
                'valor_viaticos_orden': commission_data['valor_viaticos_orden'],
                'valor_gastos_orden': commission_data['valor_gastos_orden'],
                'numero_identificacion': commission_data['numero_identificacion'],
                'primer_nombre': commission_data['primer_nombre'],
                'otros_nombres': commission_data['otros_nombres'],
                'primer_apellido': commission_data['primer_apellido'],
                'segundo_apellido': commission_data['segundo_apellido'],
                'fecha_reintegro': formulated['fecha_reintegro'],
                'fecha_limite_legalizacion': formulated['fecha_limite_legalizacion'],
                'plazo_restante_legalizacion': formulated['plazo_restante_legalizacion'],
                'alerta': formulated['alerta'],
                'estado_legalizacion': formulated['estado_legalizacion'],
                'valor_orden_legalizado': formulated['valor_orden_legalizado']
            }

            # Insert order
            response = self.client.table('ordenes').insert(order_data).execute()

            if response.data:
                return True, f"Orden #{commission_data['numero_orden']} guardada exitosamente"
            else:
                return False, "Error guardando orden"

        except Exception as e:
            error_msg = str(e)
            if 'duplicate key' in error_msg.lower() or 'unique constraint' in error_msg.lower():
                return False, f"Ya existe una orden con el número {commission_data['numero_orden']}"
            return False, f"Error guardando orden: {error_msg}"

    def search_orders(self, search_term: str) -> List[Dict]:
        """Search orders by various fields"""
        try:
            # Use ilike for case-insensitive search across multiple fields
            response = self.client.table('ordenes').select('*').or_(
                f"numero_orden.eq.{search_term},"
                f"sede.ilike.%{search_term}%,"
                f"numero_identificacion.eq.{search_term},"
                f"primer_nombre.ilike.%{search_term}%,"
                f"primer_apellido.ilike.%{search_term}%,"
                f"otros_nombres.ilike.%{search_term}%,"
                f"segundo_apellido.ilike.%{search_term}%,"
                f"radicado_memorando.ilike.%{search_term}%,"
                f"id_rubro.ilike.%{search_term}%"
            ).order('created_at', desc=True).execute()

            return response.data

        except Exception as e:
            print(f"Error searching orders: {str(e)}")
            return []

    def update_legalization(self, numero_orden: int, legalization_data: Dict) -> Tuple[bool, str]:
        """Update legalization information for an order and recalculate formulated fields"""
        try:
            # Get current order data
            response = self.client.table('ordenes').select('*').eq('numero_orden', numero_orden).execute()

            if not response.data:
                return False, f"No se encontró la orden #{numero_orden}"

            current_order = response.data[0]

            # Update with new legalization data
            current_order.update(legalization_data)

            # Recalculate formulated fields
            formulated = self.calculate_formulated_fields(current_order)

            # Prepare update data
            update_data = {
                'fecha_legalizacion': legalization_data.get('fecha_legalizacion'),
                'numero_legalizacion': legalization_data.get('numero_legalizacion'),
                'dias_legalizados': legalization_data.get('dias_legalizados'),
                'valor_viaticos_legalizado': legalization_data.get('valor_viaticos_legalizado'),
                'valor_gastos_legalizado': legalization_data.get('valor_gastos_legalizado'),
                'valor_orden_legalizado': formulated['valor_orden_legalizado'],
                'plazo_restante_legalizacion': formulated['plazo_restante_legalizacion'],
                'alerta': formulated['alerta'],
                'estado_legalizacion': formulated['estado_legalizacion']
            }

            # Update the order
            response = self.client.table('ordenes').update(update_data).eq('numero_orden', numero_orden).execute()

            if response.data:
                return True, "Legalización actualizada exitosamente"
            else:
                return False, "Error actualizando legalización"

        except Exception as e:
            return False, f"Error actualizando legalización: {str(e)}"

    def get_all_orders_df(self) -> pd.DataFrame:
        """Get all orders as pandas DataFrame with proper column mapping"""
        try:
            response = self.client.table('ordenes').select('*').order('created_at', desc=True).execute()

            if not response.data:
                return pd.DataFrame()

            df = pd.DataFrame(response.data)

            # Column mapping to original Excel names
            column_mapping = {
                'numero_orden': 'Número de Orden',
                'sede': 'Sede',
                'fecha_elaboracion': 'Fecha de Elaboración',
                'fecha_memorando': 'Fecha Memorando',
                'radicado_memorando': 'Radicado del Memorando',
                'rec': 'REC',
                'id_rubro': 'ID del Rubro',
                'fecha_inicial': 'Fecha Inicial',
                'fecha_final': 'Fecha Final',
                'numero_dias': 'Número de Días',
                'valor_viaticos_diario': 'Valor Viáticos Diario',
                'valor_viaticos_orden': 'Valor Viáticos Orden',
                'valor_gastos_orden': 'Valor Gastos Orden',
                'numero_identificacion': 'Número de Identificación',
                'primer_nombre': 'Primer Nombre',
                'otros_nombres': 'Otros Nombres',
                'primer_apellido': 'Primer Apellido',
                'segundo_apellido': 'Segundo Apellido',
                'fecha_reintegro': 'Fecha Reintegro',
                'fecha_limite_legalizacion': 'Fecha Límite Legalización',
                'plazo_restante_legalizacion': 'Plazo Restante Legalización',
                'alerta': 'Alerta',
                'fecha_legalizacion': 'Fecha Legalización',
                'estado_legalizacion': 'Estado Legalización',
                'numero_legalizacion': 'Número Legalización',
                'dias_legalizados': 'Dias Legalizados',
                'valor_viaticos_legalizado': 'Valor Viaticos Legalizado',
                'valor_gastos_legalizado': 'Valor Gastos Legalizado',
                'valor_orden_legalizado': 'Valor Orden Legalizado'
            }

            # Rename columns to match original Excel
            df = df.rename(columns=column_mapping)

            # Remove metadata columns
            metadata_columns = ['id', 'created_at', 'updated_at']
            df = df.drop(columns=[col for col in metadata_columns if col in df.columns], errors='ignore')

            return df

        except Exception as e:
            print(f"Error getting orders DataFrame: {str(e)}")
            return pd.DataFrame()

    def get_order_by_number(self, numero_orden: int) -> Optional[Dict]:
        """Get specific order by number"""
        try:
            response = self.client.table('ordenes').select('*').eq('numero_orden', numero_orden).execute()

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            print(f"Error getting order: {str(e)}")
            return None

    def export_to_excel(self, filename: str = None) -> str:
        """Export all data to Excel file in Data folder with original column names"""
        if not filename:
            filename = f"Data/ordenes_comision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        else:
            if not filename.startswith("Data/"):
                filename = f"Data/{filename}"

        # Ensure Data directory exists
        os.makedirs("Data", exist_ok=True)

        try:
            # Get data with original column names
            df_orders = self.get_all_orders_df()

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Export orders
                df_orders.to_excel(writer, sheet_name='Data', index=False)

                # Export funcionarios
                response = self.client.table('funcionarios').select('*').order('primer_apellido').execute()
                df_funcionarios = pd.DataFrame(response.data)
                if not df_funcionarios.empty:
                    df_funcionarios = df_funcionarios.drop(columns=['id', 'created_at', 'updated_at'], errors='ignore')
                df_funcionarios.to_excel(writer, sheet_name='Funcionarios', index=False)

                # Export holidays
                response = self.client.table('festivos').select('fecha', 'descripcion').order('fecha').execute()
                df_holidays = pd.DataFrame(response.data)
                if not df_holidays.empty:
                    df_holidays['fecha'] = pd.to_datetime(df_holidays['fecha']).dt.strftime('%d/%m/%Y')
                    df_holidays.columns = ['Fecha', 'Descripción']
                df_holidays.to_excel(writer, sheet_name='Festivos', index=False)

                # Export sedes
                response = self.client.table('sedes').select('codigo', 'nombre').eq('activa', True).order(
                    'nombre').execute()
                df_sedes = pd.DataFrame(response.data)
                if not df_sedes.empty:
                    df_sedes.columns = ['Código', 'Nombre']
                df_sedes.to_excel(writer, sheet_name='Sedes', index=False)

            return filename

        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
            return None

    def import_from_excel(self, excel_file, sheet_name: str = 'Data') -> Tuple[bool, str]:
        """Import data from Excel file with original column structure"""
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

            # Map original Excel columns to database columns
            reverse_column_mapping = {
                'Número de Orden': 'numero_orden',
                'Sede': 'sede',
                'Fecha de Elaboración': 'fecha_elaboracion',
                'Fecha Memorando': 'fecha_memorando',
                'Radicado del Memorando': 'radicado_memorando',
                'REC': 'rec',
                'ID del Rubro': 'id_rubro',
                'Fecha Inicial': 'fecha_inicial',
                'Fecha Final': 'fecha_final',
                'Número de Días': 'numero_dias',
                'Valor Viáticos Diario': 'valor_viaticos_diario',
                'Valor Viáticos Orden': 'valor_viaticos_orden',
                'Valor Gastos Orden': 'valor_gastos_orden',
                'Número de Identificación': 'numero_identificacion',
                'Primer Nombre': 'primer_nombre',
                'Otros Nombres': 'otros_nombres',
                'Primer Apellido': 'primer_apellido',
                'Segundo Apellido': 'segundo_apellido',
                'Fecha Reintegro': 'fecha_reintegro',
                'Fecha Límite Legalización': 'fecha_limite_legalizacion',
                'Plazo Restante Legalización': 'plazo_restante_legalizacion',
                'Alerta': 'alerta',
                'Fecha Legalización': 'fecha_legalizacion',
                'Estado Legalización': 'estado_legalizacion',
                'Número Legalización': 'numero_legalizacion',
                'Dias Legalizados': 'dias_legalizados',
                'Valor Viaticos Legalizado': 'valor_viaticos_legalizado',
                'Valor Gastos Legalizado': 'valor_gastos_legalizado',
                'Valor Orden Legalizado': 'valor_orden_legalizado'
            }

            # Rename columns to database format
            df = df.rename(columns=reverse_column_mapping)

            imported_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Prepare basic commission data (required fields)
                    commission_data = {
                        'numero_orden': int(row['numero_orden']),
                        'sede': str(row['sede']).upper() if pd.notna(row['sede']) else '',
                        'fecha_elaboracion': str(row['fecha_elaboracion']) if pd.notna(
                            row['fecha_elaboracion']) else '',
                        'fecha_memorando': str(row['fecha_memorando']) if pd.notna(row['fecha_memorando']) else '',
                        'radicado_memorando': str(row.get('radicado_memorando', '')) if pd.notna(
                            row.get('radicado_memorando', '')) else '',
                        'rec': int(row['rec']) if pd.notna(row['rec']) else 0,
                        'id_rubro': str(row.get('id_rubro', '')) if pd.notna(row.get('id_rubro', '')) else '',
                        'fecha_inicial': str(row['fecha_inicial']) if pd.notna(row['fecha_inicial']) else '',
                        'fecha_final': str(row['fecha_final']) if pd.notna(row['fecha_final']) else '',
                        'numero_dias': int(row['numero_dias']) if pd.notna(row['numero_dias']) else 0,
                        'valor_viaticos_diario': float(row['valor_viaticos_diario']) if pd.notna(
                            row['valor_viaticos_diario']) else 0.0,
                        'valor_viaticos_orden': float(row['valor_viaticos_orden']) if pd.notna(
                            row['valor_viaticos_orden']) else 0.0,
                        'valor_gastos_orden': float(row['valor_gastos_orden']) if pd.notna(
                            row['valor_gastos_orden']) else 0.0,
                        'numero_identificacion': int(row['numero_identificacion']) if pd.notna(
                            row['numero_identificacion']) else 0,
                        'primer_nombre': str(row['primer_nombre']).upper() if pd.notna(row['primer_nombre']) else '',
                        'otros_nombres': str(row.get('otros_nombres', '')).upper() if pd.notna(
                            row.get('otros_nombres', '')) else '',
                        'primer_apellido': str(row['primer_apellido']).upper() if pd.notna(
                            row['primer_apellido']) else '',
                        'segundo_apellido': str(row.get('segundo_apellido', '')).upper() if pd.notna(
                            row.get('segundo_apellido', '')) else ''
                    }

                    # Add legalization data if present
                    legalization_fields = {
                        'fecha_legalizacion': str(row.get('fecha_legalizacion', '')) if pd.notna(
                            row.get('fecha_legalizacion', '')) else '',
                        'numero_legalizacion': int(row.get('numero_legalizacion', 0)) if pd.notna(
                            row.get('numero_legalizacion', 0)) and str(
                            row.get('numero_legalizacion', 0)) != '' else None,
                        'dias_legalizados': int(row.get('dias_legalizados', 0)) if pd.notna(
                            row.get('dias_legalizados', 0)) and str(row.get('dias_legalizados', 0)) != '' else None,
                        'valor_viaticos_legalizado': float(row.get('valor_viaticos_legalizado', 0)) if pd.notna(
                            row.get('valor_viaticos_legalizado', 0)) and str(
                            row.get('valor_viaticos_legalizado', 0)) != '' else None,
                        'valor_gastos_legalizado': float(row.get('valor_gastos_legalizado', 0)) if pd.notna(
                            row.get('valor_gastos_legalizado', 0)) and str(
                            row.get('valor_gastos_legalizado', 0)) != '' else None
                    }

                    # Clean empty strings to None for optional legalization fields
                    for key, value in legalization_fields.items():
                        if value == '' or value == 0:
                            legalization_fields[key] = None

                    commission_data.update(legalization_fields)

                    # Save the commission order (this will calculate formulated fields automatically)
                    success, message = self.save_commission_order(commission_data)
                    if success:
                        imported_count += 1
                    else:
                        errors.append(f"Fila {index + 1}: {message}")

                except Exception as e:
                    errors.append(f"Fila {index + 1}: Error procesando datos - {str(e)}")

            result_message = f"✅ Se importaron {imported_count} registros exitosamente"
            if errors:
                result_message += f"\n❌ {len(errors)} errores encontrados"
                if len(errors) <= 10:  # Show first 10 errors
                    result_message += ":\n" + "\n".join(errors)

            return True, result_message

        except Exception as e:
            return False, f"Error importando desde Excel: {str(e)}"

    def recalculate_all_formulated_fields(self) -> Tuple[bool, str]:
        """Recalculate all formulated fields for existing orders"""
        try:
            # Get all orders
            response = self.client.table('ordenes').select('*').execute()
            orders = response.data

            updated_count = 0

            for order in orders:
                # Calculate formulated fields
                formulated = self.calculate_formulated_fields(order)

                # Update the order
                update_data = {
                    'fecha_reintegro': formulated['fecha_reintegro'],
                    'fecha_limite_legalizacion': formulated['fecha_limite_legalizacion'],
                    'plazo_restante_legalizacion': formulated['plazo_restante_legalizacion'],
                    'alerta': formulated['alerta'],
                    'estado_legalizacion': formulated['estado_legalizacion'],
                    'valor_orden_legalizado': formulated['valor_orden_legalizado']
                }

                self.client.table('ordenes').update(update_data).eq('numero_orden', order['numero_orden']).execute()
                updated_count += 1

            return True, f"✅ Se recalcularon {updated_count} registros exitosamente"

        except Exception as e:
            return False, f"Error recalculando campos: {str(e)}"


# Streamlit integration functions
def init_database_session():
    """Initialize Supabase database in session state"""
    if 'database_manager' not in st.session_state:
        try:
            st.session_state.database_manager = SupabaseDBManager()
            st.session_state.database_connected = True
            # Load initial data
            st.session_state.excel_data = st.session_state.database_manager.get_all_orders_df()
        except Exception as e:
            st.session_state.database_connected = False
            st.error(f"Error connecting to Supabase: {str(e)}")


def get_funcionario(numero_identificacion: str) -> Optional[Dict]:
    """Get funcionario from database"""
    if 'database_manager' not in st.session_state:
        return None

    try:
        num_id = int(numero_identificacion)
        return st.session_state.database_manager.get_funcionario(num_id)
    except ValueError:
        return None


def save_commission_order(commission_data: Dict) -> Tuple[bool, str]:
    """Save commission to database"""
    if 'database_manager' not in st.session_state:
        return False, "Database not initialized"

    return st.session_state.database_manager.save_commission_order(commission_data)


def search_orders(search_term: str) -> List[Dict]:
    """Search orders in database"""
    if 'database_manager' not in st.session_state:
        return []

    return st.session_state.database_manager.search_orders(search_term)


def update_legalization(numero_orden: int, legalization_data: Dict) -> Tuple[bool, str]:
    """Update legalization in database"""
    if 'database_manager' not in st.session_state:
        return False, "Database not initialized"

    return st.session_state.database_manager.update_legalization(numero_orden, legalization_data)


def render_database_status():
    """Render database connection status"""
    if 'database_connected' not in st.session_state:
        init_database_session()

    if st.session_state.get('database_connected') and st.session_state.get('excel_data') is not None:
        record_count = len(st.session_state.excel_data)
        st.success(f"📊 {record_count} registros cargados desde Supabase")
    elif st.session_state.get('database_connected'):
        st.info("🔗 Conectado a Supabase")
    else:
        st.error("❌ Error de conexión a Supabase")