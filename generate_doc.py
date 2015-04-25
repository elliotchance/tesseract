import markdown
import os
import StringIO
import re

def get_title(string, default_number):
    # The title starts with the index number.
    if re.match('^\d+_', string):
        return string.replace('_', ' ').split(' ', 1)

    # We must use the default number.
    return [str(default_number), string.replace('_', ' ')]

def index_folder(path, prefix, indent):
    out = ''
    number = 1
    mapping = {}
    for file in sorted(os.listdir(path)):
        if file == 'html':
            continue

        file_path = '%s/%s' % (path, file)
        if os.path.isdir(file_path):
            parts = get_title(file, number)
            title = '. '.join(parts)
            out += '%s%s%s<br />\n' % ('&nbsp;' * indent, prefix, title)
            folder, new_mappings = index_folder(file_path, prefix + '%s.' % parts[0], indent + 4)
            out += folder
            mapping.update(new_mappings)
            number += 1
        elif file.endswith('.md'):
            parts = get_title(file[:-3], number)
            title = '. '.join(parts)
            mapping[file_path] = (prefix + title).replace('.', '_').replace(' ', '_') + '.html'
            out += '%s<a href="%s">%s%s</a><br />\n' % ('&nbsp;' * indent, mapping[file_path], prefix, title)
            number += 1
    return out, mapping

def process_folder(path, depth, mapping):
    for file in os.listdir(path):
        file_path = '%s/%s' % (path, file)
        if os.path.isdir(file_path):
            process_folder(file_path, depth + 1, mapping)
        elif file.endswith('.md'):
            print('%s -> %s' % (file_path, mapping[file_path]))
            output = StringIO.StringIO()
            markdown.markdownFromFile(
                input=file_path,
                output=output,
                extensions=[
                    'markdown.extensions.tables',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.toc',
                    'markdown.extensions.fenced_code'
                ]
            )
            with open('doc/html/%s' % mapping[file_path], 'w') as html:
                style_css = "../style.css"
                html.write("""
<link rel="stylesheet" type="text/css" href="%s">
<table width="100%%" cellpadding="5" cellspacing="0">
  <tr>
    <td width="200" valign="top" style="border-right: 1px black solid" bgcolor="#ADD8E6">%s</td>
    <td valign="top"><div class="markdown-body">%s</div></td>
  </tr>
</table>
                """ % (style_css, index, output.getvalue()))

index, mappings = index_folder('doc', '', 0)
process_folder('doc', 0, mappings)
