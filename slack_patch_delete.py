import binascii
import struct
import sys
import os

def crc(d):
	return struct.pack("<I", binascii.crc32(d))

def x(d):
	return binascii.unhexlify(d.replace(" ",""))

MESSAGE_DELETED = "message_deleted"
MESSAGE_DELETED_REP = "m3ssag3_d3l3t3d"
JS_FILE_TYPE_MAGIC = x("D8 41 0D 97")

if len(sys.argv) != 1:
	print("ERROR: python3 {}".format(sys.argv[0]))
	sys.exit(1)

print("[-] Searching for Slack dir cache storage")
dir_slack = None
dir_1 = os.path.expanduser('~') + "/Library/Containers/com.tinyspeck.slackmacgap/Data/Library/Application Support/Slack/Service Worker/CacheStorage"
dir_2 = os.path.expanduser('~') + "/Library/Application Support/Slack/Service Worker/CacheStorage"
is_dir_1_exists = os.path.exists(dir_1)
if not is_dir_1_exists:
	is_dir_2_exists = os.path.exists(dir_2)
	if not is_dir_2_exists:
		print("ERROR: NO ACTIVE SLACK DIR!")
		sys.exit(1)
	else:
		dir_slack = dir_2
else:
	dir_slack = dir_1

print("[-] Slack dir found at '{}'".format(dir_slack))
print("[-] Searching for JS code cache files")

# Example: ~/Library/Application Support/Slack/Service Worker/CacheStorage/4c237d5e33167c88df3e45d9c8b59fdd4d727472/8fde8cc6-1b49-4fe7-b700-414173dceca1/7ebe8cd16474da22_0
command_grep = os.popen("grep -lir \"{}\" \"{}\"".format(MESSAGE_DELETED, dir_slack))
command_grep_output = command_grep.read().strip()

if not command_grep_output:
	print("ERROR: No relevant Slack JS code files were found")
	sys.exit(1)

slack_js_files = command_grep_output.split("\n")


for js_file in slack_js_files:
	print("\t[-] Patching '{}'".format(js_file))

	cache_file_data_fixed = b""
	with open(js_file, "rb") as f:
		js_file_data = f.read()

		# Code Cache File: header, js file path, js data, magic type?, js data size, js crc, request
		offset_js_data_start_pos = struct.unpack("<I", js_file_data[12:16])[0] + 24

		cache_file_header = js_file_data[:offset_js_data_start_pos] # 1

		cache_file_header_and_data, cache_file_metadata_and_request = js_file_data.split(b");" + JS_FILE_TYPE_MAGIC) # adding ');' to make it more unique

		js_file_data = cache_file_header_and_data[offset_js_data_start_pos:] + b");" # 2


		# Replace and fix crc
		js_file_data_fixed = js_file_data.replace(b"message_deleted", b"message_delet3d")
		crc_calc = crc(js_file_data_fixed)

		# Build cache file
		cache_file_data_fixed = cache_file_header + js_file_data_fixed + JS_FILE_TYPE_MAGIC + cache_file_metadata_and_request[:8] + crc_calc + cache_file_metadata_and_request[12:]

	with open(js_file, "wb") as f:
		f.write(cache_file_data_fixed)

print("[-] Done! restart Slack")