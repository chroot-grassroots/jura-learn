from js import document, window, fetch
import asyncio

# Use the same module loading pattern as your working old_home.html
async def load_module(module_name):
    """Load a Python module using direct fetch method."""
    try:
        response = await fetch(f'/static/py/{module_name}.py')
        if response.ok:
            module_code = await response.text()
            exec(module_code, globals())
            print(f'✅ {module_name}.py loaded successfully')
            return True
        else:
            print(f'❌ Failed to load {module_name}: {response.status}')
            return False
    except Exception as e:
        print(f'❌ Error loading {module_name}: {e}')
        return False

# Global variables
solid_auth = None
status_div = None
error_section = None
success_section = None

def update_status(message):
    """Update the connection status display."""
    if status_div:
        status_div.innerHTML = f"""
            <div class="flex items-center justify-center space-x-2 text-blue-600">
                <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="font-medium">{message}</span>
            </div>
        """

def show_error(error_msg):
    """Show error section with specific error message."""
    if status_div:
        status_div.classList.add('hidden')
    if error_section:
        error_section.classList.remove('hidden')
    
    error_message_el = document.getElementById('error-message')
    if error_message_el:
        error_message_el.textContent = error_msg

def show_success():
    """Show success message and redirect."""
    if status_div:
        status_div.classList.add('hidden')
    if success_section:
        success_section.classList.remove('hidden')
    
    print("Redirecting to learning environment...")
    window.location.href = "/learn"

async def handle_solid_connection():
    """Main OAuth handling logic using existing SolidAuth."""
    global solid_auth, status_div, error_section, success_section
    
    print("🔄 Starting handle_solid_connection...")
    
    # Get DOM elements
    status_div = document.getElementById('connection-status')
    error_section = document.getElementById('error-section')
    success_section = document.getElementById('success-section')
    
    try:
        update_status("Loading authentication modules...")
        print("📦 Loading core/solid_auth module...")
        
        # Load the SolidAuth module first
        solid_auth_loaded = await load_module('core/solid_auth')
        if not solid_auth_loaded:
            show_error("Failed to load authentication modules. Please refresh and try again.")
            return
        
        print("✅ SolidAuth module loaded successfully")
        
        update_status("Checking Solid Pod libraries...")
        
        # Check if Solid libraries are available
        if not hasattr(window, 'solidClientAuthentication'):
            show_error("Solid Pod libraries are not loaded. Please refresh and try again.")
            return
        
        print("✅ Solid libraries are available")
        
        # Initialize SolidAuth
        solid_auth = SolidAuth(debug_callback=print)
        print("✅ SolidAuth instance created")
        
        update_status("Processing authentication...")
        
        # Handle incoming OAuth redirect first
        session = window.solidClientAuthentication.getDefaultSession()
        await session.handleIncomingRedirect(window.location.href)
        print(f"🔑 Processed redirect for: {window.location.href}")
        
        # Use JavaScript-stored OAuth parameters if available
        current_url = None
        is_oauth_callback = False
        
        if hasattr(window, '_oauthParams'):
            print("📋 Using JavaScript-stored OAuth parameters")
            oauth_params = window._oauthParams.to_py()
            current_url = oauth_params['fullUrl']
            is_oauth_callback = oauth_params['isOAuthCallback']
        else:
            print("⚠️ No JavaScript OAuth params, using direct access")
            current_url = str(window.location.href)
            is_oauth_callback = 'code=' in current_url and 'state=' in current_url
        
        print(f"🔍 URL: {current_url}")
        print(f"🔍 Is OAuth callback: {is_oauth_callback}")
        
        if is_oauth_callback:
            # This is an OAuth callback - wait for session to establish
            print("🔄 OAuth callback detected - starting session establishment...")
            max_attempts = 15
            for attempt in range(max_attempts):
                print(f"🔄 Session attempt {attempt + 1}/{max_attempts}")
                await asyncio.sleep(0.5)
                
                # Get fresh session reference
                session = window.solidClientAuthentication.getDefaultSession()
                session_info = session.info
                
                if session_info and session_info.isLoggedIn:
                    webid = session_info.webId
                    print(f"✅ Session established on attempt {attempt + 1}: {webid}")
                    
                    # Store backup session data
                    import js
                    backup_data = {
                        'webId': webid,
                        'timestamp': js.Date.now(),
                        'isLoggedIn': True
                    }
                    js.localStorage.setItem('mera_solid_session_backup', js.JSON.stringify(backup_data))
                    print("💾 Backup session data stored")
                    
                    print("🎉 Authentication successful, session persisted")
                    await asyncio.sleep(1)  # Final delay for persistence
                    show_success()
                    return
                else:
                    print(f"⏳ Attempt {attempt + 1}: Session not ready (isLoggedIn={session_info.isLoggedIn if session_info else 'No info'})")
            
            # OAuth callback failed to establish session
            show_error("OAuth callback processing failed. Please try again.")
            return
        
        else:
            # Not an OAuth callback - check if already logged in
            session_info = session.info
            if session_info and session_info.isLoggedIn:
                print(f"✅ Already logged in! WebID: {session_info.webId}")
                show_success()
                return
            
            # Not logged in - start OAuth flow
            print("🔄 Not authenticated, starting OAuth flow...")
        
        # Parse custom provider from URL
        search_params = window.location.search
        custom_provider = None
        
        if search_params and 'provider=' in search_params:
            provider_start = search_params.find('provider=') + 9
            provider_end = search_params.find('&', provider_start)
            if provider_end == -1:
                provider_end = len(search_params)
            custom_provider = search_params[provider_start:provider_end]
            # URL decode
            custom_provider = custom_provider.replace('%3A', ':').replace('%2F', '/')
        
        if custom_provider and custom_provider.strip():
            print(f"Using custom provider: {custom_provider}")
            await solid_auth.login(custom_provider.strip())
        else:
            print("Using default SolidCommunity.net provider")
            await solid_auth.login("https://solidcommunity.net")
        
    except Exception as e:
        error_msg = f"Authentication error: {str(e)}"
        print(error_msg)
        show_error(error_msg)

def handle_retry():
    """Handle retry button click."""
    if error_section:
        error_section.classList.add('hidden')
    if status_div:
        status_div.classList.remove('hidden')
    
    asyncio.create_task(handle_solid_connection())

def setup_retry_button():
    """Set up retry button event listener."""
    retry_btn = document.getElementById('retry-btn')
    if retry_btn:
        retry_btn.addEventListener('click', handle_retry)

def initialize_solid_page():
    """Initialize the solid OAuth page."""
    print("🔄 /solid page PyScript starting...")
    setup_retry_button()
    asyncio.create_task(handle_solid_connection())

# Debug output
print("🚀 /solid PyScript loaded!")

# Start initialization
initialize_solid_page()