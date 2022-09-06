import binascii
import struct
import sys
import os
import platform

from pathlib import Path


MESSAGE_DELETED = b"message_deleted"
MESSAGE_DELETED_REP = b"m3ssag3_d3l3t3d"
JS_FILE_TYPE_MAGIC = binascii.unhexlify("D8 41 0D 97".replace(" ",""))


def crc(d):
	return struct.pack("<I", binascii.crc32(d))


def patch_file(file):
	cache_file_data_fixed = b""
	js_file_data = file.read_bytes()

	# Check if file needs to be patched
	if MESSAGE_DELETED in js_file_data:
		print(f"	[-] Patching file: {file}")
		# Code Cache File: header, js file path, js data, magic type?, js data size, js crc, request
		offset_js_data_start_pos = struct.unpack("<I", js_file_data[12:16])[0] + 24
		cache_file_header = js_file_data[:offset_js_data_start_pos] # 1
		# adding ');' to make it more unique
		cache_file_header_and_data, cache_file_metadata_and_request = js_file_data.split(b");" + JS_FILE_TYPE_MAGIC)
		js_file_data = cache_file_header_and_data[offset_js_data_start_pos:] + b");" # 2
		# Replace and fix crc
		js_file_data_fixed = js_file_data.replace(MESSAGE_DELETED, MESSAGE_DELETED_REP)
		crc_calc = crc(js_file_data_fixed)
		# Build cache file
		cache_file_data_fixed = cache_file_header + js_file_data_fixed + JS_FILE_TYPE_MAGIC + cache_file_metadata_and_request[:8] + crc_calc + cache_file_metadata_and_request[12:]
		# Write the patched file
		return file.write_bytes(cache_file_data_fixed)
	return False


def locate_slack():
	system = platform.system().lower()
	slack_dir = False

	print("[-] Searching for Slack dir cache storage")
	if system == 'windows':
		slack_dir = Path(os.getenv('APPDATA')) / 'Slack'
	elif system == 'darwin':
		slack_dirs = [
			"Containers/com.tinyspeck.slackmacgap/Data/Library/Application Support/Slack",
			"Application Support/Slack/Service Worker/CacheStorage"
		]
		for slack_dir in slack_dirs:
			slack_dir = Path(os.getenv('HOME')) / 'Library' / slack_dir
			if slack_dir.exists():
				break

	# Check if slack dir exists
	if not slack_dir or not slack_dir.exists():
		print(f"ERROR: Unsupported system: {system}")
		sys.exit(1)

	print(f"[-] Slack dir found at {slack_dir}")
	return slack_dir


if __name__ == "__main__":
	slack_dir = locate_slack()

	print(f"[-] Searching for JS code cache files")
	files = list(f for f in slack_dir.glob('**/*') if f.is_file())
	for f in files:
		try:
			patch_file(f)
		except Exception as e:
			continue

	print("[-] Done! restart Slack")
