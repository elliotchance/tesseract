from tesseract.server import Server
import sys
from tesseract.sql.expressions import Expression

# Start up the server.
server = Server()

# Present an unlimited amount of prompts.
while True:
    sys.stdout.write('tesseract> ')

    # Read a single line (the SQL)
    sql = sys.stdin.readline()

    # Does the person want to bail out at this point?
    if sql == 'exit\n':
        # Friendly goodbye.
        print("Bye.")
        break

    # Execute the SQL.
    result = server.execute(sql)

    if not result.success:
        # There was something wrong, lets print out the error.
        print("Error: %s" % result.error)
    else:
        # The result was successful. We can now print out the result rows.
        print('[')
        first = True
        for row in result.data:
            print("  %s%s" % (Expression.to_sql(row), ',' if first else ''))
            first = False
        print(']')

    # Print a blank line to give us some space between each prompt.
    print()
