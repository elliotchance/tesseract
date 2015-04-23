local function function_count(value)
    redis.call('HINCRBY', 'count', cjson.encode(value), '1')
end
