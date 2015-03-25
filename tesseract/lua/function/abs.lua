local function function_abs(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'number' then
        return math.abs(value)
    end

    no_such_function('abs', value)
end
