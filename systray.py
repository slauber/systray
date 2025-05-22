import win32gui
import win32con
import win32api
import time
import threading
import logging
from PIL import Image, ImageDraw, ImageFont
import os
import requests
import sys
import ctypes
from ctypes import wintypes, Structure, c_int, c_uint, c_void_p, sizeof, byref, create_unicode_buffer, windll
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define Shell_NotifyIconW function
Shell_NotifyIconW = windll.shell32.Shell_NotifyIconW
Shell_NotifyIconW.argtypes = [c_uint, c_void_p]
Shell_NotifyIconW.restype = c_int

class NOTIFYICONDATA(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('hWnd', wintypes.HWND),
        ('uID', c_uint),
        ('uFlags', c_uint),
        ('uCallbackMessage', c_uint),
        ('hIcon', wintypes.HICON),
        ('szTip', wintypes.WCHAR * 128)
    ]

class SystemTray:
    def __init__(self, config):
        self.config = config
        self.hwnd = None
        self.wc = None
        self.icons = {}
        self.update_thread = None
        self.running = False
        self.initialize_window()

    def initialize_window(self):
        """Initialize the window for system tray icons."""
        try:
            # Register window class
            self.wc = win32gui.WNDCLASS()
            self.wc.lpszClassName = "SystemTrayApp"
            self.wc.lpfnWndProc = self.wnd_proc
            self.wc.hInstance = win32gui.GetModuleHandle(None)
            self.wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
            self.wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
            
            # Register the window class
            win32gui.RegisterClass(self.wc)
            
            # Create the window
            self.hwnd = win32gui.CreateWindow(
                self.wc.lpszClassName,
                "System Tray Application",
                win32con.WS_OVERLAPPED,
                0, 0, 0, 0,
                0, 0,
                self.wc.hInstance,
                None
            )
            
            if not self.hwnd:
                raise Exception("Failed to create window")
            
            # Show the window (required for system tray icons)
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
            win32gui.UpdateWindow(self.hwnd)
                
            logger.info("Window initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing window: {e}")
            raise

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure for handling messages."""
        if msg == win32con.WM_DESTROY:
            self.running = False
            win32gui.PostQuitMessage(0)
            return 0
        elif msg == win32con.WM_USER + 20:  # System tray notification
            if lparam == win32con.WM_RBUTTONUP:
                # Create popup menu
                menu = win32gui.CreatePopupMenu()
                win32gui.AppendMenu(menu, win32con.MF_STRING, 1, "Quit")
                
                # Get cursor position
                pos = win32gui.GetCursorPos()
                
                # Show the menu
                win32gui.SetForegroundWindow(self.hwnd)
                win32gui.TrackPopupMenu(menu,
                    win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON,
                    pos[0], pos[1],
                    0, self.hwnd, None)
                
                # Clean up
                win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
            elif lparam == win32con.WM_LBUTTONUP:
                # Handle left click if needed
                pass
            return 0
        elif msg == win32con.WM_COMMAND:
            # Handle menu item selection
            if wparam == 1:  # Quit option
                self.running = False
                win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def create_icon(self, label: str, path: str) -> bool:
        """Create a system tray icon for a specific label and path."""
        try:
            logger.info(f"Creating system tray icon for {label} with path {path}")
            
            # Create a unique identifier for this icon
            icon_id = f"{label}_{path}"
            
            # Create the icon
            icon_handle = self.create_icon_from_text(label, "0")
            if not icon_handle:
                logger.error(f"Failed to create icon handle for {label}")
                return False

            # Create the NOTIFYICONDATA structure
            nid = NOTIFYICONDATA()
            nid.cbSize = sizeof(NOTIFYICONDATA)
            nid.hWnd = self.hwnd
            nid.uID = len(self.icons)  # Use unique ID for each icon
            nid.uFlags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
            nid.uCallbackMessage = win32con.WM_USER + 20
            nid.hIcon = icon_handle
            nid.szTip = f"{label}: 0"
            
            # Store the icon data
            self.icons[icon_id] = {
                'data': nid,
                'label': label,
                'path': path,
                'created': False,
                'icon_handle': icon_handle,
                'uID': nid.uID  # Store the unique ID
            }
            
            # Create the icon using Shell_NotifyIconW
            if not Shell_NotifyIconW(win32gui.NIM_ADD, byref(nid)):
                error_code = win32api.GetLastError()
                logger.error(f"Failed to create icon for {label}. Error code: {error_code}")
                return False
                
            # Mark as created
            self.icons[icon_id]['created'] = True
            logger.info(f"Created icon for {label} with ID {nid.uID}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating icon for {label}: {e}")
            return False

    def update_icon(self, icon_id: str, value: str) -> bool:
        """Update a system tray icon with a new value."""
        try:
            if icon_id not in self.icons or not self.icons[icon_id]['created']:
                logger.error(f"Icon {icon_id} not found or not created")
                return False
                
            icon_info = self.icons[icon_id]
            label = icon_info['label']
            
            # Create new icon with updated value
            new_icon = self.create_icon_from_text(label, value)
            if not new_icon:
                logger.error(f"Failed to create new icon for {label}")
                return False

            # Create new NOTIFYICONDATA structure
            nid = NOTIFYICONDATA()
            nid.cbSize = sizeof(NOTIFYICONDATA)
            nid.hWnd = self.hwnd
            nid.uID = icon_info['uID']  # Use the stored unique ID
            nid.uFlags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
            nid.uCallbackMessage = win32con.WM_USER + 20
            nid.hIcon = new_icon
            nid.szTip = f"{label}: {value}"
            
            # Update the icon using Shell_NotifyIconW
            if not Shell_NotifyIconW(win32gui.NIM_MODIFY, byref(nid)):
                error_code = win32api.GetLastError()
                logger.error(f"Failed to update icon for {label}. Error code: {error_code}")
                return False
                
            # Update stored data
            icon_info['data'] = nid
            icon_info['icon_handle'] = new_icon
            logger.info(f"Updated icon for {label} with value {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating icon for {icon_id}: {e}")
            return False

    def cleanup(self):
        """Clean up all system tray icons."""
        try:
            for icon_id, icon_info in self.icons.items():
                if icon_info['created']:
                    try:
                        if not Shell_NotifyIconW(win32gui.NIM_DELETE, byref(icon_info['data'])):
                            error_code = win32api.GetLastError()
                            logger.error(f"Failed to delete icon for {icon_info['label']}. Error code: {error_code}")
                    except Exception as e:
                        logger.error(f"Error cleaning up icon for {icon_info['label']}: {e}")
            
            # Destroy the window
            if self.hwnd:
                win32gui.DestroyWindow(self.hwnd)
            if self.wc:
                win32gui.UnregisterClass(self.wc.lpszClassName, self.wc.hInstance)
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run(self):
        """Run the system tray application."""
        try:
            logger.info("Starting application...")
            
            # Create all icons first
            for label, path in self.config['icons']:
                self.create_icon(label, path)
            
            # Wait a moment for icons to be created
            time.sleep(0.5)
            
            # Start the update thread
            self.running = True
            self.update_thread = threading.Thread(target=self.update_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
            
            # Message loop
            while self.running:
                try:
                    msg = win32gui.GetMessage(self.hwnd, 0, 0)
                    if msg[0]:
                        win32gui.TranslateMessage(msg[1])
                        win32gui.DispatchMessage(msg[1])
                    else:
                        break
                except Exception as e:
                    logger.error(f"Error in message loop: {e}")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            logger.info("Cleaning up...")
            self.running = False
            self.cleanup()
            os._exit(0)  # Force exit after cleanup

    def create_icon_from_text(self, label: str, value: str) -> int:
        """Create an icon with text and return the icon handle."""
        try:
            logger.info(f"Creating icon for {label} with value {value}")
            
            # Create a new image with transparency
            image = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Get font configuration from environment
            font_path = os.getenv('FONT_PATH', 'C:\\Windows\\Fonts\\bahnschrift.ttf')
            label_font_size = int(os.getenv('LABEL_FONT_SIZE', '13'))
            value_font_size = int(os.getenv('VALUE_FONT_SIZE', '17'))
            
            # Load fonts with different sizes
            label_font = None
            value_font = None
            try:
                label_font = ImageFont.truetype(font_path, label_font_size)
                value_font = ImageFont.truetype(font_path, value_font_size)
                logger.info(f"Using font: {font_path}")
            except Exception as e:
                logger.warning(f"Failed to load font {font_path}: {e}")
                logger.warning("Using default font")
                label_font = ImageFont.load_default()
                value_font = ImageFont.load_default()
            
            # Draw the text - measure each line separately
            label_width = draw.textlength(label, font=label_font)
            value_width = draw.textlength(value, font=value_font)
            max_width = max(label_width, value_width)
            
            # Calculate positions
            label_position = ((32 - label_width) // 2, 2)
            value_position = ((32 - value_width) // 2, 18)
            
            # Draw each line separately with different fonts
            draw.text(label_position, label, fill='black', font=label_font)
            draw.text(value_position, value, fill='black', font=value_font)
            
            # Save as PNG first (for transparency)
            png_path = f"icon_{label}.png"
            image.save(png_path, format='PNG')
            logger.debug(f"Saved PNG to {png_path}")
            
            # Convert to ICO for Windows
            ico_path = f"icon_{label}.ico"
            img = Image.open(png_path)
            img.save(ico_path, format='ICO')
            logger.debug(f"Saved ICO to {ico_path}")
            
            # Load the icon
            icon_handle = win32gui.LoadImage(
                0,
                ico_path,
                win32con.IMAGE_ICON,
                0, 0,
                win32con.LR_LOADFROMFILE
            )
            
            if not icon_handle:
                error = win32api.GetLastError()
                logger.error(f"Failed to load icon image. Error code: {error}")
                return None
                
            logger.info(f"Successfully created icon handle: {icon_handle}")
            
            # Clean up temporary files
            os.remove(png_path)
            os.remove(ico_path)
            
            return icon_handle
            
        except Exception as e:
            logger.error(f"Error creating icon from text: {e}")
            return None

    def update_loop(self):
        """Periodically update the icons with new values."""
        while self.running:
            try:
                # Get API configuration from environment
                api_url = os.getenv('API_URL')
                api_headers = {'Accept': os.getenv('API_HEADERS_ACCEPT', 'application/json')}
                poll_interval = int(os.getenv('POLL_INTERVAL', '30'))
                
                # Fetch data from API
                response = requests.get(api_url, headers=api_headers)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Received API response: {data}")
                
                # Update each icon
                for icon_id, icon_info in self.icons.items():
                    if icon_info['created']:
                        try:
                            # Get value from JSON path
                            value = data
                            for part in icon_info['path'].split('.'):
                                value = value[part]
                            value = str(int(float(value)))  # Convert to integer and then string
                            logger.info(f"Updating {icon_id} with value {value}")
                            
                            # Update the icon
                            if not self.update_icon(icon_id, value):
                                logger.error(f"Failed to update icon {icon_id}")
                        except Exception as e:
                            logger.error(f"Error updating icon {icon_id}: {e}")
                
                # Wait for next update
                time.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(5)  # Wait a bit before retrying

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Get icon configuration from environment
    icons = []
    for key, value in os.environ.items():
        if key.startswith('ICON_'):
            label = key[5:]  # Remove 'ICON_' prefix
            icons.append((label, value))
    
    # Configuration
    config = {
        'api_url': os.getenv('API_URL'),
        'api_headers': {
            "Accept": os.getenv('API_HEADERS_ACCEPT', 'application/json')
        },
        'poll_interval': int(os.getenv('POLL_INTERVAL', '30')),
        'icons': icons
    }
    
    app = None
    try:
        app = SystemTray(config)
        app.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        if app:
            app.cleanup()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if app:
            app.cleanup()
        sys.exit(1) 