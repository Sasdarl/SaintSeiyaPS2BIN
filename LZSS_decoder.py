#! /usr/bin/env python3

from helpers import Input_stream, Dictionary, LzssConfig, array_to_hexstring

DEBUG_DECODE = False


def flag_is_pointer(flags_byte, flag_no, lzss_config):

    if lzss_config.first_flag_is_lsb:
        bit_value = (flags_byte >> flag_no) & 1
    else:
        bit_value = (flags_byte >> flag_no) & 0x80

    if lzss_config.flag_set_is_pointer:
        return bit_value

    return not bit_value


def get_offset_and_length(input_stream, lzss_config):
    # Next two bytes are pointer/size pair
    byte1, byte2 = input_stream.get_2_bytes()

    if byte1 is None or byte2 is None:
        #print(f"[DEBUG] Failed to fetch dict pointer at {input_stream.pos}")
        return None, None

    if DEBUG_DECODE:
        print(f"[DEBUG] [{input_stream.pos - 2}] [xx] [xx] Processing {byte1:02X} {byte2:02X}")

    # Do some sanity checks on configuration
    if lzss_config.offset_bit_size < 8 or lzss_config.offset_bit_size > 15 or\
            lzss_config.length_bit_size < 1 or lzss_config.length_bit_size > 8:
        print(f"[ERROR] Unsupported configuration of offset_bit_size or length_bit_size")
        print(f"[ERROR] offset_bit_size = {lzss_config.offset_bit_size}, length_bit_size = {lzss_config.length_bit_size}")
        exit(-1)
        # return None, None

    # Get length
    length_mask = 0
    for x in range(lzss_config.length_bit_size):
        length_mask <<= 1
        length_mask |= 1

    length = (byte2 & length_mask)
    length += lzss_config.min_match_size

    # Get offset
    offset = 0
    offset_byte2_size = lzss_config.offset_bit_size - 8
    offset_byte2_mask = 0xFF - length_mask

    if lzss_config.offset_bit_size > 8:
        offset = ((byte2 & offset_byte2_mask) << offset_byte2_size)

    offset |= byte1

    # print(" !!! DEBUG !!!   length_mask = ",  length_mask)
    # print(" !!! DEBUG !!!   Length = ",  length)

    return offset, length


def lzss_decode(lzss_config, compressed_data):
    dictionary = Dictionary(lzss_config.dictionary_size, lzss_config.dictionary_start_position)

    input_stream = Input_stream(compressed_data)
    decompressed_data = bytearray()

    while input_stream.get_available_data_size() > 0:

        flags_byte = input_stream.get_byte()

        # dictionary.print_content()

        if DEBUG_DECODE:
            print(f"[DEBUG] [{input_stream.pos-1}] Getting flags: {flags_byte:02X} ({(flags_byte >> 4):04b} {flags_byte & 0x0F:04b})")

        # Iterate 8 operations at a time, processing all 8 flags in a "flags" byte
        for flag_index in range(8):

            # Check if flag is set to pointer or literal type
            if flag_is_pointer(flags_byte, flag_index, lzss_config):

                offset, length = get_offset_and_length(input_stream, lzss_config)

                if input_stream.pos-2 == 7:
                    dictionary.print_content()

                if DEBUG_DECODE:
                    print(f"[DEBUG] [{input_stream.pos-2}] [{len(decompressed_data)}] Putting matched string, offset: {offset}, len: {length}, symbols:", end='')

                if offset is None or length is None:
                    break

                if offset == 958:
                    # breakpoint()
                    pass

                for j in range(length):
                    if lzss_config.relative_offset:
                        index = dictionary.pos - offset - 1
                    else:
                        index = offset + j
                    literal = dictionary.get_byte(index)
                    decompressed_data.append(literal)
                    dictionary.add_byte(literal)
                    if DEBUG_DECODE:
                        print(f" {literal:02X}", end='')

                if DEBUG_DECODE:
                    print("")
            else:
                # Next input byte is literal
                literal = input_stream.get_byte()
                if literal is None:
                    break

                if DEBUG_DECODE:
                    print(f"[DEBUG] [{input_stream.pos-1}] [{len(decompressed_data)}] Putting literal {literal:02X}")

                decompressed_data.append(literal)
                dictionary.add_byte(literal)


    if DEBUG_DECODE:
        print("Dictionary content: " + array_to_hexstring(dictionary.data))

    return bytes(decompressed_data)


def decode_lzss_file(input_file, output_file):
    # Read the input file
    with open(input_file, "rb") as f:
        input_data = f.read()

    # Skip the first 8 bytes
    input_data = input_data[8:]

    lzss_config = LzssConfig()
    lzss_config.dictionary_start_position = 958
    lzss_config.flag_set_is_pointer = False
    lzss_config.relative_offset = False

    # Call lzss_decode with the input data
    decompressed_data = lzss_decode(lzss_config, input_data)

    # Write the output to the output file
    with open(output_file, "wb") as f:
        f.write(decompressed_data)


def main():

    lzss_config = LzssConfig()

    simple_data_1_compressed = bytes([0x00, 1, 2, 3, 4, 5, 6, 7, 8])
    simple_data_1_decompressed = bytes([1, 2, 3, 4, 5, 6, 7, 8])

    simple_data_2_compressed = bytes([0x00, 1, 2, 3, 4, 5, 6, 7, 8, 0x03, 0x00, 0x00, 0x0, 0x0])
    simple_data_2_decompressed = bytes([1, 2, 3, 4, 5, 6, 7, 8,   8, 8, 8,   8, 8, 8])

    simple_data_3_compressed = bytes([0x00, 1, 2, 3, 4, 5, 6, 7, 8, 0x03, 0x01, 0x00, 0x1, 0x0])
    simple_data_3_decompressed = bytes([1, 2, 3, 4, 5, 6, 7, 8,   7, 8, 7,   8, 7, 8])

    simple_data_4_compressed = bytes([0x00, 1, 2, 3, 4, 5, 6, 7, 8, 0x03, 0x02, 0x00, 0x2, 0x0])
    simple_data_4_decompressed = bytes([1, 2, 3, 4, 5, 6, 7, 8,   6, 7, 8,   6, 7, 8])

    test_cases = [
        ("simple_data_1_compressed", simple_data_1_compressed, simple_data_1_decompressed),
        ("simple_data_2_compressed", simple_data_2_compressed, simple_data_2_decompressed),
        ("simple_data_3_compressed", simple_data_3_compressed, simple_data_3_decompressed),
        ("simple_data_4_compressed", simple_data_4_compressed, simple_data_4_decompressed),
    ]

    failed_tests = 0

    for i, (name, compressed, decompressed) in enumerate(test_cases, start=1):
        decompressed_output = lzss_decode(lzss_config, compressed)

        print(f"[TEST {name}] Input:  ", array_to_hexstring(compressed))
        print(f"[TEST {name}] Output: ", array_to_hexstring(decompressed_output))
        print("")

        if decompressed_output != decompressed:
            print(f"[TEST] Failed simple_data_{i}_compressed!")
            failed_tests += 1

    if failed_tests == 0:
        print("\033[32m[TEST] All tests successful\033[0m")  # Green text
    else:
        print(f"\033[31m[TEST] {failed_tests} test(s) failed\033[0m")  # Red text

    input_file = "740__53534.lzss"
    output_file = "py_output.bin"
    decode_lzss_file(input_file, output_file)


if __name__ == '__main__':
    main()
