local function operator_like(value, regex)
    -- If either value is null then the result is always null.
    if value == cjson.null or regex == cjson.null then
        return cjson.null
    end

    regex = '^' .. regex:gsub('%%', '.*') .. '$'
    return value:find(regex) ~= nil
end
