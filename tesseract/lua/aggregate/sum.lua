local function function_sum(group, value)
    -- A single null value means this group is now and forever null.
    if value == cjson.null or value == nil then
        redis.call('HSET', 'count', group, 'null')
    elseif redis.call('HGET', 'count', group) ~= 'null' then
        redis.call('HINCRBY', 'count', group, tostring(value))
    end
end
