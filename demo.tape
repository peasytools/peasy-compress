# peasy-compress — Zero-Dependency Archive & Compression Library Demo
Output demo.gif

Set FontSize 20
Set Width 1000
Set Height 580
Set Shell "zsh"
Set Theme "Catppuccin Mocha"
Set TypingSpeed 30ms
Set Padding 24

Type "uv run --with peasy-compress python3"
Enter
Sleep 2.5s

Type "from peasy_compress import gzip_compress, gzip_decompress, zip_create, zip_list"
Enter
Sleep 1s

Type "# Gzip compress a string"
Enter
Sleep 0.5s

Type "data = b'Hello, Peasy!' * 100"
Enter
Sleep 0.5s

Type "compressed = gzip_compress(data)"
Enter
Sleep 1s

Type "print(f'{len(data)} bytes -> {len(compressed)} bytes ({len(compressed)/len(data)*100:.1f}%)')"
Enter
Sleep 2s

Type "# Roundtrip: decompress back"
Enter
Sleep 0.5s

Type "gzip_decompress(compressed) == data"
Enter
Sleep 1.5s

Type "# Create a ZIP archive in memory"
Enter
Sleep 0.5s

Type "zdata = zip_create({'readme.txt': b'Hello!', 'data.csv': b'a,b\\n1,2'})"
Enter
Sleep 1.5s

Type "info = zip_list(zdata)"
Enter
Sleep 1s

Type "print(f'{info.file_count} files, {info.total_size} bytes')"
Enter
Sleep 2s

Type "exit()"
Enter
Sleep 1s
