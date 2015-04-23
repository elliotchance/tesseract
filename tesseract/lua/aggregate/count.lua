local function function_count(value)
    if value ~= cjson.null and value ~= nil then
        redis.call('HINCRBY', 'count', 'col1', '1')
    end
end
