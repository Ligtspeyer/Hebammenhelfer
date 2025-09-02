import imapclient
import ssl
import sys

# Configuration
EMAIL = "ole.kleinke@gmx.de"
PASSWORD = "Penis54321!"  # Note: It's generally not good practice to hardcode passwords
IMAP_SERVER = "imap.gmx.net"

def test_connection_with_ssl_verification():
    """Test connection with default SSL verification"""
    try:
        print("Attempting connection with default SSL verification...")
        mail = imapclient.IMAPClient(IMAP_SERVER, ssl=True)
        mail.login(EMAIL, PASSWORD)
        print("Connection successful!")
        mail.logout()
        return True
    except Exception as e:
        print(f"Connection failed with error: {e}")
        return False

def test_connection_without_ssl_verification():
    """Test connection with SSL verification disabled"""
    try:
        print("Attempting connection with SSL verification disabled...")
        # Create a custom SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        mail = imapclient.IMAPClient(IMAP_SERVER, ssl=True, ssl_context=ssl_context)
        mail.login(EMAIL, PASSWORD)
        print("Connection successful!")
        mail.logout()
        return True
    except Exception as e:
        print(f"Connection failed with error: {e}")
        return False

def test_connection_with_custom_context():
    """Test connection with a custom SSL context that loads default certificates"""
    try:
        print("Attempting connection with custom SSL context...")
        # Create a default SSL context that loads certificates from the default location
        ssl_context = ssl.create_default_context()
        
        mail = imapclient.IMAPClient(IMAP_SERVER, ssl=True, ssl_context=ssl_context)
        mail.login(EMAIL, PASSWORD)
        print("Connection successful!")
        mail.logout()
        return True
    except Exception as e:
        print(f"Connection failed with error: {e}")
        return False

if __name__ == "__main__":
    print("Testing IMAP connection to", IMAP_SERVER)
    print("-" * 50)
    
    # Try all connection methods
    default_success = test_connection_with_ssl_verification()
    custom_context_success = test_connection_with_custom_context()
    no_verify_success = test_connection_without_ssl_verification()
    
    print("\nResults:")
    print(f"Default SSL verification: {'Success' if default_success else 'Failed'}")
    print(f"Custom SSL context: {'Success' if custom_context_success else 'Failed'}")
    print(f"No SSL verification: {'Success' if no_verify_success else 'Failed'}")
    
    # Provide recommendations
    print("\nRecommendation:")
    if default_success:
        print("The default connection works fine. No changes needed.")
    elif custom_context_success:
        print("Use a custom SSL context with default certificates.")
    elif no_verify_success:
        print("WARNING: Connection only works with SSL verification disabled.")
        print("This is not secure for production use.")
        print("Consider installing proper SSL certificates or using a different approach.")
    else:
        print("All connection methods failed. Check your credentials and server settings.")