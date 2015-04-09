from tesseract.server import Server

import time

server = Server()

# 1_setup
print('Running 1_setup...')
start_time = time.time()
parser_time = 0
execute_time = 0
for iteration in xrange(0, 1):
    result = server.execute('DELETE FROM mytable')
    result = server.execute('INSERT INTO mytable {"id": 1}')
    parser_time += result.time['parser']
    execute_time += result.time['execute']
    assert result.success
elapsed = time.time() - start_time
print('  Total: %.3f seconds' % elapsed)
print('  Parser: %.3f seconds' % parser_time)
print('  Execute: %.3f seconds' % execute_time)

# 2_select_by_id
print('Running 2_select_by_id...')
start_time = time.time()
parser_time = 0
execute_time = 0
for iteration in xrange(0, 10000):
    result = server.execute('SELECT * FROM mytable WHERE id = 1')
    parser_time += result.time['parser']
    execute_time += result.time['execute']
    assert result.success
elapsed = time.time() - start_time
print('  Total: %.3f seconds' % elapsed)
print('  Parser: %.3f seconds' % parser_time)
print('  Execute: %.3f seconds' % execute_time)

