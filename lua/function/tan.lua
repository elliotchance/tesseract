local function function_tan(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'number' then
        return math.tan(value)
    end

    no_such_function('tan', value)
end
