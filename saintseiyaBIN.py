import struct
import argparse
from pathlib import Path
from struct import unpack
from LZSS_decoder import *
from LZSS_encoder import *
from helpers import LzssConfig

def ru32(buf, offset):
    return struct.unpack("<I", buf[offset:offset+4])[0]

def wu32(value):
    return struct.pack("<I", value)

def decode_lzss_file(input_file, output_file):
    # Read the input file
    with open(input_file, "rb") as f:
        input_data = f.read()

    # Skip the first 16 bytes
    input_data = input_data[16:]

    lzss_config = LzssConfig()
    lzss_config.dictionary_start_position = -18
    lzss_config.first_flag_is_lsb = True
    lzss_config.flag_set_is_pointer = False
    lzss_config.relative_offset = False
    lzss_config.offset_bit_size = 12
    lzss_config.length_bit_size = 4
    lzss_config.dictionary_size = 4096

    # Call lzss_decode with the input data
    decompressed_data = lzss_decode(lzss_config, input_data)

    # Write the output to the output file
    with open(output_file, "wb") as f:
        f.write(decompressed_data)
    return 0

def encode_lzss_file(input_file, output_file):
    # Read the input file
    with open(input_file, "rb") as file:
        input_data = file.read()

    # Compress the data
    print("This operation may take a long time. Please wait...")
    encoded_data = lzss_encode(input_data)

    # Write the output to the output file
    # In first 16 bytes it writes:
    #   0-3: "CMPS"
    #   4-7: 0
    #   8-11: Size of compressed data in little endian
    #   12-15: 0
    # The rest of the file is the compressed data
    with open(output_file, "wb") as file:
        file.write(b"CMPS")
        file.write(wu32(0))
        size = len(input_data) & 0xFFFFFFFF

        file.write(size.to_bytes(4, byteorder='little'))
        file.write(wu32(0))
        file.write(encoded_data)
    return 0

parser = argparse.ArgumentParser(description='SS BIN Decompression/Compression') # I was bored
parser.add_argument("inpath", help="File Input (BIN/TPL)")
parser.add_argument("-o", "--outpath", type=str, default="", help="Optional. The name used for the output folder or file.")

args = parser.parse_args()

if Path(args.inpath).is_file() and not Path(args.inpath).is_dir():
    with open(args.inpath, "rb") as input_file:
        input_buffer = bytearray( input_file.read() )

        outpath = "./"
        if len(args.outpath) > 0: # Outpath takes priority!!
            outpath += args.outpath
        else:
            outpath = "output.bin"

        if (len(outpath.rsplit("/",1)) > 1):
            output_folder = outpath.rsplit("/",1)[0]+"/" # Split output into folder and filename
            output_file = outpath.rsplit("/",1)[1]
            Path(output_folder).mkdir(parents=True,exist_ok=True)
        if (ru32(input_buffer, 0) == 0x53504D43):
            un = decode_lzss_file(args.inpath, outpath)
            if un == 0:
                print(f"Successfully decompressed to {outpath}")
        else:
            if (ru32(input_buffer, 0) == 0x464A46):
                re = encode_lzss_file(args.inpath, outpath)
                if re == 0:
                    print(f"Successfully recompressed to {outpath}")
            else:
                print("This file is not compressed.")
        input_file.close()
