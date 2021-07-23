import ebooklib, os, shutil, argparse

from ebooklib import epub
from bs4 import BeautifulSoup
from fpdf import FPDF
from pdf2image import convert_from_path
from PIL import Image
import Book

def epub_to_obj(file_path):
    obj = Book()
    book = epub.read_epub(file_path)
    obj.title, obj.author = book.get_metadata('DC', 'title')[0][0], book.get_metadata('DC', 'creator')[0][0]

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        html = item.get_content()
        heading, content = parse_epub_chapter(html)
        ch = Book.Chapter(heading, content)
        obj.chapters.append(ch) 
    
    return obj
    
def parse_epub_chapter(raw_ch):
    blacklist = ['[document]','noscript','header','html','meta','head','input','script', 'h2']

    soup = BeautifulSoup(raw_ch, 'html.parser')
    text = soup.find_all(text=True)

    # heading
    heading = ''
    for item in text:
        if item.parent.name == 'h2':
            heading += '{} '.format(item)
            break
    # content
    content = ''
    for item in text:
        if item.parent.name not in blacklist:
            content += '{} '.format(item)

    return heading, content

def obj_to_html(obj):
    f = open('product.html', 'w')
    f.write('<!DOCTYPE html>' +
            '<html>' +
            '<head>' +
            '<title>' + obj.title + '</title>' +
            '</head>' +
            '<body>')

    f.write('<h1 id="title">' + obj.title + '</h1>')
    f.write('<h1 id="author">' + obj.author + '</h1>')

    chapters = obj.chapters
    for ch in chapters:
        f.write('<div>')
        f.write('<h2>' + ch.heading + '</h2>')
        f.write('<p>' + ch.content + '</p>')
        f.write('</div>')


    f.write('</body>' +
            '</html>')
    f.close()

def html_to_obj(path='product.html'):
    f = open(path, 'r')
    html = f.read()
    soup = BeautifulSoup(html, 'html.parser')

    obj = Book()
    obj.title = soup.find('h1', id='title').string
    obj.author = soup.find('h1', id='author').string
    
    chs = soup.find_all('div')
    
    for item in chs:
        h2 = item.find('h2')
        p = item.find('p')
        heading = h2.string
        content = p.string
        obj.chapters.append(Book.Chapter(heading, content))
    
    return obj

body_size = 8
heading_size = 15
title_size = 17.5
grey = 128
black = 0
body_type = 'Times'
title_type = 'Arial'

class TINY_BOOK(FPDF):
    def print_cover_page(self, title: str, author: str):
        self.add_page()
        self.ln(5)
        self.set_text_color(black)
        self.set_font(title_type, 'B', title_size)
        
        # title
        self.multi_cell(0, h=8, txt=title.upper(), align='L')
        # author
        self.set_text_color(grey)
        self.multi_cell(0, h=8, txt=author.upper(), align='L')
        self.set_text_color(black)

    # def header(self):
    #     pass

    def footer(self):
        # Position at 10mm from bottom
        self.set_y(-7)
        # Iowan bold 8
        self.set_font(body_type, 'B', body_size)
        self.set_text_color(grey)
        # Page number
        self.cell(0, h=0, txt=str(self.page_no()), align='C')

    def chapter_title(self, heading):
        self.set_text_color(black)
        # Iowan 12
        self.set_font(body_type, '', heading_size)
        # Title

        self.ln(5)
        self.multi_cell(0, h=5, txt=heading, align='C')
        # Line break

    def chapter_body(self, content):
        self.set_text_color(black)
        # Iowan 8
        self.set_font(body_type, '', body_size)
        # Output justified text
        self.multi_cell(0, 4, content, align='J')

    def print_chapter(self, heading, content):
        self.add_page()
        self.chapter_title(heading)
        self.chapter_body(content)

def obj_to_pdf(obj, out_name):
    pdf = TINY_BOOK(format=(75,150))
    pdf.set_title(obj.title)
    pdf.set_author(obj.author)
    pdf.set_margins(8, 10)
    pdf.set_auto_page_break(True, 11)
    
    # add cover
    pdf.print_cover_page(obj.title, obj.author)
    # add chapters
    for chapter in obj.chapters:
        pdf.print_chapter(chapter.heading, chapter.content)

    if pdf.page_no() % 2 != 0:
        pdf.print_cover_page('back page', '...')
    
    pdf.output(out_name, 'F')

def tiny_name(obj):
    name = obj.title
    return name.casefold().strip(' ').replace(' ', '-') + '.pdf'

def pdf_to_jpeg(filename: str):
    images = convert_from_path(filename, 600)
    dir_path = filename + '_images'

    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)

    for i, image in enumerate(images):
        image.save(dir_path + '/' + str(i), 'PNG')

def make_booklet(dir_path: str):
    pages = [int(file) for file in os.listdir(dir_path)]
    pages = sorted(pages)
    images = [Image.open(dir_path + '/' + str(page)) for page in pages]
    blank = Image.open('blank.jpg')
    N = len(images)
    if N%4 == 2:
        images.insert(1, blank.copy())
        images.insert(-1, blank.copy())
        N += 2
    
    booklet = []
    width, height = images[0].size
    booklet_width = width * 2
    booklet_height = height

    for i in range(int(N/2)):
        new_page = Image.new('RGB', (booklet_width, booklet_height))
        front, back = images[i], images[N-1-i]
        if i%2 == 0:
            # back first
            new_page.paste(back, (0, 0))
            new_page.paste(front, (int(booklet_width/2), 0))
        else:
            # front first
            new_page.paste(front, (0, 0))
            new_page.paste(back, (int(booklet_width/2), 0))

        booklet.append(new_page)
    booklet[0].save("out.pdf", save_all=True, append_images=booklet[1:])
    
def main(filename):
    print('Converting epub...')
    obj = epub_to_obj( filename +'.epub')
    obj_to_html(obj)
    print('Succesfully converted epub to html')
    print('Converting html...')
    obj = html_to_obj()
    obj_to_pdf(obj, filename + '.pdf')
    print('Succesfully converted html to pdf')
    print('making booklet')
    pdf_to_jpeg(filename + '.pdf')
    make_booklet(filename + '.pdf' + '_images')
    print('Done making booklet, ready to print')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args[1])
    