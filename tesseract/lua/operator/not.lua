local function operator_not(value)
    -- NOT with null is always null.
    if value == cjson.null then
        return cjson.null
    end

    -- We only allow the NOT of booleans
    if type(value) ~= 'boolean' then
        no_such_mono_operator('NOT', value)
    end

    return not value
end
