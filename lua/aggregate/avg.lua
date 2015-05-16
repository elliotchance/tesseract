local function function_avg(group, value)
    -- A single null value means this group is now and forever null.
    if value == cjson.null or value == nil then
        redis.call('HSET', 'agg', group, 'null')
        return
    end

    if type(value) ~= 'number' then
        error('avg() can only be used with null or numbers.')
    end

    if redis.call('HGET', 'agg', group) ~= 'null' then
        redis.call('HINCRBY', 'agg', group, tostring(value))
    end
end

local function function_avg_post(unique_group, group)
    local total = tonumber(redis.call('HGET', 'agg', group))
    local count = tonumber(redis.call('HGET', 'group', unique_group))
    if total == nil then
        return cjson.null
    end
    return total / count
end
