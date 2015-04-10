local function function_bit_length(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'string' then
        return value:len() * 8
    end

    no_such_function('bit_length', value)
end
