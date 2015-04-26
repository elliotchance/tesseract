local function function_max(group, value)
    -- A single null value means this group is now and forever null.
    if value == cjson.null or value == nil then
        redis.call('HSET', 'agg', group, 'null')
    else
        if type(value) ~= 'number' then
            error('max() can only be used with null or numbers.')
        end

        local current_value = redis.call('HGET', 'agg', group)
        if tonumber(current_value) == nil then
            redis.call('HSET', 'agg', group, tostring(value))
        elseif (current_value ~= 'null' and value > tonumber(current_value)) then
            redis.call('HSET', 'agg', group, tostring(value))
        end
    end
end

local function function_max_post(unique_group, group)
    return redis.call('HGET', 'agg', group)
end
