#!/usr/bin/env python
import os
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle, prompt

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory, AutoSuggest, Suggestion
from prompt_toolkit.history import FileHistory

# Searchable operators.
# See https://ui.adsabs.harvard.edu/help/search/comprehensive-solr-term-list
operators = [    
    "year",
]

operator_family = {
    "orcid": "orcid",
    "orcid_pub": "orcid",
    "orcid_user": "orcid",
    "orcid_other": "orcid",
    #"title": "title",
    "alternate_title": "title",
    "arxiv": "arxiv",
    "arxiv_class": "arxiv",
}

family_colors = {
    "orcid": "ansigreen",
    "title": "ansiblue",
    "arxiv": "ansiyellow"
}

from collections import OrderedDict

# Use an ordereddict to show more common operators first.
operators = OrderedDict([
    ("abstract", HTML("Search for text in the <ansired>abstract</ansired> of a record.")),
    ("ack", HTML("Search <ansired>ack</ansired>nowledgements extracted from fulltexts.")),
    ("aff", HTML("Search <ansired>aff</ansired>iliation string.")),
    ("aff_id", HTML("Search for a curated affiliation ID.")),
    ("alternate_bibcode", HTML("Search alternate bibcodes.")),
    ("alternate_title", HTML("Search alternate titles, usually when the original title is not in English.")),
    ("arxiv", HTML("Search for an ArXiv ID.")),
    ("arxiv_class", HTML("The arXiv class a document was submitted to.")),
    ("orcid", HTML("Combined search for <ansigreen>orcid_pub</ansigreen>, <ansigreen>orcid_user</ansigreen>, and <ansigreen>orcid_other</ansigreen>.")),
    ("orcid_pub", HTML("ORCIDs supplied by publishers.")),
    ("orcid_user", HTML("ORCID claims from users who gave ADS consent to expose their public profiles.")),
    ("orcid_other", HTML("ORCID claims from users who used the ADS claiming interface.")),
    ("author", HTML("Search by author name or position.")),
    ("author_count", None),
    ("bibcode", None),
    ("bibgroup", None),
    ("bibstem", None),
    ("body", None),
    ("citation_count", None),
    ("copyright", None),
    ("data", None),
    ("database", None),
    ("pubdate", None),
    ("doctype", None),
    ("doi", None),
    ("grant", None),
    ("identifier", None),
    ("inst", None),
    ("issue", None),
    ("keyword", None),
    ("lang", None),
    ("object", None),
    ("page", None),
    ("bibstem", None),
    ("property", None),
    ("read_count", None),
    ("title", None),
    ("vizier", None),
    ("volume", None),
])
common_operators = ("title", "author", "year", "body")

class OperatorCompleter(Completer):
    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        if not word:
            use_operators = common_operators
        else:
            use_operators = operators

        for operator in use_operators:
            if operator.startswith(word):
                if operator in operator_family:
                    family = operator_family[operator]
                    family_color = family_colors.get(family, "default")
                    display = HTML(
                        "<b>%s:</b> (<"
                        + family_color
                        + ">%s</"
                        + family_color
                        + ">)"
                    ) % (operator, family)
                else:
                    display = operator

                yield Completion(
                    f"{operator}:(",
                    start_position=-len(word),
                    display=display,
                    display_meta=operators.get(operator)
                )



import asyncio

from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession



async def print_counter():
    """
    Coroutine that prints counters.
    """
    try:
        i = 0
        while True:
            print("Counter: %i" % i)
            i += 1
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        print("Background task cancelled.")


async def interactive_shell():
    """
    Like `interactive_shell`, but doing things manual.
    """

    bindings = KeyBindings()
    

    @bindings.add("<any>")
    async def _(event):
        """
        Example of asyncio coroutine as a key binding.
        """
        event.app.current_buffer.insert_text(event.data)

        try:
            #for i in range(5):
            async with in_terminal():
                print(event.app.current_buffer)
            #await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("Prompt terminated before we completed.")


    # Create some history first. (Easy for testing.)
    history_path = os.path.expanduser("~/.ads/cli_history")
    os.makedirs(os.path.dirname(history_path), exist_ok=True)

    history = FileHistory(history_path)
    # TODO: Only commit queries to history if the server said were valid.

    # Print help.

    session = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=True,
    )

    # Create Prompt.
    session = PromptSession(
        "Say something: ", 
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
    )

    # Run echo loop. Read text from stdin, and reply it back.
    while True:
        try:
            result = await session.prompt_async(   
                key_bindings=bindings,     
                completer=OperatorCompleter(),
                #complete_style=CompleteStyle.MULTI_COLUMN,
                complete_while_typing=True,
                complete_in_thread=True
                )
            print('You said: "{0}"'.format(result))
        except (EOFError, KeyboardInterrupt):
            return


from prompt_toolkit.application import in_terminal
from prompt_toolkit.key_binding import KeyBindings

from prompt_toolkit.eventloop.inputhook import set_eventloop_with_inputhook

    
from prompt_toolkit.buffer import Buffer

from prompt_toolkit.application import Application
from prompt_toolkit.document import Document
from prompt_toolkit.filters import has_focus
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Float, FloatContainer, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.widgets import HorizontalLine

