"""Bot executable creation script."""
import PyInstaller.__main__

PyInstaller.__main__.run([
    'tft.py',
    '--onefile',
    '--add-data',
    'captures;captures',
    '-n',
    'TFT Bot',
    '-i',
    'tft_logo_with_bot.ico',
    '--console',
    '--win-private-assemblies',
    '--win-no-prefer-redirects',
    '--clean'
])
