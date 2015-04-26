local function function_avg(group, value)
    -- A single null value means this group is now and forever null.
    if value == cjson.null or value == nil then
        redis.call('HSET', 'agg', group, 'null')
    elseif redis.call('HGET', 'agg', group) ~= 'null' then
        redis.call('HINCRBY', 'agg', group, tostring(value))
    end
end

local function function_avg_post(unique_group, group)
    return redis.call('HGET', 'agg', group) / redis.call('HGET', 'group', unique_group)
end
