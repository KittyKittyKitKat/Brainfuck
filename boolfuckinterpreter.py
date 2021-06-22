from bfinterpreter import BrainfuckInterpreter as BFI, INFINTIY
from typing import Any


class BoolFuckInterpreter(BFI):
    def __init__(self,
                 code: str,
                 *,
                 input_stream: str = '',
                 pointer_start: int = 50) -> None:
        super().__init__(code, bits=1, max_tape_size=INFINTIY)
        self.code = BFI.strip_code(code, allowed_chrs='[]<>+,;')
        self.command_map = {
            '>': self.move_right,
            '<': self.move_left,
            '+': self.flip,
            ';': self.write,
            ',': self.read,
            '[': self.jump_if_zero,
            ']': self.jump_unless_zero
        }
        self.pointer = 0
        self.tape = [0]
        self.input_stream = [str(chr) for chr in reversed(input_stream)]
        self.input_bit_buffer: list[int] = []
        self.output_stream: list[Any] = []

    def move_left(self) -> None:
        self.pointer -= 1
        if self.pointer < 0:
            self.tape.insert(0, 0)
            self.pointer = 0

    def flip(self) -> None:
        self.check_pointer()
        self.tape[self.pointer] = int(not self.tape[self.pointer])

    def read(self) -> None:
        self.check_pointer()
        if not self.input_bit_buffer:
            try:
                next_chr: Any = ord(self.input_stream.pop())
            except IndexError:
                next_chr = 0
            if next_chr == '\x04':
                bits: list[Any] = [0] * 8
            else:
                bits = [bit for bit in format(next_chr, '#010b')[2:]]
            self.input_bit_buffer = bits
        self.tape[self.pointer] = self.input_bit_buffer.pop()

    def write(self) -> None:
        self.check_pointer()
        self.output_stream.append(self.tape[self.pointer])

    def run_program(self) -> None:
        super().run_program()
        output = ''
        for i in range(0, len(self.output_stream), 8):
            bits = reversed(self.output_stream[i:i + 8])
            bits_str = '0b' + ''.join(str(bit) for bit in bits)
            output += chr(int(bits_str, 2))
        print(output, end='')
