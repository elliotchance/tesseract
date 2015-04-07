local function function_floor(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'number' then
        return math.floor(value)
    end

    no_such_function('floor', value)
end
