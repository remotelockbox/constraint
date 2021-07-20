import shutil
import textwrap


class Output:
    def __init__(self):
        self._para_written = False
        self.width = min(72, shutil.get_terminal_size()[0])

    def println(self, msg):
        self._para_written = True

        unwrapped_lines = msg.splitlines()
        for unwrapped in unwrapped_lines:
            for line in textwrap.wrap(str(unwrapped),
                                      self.width,
                                      subsequent_indent=self.__count_indent(unwrapped)):
                print(line)

    def start_paragraph(self):
        if self._para_written:
            print('')
        self._para_written = False

    def print_paragraph(self, msg):
        self.start_paragraph()
        if msg:
            self.println(msg)

    @staticmethod
    def __count_indent(msg):
        indent = ''
        for c in msg:
            if c in [' ', '-']:
                indent += ' '
            else:
                break
        return indent


out = Output()
