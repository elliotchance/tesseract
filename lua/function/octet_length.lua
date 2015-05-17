local function function_octet_length(value)
    if value == cjson.null then
        return value
    end

    if type(value) == 'string' then
        return value:len()
    end

    no_such_function('octet_length', value)
end
