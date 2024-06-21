# ORIGINAL WORK BY Danijelk, 07/03/2024
# MODIFIED 6/20/2024: ADDED NOTICE OF ORIGINAL AUTHOR
class Input_stream:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def get_byte(self):
        if self.pos >= len(self.data):
            return None
        byte = self.data[self.pos]
        self.pos += 1
        return byte

    def get_2_bytes(self):
        byte1 = self.get_byte()
        byte2 = self.get_byte()
        return byte1, byte2

    def get_available_data_size(self):
        return len(self.data) - self.pos


class Dictionary:
    def __init__(self, dict_size, dict_start_position):
        self.data = bytearray(dict_size)
        self.pos = dict_start_position
        self.size = dict_size

    def add_byte(self, byte):
        self.data[self.pos] = byte
        self.pos = (self.pos + 1) % len(self.data)

    def get_byte(self, index):
        return self.data[index % len(self.data)]

    def get_byte_by_linear_addr(self, address):
        phy_address = self.linear_to_phy_address(address)
        # print(f"[DICTIONARY DEBUG] get_byte_by_linear_addr() lin_address = {address}, phy_address = {phy_address}")
        return self.get_byte(phy_address)

    def linear_to_phy_address(self, address):
        phy_address = (len(self.data) + self.pos + address) % len(self.data)
        # print(f"[DICTIONARY DEBUG] linear_to_phy_address() lin_address = {address}, phy_address = {phy_address}")
        return phy_address

    def print_content(self):
        print("[DICTIONARY CONTENT] ")
        #print("Dict len: ", len(self.data))
        print(f"{0:04}:  ", end="")
        for i, byte in enumerate(self.data):
            print(f"{byte:02X} ", end="")
            if (i+1) % 8 == 0: print(" ", end="")
            if (i+1) % (32) == 0:
                print("")
                print(f"{(i+1):04}:  ", end="")
        print(f"\nDict pos: {self.pos} ")
        print("[DICTIONARY CONTENT] ")


class LzssConfig:
    def __init__(
        self,
        dictionary_start_position=0,
        first_flag_is_lsb=True,
        flag_set_is_pointer=True,
        min_match_size=3,
        offset_bit_size=10,
        length_bit_size=6,
        relative_offset=True,
    ):
        self.dictionary_size = 2**offset_bit_size
        if dictionary_start_position > self.dictionary_size:
            print("[ERROR] dictionary_start_position > dictionary_size")
            exit(-1)
        self.dictionary_start_position = dictionary_start_position
        self.first_flag_is_lsb = first_flag_is_lsb
        self.flag_set_is_pointer = flag_set_is_pointer
        self.min_match_size = min_match_size
        self.max_match_size = 2**length_bit_size + min_match_size
        self.offset_bit_size = offset_bit_size
        self.length_bit_size = length_bit_size
        self.relative_offset = relative_offset


def set_bit(value, bit_position):
    # Left shift 1 by bit_position to create a bitmask
    bitmask = 1 << bit_position

    # Use bitwise OR to set the bit at the specified position to 1
    result = value | bitmask

    return result


def array_to_hexstring(array):
    return ''.join('{:02x} '.format(x) for x in array)

