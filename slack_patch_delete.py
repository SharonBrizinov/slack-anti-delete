import binascii
import struct
import sys
import os
import platform

from pathlib import Path


system = platform.system().lower()

MESSAGE_DELETED = "message_deleted"
MESSAGE_DELETED_REP = "m3ssag3_d3l3t3d"


def crc(d):
	return struct.pack("<I", binascii.crc32(d))


def patch_file(file):
	print(f"[-] Patching file: {file}")
	cache_file_data_fixed = b""
	js_file_data = file.read_bytes()

	# Code Cache File: header, js file path, js data, magic type?, js data size, js crc, request
	offset_js_data_start_pos = struct.unpack("<I", js_file_data[12:16])[0] + 24

	cache_file_header = js_file_data[:offset_js_data_start_pos] # 1

	# adding ');' to make it more unique
	cache_file_header_and_data, cache_file_metadata_and_request = js_file_data.split(b");" + JS_FILE_TYPE_MAGIC)
	js_file_data = cache_file_header_and_data[offset_js_data_start_pos:] + b");" # 2

	# Replace and fix crc
	js_file_data_fixed = js_file_data.replace(b"message_deleted", b"message_delet3d")
	crc_calc = crc(js_file_data_fixed)

	# Build cache file
	cache_file_data_fixed = cache_file_header + js_file_data_fixed + JS_FILE_TYPE_MAGIC + cache_file_metadata_and_request[:8] + crc_calc + cache_file_metadata_and_request[12:]

	file.write_bytes(cache_file_data_fixed)


if __name__ == "__main__":
	print("[-] Searching for Slack dir cache storage")

	if system == 'windows':
		slack_dir = Path(os.getenv('APPDATA')) / 'Slack'
	elif system == 'darwin':
		slack_dir = Path(os.getenv('HOME')) / 'Library/Application Support/Slack/Service Worker/CacheStorage'
	else:
		slack_dir = False

	if not slack_dir or not slack_dir.exists():
		print(f"ERROR: Unsupported system: {system}")
		sys.exit(1)

	print(f"[-] Slack dir found at {slack_dir}")
	print(f"[-] Searching for JS code cache files")

	files = list(f for f in slack_dir.glob('**/*') if f.is_file())
	for f in files:
		try:
			data = f.read_text()
			if MESSAGE_DELETED in data:
				patch_file(f)
		except:
			continue

	print("[-] Done! restart Slack")
