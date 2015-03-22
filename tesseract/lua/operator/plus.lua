local function operator_plus(left, right)
    -- If either value is null then the result is always null.
    if left == cjson.null or right == cjson.null then
        return cjson.null
    end

    -- We only allow the addition of numbers
    if type(left) ~= 'number' or type(right) ~= 'number' then
        no_such_operator(left, '+', right)
    end

    -- Let Lua handle converting string and numbers for normal addition.
    return left + right
end
