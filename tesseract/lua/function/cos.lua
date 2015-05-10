local function function_cos(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'number' then
        return math.cos(value)
    end

    no_such_function('cos', value)
end
