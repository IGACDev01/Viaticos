# 🧭 Sistema de Registro de Órdenes de Comisión - IGAC

Sistema web desarrollado en Streamlit para el manejo integral de órdenes de comisión del Instituto Geográfico Agustín Codazzi (IGAC), con integración a base de datos Supabase para almacenamiento en tiempo real.

## 🌟 Características Principales

### 📋 Gestión de Órdenes de Comisión
- **Registro automatizado** de órdenes con validación de datos
- **Búsqueda inteligente** de funcionarios en base de datos
- **Cálculo automático** de fechas límite y plazos de legalización
- **Validación** de campos obligatorios y rangos de fechas

### 🏢 Gestión de Funcionarios
- **Base de datos centralizada** de funcionarios
- **Autocompletado** de información personal
- **Guardado automático** de nuevos funcionarios para futuras comisiones

### 📊 Dashboard Analítico
- **Métricas en tiempo real** del estado de órdenes
- **Alertas automáticas** por vencimiento de plazos
- **Gráficos interactivos** con Plotly
- **Análisis temporal** mensual y trimestral
- **Exportación** a Excel de reportes

### 🔍 Sistema de Legalización
- **Búsqueda avanzada** de órdenes por múltiples campos
- **Seguimiento** del estado de legalización
- **Comparación** automática con valores originales
- **Validaciones** de montos y plazos

## 🏗️ Arquitectura del Sistema

### 🗄️ Base de Datos (Supabase PostgreSQL)
```
Tablas principales:
├── ordenes (órdenes de comisión)
├── funcionarios (información personal)
├── festivos (días festivos colombianos 2025)
└── sedes (sedes del IGAC)
```

### 📁 Estructura del Proyecto
```
proyecto/
├── app.py                      # Aplicación principal
├── data_manager.py            # Gestión de base de datos Supabase
├── tab_commission_form.py     # Formulario de órdenes
├── tab_legalization_form.py   # Formulario de legalización
├── tab_dashboard.py           # Dashboard analítico
├── utils.py                   # Utilidades y formateo
├── data_migration.py          # Migración de datos Excel
└── requirements.txt           # Dependencias
```

## 🚀 Instalación y Configuración

### 1. Prerrequisitos
```bash
Python 3.8+
pip install -r requirements.txt
```

### 2. Dependencias Principales
```
streamlit>=1.28.0
supabase>=2.0.0
pandas>=1.5.0
plotly>=5.15.0
openpyxl>=3.1.0
```

### 3. Configuración de Supabase

#### Variables de Entorno (secrets.toml)
```toml
[secrets]
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_ANON_KEY = "tu_clave_anonima"
SUPABASE_SERVICE_KEY = "tu_clave_servicio"
```

#### Estructura de Tablas SQL
```sql
-- Tabla de órdenes
CREATE TABLE ordenes (
    id SERIAL PRIMARY KEY,
    numero_orden INTEGER UNIQUE NOT NULL,
    sede TEXT NOT NULL,
    fecha_elaboracion TEXT,
    fecha_memorando TEXT,
    radicado_memorando TEXT,
    rec INTEGER,
    id_rubro TEXT,
    fecha_inicial TEXT,
    fecha_final TEXT,
    numero_dias INTEGER,
    valor_viaticos_diario DECIMAL,
    valor_viaticos_orden DECIMAL,
    valor_gastos_orden DECIMAL,
    numero_identificacion INTEGER,
    primer_nombre TEXT,
    otros_nombres TEXT,
    primer_apellido TEXT,
    segundo_apellido TEXT,
    fecha_reintegro TEXT,
    fecha_limite_legalizacion TEXT,
    plazo_restante_legalizacion INTEGER,
    alerta TEXT,
    fecha_legalizacion TEXT,
    estado_legalizacion TEXT,
    numero_legalizacion INTEGER,
    dias_legalizados INTEGER,
    valor_viaticos_legalizado DECIMAL,
    valor_gastos_legalizado DECIMAL,
    valor_orden_legalizado DECIMAL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de funcionarios
CREATE TABLE funcionarios (
    id SERIAL PRIMARY KEY,
    numero_identificacion INTEGER UNIQUE NOT NULL,
    primer_nombre TEXT NOT NULL,
    otros_nombres TEXT,
    primer_apellido TEXT NOT NULL,
    segundo_apellido TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de festivos
CREATE TABLE festivos (
    id SERIAL PRIMARY KEY,
    fecha TEXT NOT NULL,
    descripcion TEXT
);

-- Tabla de sedes
CREATE TABLE sedes (
    id SERIAL PRIMARY KEY,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    activa BOOLEAN DEFAULT TRUE
);
```

### 4. Ejecución
```bash
streamlit run app.py
```

## 📖 Guía de Uso

### 🔐 Inicio de Sesión
El sistema se conecta automáticamente a Supabase al iniciar y muestra el estado de conexión en tiempo real.

