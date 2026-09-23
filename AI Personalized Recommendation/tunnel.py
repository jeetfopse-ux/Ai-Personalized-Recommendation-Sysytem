import os
import sys
from dotenv import load_dotenv

load_dotenv()

def start_tunnel(port=5000):
    """Establishes an ngrok tunnel to the local Flask application."""
    try:
        from pyngrok import ngrok, conf
        
        token = os.getenv("NGROK_AUTHTOKEN", "").strip()
        if token:
            ngrok.set_auth_token(token)
        
        # Connect tunnel
        tunnel = ngrok.connect(port, "http")
        public_url = tunnel.public_url
        if public_url.startswith("http://"):
            public_url = public_url.replace("http://", "https://", 1)
            
        print("=" * 60)
        print("  [+] NGROK PUBLIC TUNNEL ESTABLISHED SUCCESSFULLY!")
        print(f"  [>] Public URL:  {public_url}")
        print(f"  [*] Local App:   http://127.0.0.1:{port}")
        print("=" * 60)
        return public_url
    except Exception as e:
        print(f"[!] Ngrok tunnel notice: {e}")
        print("To enable full ngrok public tunneling, set NGROK_AUTHTOKEN in your .env file.")
        return None

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    if "--test" in sys.argv:
        print(f"Testing ngrok configuration on port {port}...")
    url = start_tunnel(port)
    if url:
        print("Tunnel running. Press Ctrl+C to terminate.")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down tunnel...")
