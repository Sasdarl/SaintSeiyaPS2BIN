#! /usr/bin/env python3

import sys
from helpers import Dictionary, LzssConfig, array_to_hexstring, set_bit


# ABOUT LZSS
#
#   https://michaeldipperstein.github.io/lzss.html
#   https://community.bistudio.com/wiki/Compressed_LZSS_File_Format
#   https://go-compression.github.io/algorithms/lzss/


# Note: If you change bitsizes, the function encode_pointer_and_length()
#       must be appropriately adjusted
POINTER_BITSIZE = 12
LENGTH_BITSIZE  =  4

DICTIONARY_SIZE = 4096  # Maximum pointer values dictates the usable dictionary size
MATCH_SIZE      = 2**LENGTH_BITSIZE   # Maximum length value dictates how much we tray to match with directory data

DICTIONARY_START_POS = -18

MIN_MATCH_SIZE = 3  # Since encoding pointer to (and length of) data in the dictionary takes 2 bytes, it makes no sense to try to compress less than 3 bytes

MAX_MATCH_SIZE = MATCH_SIZE + MIN_MATCH_SIZE - 1  # Since we will never encode anything smaller than MIN_MATCH_SIZE hte values 0,1,2 would never be used as a encoded length
                                                  # So we used those values to encode from MIN_MATCH_SIZE to MATCH_SIZE + MIN_MATCH_SIZE
                                                  # For example, instead of from 0 to 63 we encode 3 to 66


def encode_pointer_and_length(match_pos, match_len):
    # Match size is offsetted so that smallest possible match start at zero
    offsetted_match_len = match_len - MIN_MATCH_SIZE

    # Pack offset and len information into two bytes
    # Offset/pointer is encoded as 10-bit -  byte2[6-7], byte1[0-7]
    # The length is encoded as 6-bit - byte2[0-5]
    byte1 = (match_pos & 0xFF)
    byte2 = ((match_pos & 0b111100000000) >> 4) | (offsetted_match_len & 0b00001111)

    return byte1, byte2


