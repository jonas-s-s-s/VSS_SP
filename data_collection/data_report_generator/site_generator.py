from jinja2 import Environment, FileSystemLoader
import os
import shutil

def generate(db):
    env = Environment(loader=FileSystemLoader('templates'))

    #########################################
    # Prepare nav bar objects
    #########################################
    nav_items = [
        {'label': 'Home', 'href': 'index.html'},
        {'label': 'About', 'href': 'about.html'},
        {'label': 'Contact', 'href': 'contact.html'},
        {'label': 'Home', 'href': 'index.html'},
        {'label': 'About', 'href': 'about.html'},
        {'label': 'Contact', 'href': 'contact.html'},
        {'label': 'Home', 'href': 'index.html'},
        {'label': 'About', 'href': 'about.html'},
        {'label': 'Contact', 'href': 'contact.html'},
        {'label': 'Home', 'href': 'index.html'},
        {'label': 'About', 'href': 'about.html'},
        {'label': 'Contact', 'href': 'contact.html'},
        {'label': 'Home', 'href': 'index.html'},
        {'label': 'About', 'href': 'about.html'},
        {'label': 'Contact', 'href': 'contact.html'},
        {'label': 'Home', 'href': 'index.html'},
        {'label': 'About', 'href': 'about.html'},
        {'label': 'Contact', 'href': 'contact.html'},

    ]

    #########################################
    # Prepare page objects
    #########################################

    table_data = [
        {"date": "2023-01-01", "close": 45},
        {"date": "2023-02-01", "close": 50},
        {"date": "2023-03-01", "close": 55},
        {"date": "2023-04-01", "close": 50},
        {"date": "2023-05-01", "close": 45},
        {"date": "2023-06-01", "close": 50},
    ]


    pages = [
        {'template': 'index.html', 'output': 'index.html', 'context': {'title': 'Home', 'name': 'John', "table_data": table_data}},
    ]


    #########################################
    # Generate each page
    #########################################
    os.makedirs('output', exist_ok=True)
    for page in pages:
        template = env.get_template(page['template'])
        # Merge nav items into each page's context
        context = {**page['context'], 'nav': nav_items}
        rendered = template.render(**context)
        with open(f"output/{page['output']}", 'w') as f:
            f.write(rendered)

    #########################################
    # Copy the static assets
    #########################################
    shutil.copytree('static', 'output/static', dirs_exist_ok=True)