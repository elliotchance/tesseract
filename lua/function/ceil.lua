local function function_ceil(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'number' then
        return math.ceil(value)
    end

    no_such_function('ceil', value)
end
