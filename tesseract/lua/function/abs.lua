local function function_abs(value)
    if value == cjson.null then
        return value
    end

    return math.abs(value)
end
