"""
Authentication module using Streamlit secrets
Handles user login and session management
"""

import streamlit as st
from typing import Tuple, Optional


def check_credentials(username: str, password: str) -> Tuple[bool, str]:
    """
    Verify user credentials against Streamlit secrets

    Args:
        username: User's username
        password: User's password

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        # Get credentials from secrets
        secrets = st.secrets.get("users", {})

        if not secrets:
            return False, "No hay usuarios configurados en los secretos"

        # Check if username exists
        if username not in secrets:
            return False, "Usuario o contraseña incorrectos"

        # Check password
        stored_password = secrets[username].get("password", "")
        if password != stored_password:
            return False, "Usuario o contraseña incorrectos"

        return True, f"Bienvenido {username}"

    except Exception as e:
        return False, f"Error al verificar credenciales: {str(e)}"


def initialize_auth_session():
    """Initialize authentication session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)


def get_current_user() -> Optional[str]:
    """Get current logged-in username"""
    return st.session_state.get('username')


def logout():
    """Logout the current user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.login_attempts = 0
    st.success("✅ Sesión cerrada exitosamente")


def render_login_page():
    """Render the login page"""

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 40px 0;'>
            <h1>🔐 Sistema de Registro de Órdenes</h1>
            <h3>Instituto Geográfico Agustín Codazzi (IGAC)</h3>
            <p style='color: #666;'>Viaticos y Comisiones v3.0</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Login form
        with st.form("login_form", clear_on_submit=True):
            st.markdown("<h2 style='text-align: center;'>Iniciar Sesión</h2>", unsafe_allow_html=True)

            username = st.text_input(
                "👤 Usuario",
                placeholder="Ingrese su usuario",
                help="Usuario proporcionado por el administrador"
            )

            password = st.text_input(
                "🔑 Contraseña",
                type="password",
                placeholder="Ingrese su contraseña",
                help="Contraseña proporcionada por el administrador"
            )

            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

            with col_btn2:
                submitted = st.form_submit_button(
                    "🔓 Iniciar Sesión",
                    use_container_width=True
                )

            if submitted:
                if not username or not password:
                    st.error("⚠️ Por favor ingrese usuario y contraseña")
                else:
                    is_valid, message = check_credentials(username, password)

                    if is_valid:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.login_attempts = 0
                        st.success(message)
                        st.rerun()
                    else:
                        st.session_state.login_attempts = st.session_state.get('login_attempts', 0) + 1
                        st.error(message)

                        # Show warning after multiple failed attempts
                        if st.session_state.login_attempts >= 3:
                            st.warning(f"""
                            ⚠️ Ha habido {st.session_state.login_attempts} intentos fallidos.

                            Si ha olvidado su contraseña, contacte al administrador.
                            """)

        st.markdown("---")

        # Info section
        st.markdown("""
        <div style='padding: 20px; background: #f0f2f6; border-radius: 5px; margin-top: 30px;'>
            <p style='text-align: center; margin: 0;'>
                <strong>💡 Información de Acceso</strong>
            </p>
            <p style='text-align: center; margin: 10px 0; color: #666; font-size: 0.9em;'>
                Si no tiene credenciales de acceso o ha olvidado su contraseña,<br>
                por favor contacte al administrador del sistema.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.markdown("")

        # Footer
        st.markdown("""
        <div style='text-align: center; padding: 20px; color: #999; font-size: 0.85em;'>
            © 2025 IGAC - Todos los derechos reservados<br>
            Sistema Seguro de Registro de Órdenes de Comisión
        </div>
        """, unsafe_allow_html=True)


def render_logout_button():
    """Render logout button in sidebar"""
    col1, col2, col3 = st.sidebar.columns([1, 1, 1])

    with col2:
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            logout()
            st.rerun()


def render_user_info():
    """Render current user information in sidebar"""
    current_user = get_current_user()

    if current_user:
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"""
        <div style='padding: 10px; background: #f0f2f6; border-radius: 5px;'>
            <p style='margin: 5px 0; font-size: 0.9em;'><strong>👤 Usuario:</strong></p>
            <p style='margin: 5px 0; font-size: 0.9em; color: #666;'>{current_user}</p>
        </div>
        """, unsafe_allow_html=True)

        render_logout_button()
