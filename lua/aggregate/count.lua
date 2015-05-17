local function function_count(group, value)
    if value ~= cjson.null and value ~= nil then
        redis.call('HINCRBY', 'agg', group, '1')
    end
end

--noinspection UnusedDef
local function function_count_post(unique_group, group)
    return redis.call('HGET', 'agg', group)
end
