
import re

from python_utils_aisu import utils, utils_japanese

from . import text_handler

class TextHandlerJapanese(text_handler.TextHandler):
    def __init__(
        self,
        print_romaji=True,
        characters_to_spaces=[],
        camelcase_to_spaces=False,
        english_to='', # '', or, 'katakana', or 'engrish'
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.print_romaji = print_romaji
        self.characters_to_spaces = characters_to_spaces
        self.camelcase_to_spaces = camelcase_to_spaces
        self.english_to = english_to

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
            text = utils.camel_case_to_spaces(text)
        return text

    def text_postprocess(self, text, args):
        if self.english_to == 'katakana':
            text = utils_japanese.english_replace_with_f(
                text, utils_japanese.replace_match_with_katakana)
        elif self.english_to == 'engrish':
            text = utils_japanese.english_replace_with_f(
                text, utils_japanese.replace_match_with_engrish)
            text = (text)
        return text

    def get_output(self, text_new, args):
        text_new = self.text_preprocess(text_new, args)
        text_output = super().get_output(text_new, args)
        text_output = self.text_postprocess(text_output, args)
        return text_output
