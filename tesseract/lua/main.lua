-- First thing is to convert all the incoming values from JSON to native.
-- Skipping the first two arguments that are not JSON and will always exist.
local args = {}
for i = 3, #ARGV do
    args[i] = cjson.decode(ARGV[i])
end

-- Get one page - at the moment this is the whole table.
local records = redis.call('HVALS', ARGV[1])

-- Iterate each record in the page.
local matches = {}
for i, data in ipairs(records) do
    -- Each row is stored as a JSON string and needs to be decoded before we can
    -- use it.
    local row = cjson.decode(data)

    -- Process the fields in the SELECT clause.
    local tuple = process_fields_in_select_clause(row)

    -- Test if the WHERE clause allows this record to be added to the result.
    if matches_where_clause(row) then
        table.insert(matches, tuple)
    end
end

-- The `matches` will be an array which Python can not decode on the other end
-- so we wrap it into an object.
return cjson.encode({result = matches})
