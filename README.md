# System Tray Monitor

A Windows system tray application that displays real-time values from a JSON API as system tray icons. Each icon shows a label and a value that updates periodically.

## Features

- Multiple system tray icons with labels and values
- Configurable polling interval for API updates
- Right-click menu with Quit option
- Customizable font settings
- Environment-based configuration
- Automatic error handling and recovery

## Requirements

- Windows 10 or later
- Python 3.7 or later
- Required Python packages (see Installation)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/slauber/systray.git
cd systray
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project directory with your configuration (see Configuration section).

## Configuration

Create a `.env` file in the project directory with the following settings:

```env
# API Configuration
API_URL=your_api_url_here
API_HEADERS_ACCEPT=application/json
POLL_INTERVAL=30

# Font Configuration
FONT_PATH=C:\Windows\Fonts\bahnschrift.ttf
LABEL_FONT_SIZE=13
VALUE_FONT_SIZE=17

# Icon Configuration
ICON_PV=pvPower
ICON_DESK=deskPower
ICON_TEMP=temp
```

### Configuration Options

- `API_URL`: The URL of your JSON API endpoint
- `API_HEADERS_ACCEPT`: The Accept header for API requests (default: application/json)
- `POLL_INTERVAL`: How often to update values in seconds (default: 30)
- `FONT_PATH`: Path to the TrueType font file to use
- `LABEL_FONT_SIZE`: Font size for icon labels (default: 13)
- `VALUE_FONT_SIZE`: Font size for icon values (default: 17)
- `ICON_*`: Define icons to display. The key format is `ICON_LABEL` where LABEL is what appears above the value. The value is the JSON path to get the value from the API response.

## Usage

1. Start the application:
```bash
python systray.py
```

2. The application will create system tray icons for each configured value.

3. Each icon shows:
   - Label (top)
   - Current value (bottom)
   - Updates automatically based on POLL_INTERVAL

4. Right-click any icon to:
   - Quit the application

## Troubleshooting

### Common Issues

1. **Icons not appearing**
   - Check if the API URL is correct
   - Verify the JSON paths in your ICON_* settings
   - Check the application logs for errors

2. **Font issues**
   - Ensure the font path is correct
   - Try using a different system font
   - Check if the font file exists

3. **API connection issues**
   - Verify your API URL
   - Check your network connection
   - Ensure the API is accessible

### Logging

The application logs to the console with timestamps. Check the logs for detailed error messages and debugging information.

## Development

### Project Structure

- `systray.py`: Main application code
- `.env`: Configuration file
- `requirements.txt`: Python package dependencies

### Adding New Icons

To add a new icon:

1. Add a new entry to your `.env` file:
```env
ICON_NEWLABEL=json.path.to.value
```

2. Restart the application

### Building from Source

No build step is required. The application runs directly from the Python source.

## License

[Your chosen license]

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 