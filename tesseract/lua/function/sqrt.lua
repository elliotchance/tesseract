local function function_sqrt(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'number' then
        if value < 0 then
            error(string.format('Cannot calculate square root with negative number %s', value))
        end

        return math.sqrt(value)
    end

    no_such_function('sqrt', value)
end
