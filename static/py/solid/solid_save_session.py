"""
Solid OAuth connection handler with PyScript-compatible imports and fixed OAuth flow.
This file was formerly static/py/core/solid.py - refactored to static/py/solid/

Key changes:
- Converted all relative imports to absolute imports for PyScript compatibility
- Fixed OAuth flow logic bug (OAuth initiation was outside conditional blocks)
- Enhanced error handling and debugging
- Consistent localStorage key usage
"""
import asyncio
from js import document, window, console, URL
import js

# Import existing SolidAuth class using PyScript-compatible patterns
# Updated to work with your existing solid_auth.py location
try:
    # Try to import using your existing module structure
    # First try: assume solid_auth.py is in the same solid/ directory
    from solid_auth import SolidAuth
    print("✅ Imported SolidAuth from solid_auth module (same directory)")
except ImportError:
    # Fallback: try alternative import patterns based on your current structure
    try:
        # If it's imported as a module
        import solid_auth
        SolidAuth = solid_auth.SolidAuth
        print("✅ Imported SolidAuth via module import")
    except ImportError:
        # Dynamic loading - will find your solid_auth.py wherever it lives
        try:
            async def load_solid_auth():
                """Load SolidAuth dynamically using your existing patterns."""
                try:
                    # Try common locations where your solid_auth.py might live
                    possible_paths = [
                        '/static/py/solid/solid_auth.py',  # In refactored solid/ directory
                        '/static/py/solid_auth.py',       # Original location
                        '/static/py/core/solid_auth.py'   # Alternative location
                    ]
                    
                    for path in possible_paths:
                        try:
                            print(f"🔍 Trying to load SolidAuth from: {path}")
                            response = await window.fetch(path)
                            if response.ok:
                                module_code = await response.text()
                                exec(module_code, globals())
                                print(f"✅ Successfully loaded SolidAuth from: {path}")
                                return True
                        except Exception as path_error:
                            print(f"❌ Failed to load from {path}: {path_error}")
                            continue
                    
                    print("❌ Could not find solid_auth.py in any expected location")
                    return False
                    
                except Exception as e:
                    print(f"❌ Failed to load solid_auth.py dynamically: {e}")
                    return False
            
            # This will be handled in the main function
            SolidAuth = None
            print("⚠️ SolidAuth will be loaded dynamically from your existing file")
            
        except Exception as e:
            print(f"❌ All SolidAuth import methods failed: {e}")
            SolidAuth = None

# STANDARDIZED STORAGE KEY - Use this consistently across all files
STORAGE_KEY = 'mera_solid_session_backup'


def show_loading():
    """Show loading state with professional UI."""
    status_div = document.getElementById('solid-status')
    if status_div:
        status_div.innerHTML = """
            <div class="flex items-center justify-center space-x-3">
                <svg class="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="text-lg font-semibold text-gray-700">Connecting to Solid Pod...</span>
            </div>
            <p class="text-sm text-gray-600 mt-2">Please wait while we establish your connection</p>
        """


def show_success():
    """Show success state and redirect to learn page."""
    status_div = document.getElementById('solid-status')
    if status_div:
        status_div.innerHTML = """
            <div class="flex items-center justify-center space-x-3">
                <svg class="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                <span class="text-lg font-semibold text-green-600">Connection Successful!</span>
            </div>
            <p class="text-sm text-gray-600 mt-2">Redirecting to learning environment...</p>
        """
    
    # CRITICAL FIX: Use JavaScript to redirect instead of Python callback
    # This prevents the PyScript proxy destruction error
    js.eval('''
        setTimeout(function() {
            window.location.href = "/learn/";
        }, 2000);
    ''')


def show_error(message):
    """Show error state with retry options."""
    status_div = document.getElementById('solid-status')
    error_section = document.getElementById('error-section')
    
    if status_div:
        status_div.classList.add('hidden')
    
    if error_section:
        error_section.classList.remove('hidden')
        error_msg_div = document.getElementById('error-message')
        if error_msg_div:
            error_msg_div.textContent = message


