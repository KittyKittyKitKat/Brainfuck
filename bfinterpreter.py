import sys
import re
from enum import Enum, auto
from typing import Union, Any

INFINTIY = float('inf')
NEGATIVE_INFINITY = float('-inf')


class EOF_BEHAVIOUR(Enum):
    ZERO = auto()
    NO_CHANGE = auto()


class BrainfuckInterpreter():
    def __init__(self,
                 code: str,
                 *,
                 bits: int = 8,
                 unsigned: bool = True,
                 bit_wrapping: bool = True,
                 tape_wrapping: bool = False,
                 max_tape_size: Union[int, float] = 32768,
                 eof_behavior: EOF_BEHAVIOUR = EOF_BEHAVIOUR.NO_CHANGE,
                 extended_uncode_support: bool = True) -> None:
        if eof_behavior not in EOF_BEHAVIOUR:
            raise ValueError('Invalid EOF behaviour specified')
        self.code = BrainfuckInterpreter.strip_code(code)
        self.bracket_matches = self.bracket_balance_match()
        self.reversed_bracket_matches = {
            value: key for key, value in self.bracket_matches.items()
        }
        if unsigned:
            self.max_cell_value = 2**bits - 1
            self.min_cell_value = 0
        else:
            self.max_cell_value = 2**bits // 2 - 1
            self.min_cell_value = ~self.max_cell_value
        self.bit_wrapping = bit_wrapping
        self.max_tape_size = max_tape_size
        self.tape_wrapping = tape_wrapping
        if self.max_tape_size == INFINTIY:
            self.tape_wrapping = False
        self.eof_behavior = eof_behavior
        self.extended_uncode_support = extended_uncode_support
        self.tape = [0] * (self.max_tape_size if self.tape_wrapping else 1)  # type: ignore
        self.pointer = 0
        self.program_counter = 0
        self.stdout_stream = ''

        self.command_map = {
            '>': self.move_right,
            '<': self.move_left,
            '+': self.increment,
            '-': self.decrement,
            '.': self.write,
            ',': self.read,
            '[': self.jump_if_zero,
            ']': self.jump_unless_zero
        }

    @classmethod
    def from_file(cls: Any,
                  code_file: str,
                  **kwargs: Any) -> Any:
        with open(code_file) as fp:
            code = ''.join([line.strip() for line in fp])
        return cls(code, **kwargs)

    @staticmethod
    def strip_code(raw_code: str, allowed_chrs: str = '+-<>,.[]') -> str:
        inverse_regex = r'[^' + re.escape(allowed_chrs) + ']'
        return re.sub(inverse_regex, '', raw_code.strip())

    def check_pointer(self) -> None:
        if self.pointer < 0 and not self.tape_wrapping:
            raise IndexError(f'Cannot access index {self.pointer} on tape')

    def bracket_balance_match(self) -> dict[int, int]:
        opening_positions = []
        bracket_queue = []
        bracket_matches = {}
        for x, i in enumerate(self.code):
            if i == '[':
                bracket_queue.append(']')
                opening_positions.append(x)
            elif i == ']':
                if not bracket_queue or i != bracket_queue.pop():
                    raise SyntaxError('Mismatched brackets')
                bracket_matches[opening_positions.pop()] = x
        if bracket_queue:
            raise SyntaxError('Mismatched brackets')
        return bracket_matches

    def move_right(self) -> None:
        self.pointer += 1
        try:
            self.tape[self.pointer]
        except IndexError:
            if len(self.tape) < self.max_tape_size:
                self.tape.append(0)
            else:
                msg = f'Maximum tape length of {self.max_tape_size} exceeded'
                raise MemoryError(msg)

    def move_left(self) -> None:
        self.pointer -= 1

    def increment(self) -> None:
        self.check_pointer()
        if self.tape[self.pointer] == self.max_cell_value:
            if self.bit_wrapping:
                self.tape[self.pointer] = self.min_cell_value
            else:
                msg = f'Minimum cell value of {self.min_cell_value} exceeded'
                raise ValueError(msg)
        else:
            self.tape[self.pointer] += 1

    def decrement(self) -> None:
        self.check_pointer()
        if self.tape[self.pointer] == self.min_cell_value:
            if self.bit_wrapping:
                self.tape[self.pointer] = self.max_cell_value
            else:
                msg = f'Maximum cell value of {self.max_cell_value} exceeded'
                raise ValueError(msg)
        else:
            self.tape[self.pointer] -= 1

    def write(self) -> None:
        self.check_pointer()
        c = self.tape[self.pointer]
        UTF8 = True

        if self.extended_uncode_support and c > 0x7f and len(self.stdout_stream) and UTF8:
            n = 1
            v = c & 0x3f
            h = 0x80
            while True:
                cc = ord(self.stdout_stream[len(self.stdout_stream) - n]) or 0
                if cc > 0xff or not (cc and 0x80):
                    UTF8 = False
                    break
                h |= h >> 1
                if (cc & h) == h and not(cc & ((h >> 1) & (~h))):
                    c = v | (cc & ~h) << (n * 6)
                    self.stdout_stream = self.stdout_stream[:len(self.stdout_stream) - n]
                    break
                elif cc & 0x80 and not(cc & 0x40) and n < 5:
                    v |= (cc & 0x3f) << (n * 6)
                n += 1

        self.stdout_stream += chr(c)
        if UTF8:
            print(chr(c), end='')

    def read(self) -> None:
        self.check_pointer()
        try:
            val: Any = input()
        except EOFError:
            if self.eof_behavior is EOF_BEHAVIOUR.NO_CHANGE:
                return
            elif self.eof_behavior is EOF_BEHAVIOUR.ZERO:
                val = 0
        except KeyboardInterrupt:
            sys.exit(0)
        else:
            if not val:
                val = '\n'
            val = ord(val[0])
        self.tape[self.pointer] = val

    def jump_if_zero(self) -> None:
        if not self.tape[self.pointer]:
            new_pc = self.bracket_matches[self.program_counter]
            self.program_counter = new_pc

    def jump_unless_zero(self) -> None:
        if self.tape[self.pointer]:
            new_pc = self.reversed_bracket_matches[self.program_counter]
            self.program_counter = new_pc

    def run_program(self) -> None:
        program_len = len(self.code)
        while self.program_counter < program_len:
            self.command_map[self.code[self.program_counter]]()
            self.program_counter += 1
