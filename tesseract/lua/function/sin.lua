local function function_sin(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'number' then
        return math.sin(value)
    end

    no_such_function('sin', value)
end