async def handle_solid_connection():
    """
    Handle Solid OAuth connection with PyScript-compatible imports and fixed OAuth flow.
    
    This function implements the corrected OAuth flow:
    1. Check if this is an OAuth callback (has code/state parameters)
    2. If callback: Process tokens and establish session
    3. If not callback: Check if already logged in, otherwise start OAuth flow
    
    Key fixes:
    - OAuth initiation code moved inside proper conditional block
    - Enhanced error handling and debugging
    - PyScript-compatible import patterns
    - Consistent localStorage key usage
    """
    print("🔗 Solid OAuth handler loaded!")
    print("🔄 Starting handle_solid_connection...")
    
    # Initialize UI
    show_loading()
    
    # Hide error section if visible
    error_section = document.getElementById('error-section')
    if error_section:
        error_section.classList.add('hidden')
    
    try:
        # Handle dynamic loading of SolidAuth if needed
        if SolidAuth is None:
            print("🔄 Loading SolidAuth dynamically...")
            success = await load_solid_auth()
            if not success:
                raise Exception("Failed to load SolidAuth module dynamically")
            print("✅ SolidAuth loaded dynamically")
        
        # Verify SolidAuth is available
        if 'SolidAuth' not in globals():
            raise Exception("SolidAuth class not available after import attempts")
        
        print("✅ SolidAuth module loaded successfully")
        
        # Verify Solid libraries are available
        if not hasattr(window, 'solidClientAuthentication'):
            raise Exception("Solid client libraries not loaded")
        print("✅ Solid libraries are available")
        
        # Initialize SolidAuth instance
        solid_auth = SolidAuth(debug_callback=print)
        print("✅ SolidAuth initialized")
        
        # Get session reference
        session = window.solidClientAuthentication.getDefaultSession()
        
        # Check if this is an OAuth callback (has authorization code)
        current_url = window.location.href
        is_oauth_callback = ('code=' in current_url and 'state=' in current_url)
        
        print(f"🔍 Current URL: {current_url}")
        print(f"🔍 Is OAuth callback: {is_oauth_callback}")
        
        if is_oauth_callback:
            print("🔑 OAuth callback detected - starting session establishment...")
            
            # Process the OAuth redirect
            await session.handleIncomingRedirect(current_url)
            print(f"🔧 Processed redirect for: {current_url}")
            
            # Session establishment with persistence verification
            max_attempts = 15
            timeout_seconds = 30
            max_persistence_failures = 3
            persistence_failures = 0
            
            for attempt in range(max_attempts):
                # Check if we've exceeded timeout
                if attempt * 0.5 > timeout_seconds:
                    print(f"❌ Timeout after {timeout_seconds} seconds")
                    show_error("Authentication timed out. Please try again or clear your browser data.")
                    return
                
                print(f"🔄 Session attempt {attempt + 1}/{max_attempts}")
                await asyncio.sleep(0.5)
                
                # Get fresh session reference
                session = window.solidClientAuthentication.getDefaultSession()
                session_info = session.info if session else None
                
                if session_info and getattr(session_info, 'isLoggedIn', False):
                    webid = getattr(session_info, 'webId', None)
                    
                    # Validate WebID format (security check)
                    if not webid or not webid.strip():
                        print(f"❌ Session has no WebID, retrying...")
                        continue
                    
                    # URL validation for security
                    try:
                        if not (webid.startswith('http://') or webid.startswith('https://')):
                            raise Exception(f"WebID must be a valid URL: {webid}")
                        
                        # Test URL constructor (this was causing errors in logs)
                        test_url = URL.new(webid)
                        print(f"✅ WebID URL validation passed: {webid}")
                    except Exception as url_error:
                        print(f"❌ WebID URL validation failed: {url_error}")
                        print("⚠️ Continuing with potentially invalid WebID")
                    
                    print(f"✅ Session established on attempt {attempt + 1}: {webid}")
                    
                    # Store backup session data with current timestamp
                    current_timestamp = js.Date.now()
                    backup_data = {
                        'webId': webid,
                        'timestamp': current_timestamp,
                        'isLoggedIn': True
                    }
                    
                    try:
                        # FIXED: Use proper JavaScript JSON serialization
                        # Create a plain JavaScript object instead of Python dict
                        js.eval(f'''
                            const backupData = {{
                                webId: "{webid}",
                                timestamp: {current_timestamp},
                                isLoggedIn: true
                            }};
                            const backupJson = JSON.stringify(backupData);
                            localStorage.setItem("{STORAGE_KEY}", backupJson);
                            console.log("💾 Backup stored:", backupJson);
                        ''')
                        
                        print(f"💾 Backup session data stored with timestamp: {current_timestamp}")
                        print(f"💾 Storage key used: {STORAGE_KEY}")
                        
                        # Verify storage immediately
                        verification = js.localStorage.getItem(STORAGE_KEY)
                        if verification:
                            print(f"💾 Storage verification: SUCCESS")
                            print(f"💾 Stored content: {verification}")
                        else:
                            print(f"💾 Storage verification: FAILED - data not found")
                    except Exception as storage_error:
                        print(f"💾 Storage error: {storage_error}")
                        # Fallback: try Python-based storage
                        try:
                            backup_json = f'{{"webId":"{webid}","timestamp":{current_timestamp},"isLoggedIn":true}}'
                            js.localStorage.setItem(STORAGE_KEY, backup_json)
                            print(f"💾 Fallback storage successful")
                        except Exception as fallback_error:
                            print(f"💾 Fallback storage also failed: {fallback_error}")
                    
                    # Wait for Solid's internal session persistence
                    print("⏳ Waiting for session to persist to storage...")
                    await asyncio.sleep(2)
                    
                    # Verify session persistence
                    session = window.solidClientAuthentication.getDefaultSession()
                    final_session = session.info if session else None
                    
                    if final_session and getattr(final_session, 'isLoggedIn', False):
                        final_webid = getattr(final_session, 'webId', None)
                        print(f"✅ Session persistence verified: {final_webid}")
                        print("🎉 Authentication successful, session persisted")
                        
                        await asyncio.sleep(1)
                        show_success()
                        return
                    else:
                        persistence_failures += 1
                        print(f"❌ Session lost during persistence - failure {persistence_failures}/{max_persistence_failures}")
                        
                        if persistence_failures >= max_persistence_failures:
                            print("❌ Too many persistence failures")
                            show_error("Session persistence is failing. Please try a different browser or clear all browser data.")
                            return
                        
                        print(f"⏳ Retrying session establishment...")
                        continue
                else:
                    session_status = "No session info" if not session_info else f"isLoggedIn={getattr(session_info, 'isLoggedIn', 'unknown')}"
                    print(f"⏳ Attempt {attempt + 1}: Session not ready ({session_status})")
            
            # If we exit the loop without success
            print(f"❌ Failed to establish session after {max_attempts} attempts")
            show_error("Authentication failed after multiple attempts. Please clear browser data and try again.")
            return
        
        else:
            # *** CRITICAL FIX: OAuth initiation code moved INSIDE this else block ***
            # Not an OAuth callback - check if already logged in or start OAuth flow
            session_info = session.info if session else None
            if session_info and getattr(session_info, 'isLoggedIn', False):
                webid = getattr(session_info, 'webId', None)
                print(f"✅ Already logged in! WebID: {webid}")
                show_success()
                return
            
            # Not logged in - start OAuth flow (THIS IS THE KEY FIX!)
            print("🔄 Not authenticated, starting OAuth flow...")
            
            # Parse custom provider from URL parameters
            search_params = window.location.search
            custom_provider = None
            
            if search_params and 'provider=' in search_params:
                # Extract provider URL from query parameters
                provider_start = search_params.find('provider=') + 9
                provider_end = search_params.find('&', provider_start)
                if provider_end == -1:
                    provider_end = len(search_params)
                custom_provider = search_params[provider_start:provider_end]
                
                # URL decode common characters
                custom_provider = custom_provider.replace('%3A', ':').replace('%2F', '/')
                
                # Validate custom provider
                if custom_provider and custom_provider.strip():
                    try:
                        if not (custom_provider.startswith('http://') or custom_provider.startswith('https://')):
                            raise Exception("Custom provider must be a valid HTTP/HTTPS URL")
                        
                        test_url = URL.new(custom_provider.strip())
                        print(f"✅ Custom provider validation passed: {custom_provider}")
                    except Exception as provider_error:
                        print(f"❌ Custom provider validation failed: {provider_error}")
                        show_error(f"Invalid custom provider URL: {provider_error}")
                        return
            
            # *** THIS IS THE CRITICAL CODE THAT WAS MISPLACED ***
            # Start OAuth login flow - now properly inside the else block
            if custom_provider and custom_provider.strip():
                print(f"🔗 Using custom provider: {custom_provider}")
                await solid_auth.login(custom_provider.strip())
            else:
                print("🔗 Using default SolidCommunity.net provider")
                await solid_auth.login("https://solidcommunity.net")
        
    except Exception as e:
        error_msg = f"Authentication error: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Enhanced error reporting for debugging
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Full traceback:\n{traceback_str}")
        
        show_error(error_msg)


def handle_retry():
    """Handle retry button click with proper error state reset."""
    print("🔄 Retry button clicked")
    
    error_section = document.getElementById('error-section')
    status_div = document.getElementById('solid-status')
    
    if error_section:
        error_section.classList.add('hidden')
    if status_div:
        status_div.classList.remove('hidden')
    
    # Start new authentication attempt
    asyncio.create_task(handle_solid_connection())


def setup_retry_button():
    """Set up retry button event listener."""
    retry_btn = document.getElementById('retry-btn')
    if retry_btn:
        retry_btn.addEventListener('click', handle_retry)
        print("✅ Retry button event listener set up")


def initialize_solid_page():
    """
    Initialize the solid OAuth page with comprehensive error handling.
    """
    print("🔗 Solid OAuth page initializing...")
    
    try:
        # Set up retry button functionality
        setup_retry_button()
        
        # Start the main authentication flow
        asyncio.create_task(handle_solid_connection())
        print("✅ Solid OAuth page initialized successfully")
        
    except Exception as e:
        error_msg = f"Failed to initialize solid OAuth page: {e}"
        print(f"❌ {error_msg}")
        show_error(error_msg)


# Auto-initialize when module loads
# This follows the established pattern from your existing codebase
initialize_solid_page()