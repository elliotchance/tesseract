local function operator_ilike(value, regex)
    -- If either value is null then the result is always null.
    if value == nil or regex == nil or
            value == cjson.null or regex == cjson.null then
        return cjson.null
    end

    -- We only allow strings to be processed
    if type(value) ~= 'string' or type(regex) ~= 'string' then
        no_such_operator(value, 'ILIKE', regex)
    end

    regex = '^' .. regex:gsub('%%', '.*') .. '$'
    return value:lower():find(regex:lower()) ~= nil
end
