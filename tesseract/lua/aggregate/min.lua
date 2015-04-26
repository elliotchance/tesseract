local function function_min(group, value)
    -- A single null value means this group is now and forever null.
    if value == cjson.null or value == nil then
        redis.call('HSET', 'agg', group, 'null')
    else
        local current_value = redis.call('HGET', 'agg', group)
        if tonumber(current_value) == nil then
            redis.call('HSET', 'agg', group, tostring(value))
        elseif (current_value ~= 'null' and value < tonumber(current_value)) then
            redis.call('HSET', 'agg', group, tostring(value))
        end
    end
end

local function function_min_post(unique_group, group)
    -- if tonumber(redis.call('HGET', 'agg', group)) == nil then
    --     return cjson.null
    -- end

    return redis.call('HGET', 'agg', group)
end