### 📝 Registro de Órdenes
1. **Navegar** a la pestaña "📋 Órdenes de Comisión"
2. **Buscar funcionario** (opcional) ingresando número de identificación
3. **Completar** información de la comisión
4. **Guardar** - el sistema calcula automáticamente:
   - Fecha de reintegro (WORKDAY + 1 día)
   - Fecha límite legalización (WORKDAY + 5 días)
   - Alertas por vencimiento de plazos

### 🔍 Legalización
1. **Navegar** a la pestaña "📄 Legalización"
2. **Buscar orden** por número, funcionario o sede
3. **Seleccionar** la orden a legalizar
4. **Completar** información de legalización con validaciones automáticas
5. **Guardar** - actualiza estado y recalcula métricas

### 📊 Dashboard
- **Visualizar métricas** en tiempo real
- **Analizar tendencias** temporales
- **Exportar reportes** a Excel
- **Monitorear alertas** de vencimiento

### ⚙️ Administración
- **Exportar** base de datos completa
- **Importar** datos desde Excel
- **Recalcular** campos automáticos
- **Monitorear** estado de conexión

## 🔧 Características Técnicas

### 🎯 Cálculos Automáticos
- **Días hábiles**: Excluye weekends y festivos colombianos
- **WORKDAY**: Función equivalente a Excel para cálculo de fechas laborales
- **Alertas**: Sistema automatizado de notificaciones por vencimientos

### 📊 Reportes y Análisis
- **Gráficos interactivos**: Plotly con zoom, filtros y exportación
- **Métricas dinámicas**: Actualización en tiempo real
- **Exportación Excel**: Formato profesional con múltiples hojas

### 🔒 Validaciones
- **Integridad de datos**: Validación de rangos y formatos
- **Duplicados**: Prevención de órdenes duplicadas
- **Montos**: Validación de valores de legalización vs originales

## 🏢 Sedes Soportadas
```
Sede Central, Atlántico, Bolívar, Boyacá, Caquetá, Caldas,
Casanare, Cauca, Córdoba, Cesar, Cundinamarca, Magdalena,
Guajira, Huila, Norte de Santander, Meta, Nariño, Quindío,
Risaralda, Sucre, Santander, Tolima, Valle del Cauca
```

## 📅 Festivos Configurados (2025)
El sistema incluye todos los festivos colombianos para 2025:
- Año Nuevo, Reyes Magos, San José
- Jueves Santo, Viernes Santo
- Día del Trabajo, Ascensión, Corpus Christi
- Sagrado Corazón, San Pedro y San Pablo
- Día de la Independencia, Batalla de Boyacá
- Asunción de la Virgen, Día de la Raza
- Todos los Santos, Independencia de Cartagena
- Inmaculada Concepción, Navidad

## 🛠️ Mantenimiento

### 🔄 Actualización de Datos
```python
# Recalcular todos los campos automáticos
st.session_state.database_manager.recalculate_all_formulated_fields()

# Exportar respaldo
filename = st.session_state.database_manager.export_to_excel()
```

### 🗄️ Migración de Datos
```python
# Importar desde Excel
success, message = st.session_state.database_manager.import_from_excel(
    excel_file, sheet_name
)
```

## 📈 Métricas del Sistema

### 🎯 KPIs Principales
- **Total de órdenes** registradas
- **Funcionarios únicos** en el sistema
- **Total de viáticos** girados
- **Promedio de días** por comisión
- **Órdenes con alertas** (vencidas/próximas)

### 📊 Análisis Disponibles
- **Temporal**: Evolución mensual y trimestral
- **Por sede**: Distribución geográfica
- **Financiero**: Análisis de montos y presupuestos
- **Operativo**: Plazos y cumplimiento

## 🚨 Alertas Automáticas

### 🔴 Plazo Vencido
Órdenes que superaron los 5 días hábiles desde la fecha final

### 🟡 Plazo Próximo
Órdenes con 2 días hábiles o menos para legalizar

### 🟢 Tiempo Suficiente
Órdenes con más de 2 días hábiles disponibles

## 💾 Respaldos y Seguridad

### 🔐 Supabase Cloud
- **Respaldos automáticos** diarios
- **SSL/TLS** encryption
- **Row Level Security** (RLS)
- **API Rate Limiting**

### 📂 Exportaciones Locales
- **Excel** con formato profesional
- **Múltiples hojas**: Datos, Funcionarios, Festivos, Sedes
- **Timestamp** automático en nombres de archivo

## 🆘 Soporte y Contacto

### 📧 Contacto Técnico
- **Sistema**: Aplicación Streamlit + Supabase
- **Versión**: 3.0 (Supabase Integration)
- **Institución**: Instituto Geográfico Agustín Codazzi (IGAC)

### 🐛 Reporte de Errores
Para reportar problemas o sugerencias, incluir:
1. **Descripción** del error
2. **Pasos** para reproducir
3. **Screenshots** si es aplicable
4. **Datos** de conexión (sin credenciales)

---

**© 2025 Instituto Geográfico Agustín Codazzi (IGAC) - Todos los derechos reservados**

*Sistema de Registro de Órdenes de Comisión v3.0 (Supabase)*
