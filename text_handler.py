import threading
import json
import logging
from typing import Any, Iterable

from python_utils_aisu import utils, utils_japanese

logger = utils.loggingGetLogger(__name__)


class TextHandler:
    def __init__(
        self,
        use_output_cache=True,
        start_from_history_file="",
        history=None,
        history_output=None,
        output_cache=None,
        history_cut=0,
        FileWriterArgs={
            "directory": "history",
            "directory_timestamped": "history/old",
        },
        print_format={
            'input': '\n=-=\n{print_text}\n=-= {history_length} - {history_cut}',
            'output': '{print_text}',
        },
        get_output_args={
        },
        language={
            'src': None,
            'dest': None,
        },
    ):
        self.use_output_cache = use_output_cache
        self.start_from_history_file = start_from_history_file
        self.history = history or []
        self.history_output = history_output or []
        self.output_cache = output_cache or {}
        self.history_cut = history_cut
        self.LOCK = threading.Lock()

        self.FileWriter = utils.FileWriter(
            **FileWriterArgs,
        )

        self.print_format = print_format
        self.get_output_args = get_output_args
        self.language = language

        if self.start_from_history_file:
            with open(self.start_from_history_file, mode="r", encoding="utf-8") as f:
                history_json = json.load(f)
                for t in history_json:
                    self.history.append(t[0])
                    self.history_output.append(t[1])
                    if t[0] in self.output_cache:
                        self.output_cache[t[0]].append(t[1])
                    else:
                        self.output_cache[t[0]] = [t[1]]

            print("get history_cut...")
            self.history_cut = self.find_history_cut("whatever")
            print(f"history_cut = {self.history_cut}")

        self.wait: Any = None

    def is_size_ok(self, text_new, history_cut_):
        over_size = len(self.history[history_cut_:]) - 1
        too_big = over_size > 0
        return not too_big

    def find_history_cut(self, text_new):
        def is_size_ok_(history_cut):
            return self.is_size_ok(text_new, history_cut)

        too_big = not self.is_size_ok(text_new, self.history_cut)
        if too_big:
            self.history_cut = utils.binary_search(
                self.history_cut, len(self.history), is_size_ok_)
        return self.history_cut

    def history_og_current(self):
        return self.history[self.history_cut:]

    def history_output_current(self):
        return self.history_output[self.history_cut:]

    def save_state(self, timestamp=False, directory="history"):
        if timestamp:
            timestamp = utils.get_timestamp()

        flattened_interleaved_history = [elem for (o, t) in zip(
            self.history, self.history_output) for elem in (o, t)]

        replacer = ['\n', r'\n']
        history_nonl = (f"{o.replace(*replacer)}={t.replace(*replacer)}" for (o, t)
                 in zip(self.history, self.history_output))

        writers = [(
            "history_og",
            lambda: self.FileWriter.write(self.history, "history_og",
                                          timestamp=timestamp, json_write=True),
        ),
            (
            "history_tr",
            lambda: self.FileWriter.write(self.history_output, "history_tr",
                                          timestamp=timestamp, json_write=True),
        ),
            (
            "history",
            lambda: self.FileWriter.write([(o, t) for (o, t) in zip(self.history, self.history_output)], "history",
                                          timestamp=timestamp, json_write=True),
        ),
            (
            "history_og",
            lambda: self.FileWriter.write(self.history, "history_og",
                                          timestamp=timestamp, json_write=False),
        ),
            (
            "history_tr",
            lambda: self.FileWriter.write(self.history_output, "history_tr",
                                          timestamp=timestamp, json_write=False),
        ),
            (
            "history",
            lambda: self.FileWriter.write(flattened_interleaved_history, "history",
                                          timestamp=timestamp, json_write=False),
        ),
            (
            "history_nonl",
            lambda: self.FileWriter.write(history_nonl, "history_nonl",
                                          timestamp=timestamp, json_write=False),
        ),
        ]

        exceptions = []
        for name, f in writers:
            try:
                f()
            except Exception as e:
                exceptions.append((name, e))
                logger.exception(f"Error while writing {name}")
        return exceptions

    def get_output(self, text_new, args):
        return text_new

    def print_input(self, text_new):
        print_text = text_new
        print(self.print_format['input'].format(
            print_text=print_text,
            history_length=len(self.history),
            history_cut=self.history_cut,
        ), flush=True)

    def print_output(self, output):
        print_text = output
        print(self.print_format['output'].format(
            print_text=print_text,
            history_length=len(self.history),
            history_cut=self.history_cut,
        ))

    def append_to_history(self, text_input, text_output):
        self.history.append(text_input)
        self.history_output.append(text_output)
        self.output_cache[text_input] = text_output
        self.save_state()

    def handle(self, text_new, get_output_args={}):
        get_output_args = {**self.get_output_args, **get_output_args}
        if not text_new:
            return ""
        with self.LOCK:
            if len(self.history) > 1 and text_new.replace("\n", "") == self.history[-1].replace("\n", ""):
                return self.history_output[-1]
            text_new = text_new.replace('\r\n', '\n')

            self.print_input(text_new)
            try:
                text_output = ""
                if self.use_output_cache and text_new in self.output_cache:
                    text_output = self.output_cache[text_new]
                else:
                    self.history_cut = self.find_history_cut(text_new)
                    text_output = self.get_output(text_new, get_output_args)
                self.append_to_history(text_new, text_output)
                self.print_output(text_output)
                if self.wait:
                    if isinstance(self.wait, Iterable):
                        for w in self.wait:
                            w.join()
                    else:
                        self.wait.join()
                return text_output
            except RuntimeError as e:
                print(f"Error handling ```\n{text_new}\n```\n{e}")
            return None

    def handle_spawn_thread(self, text_new):
        thread = threading.Thread(target=self.handle, args=(text_new,))
        return thread

    def retry_last(self, get_output_args={}):
        if len(self.history) < 1:
            return None
        text_new = self.history[-1]
        if text_new in self.output_cache:
            del self.output_cache[text_new]
        self.history = self.history[:-1]
        self.history_output = self.history_output[:-1]
        return self.handle(text_new, get_output_args=get_output_args)

    def retry_last_input_args(self):
        if len(self.history) < 1:
            return None

        json_string = input(
            f"Current args: {self.get_output_args})\n paste valid json args:")

        try:
            get_output_args = json.loads(json_string)
            self.retry_last(get_output_args=get_output_args)
        except json.JSONDecodeError:
            # The string is not valid JSON
            print("Invalid JSON string")
            return None

    def clear_history(self, inp):
        if int(inp) > 0:
            self.save_state(True)
            self.history = self.history[:-int(inp)]
            self.history_output = self.history_output[:-int(inp)]
            self.save_state()
