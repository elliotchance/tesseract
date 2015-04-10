local function function_char_length(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'string' then
        return value:len()
    end

    no_such_function('char_length', value)
end
