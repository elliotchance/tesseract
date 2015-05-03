local function function_min(group, value)
    -- A single null value means this group is now and forever null.
    if value == cjson.null or value == nil then
        redis.call('HSET', 'agg', group, 'null')
        return
    end

    if type(value) ~= 'number' then
        error('min() can only be used with null or numbers.')
    end

    local current_value = redis.call('HGET', 'agg', group)
    if current_value == 'null' then
        return
    end

    if current_value == false then
        redis.call('HSET', 'agg', group, tostring(value))
    elseif value < tonumber(current_value) then
        redis.call('HSET', 'agg', group, tostring(value))
    end
end

local function function_min_post(unique_group, group)
    return redis.call('HGET', 'agg', group)
end
