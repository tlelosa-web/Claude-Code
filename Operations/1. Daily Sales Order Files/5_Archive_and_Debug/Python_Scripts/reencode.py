import codecs
with codecs.open('report_dump.txt', 'r', 'utf-16le') as f:
    text = f.read()
with codecs.open('report_output_utf8.txt', 'w', 'utf-8') as f:
    f.write(text)