def lzss_encode(raw_input):
    encoded_output = bytearray()

    dictionary = Dictionary(DICTIONARY_SIZE, DICTIONARY_START_POS)

    input_pos = 0

    while input_pos < len(raw_input):

        flags_byte = 0
        current_loop_output = bytearray()
        debug_print_output = ""

        for flag_cnt in range(8):

            if input_pos >= len(raw_input):
                break

            if dictionary.pos == 24:
                # dictionary.print_content()
                pass

            if input_pos == 1661:
                # dictionary.print_content()
                # breakpoint()
                pass

            # Find the longest match within the window
            match_pos = 0
            match_len = 0

            current_look_ahead_buffer_size = min(MAX_MATCH_SIZE, len(raw_input)-input_pos)

            look_ahead_buffer = raw_input[input_pos:input_pos+current_look_ahead_buffer_size]

            # Find match:
            # First iteration
            # Iterate over part where "match window" cannot contain the input bytes
            # Iterate over all bytes of dict from current first/oldest+MAX_MATCH_SIZE up to the newest-MAX_MATCH_SIZE
            for dict_itr in range(0+MAX_MATCH_SIZE, 958):
                local_match_pos = 0
                local_match_len = 0

                if dict_itr == 18:
                    pass

                # Compare from current byte of dict with look_ahead_buffer
                for i in range(current_look_ahead_buffer_size):
                    dict_byte = dictionary.get_byte_by_linear_addr(dict_itr + i)
                    input_byte = look_ahead_buffer[i]
                    if dict_byte != input_byte:
                        break
                    local_match_pos = dictionary.linear_to_phy_address(dict_itr)
                    local_match_len += 1

                if local_match_len >= MIN_MATCH_SIZE:
                    # Added "=" to the check because looks like orig. encoder always set offset to the last found match
                    #   x) The search starts at HEAD 958 and overflows up to 957 where the last positive match happens
                    if local_match_len >= match_len:
                        if dictionary.pos == 24:
                            # print("New best match ")
                            pass
                        match_len = local_match_len
                        match_pos = local_match_pos


            # Second iteration with input
            # Iterate over all bytes where "match window" will contain some of the input bytes
            # Iterate over all bytes of dict from newest_byte - MAX_MATCH_SIZE up to the last byte of the dict
            for dict_byte_iter in range(958, 1024):

                # if input_pos == 163 and dict_byte_iter == 1023:
                if input_pos == 1661:
                    # dictionary.print_content()
                    #breakpoint()
                    pass

                # print(f"dict_byte_iter {dict_byte_iter}")

                if dict_byte_iter == 1020:
                    pass

                local_match_pos = 0
                local_match_len = 0

                # Compare from current byte of dict with look_ahead_buffer
                for i in range(current_look_ahead_buffer_size):

                    dict_index = dict_byte_iter + i

                    # If index got out of dictionary range then read from input, else read from dict
                    if dict_index >= dictionary.size:
                        input_index = dict_index - dictionary.size
                        compare_byte = raw_input[input_pos + input_index]
                    else:
                        compare_byte = dictionary.get_byte_by_linear_addr(dict_byte_iter + i)

                    if look_ahead_buffer[i] != compare_byte:
                        break
                    local_match_pos = dictionary.linear_to_phy_address(dict_byte_iter)
                    local_match_len += 1

                if local_match_len >= MIN_MATCH_SIZE:
                    # Added "=" to the check because looks like orig. encoder always set offset to the last found match
                    #   x) The search starts at HEAD 958 and overflows up to 957 where the last positive match happens
                    if local_match_len >= match_len:
                        match_len = local_match_len
                        match_pos = local_match_pos

            if match_len == 0:
                # Write literal to the output
                flags_byte = set_bit(flags_byte, flag_cnt)
                literal = raw_input[input_pos]

                if literal == 5:
                    # breakpoint()
                    pass

                dictionary.add_byte(literal)
                current_loop_output.append(literal)
                input_pos += 1

                #print(f"[DEBUG] [{len(encoded_output)+len(current_loop_output)}] [{input_pos-1}] Literal {literal:02X} ")
            else:
                # Write pointer to the output
                # dictionary.print_content()
                #print(f"[DEBUG] [{len(encoded_output)+len(current_loop_output)+1}] [{input_pos}] Matched string, offset: {match_pos}, len: {match_len}, symbols:", end="")
                # Add matched bytes into dictionary
                for i in range(match_len):
                    #value = dictionary.get_byte(match_pos + i)
                    value = look_ahead_buffer[i]
                    dictionary.add_byte(value)
                    #print(f" {value:02X}", end="")
                #print(" ")

                byte1, byte2 = encode_pointer_and_length(match_pos, match_len)

                current_loop_output.append(byte1)
                current_loop_output.append(byte2)
                input_pos += match_len
                #print(f"[DEBUG] [{len(encoded_output)+len(current_loop_output)+1-2}] [{input_pos-match_len}] Ring head {dictionary.pos-match_len} ")
                #print(f"[DEBUG] [{len(encoded_output) + len(current_loop_output) + 1 -2}] [{input_pos-match_len}] Pointer {byte1:02X} {byte2:02X} ")
                #print(debug_print_output_local

        #print(debug_print_output)
        #print(f"[DEBUG] [{len(encoded_output)}] Flags: {flags_byte:02X} \n")

        encoded_output.append(flags_byte)
        encoded_output.extend(current_loop_output)

    #dictionary.print_content()

    #print(f"Pointer bitsize: {POINTER_BITSIZE}")
    #print(f"Lenght  bitsize: {LENGTH_BITSIZE}")
    #print(f"Dictionary size: {DICTIONARY_SIZE}")
    #print(f"Match size:      {MATCH_SIZE}")
    #print(f"Min. Match size: {MIN_MATCH_SIZE}")
    #print(f"Max. Match size: {MAX_MATCH_SIZE}")

    return encoded_output


def encode_lzss_file(input_file, output_file):
    # Read the input file
    with open(input_file, "rb") as file:
        input_data = file.read()

    # Compress the data
    encoded_data = lzss_encode(input_data)

    # Write the output to the output file
    # In first 8 bytes it writes:
    #   0-3: "LZSS"
    #   4-7: Size of compressed data in big endian
    # The resto of the file is the compressed data
    with open(output_file, "wb") as file:
        file.write(b"LZSS")
        size = len(input_data) & 0xFFFFFFFF

        file.write(size.to_bytes(4, byteorder='big'))

        file.write(encoded_data)


def main():
    input_file = ""
    output_file = "py_output.bin"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]

    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    encode_lzss_file(input_file, output_file)


if __name__ == '__main__':
    main()
