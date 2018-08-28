#!/usr/bin/env python

import argparse
import os
import struct
import sys

parser = argparse.ArgumentParser()
parser.add_argument('file', help='NSP file')
parser.add_argument('--quiet', '-q', help='Do not display verbose log', action='store_true')

args = parser.parse_args()

# https://switchbrew.org/index.php?title=NCA_Format#PFS0
with open(args.file, 'rb') as fin:
    magic = fin.read(4)
    if magic != b'PFS0'[:4]:
        print('Not a valid NSP file')
        sys.exit(1)

    size = os.stat(args.file).st_size
    if not args.quiet:
        print('File size: {:08X}'.format(size))
        print('')

    number_of_files = struct.unpack('i', fin.read(4))[0]
    size_of_the_string_table = struct.unpack('i', fin.read(4))[0]
    struct.unpack('i', fin.read(4))[0] # Zero/Reserved
    
    string_table_offset = 0x10 + (0x18 * number_of_files)
    data_offset = string_table_offset + size_of_the_string_table
    
    if not args.quiet:
        print('Number of files: {}'.format(number_of_files))
        print('String Table offset: {:08X}'.format(string_table_offset))
        print('Data offset: {:08X}'.format(data_offset))
        print('')
    
    fin.seek(0x10)
    
    files = []
    
    for i in range(0, number_of_files):
        offset_of_file_in_data = struct.unpack('q', fin.read(8))[0]
        size_of_file_in_data = struct.unpack('q', fin.read(8))[0]
        offset_of_filename_in_string_table = struct.unpack('i', fin.read(4))[0]
        struct.unpack('i', fin.read(4))[0] # Zero/Reserved
        
        files.append((offset_of_file_in_data, size_of_file_in_data, offset_of_filename_in_string_table, ))
    
    tail = 0

    for f in files:
        fin.seek(string_table_offset + f[2])
        
        filename = ''
        while True:
            c = fin.read(1)
            if c == b'\x00':
                break
            filename += c.decode('utf-8')

        if not args.quiet:
            status = 'Complete'
            if data_offset + f[0] > size:
                status = 'Missing'
            elif data_offset + f[0] + f[1] > size:
                status = 'Truncated'

            print('{}: {:08X} - {:08X} [{}]'.format(filename, data_offset + f[0], data_offset + f[0] + f[1], status))

        tail = max(tail, data_offset + f[0] + f[1])

    print('')

    if size == tail:
        print('NSP file verified')
        sys.exit(0)
    elif size > tail:
        print('NSP file has extra data')
        sys.exit(3)
    else:
        print('NSP file incomplete')
        sys.exit(2)

sys.exit(1)