from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.processors import Processor, Transformation



BEFORE_PROMPT = "\033]133;A\a"
AFTER_PROMPT = "\033]133;B\a"
BEFORE_OUTPUT = "\033]133;C\a"
AFTER_OUTPUT = (
    "\033]133;D;{command_status}\a"  # command_status is the command status, 0-255
)

def get_prompt_text():
    # Generate the text fragments for the prompt.
    # Important: use the `ZeroWidthEscape` fragment only if you are sure that
    #            writing this as raw text to the output will not introduce any
    #            cursor movements.
    return [
        ("[ZeroWidthEscape]", BEFORE_PROMPT),
        ("", " Search ADS: "),
        ("[ZeroWidthEscape]", AFTER_PROMPT),
    ]


class SuggestBracket(AutoSuggest):
    def get_suggestion(self, buffer, document):
        # Check if we have an open bracket.
        brackets = ("[]", "()")
        for left, right in brackets:
            if document.text.rfind(left) > document.text.rfind(right):
                return Suggestion(f"  {right}")


import ads.search

async def main(args):

    # The key bindings.
    kb = KeyBindings()

    @kb.add("c-c")
    @kb.add("c-q")
    def _(event):
        "Pressing Ctrl-Q or Ctrl-C will exit the user interface."
        event.app.exit()

    # The layout.
    # Create some history first. (Easy for testing.)
    history_path = os.path.expanduser("~/.ads/cli_history")
    os.makedirs(os.path.dirname(history_path), exist_ok=True)

    history = FileHistory(history_path)

    search_field = SearchToolbar(ignore_case=True) 

    input_field = TextArea(
        multiline=False, 
        prompt=get_prompt_text, 
        history=history,
        completer=OperatorCompleter(), 
        auto_suggest=AutoSuggestFromHistory(),
        complete_while_typing=True,
        search_field=search_field,
    )
    output_field = TextArea(
        style="class:output-field", 
        scrollbar=True, 
        height=10,
        #read_only=True,
        line_numbers=True)


    def accept(buff):                
        # TODO: If it's not a valid query, don't add it to history.
        q = input_field.text
        
        # do the search
        output_text = ""
        with ads.search.SearchQuery(q=q, rows=5) as query:
            for document in query:
                output_text += f"<i>{document.title[0][:50]}</i>, {document.author[0]}\n"

        # Add text to output buffer.
        output_field.buffer.document = Document(
            text=output_text, cursor_position=len(output_text)
        )
        #application.layout.focus(input_field)


    input_field.accept_handler = accept

    #@kb.add("<any>")
    #async def _(event):
    #    event.app.current_buffer.insert_text(event.data)
        
    body = FloatContainer(
        content=HSplit(
            [
                search_field,
                input_field,
                HorizontalLine(),
                output_field,
            ]
        ),
        floats=[
            Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(max_height=5, scroll_offset=1, display_arrows=True),
            )
        ],
    )


    application = Application(
        layout=Layout(body, focused_element=input_field),
        key_bindings=kb,
        #style=style,
        mouse_support=True,
        full_screen=False,
    )
    if args:
        input_field.text = " ".join(args)
        input_field.accept_handler(None)

    result = await application.run_async()


if __name__ == "__main__":
    import sys
    asyncio.get_event_loop().run_until_complete(main(sys.argv[1:]))
    """
    try:
        from asyncio import run
    except ImportError:
        asyncio.run_until_complete(main())
    else:
        asyncio.run(main())
    """


'''
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import ProgressBar

bottom_toolbar = HTML(' <b>[f]</b> Print "f" <b>[x]</b> Abort.')

from prompt_toolkit.application import in_terminal

def main():
        
    bindings = KeyBindings()

    @bindings.add("o")
    async def _(event):
        """
        Example of asyncio coroutine as a key binding.
        """
        try:
            #for i in range(5):
            async with in_terminal():
                print(event)
            #await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("Prompt terminated before we completed.")


    # application.
    with patch_stdout():
        prompt(
            "Type an animal: ",
            completer=OperatorCompleter(),
            complete_style=CompleteStyle.MULTI_COLUMN,
            key_bindings=bindings
        )


from prompt_toolkit.application import Application

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout

buffer1 = Buffer()  # Editable buffer.

root_container = VSplit([
    # One window that holds the BufferControl with the default buffer on
    # the left.
    Window(content=BufferControl(buffer=buffer1)),

    # A vertical line in the middle. We explicitly specify the width, to
    # make sure that the layout engine will not try to divide the whole
    # width by three for all these windows. The window will simply fill its
    # content by repeating this character.
    Window(width=1, char='|'),

    # Display the text 'Hello world' on the right.
    Window(content=FormattedTextControl(text='Hello world')),
])

layout = Layout(root_container)


kb = KeyBindings()

@kb.add('c-q')
def exit_(event):
    """
    Pressing Ctrl-Q will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `Application.run()` call.
    """
    event.app.exit()


async def main():
    # Define application.
    application = Application(layout=layout, key_bindings=kb, full_screen=True)

    result = await application.run_async()
    print(result)

asyncio.get_event_loop().run_until_complete(main())
'''