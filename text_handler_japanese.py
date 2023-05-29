import threading
import json
import logging

from python_utils_aisu import utils, utils_japanese

from . import text_handler

class TextHandlerJapanese(text_handler.TextHandler):
    def __init__(
        self,
        language = {
            'src': None,
            'dest': None,
        },
        print_romaji=True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.language = language
        self.print_romaji = print_romaji

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
