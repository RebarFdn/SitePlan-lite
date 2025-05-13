from datetime import datetime
from starlette.routing import Mount
from shiny import App, module, ui, reactive, render
from config import DOCS_PATH, Path
import os


time_path:Path = DOCS_PATH / "time.txt" 

# Get the current time every second
@reactive.calc
def cur_time():
    reactive.invalidate_later(1)
    return datetime.now().strftime('%H:%M:%S')

# Write cur_time() to a file (every second)
@reactive.effect
def _():
    with open(time_path, "w") as f:
        f.write(cur_time())

#f = open(time_path, "w")  # Create the file if it doesn't exist


# Read and display whenever the file changes
@render.ui
@reactive.file_reader(time_path)
def time():
    with open(time_path) as f:
        return f"Current time {f.read()}"


@render.ui
def clock():
    return f"Current time: {cur_time()}"


@module.ui
def row_ui():
    return ui.layout_columns(
        ui.card(ui.input_text("text_in", "Enter text")),
        ui.card(ui.output_text("text_out")),
    )


@module.server
def row_server(input, output, session):
    @output
    @render.text
    def text_out():
        return f'You entered "{input.text_in()}"'

@module.ui
def card_ui():
    return ui.card(
        ui.card_header("Card header"),
        "Card body"
    )


app_ui = ui.page_fluid(
    ui.tags.link(href="/static/css/site.css", rel="stylesheet"),   
    row_ui("row_1"),
    card_ui("card_1"),
    ui.HTML(f"<p>The Time Is:  <strong>{ os.path.getmtime(time_path) }</strong>!</p>"),
    ui.div("Daddy &", ui.span("Son"), "!"),
    
    ui.tags.video(src="/static/vids/ekato.mp4", controls=True),
    ui.TagList(
    ui.div("Hello"),
    ui.span("World"),
    ui.a("Help", href="help.html"),
    ui.a({"href": "help.html"}, "Hello"),
    "!"
)
    
)


def server(input, output, session):
    row_server("row_1")
    row_server("row_2")
    
    
    


app = App(app_ui, server)

# combine apps ----
router = [
   
    Mount('/shiny', app=app)
]