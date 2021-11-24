
import os
from prompt_toolkit import document
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.formatted_text.base import FormattedText
from prompt_toolkit.layout.margins import Margin, NumberedMargin
from prompt_toolkit.shortcuts import CompleteStyle, prompt

from prompt_toolkit.layout.containers import (
    HSplit,
    VerticalAlign,
    VSplit,
    Window,
    WindowAlign,
)

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory, AutoSuggest, Suggestion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.widgets.menus import MenuContainer


from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession

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
from prompt_toolkit.widgets import SearchToolbar, TextArea, Box

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

from prompt_toolkit.layout import (
    CompletionsMenu,
    Float,
    Container,
    FloatContainer,
    HSplit,
    Layout,
    ScrollablePane,
    VSplit,
)
from prompt_toolkit.widgets import Frame, Label, TextArea, Checkbox, Label

from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous




BEFORE_PROMPT = "\033]133;A\a"
AFTER_PROMPT = "\033]133;B\a"
BEFORE_OUTPUT = "\033]133;C\a"
AFTER_OUTPUT = (
    "\033]133;D;{command_status}\a"  # command_status is the command status, 0-255
)

class PaddedMargin(Margin):

    def get_width(self, get_ui_content):
        return 7


    def create_margin(self, window_render_info, width, height):
        return []


def get_prompt_text():
    # Generate the text fragments for the prompt.
    # Important: use the `ZeroWidthEscape` fragment only if you are sure that
    #            writing this as raw text to the output will not introduce any
    #            cursor movements.
    return [
        ("[ZeroWidthEscape]", BEFORE_PROMPT),
        ("", " Search NASA/ADS: "),
        ("[ZeroWidthEscape]", AFTER_PROMPT),
    ]

from prompt_toolkit.styles.pygments import style_from_pygments_cls
from pygments.styles import get_style_by_name
from prompt_toolkit.widgets import Box, Button, Frame
style = style_from_pygments_cls(get_style_by_name('monokai'))

from prompt_toolkit.layout.dimension import LayoutDimension as D

style = Style.from_dict({
     '.focused': 'underline',
})

abstract = """We report new precision measurements of the properties of our Galaxy's supermassive black hole. Based on astrometric (1995-2007) and radial velocity (RV; 2000-2007) measurements from the W. M. Keck 10 m telescopes, a fully unconstrained Keplerian orbit for the short-period star S0-2 provides values for the distance (R<SUB>0</SUB>) of 8.0 +/- 0.6 kpc, the enclosed mass (M<SUB>bh</SUB>) of 4.1 +/- 0.6 × 10<SUP>6</SUP> M<SUB>⊙</SUB>, and the black hole's RV, which is consistent with zero with 30 km s<SUP>-1</SUP> uncertainty. If the black hole is assumed to be at rest with respect to the Galaxy (e.g., has no massive companion to induce motion), we can further constrain the fit, obtaining R<SUB>0</SUB> = 8.4 +/- 0.4 kpc and M<SUB>bh</SUB> = 4.5 +/- 0.4 × 10<SUP>6</SUP> M<SUB>⊙</SUB>. More complex models constrain the extended dark mass distribution to be less than 3-4 × 10<SUP>5</SUP> M<SUB>⊙</SUB> within 0.01 pc, ~100 times higher than predictions from stellar and stellar remnant models. For all models, we identify transient astrometric shifts from source confusion (up to 5 times the astrometric error) and the assumptions regarding the black hole's radial motion as previously unrecognized limitations on orbital accuracy and the usefulness of fainter stars. Future astrometric and RV observations will remedy these effects. Our estimates of R<SUB>0</SUB> and the Galaxy's local rotation speed, which it is derived from combining R<SUB>0</SUB> with the apparent proper motion of Sgr A*, (θ<SUB>0</SUB> = 229 +/- 18 km s<SUP>-1</SUP>), are compatible with measurements made using other methods. The increased black hole mass found in this study, compared to that determined using projected mass estimators, implies a longer period for the innermost stable orbit, longer resonant relaxation timescales for stars in the vicinity of the black hole and a better agreement with the M<SUB>bh</SUB>-σ relation."""

from prompt_toolkit.filters import Condition


