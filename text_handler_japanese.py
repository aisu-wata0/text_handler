
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
        english_to_katakana=True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.print_romaji = print_romaji
        self.characters_to_spaces = characters_to_spaces
        self.camelcase_to_spaces = camelcase_to_spaces
        self.english_to_katakana = english_to_katakana
        if self.english_to_katakana:
            import romajitable
            self.romajitable = romajitable

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

    def text_preprocess(self, text, args):
        for c in self.characters_to_spaces:
            text = text.replace(c, " ")

        if self.camelcase_to_spaces:
            text = camel_case_to_spaces(text)
        return text

    def text_postprocess(self, text, args):
        if self.english_to_katakana:
            text = utils_japanese.english_to_katakana(text)
        return text

    def get_output(self, text_new, args):
        text_new = self.text_preprocess(text_new, args)
        text_output = super().get_output(text_new, args)
        text_output = self.text_postprocess(text_output, args)
        return text_output
