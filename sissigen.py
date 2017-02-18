#!venv/bin/python3

import markdown2
from jinja2 import Template, FileSystemLoader, Environment
import glob
import os
from bs4 import BeautifulSoup as bs, NavigableString
import shutil
import sys
import pkg_resources
import http.server
import socketserver

PORT = 8000
CONTENT_FOLDER = 'posts'
MAX_SUBTITLE = 200
PARSER = 'html.parser'
TEMPLATE_DIRECTORY = 'templates'
MAIN_TEMPLATE = 'main.html'
CONTENTS_TEMPLATE = 'contents.html'
OUTPUT = 'site'
STRUCTURE = 'structure'
STATIC = 'static'
INDEX = 'index.md'
sissis = {}

def sissi(func):
    sissis[func.__name__] = func


@sissi
def subtitle(item):
    """Return the first paragraph of an html string."""
    soup = bs(item['html'], PARSER)
    sub = soup.p.renderContents().decode('utf-8')
    if len(sub) > MAX_SUBTITLE:
        sub = sub[0:MAX_SUBTITLE-3] + '...'
    return sub


@sissi
def title(item):
    try:
        return title_from_html(item['html'])
    except AttributeError:
        # There is no title
        return title_from_filename(item['path'])


def title_from_html(html):
    """Return the title from a filename."""
    soup = bs(html, PARSER)
    title = soup.h1.renderContents().decode('utf-8')
    return title


def title_from_filename(path):
    _, filename = os.path.split(path)
    title, _ = os.path.splitext(filename)
    return title


def make_item(path):
    item = {'path': path,
            'content': read_file(path),
            'filename': title_from_filename(path),
            'output': os.path.join(OUTPUT,
                                    title_from_filename(path)+'.html')
            }
    item['html'] = to_html(item['content'])
    item['href'] = item['output']
    for key, val in sissis.items():
        item[key] = val(item)
    return item


def find_content(base_path):
    return glob.iglob(os.path.join(base_path, '*.md'))


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


def to_html(markdown):
    return markdown2.markdown(markdown)


def render(html, template):
    return template.render(html=html)


def make_contents(posts):
    return sorted(posts, key=lambda p: p['filename'], reverse=True)


def render_contents(lead, contents, template):
    return template.render(lead=lead, items=contents)


def copytree(src, dst):
    for item in os.listdir(src):
        this_src = os.path.join(src, item)
        this_dst = os.path.join(dst, item)
        if os.path.isdir(this_src):
            shutil.copytree(this_src, this_dst, False, None)
        else:
            shutil.copy2(this_src, this_dst)


def init():
    STRUCTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              STRUCTURE)
    copytree(STRUCTURE_DIR, '.')


def build():
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIRECTORY))
    TEMPLATE = env.get_template(MAIN_TEMPLATE)
    CONTENTS_LIST = env.get_template(CONTENTS_TEMPLATE)

    posts = []
    for post in find_content(CONTENT_FOLDER):
        print('Making post {}'.format(post))
        posts.append(make_item(post))
    print('Making contents.')
    lead = to_html(read_file(INDEX))
    contents = make_contents(posts)
    contents_page = render_contents(lead, contents, CONTENTS_LIST)

    print('Writing files.')
    if os.path.isdir(OUTPUT):
        shutil.rmtree(OUTPUT)
    os.mkdir(OUTPUT)
    for post in posts:
        with open(post['output'], 'w') as out:
            out.write(render(post['html'], TEMPLATE))
    with open('index.html', 'w') as out:
        out.write(render(contents_page, TEMPLATE))
    shutil.copytree(STATIC, os.path.join(OUTPUT, STATIC))


def preview():
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), Handler)
    print("serving at port", PORT)
    httpd.serve_forever()


def main(arg=None):
    if not arg:
        arg = sys.argv[1]
    commands = {'init': init,
                'build': build,
                'preview': preview,
                }
    if arg in commands.keys():
        commands[arg]()
    else:
        raise ValueError('Unrecognised command.')
