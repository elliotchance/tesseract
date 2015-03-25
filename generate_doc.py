import markdown
import os
import StringIO

def index_folder(path, prefix, indent):
    out = ''
    for file in os.listdir(path):
        file_path = '%s/%s' % (path, file)
        if os.path.isdir(file_path):
            parts = file.replace('_', ' ').split(' ', 2)
            title = prefix + '. '.join(parts)
            out += '%s%s%s<br />\n' % ('&nbsp;' * indent, prefix, title)
            out += index_folder(file_path, '%s.' % parts[0], indent + 4)
        elif file.endswith('.md'):
            title = '. '.join(file[:-3].replace('_', ' ').split(' ', 2))
            out += '%s<a href="%s.html">%s%s</a><br />\n' % ('&nbsp;' * indent, file[:-3], prefix, title)
    return out

def process_folder(path):
    for file in os.listdir(path):
        file_path = '%s/%s' % (path, file)
        if os.path.isdir(file_path):
            process_folder(file_path)
        elif file.endswith('.md'):
            print(file_path)
            output = StringIO.StringIO()
            markdown.markdownFromFile(
                input=file_path,
                output=output
            )
            with open('%shtml' % file_path[:-2], 'w') as html:
                html.write("""
<link rel="stylesheet" type="text/css" href="./codehilite.css">
<table width="100%%">
  <tr>
    <td width="200" valign="top">%s</td>
    <td valign="top">%s</td>
  </tr>
</table>
                """ % (index, output.getvalue()))




index = index_folder('doc', '', 0)

process_folder('doc')
