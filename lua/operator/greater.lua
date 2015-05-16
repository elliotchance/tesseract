local function operator_greater(left, right)
    -- If either value is null then the result is always null.
    if left == nil or right == nil or
            left == cjson.null or right == cjson.null then
        return cjson.null
    end

    -- Comparing different types is not allowed.
    if type(left) ~= type(right) then
        no_such_operator(left, '>', right)
    end

    -- We only allow the comparison of numbers.
    if type(left) ~= 'number' and type(right) ~= 'string' then
        no_such_operator(left, '>', right)
    end

    return left > right
end
