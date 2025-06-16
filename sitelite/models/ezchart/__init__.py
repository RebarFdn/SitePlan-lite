# ezchart
from pathlib import Path
from secrets import token_urlsafe

# Config
BASE_PATH = Path(__file__).resolve().parent
CHART_CSS = BASE_PATH / "apexcharts.css"
CHART_JS = BASE_PATH / "apexcharts.js"
 

def require(file_path:Path=None):
    if file_path.exists() and file_path.is_file():
        with open(file_path) as file:
            return file.read() 
    else:
        return None


class ezChart:
    """ """
    def __init__(self, options:dict=None):
        if options:
            self.options = options


    def chart(self):
        """Returns a html chart from the given data"""
        chart_str:str =""
        for i in  self.generate_chart():
           chart_str += i
        return  chart_str
    

    @property
    def head(self)-> str:
        return f"""<!DOCTYPE html><html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>ezChart </title>                                
                   
                    <style>{require(CHART_CSS)}</style>
                    <script>{require(CHART_JS)}</script>
                     
                </head>
                <body> 
                <input id="chart_token" type="text" name="chart_token" value="{token_urlsafe(32)}" hidden></input>
                """
    
    @property
    def foot(self)-> str:
        return """ </body></html>"""
    
    def chart_data(self, options:dict={}):
        if self.options:
            options = self.options
        
        
        
        data = f"""<script>
            const False = false
            const True = true
            var chart = new ApexCharts(document.querySelector("#chart"), {options});

            chart.render();
        
        </script>"""
        return data
    
    def generate_chart(self):
        """Generates an Apex Chart """
        yield self.head
        yield '<div id="chart"> <div id="responsive-chart"></div></div>'
        # chart script
        yield self.chart_data()
        yield self.foot

    
