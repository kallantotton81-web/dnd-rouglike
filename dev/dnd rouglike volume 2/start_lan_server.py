import http.server
import socketserver
import socket
import os
import sys

PORT = 8000

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# Change directory to the project root (where this script is located)
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

Handler = http.server.SimpleHTTPRequestHandler

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        local_ip = get_ip()
        print("=" * 60)
        print("!!! D&D ROGUELIKE VOLUME 2 LAN SERVER !!!")
        print("=" * 60)
        print(f"Status:    RUNNING")
        print(f"Port:      {PORT}")
        print(f"Local URL: http://localhost:{PORT}/website/")
        print(f"LAN URL:   http://{local_ip}:{PORT}/website/")
        print("-" * 60)
        print("INSTRUCTIONS:")
        print(f"1. Tell your friends to go to: http://{local_ip}:{PORT}/website/")
        print("2. Source files are available at: http://{local_ip}:{PORT}/")
        print("-" * 60)
        print("IF IT DOESN'T WORK:")
        print("- Check Windows Firewall: Allow 'python' or Port 8000.")
        print("- Ensure your Network Profile is set to 'Private' not 'Public'.")
        print("-" * 60)
        print("Press Ctrl+C to stop the server.")
        print("=" * 60)
        
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nStopping server... Done.")
    sys.exit(0)
except OSError as e:
    if e.errno == 10048:
        print(f"\nERROR: Port {PORT} is already in use.")
        print("Please close any other servers or wait 60 seconds and try again.")
    else:
        print(f"\nOS ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)
