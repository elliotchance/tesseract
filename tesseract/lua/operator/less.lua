local function operator_less(left, right)
    -- If either value is null then the result is always null.
    if left == cjson.null or right == cjson.null then
        return cjson.null
    end

    -- We only allow the comparison of numbers.
    if type(left) ~= 'number' and type(right) ~= 'string' then
        no_such_operator(left, '<', right)
    end

    return left < right
end
