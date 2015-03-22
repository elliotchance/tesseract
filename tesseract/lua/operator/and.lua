local function operator_and(left, right)
    -- If either value is null then the result is always null.
    if left == cjson.null or right == cjson.null then
        return cjson.null
    end

    -- We only allow the AND of booleans
    if type(left) ~= 'boolean' or type(right) ~= 'boolean' then
        no_such_operator(left, 'AND', right)
    end

    return left and right
end
