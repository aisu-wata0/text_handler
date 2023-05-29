
import re

from python_utils_aisu import utils, utils_japanese

from . import text_handler

def camel_case_to_spaces(text):
    # Use regular expression to split camel case words
    spaced_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # Convert to lowercase and remove leading/trailing spaces
    spaced_text = spaced_text.lower().strip()
    return spaced_text

class TextHandlerJapanese(text_handler.TextHandler):
    def __init__(
        self,
        print_romaji=True,
        characters_to_spaces=['_'],
        camelcase_to_spaces=True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.print_romaji = print_romaji
        self.characters_to_spaces = characters_to_spaces
        self.camelcase_to_spaces = camelcase_to_spaces

    def print_input(self, text_new):
        print_text = text_new
        if self.print_romaji:
            if self.language['src'] == 'ja':
                print_text = utils.text_lines_collate(
                    text_new, utils_japanese.convert_japanese_to_romaji(text_new))
        super().print_input(print_text)

    def print_output(self, output):
        print_text = output
        if self.print_romaji:
            if self.language['dest'] == 'ja':
                print_text = utils.text_lines_collate(
                    output, utils_japanese.convert_japanese_to_romaji(output))
        super().print_output(print_text)

    def get_output(self, text_new, args):
        for c in self.characters_to_spaces:
            text_new = text_new.replace(c, " ")

        if self.camelcase_to_spaces:
            text_new = camel_case_to_spaces(text_new)

        return super().get_output(text_new, args)