def get_statusbar_text():
    return [
        ("class:status", "ADS client 1.0.1 (Python 3.6.4) - github.com/andycasey/ads - andrew.casey@monash.edu"),
    ]



def main(args):

    # The key bindings.
    kb = KeyBindings()

    @kb.add("c-c")
    @kb.add("c-q")
    def _(event):
        "Pressing Ctrl-Q or Ctrl-C will exit the user interface."
        event.app.exit()





    #kb.add('s-left')(focus_previous)

    # The layout.
    # Create some history first. (Easy for testing.)
    history_path = os.path.expanduser("~/.ads/cli_history")
    os.makedirs(os.path.dirname(history_path), exist_ok=True)

    history = FileHistory(history_path)

    search_field = SearchToolbar(ignore_case=True) 

    is_expanded = -1


    input_field = TextArea(
        multiline=False, 
        prompt=get_prompt_text, 
        history=history,
        #completer=OperatorCompleter(), 
        auto_suggest=AutoSuggestFromHistory(),
        complete_while_typing=True,
        search_field=search_field,
       # on_completions_changed = foo
    )
    def foo(_):
        nonlocal is_expanded
        is_expanded += 1
        is_expanded = (is_expanded % 2)
        
    #input_field.accept_handler = foo

    def get_bibcode(index):
        return f"2022MNRAS.509..844T{index}"


    def show_document(i):

        kb2 = KeyBindings()

        @kb2.add("enter")
        @kb2.add("space")
        def _(event):
            nonlocal is_expanded
            if is_expanded == i:
                # hide.
                is_expanded = -1
            else:
                is_expanded = i


        bibcode = FormattedTextControl(lambda: get_bibcode(i), focusable=True, key_bindings=kb2)

        foo = [    
                VSplit([          
                    TextArea(text=f" {i:.0f}. ", width=7, dont_extend_width=True, focusable=False),
                    Window(bibcode),
                    Window(FormattedTextControl(text="2022/01", focusable=False)),
                    Window(FormattedTextControl(text="3 citations", focusable=False)),
                    Window(FormattedTextControl(text="54 reads", focusable=False))
                ], height=1),
                Window(
                    FormattedTextControl(HTML("\n<b>Identifying resonances of the Galactic bar in Gaia DR2: II. Clues from angle space</b>\nAuthor et al.\n")),
                    left_margins=[PaddedMargin()],
                    dont_extend_height=True,
                ),
                ConditionalContainer(
                    content=HSplit([
                        Window(
                            FormattedTextControl(HTML(abstract+"\n"), focusable=False),
                            left_margins=[PaddedMargin()],
                            right_margins=[PaddedMargin()],
                            wrap_lines=True,
                            dont_extend_height=True,                      
                        ),
                        VSplit([
                            Window(width=7),
                            Button("Read", width=8),
                            Window(width=3),
                            Button("Cite", width=8),
                            Window(width=3),
                            Button("View in ADS", width=15),
                        ]),
                        Window(height=1)
                    ]),
                    filter=Condition(lambda: is_expanded == i),
                ),
            ]
        return foo

        
    kb.add('s-left')(focus_previous)
    kb.add('s-right')(focus_next)

    kb.add('down', is_global=True)(focus_next)
    kb.add('up', is_global=True)(focus_previous)


    body = FloatContainer(
        content=HSplit(
            [
                search_field,
                input_field,
                HorizontalLine(),
                Window(FormattedTextControl(HTML("Showing first 10 of <b>83,231</b> results for <b>title:()</b>\n"))),
                ScrollablePane(content=HSplit([
                    *show_document(1),
                    *show_document(2),
                    *show_document(3),
                    *show_document(4),
                    *show_document(5),
                    *show_document(6),
                    *show_document(7),
                    *show_document(8),
                    *show_document(9),
                    *show_document(10),
                ])),
                Window(
                    content=FormattedTextControl(get_statusbar_text),
                    height=D.exact(1),
                    style="class:status",
                ),                
            ],
            align=VerticalAlign.TOP,
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
        style=style,
        mouse_support=True,
        full_screen=True,
    )
    if args:
        input_field.text = " ".join(args)
        input_field.accept_handler(None)

    result = application.run()

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
