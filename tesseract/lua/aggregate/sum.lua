local function function_sum(group, value)
    if value ~= cjson.null and value ~= nil then
        redis.call('HINCRBY', 'count', group, tostring(value))
    end
end
