local function operator_or(left, right)
    -- If either value is null then the result is always null.
    if left == nil or right == nil or
            left == cjson.null or right == cjson.null then
        return cjson.null
    end

    -- We only allow the AND of booleans
    if type(left) ~= 'boolean' or type(right) ~= 'boolean' then
        no_such_operator(left, 'OR', right)
    end

    return left or right
end
