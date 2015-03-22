local function operator_minus(left, right)
    -- If either value is null then the result is always null.
    if left == cjson.null or right == cjson.null then
        return cjson.null
    end

    -- We only allow the subtraction of numbers
    if type(left) ~= 'number' or type(right) ~= 'number' then
        no_such_operator(left, '-', right)
    end

    return left - right
end
