local function function_sum(group, value)
    -- A single null value means this group is now and forever null.
    if value == cjson.null or value == nil then
        redis.call('HSET', 'agg', group, 'null')
        return
    end

    if type(value) ~= 'number' then
        error('sum() can only be used with null or numbers.')
    end

    if redis.call('HGET', 'agg', group) ~= 'null' then
        redis.call('HINCRBY', 'agg', group, tostring(value))
    end
end

--noinspection UnusedDef
local function function_sum_post(unique_group, group)
    return redis.call('HGET', 'agg', group)
end
